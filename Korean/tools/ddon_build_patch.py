#!/usr/bin/env python3
"""
DDON 한국어 패치 증분 빌드 (r20 -> r21 방식)

하는 일
1. 기준 CSV와 새 CSV를 비교해 바뀐 문장이 들어 있는 ARC만 다시 패킹한다.
   (Arrowgene packGmd와 같은 매칭 규칙: Key+ReadIndex > Key > ReadIndex)
2. 새 CSV에 쓰였지만 폰트(GFD)에 없는 한글을 찾아,
   기존 폰트는 그대로 두고 빈 일본어 한자 슬롯에 새 글자만 추가한다.
   - 글자 렌더링은 ddon_font_builder_final_v1.py와 같은 방식(맑은 고딕 Bold 29, Y+3)
   - 텍스처는 바뀐 4x4 블록만 BC3로 다시 인코딩하고 나머지 바이트는 그대로 둔다.
   - GFD는 코드포인트 순으로 다시 정렬한다.
3. 기준 패키지(r20)를 복사해 바뀐 파일만 교체한 새 패키지를 만든다.
   manifest / SHA256SUMS / VERSION / README를 갱신하므로 기존 설치기로 바로 업그레이드할 수 있다.
4. 결과를 다시 읽어 검증하고 build_report.txt와 새 글자 미리보기 PNG를 남긴다.

필요: Python 3.10+, pillow, pycryptodome
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import shutil
import struct
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow가 필요합니다: py -3.10 -m pip install pillow")
try:
    from Crypto.Cipher import Blowfish
except ImportError:
    sys.exit("pycryptodome이 필요합니다: py -3.10 -m pip install pycryptodome")

# ---------------------------------------------------------------- ARC (ARCC)
ARC_KEY = b"ABB(DF2I8[{Y-oS_CCMy(@<}qR}WYX11M)w[5V.~CbjwM5q<F1Iab+-"
_BF = Blowfish.new(ARC_KEY, Blowfish.MODE_ECB)
GMD_CRC = 0x242BB29A
GFD_CRC = 0x2D462600
TEX_CRC = 0x241F5DEB


def _swap32(b: bytes) -> bytes:
    a = bytearray(b)
    for i in range(0, len(a) - len(a) % 4, 4):
        a[i:i + 4] = a[i:i + 4][::-1]
    return bytes(a)


def bf_decrypt(b: bytes) -> bytes:
    n = len(b) - len(b) % 8
    return _swap32(_BF.decrypt(_swap32(b[:n]))) + b[n:]


def bf_encrypt(b: bytes) -> bytes:
    if len(b) % 8:
        b = b + b"\0" * (8 - len(b) % 8)
    return _swap32(_BF.encrypt(_swap32(b)))


class Arc:
    def __init__(self, data: bytes):
        self.magic = data[:4]
        mid, cnt = struct.unpack_from("<HH", data, 4)
        if self.magic not in (b"ARC\0", b"ARCC") or mid != 7:
            raise ValueError(f"지원하지 않는 ARC: {self.magic!r} {mid}")
        self.cyph = self.magic == b"ARCC"
        self.entries = []
        for i in range(cnt):
            e = data[8 + i * 80: 8 + i * 80 + 80]
            if self.cyph:
                e = bf_decrypt(e)
            name = e[:64].split(b"\0")[0].decode("utf-8")
            crc, csz, flags, off = struct.unpack_from("<IIII", e, 64)
            self.entries.append(dict(name=name, crc=crc, flags=flags,
                                     raw=data[off:off + csz], off=off, new=None))
        self.data_start = min((x["off"] for x in self.entries), default=0x8000)

    def read(self, i: int) -> bytes:
        e = self.entries[i]
        if e["new"] is not None:
            return e["new"]
        raw = bf_decrypt(e["raw"]) if self.cyph else e["raw"]
        size = e["flags"] & ((1 << 29) - 1)
        out = zlib.decompressobj().decompress(raw)
        if len(out) != size:
            raise ValueError(f"압축 해제 크기 불일치: {e['name']}")
        return out

    def find(self, crc: int, name: str | None = None) -> list[int]:
        return [i for i, e in enumerate(self.entries)
                if e["crc"] == crc and (name is None or e["name"].lower() == name.lower())]

    def replace(self, i: int, data: bytes) -> None:
        self.entries[i]["new"] = data

    def save(self) -> bytes:
        cnt = len(self.entries)
        if 8 + cnt * 80 > self.data_start:
            raise ValueError("ARC 인덱스 공간 부족")
        out = bytearray(self.data_start)
        out[0:8] = self.magic + struct.pack("<HH", 7, cnt)
        pos = self.data_start
        blobs = []
        for i, e in enumerate(self.entries):
            if e["new"] is None:
                raw, flags = e["raw"], e["flags"]
            else:
                comp = zlib.compress(e["new"], 9)
                raw = bf_encrypt(comp) if self.cyph else comp
                flags = (e["flags"] & ~((1 << 29) - 1)) | len(e["new"])
            ent = bytearray(80)
            nb = e["name"].encode("utf-8")
            ent[:len(nb)] = nb
            struct.pack_into("<IIII", ent, 64, e["crc"], len(raw), flags, pos)
            if self.cyph:
                ent = bf_encrypt(bytes(ent))
            out[8 + i * 80: 8 + i * 80 + 80] = ent
            blobs.append(raw)
            pos += len(raw)
        return bytes(out) + b"".join(blobs)


# ---------------------------------------------------------------- GMD
class Gmd:
    def __init__(self, b: bytes):
        if b[:4] != b"GMD\0":
            raise ValueError("GMD 아님")
        self.b = b
        kc, sc, ks, ss, sl = struct.unpack_from("<5I", b, 20)
        p = 40 + sl + 1
        if kc:
            p += kc * 20 + 256 * 4
        keys = []
        for _ in range(kc):
            e = b.index(b"\0", p)
            keys.append(b[p:e].decode("utf-8"))
            p = e + 1
        self.str_start = p
        msgs = []
        for _ in range(sc):
            e = b.index(b"\0", p)
            msgs.append(b[p:e].decode("utf-8"))
            p = e + 1
        self.tail = b[p:]
        self.keys, self.msgs = keys, msgs

    def save(self) -> bytes:
        body = b"".join(m.encode("utf-8") + b"\0" for m in self.msgs)
        head = bytearray(self.b[:self.str_start])
        struct.pack_into("<I", head, 32, len(body))
        return bytes(head) + body + self.tail


# ---------------------------------------------------------------- CSV
def read_csv(path: Path) -> list[list[str]]:
    text = path.read_bytes().decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text, newline="")))


def norm(p: str) -> str:
    return p.replace("/", "\\").lower().lstrip("\\")


def is_hangul(cp: int) -> bool:
    return 0xAC00 <= cp <= 0xD7A3


def is_cjk(cp: int) -> bool:
    return 0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF


def apply_csv_to_gmd(g: Gmd, rows: list[list[str]]) -> int:
    changed = 0
    for ri in range(len(g.msgs)):
        key = g.keys[ri] if ri < len(g.keys) else ""
        km = [r for r in rows if key and r[1] == key]
        im = [r for r in rows if not (key and r[1] == key) and r[7] == str(ri)]
        m = next((r for r in km if r[7] == str(ri)), None) or (km[0] if km else None) or (im[0] if im else None)
        if m is None or not m[3]:
            continue
        if g.msgs[ri] != m[3]:
            g.msgs[ri] = m[3]
            changed += 1
    return changed


# ---------------------------------------------------------------- BC3
def dds_from_bc3(w: int, h: int, data: bytes) -> bytes:
    hdr = struct.pack("<4sIIIIIII44sII4s20sIIIII", b"DDS ", 124, 0x81007, h, w,
                      len(data), 0, 1, b"\0" * 44, 32, 4, b"DXT5",
                      b"\0" * 20, 0x1000, 0, 0, 0, 0)
    return hdr + data


def rgb565(c):
    return ((c[0] >> 3) << 11) | ((c[1] >> 2) << 5) | (c[2] >> 3)


def expand565(v):
    r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def encode_bc3_block(px: list[tuple[int, int, int, int]]) -> bytes:
    # alpha
    al = [p[3] for p in px]
    a0, a1 = max(al), min(al)
    if a0 == a1:
        ablk = bytes([a0, a1]) + b"\0" * 6
    else:
        pal = [a0, a1] + [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)]
        bits = 0
        for n, a in enumerate(al):
            idx = min(range(8), key=lambda k: abs(pal[k] - a))
            bits |= idx << (3 * n)
        ablk = bytes([a0, a1]) + bits.to_bytes(6, "little")
    # color: 가장 멀리 떨어진 두 픽셀을 끝점으로 사용
    cols = [p[:3] for p in px]
    best, e0, e1 = -1, cols[0], cols[0]
    uniq = list(set(cols))
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            d = sum((uniq[i][k] - uniq[j][k]) ** 2 for k in range(3))
            if d > best:
                best, e0, e1 = d, uniq[i], uniq[j]
    c0, c1 = rgb565(e0), rgb565(e1)
    if c0 < c1:
        c0, c1 = c1, c0
    if c0 == c1:
        return ablk + struct.pack("<HHI", c0, c1, 0)
    p0, p1 = expand565(c0), expand565(c1)
    pal = [p0, p1,
           tuple((2 * p0[k] + p1[k]) // 3 for k in range(3)),
           tuple((p0[k] + 2 * p1[k]) // 3 for k in range(3))]
    bits = 0
    for n, c in enumerate(cols):
        idx = min(range(4), key=lambda q: sum((pal[q][k] - c[k]) ** 2 for k in range(3)))
        bits |= idx << (2 * n)
    return ablk + struct.pack("<HHI", c0, c1, bits)


def patch_bc3(data: bytearray, w: int, before: Image.Image, after: Image.Image) -> int:
    bw = w // 4
    a, b = before.tobytes(), after.tobytes()
    stride = w * 4
    count = 0
    for by in range(after.height // 4):
        for bx in range(bw):
            diff = False
            for yy in range(4):
                o = (by * 4 + yy) * stride + bx * 16
                if a[o:o + 16] != b[o:o + 16]:
                    diff = True
                    break
            if not diff:
                continue
            px = []
            for yy in range(4):
                o = (by * 4 + yy) * stride + bx * 16
                for xx in range(4):
                    q = o + xx * 4
                    px.append(tuple(b[q:q + 4]))
            off = (by * bw + bx) * 16
            data[off:off + 16] = encode_bc3_block(px)
            count += 1
    return count


# ---------------------------------------------------------------- 폰트 (원래 빌더와 같은 규칙)
def decode_record(index: int, offset: int, raw: bytes) -> dict:
    cp, pxp, pxy, wr, hr, adv, flags = struct.unpack("<I6H", raw)
    page = pxp & 0xFF
    x = (pxp >> 8) | ((pxy & 0x0003) << 8)
    y_base = ((pxy >> 8) << 4) | ((pxy & 0x00F0) >> 4)
    vo = hr >> 8
    return dict(index=index, offset=offset, codepoint=cp, page=page, x=x, y_base=y_base,
                vertical_offset=vo, y_bitmap=y_base + vo,
                width=max(1, int(round(wr / 256.0))), height=max(1, int(round((hr & 0xFF) / 4.0))),
                advance=adv)


def detect_colors(image: Image.Image):
    getter = getattr(image, "get_flattened_data", None) or image.getdata
    ranked = Counter(getter()).most_common(64)
    background, foreground = ranked[0][0], None
    for color, _ in ranked[1:]:
        r, g, b, a = color
        if a > 0 and color != background and max(r, g, b) >= 128 and g >= r and g >= b:
            foreground = color
            break
    return background, foreground or (123, 255, 123, 255)


def render_glyph(image, glyph, char, font_path, font_size, x_off, y_off, bg, fg):
    draw = ImageDraw.Draw(image)
    x, yb, w, h = glyph["x"], glyph["y_bitmap"], glyph["width"], glyph["height"]
    top = glyph["y_base"]
    draw.rectangle((x, top, min(image.width - 1, x + w - 1),
                    min(image.height - 1, top + h + glyph["vertical_offset"] + 1)), fill=bg)
    size = font_size
    while size >= 8:
        font = ImageFont.truetype(str(font_path), size=size)
        bbox = font.getbbox(char)
        if bbox[2] - bbox[0] <= max(1, w - 2) and bbox[3] - bbox[1] <= max(1, h - 2):
            break
        size -= 1
    else:
        raise ValueError(f"글자 {char}를 슬롯에 맞출 수 없음")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x + (w - tw) // 2 - bbox[0] + x_off, yb + (h - th) // 2 - bbox[1] + y_off),
              char, font=font, fill=fg)
    return size


def sha(p: Path | bytes) -> str:
    h = hashlib.sha256(p if isinstance(p, bytes) else p.read_bytes())
    return h.hexdigest().upper()


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-package", required=True)
    ap.add_argument("--base-csv", required=True)
    ap.add_argument("--new-csv", required=True)
    ap.add_argument("--font", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--font-size", type=int, default=29)
    ap.add_argument("--x-offset", type=int, default=0)
    ap.add_argument("--y-offset", type=int, default=3)
    ap.add_argument("--pages", default="0,1,2,3,4,5,6,7,8")
    ap.add_argument("--readme-note", default="")
    ap.add_argument("--rerender-hangul", action="store_true", help="이미 등록된 한글 글자도 --font 로 전부 다시 그림")
    ap.add_argument("--readme-file", default="", help="README_KO.txt를 이 파일 내용으로 통째로 교체")
    ap.add_argument("--game-dir", default="", help="기준 패키지에 없는 ARC를 읽어 올 게임 폴더(원본 파일)")
    ap.add_argument("--tex-patch", default="", help="텍스처 교체 목록 JSON (arc, tex, png)")
    a = ap.parse_args()

    base_pkg, out_pkg = Path(a.base_package), Path(a.out)
    font_path = Path(a.font)
    for p in (base_pkg / "package_manifest.json", Path(a.base_csv), Path(a.new_csv), font_path):
        if not p.exists():
            print(f"[오류] 파일이 없습니다: {p}")
            return 2
    if out_pkg.exists():
        print(f"[오류] 출력 폴더가 이미 있습니다. 지우거나 이름을 바꾼 뒤 다시 실행하세요: {out_pkg}")
        return 2
    report: list[str] = [f"DDON 한국어 패치 빌드 {a.version}", f"생성: {dt.datetime.now().isoformat(timespec='seconds')}", ""]
    log = lambda s="": (print(s), report.append(s))

    manifest = json.loads((base_pkg / "package_manifest.json").read_text(encoding="utf-8-sig"))
    payload_root = base_pkg / "payload"
    shipped = {norm(f["path"]).removeprefix("nativepc\\rom\\"): f for f in manifest["files"]}
    extra_src: dict[str, bytes] = {}
    def load_arc(rel: str) -> bytes:
        return extra_src[rel] if rel in extra_src else (payload_root / Path(shipped[rel]["path"])).read_bytes()

    # 1) CSV 비교
    log("[1/5] CSV 비교")
    base, new = read_csv(Path(a.base_csv)), read_csv(Path(a.new_csv))
    if len(base) != len(new):
        print("[오류] 두 CSV의 행 수가 다릅니다. 행 추가·삭제가 있는 CSV는 이 증분 빌드로 처리할 수 없습니다.")
        return 2
    changed_rows = [i for i in range(1, len(new)) if base[i][3] != new[i][3]]
    for i in changed_rows:
        if base[i][:3] + base[i][4:8] != new[i][:3] + new[i][4:8]:
            print(f"[오류] MsgEn 외 열이 바뀐 행이 있습니다: {i + 1}행")
            return 2
    arcs_to_patch = sorted({norm(new[i][5]) for i in changed_rows})
    log(f"  바뀐 행: {len(changed_rows):,} / 영향받는 ARC: {len(arcs_to_patch):,}")
    tex_specs = []
    if a.tex_patch:
        tp = Path(a.tex_patch)
        tex_specs = json.loads(tp.read_text(encoding="utf-8"))
        for t in tex_specs:
            t["arc"] = norm(t["arc"])
            t["png"] = str((tp.parent / t["png"]).resolve())
    missing = sorted({x for x in arcs_to_patch + [t["arc"] for t in tex_specs] if x not in shipped})
    if missing:
        rom = Path(a.game_dir) / "nativePC" / "rom" if a.game_dir else None
        if rom is None or not rom.is_dir():
            print("[오류] 기준 패키지에 없는 ARC가 있습니다. --game-dir 로 게임 폴더를 지정하세요:")
            for x in missing:
                print("   ", x)
            return 2
        log(f"  게임 폴더에서 원본 ARC {len(missing)}개를 추가로 가져옵니다")
        for x in missing:
            cur, parts = rom, x.split("\\")
            for part in parts:
                hit = [c for c in cur.iterdir() if c.name.lower() == part] if cur.is_dir() else []
                if not hit:
                    print(f"[오류] 게임 폴더에 파일이 없습니다: {x}")
                    return 2
                cur = hit[0]
            relpath = "nativePC/rom/" + cur.relative_to(rom).as_posix()
            data = cur.read_bytes()
            entry = {"path": relpath, "original_sha256": sha(data), "patched_sha256": sha(data), "size": len(data)}
            manifest["files"].append(entry)
            shipped[x] = entry
            extra_src[x] = data
    lookup = defaultdict(lambda: defaultdict(list))
    for r in new[1:]:
        lookup[norm(r[5])][norm(r[4])].append(r)

    new_files: dict[str, bytes] = {}

    # 2) 텍스트 ARC 재패킹
    log("[2/5] 문장 ARC 다시 패킹")
    for rel in arcs_to_patch:
        arc = Arc(load_arc(rel))
        n = 0
        for i, e in enumerate(arc.entries):
            if e["crc"] != GMD_CRC:
                continue
            rows = lookup[rel].get(norm(e["name"] + ".gmd"))
            if not rows:
                continue
            g = Gmd(arc.read(i))
            c = apply_csv_to_gmd(g, rows)
            if c:
                arc.replace(i, g.save())
                n += c
        if n:
            new_files[rel] = arc.save()
        log(f"  {rel}: 문장 {n}개 교체")

    # 2-b) 텍스처 글자 교체
    if tex_specs:
        log("[2b] 텍스처 글자 교체")
    for t in tex_specs:
        arc = Arc(new_files[t["arc"]] if t["arc"] in new_files else load_arc(t["arc"]))
        hit = [i for i, e in enumerate(arc.entries) if e["crc"] == TEX_CRC and e["name"].lower() == t["tex"].lower()]
        if not hit:
            print(f"[오류] 텍스처를 찾을 수 없습니다: {t['arc']} / {t['tex']}")
            return 2
        tex = arc.read(hit[0])
        h8, h12 = struct.unpack_from("<II", tex, 8)
        w, h = (h8 >> 6) & 0x1FFF, (h8 >> 19) & 0x1FFF
        fmt, data_off = (h12 >> 8) & 0xFF, struct.unpack_from("<I", tex, 16)[0]
        if (h8 & 0x3F) != 1 or fmt not in (0x17, 0x18, 0x2A, 0x2B) or len(tex) - data_off != w * h:
            print(f"[오류] 지원하지 않는 TEX 형식: {t['tex']} (fmt 0x{fmt:X}, mip {h8 & 0x3F})")
            return 2
        before = Image.open(io.BytesIO(dds_from_bc3(w, h, tex[data_off:]))).convert("RGBA")
        after = Image.open(t["png"]).convert("RGBA")
        if after.size != before.size:
            print(f"[오류] PNG 크기가 텍스처와 다릅니다: {t['png']}")
            return 2
        body = bytearray(tex[data_off:])
        nblk = patch_bc3(body, w, before, after)
        arc.replace(hit[0], bytes(tex[:data_off]) + bytes(body))
        new_files[t["arc"]] = arc.save()
        log(f"  {t['arc']} / {t['tex']}: 블록 {nblk}개 교체")

    # 3) 폰트
    log("[3/5] 폰트 글자 추가")
    gui_rel = "ui\\gui_cmn.arc"
    gui = Arc(new_files[gui_rel] if gui_rel in new_files else load_arc(gui_rel))
    gi = gui.find(GFD_CRC, "ui\\00_font\\ddo_font_jpn_win")[0]
    gfd = bytearray(gui.read(gi))
    gcount = struct.unpack_from("<I", gfd, 0x1C)[0]
    toff = len(gfd) - gcount * 16
    glyphs = [decode_record(i, toff + i * 16, bytes(gfd[toff + i * 16: toff + i * 16 + 16])) for i in range(gcount)]
    registered = {g["codepoint"] for g in glyphs}
    used_hangul, preserved_cjk = Counter(), set()
    for r in new[1:]:
        for ch in r[3]:
            cp = ord(ch)
            if is_hangul(cp):
                used_hangul[ch] += 1
            elif is_cjk(cp):
                preserved_cjk.add(ch)
    need = sorted((c for c in used_hangul if ord(c) not in registered), key=ord)
    log(f"  CSV 사용 한글 {len(used_hangul):,}자 / 폰트 등록 한글 {sum(1 for c in registered if is_hangul(c)):,}자 / 추가 필요 {len(need)}자")
    mapping = []
    rerender = []
    if a.rerender_hangul:
        rerender = [g for g in glyphs if is_hangul(g["codepoint"])]
        log(f"  기존 한글 {len(rerender):,}자를 새 폰트로 다시 그립니다")
    if need or rerender:
        slots = []
        if need:
            pages = {int(x) for x in a.pages.split(",")}
            cands = [g for g in glyphs if g["page"] in pages and is_cjk(g["codepoint"])
                     and chr(g["codepoint"]) not in preserved_cjk
                     and g["width"] >= 28 and g["height"] >= 28 and g["advance"] >= 28]
            cands.sort(key=lambda g: (abs(g["width"] - 32) + abs(g["height"] - 32) + abs(g["advance"] - 32),
                                      g["page"], g["y_base"], g["x"], g["index"]))
            if len(cands) < len(need):
                print(f"[오류] 남은 슬롯 부족: {len(cands)} < {len(need)}")
                return 1
            slots = cands[:len(need)]
        tex_idx = {}
        for i, e in enumerate(gui.entries):
            if e["crc"] == TEX_CRC and e["name"].lower().startswith("ui\\00_font\\ddo_font_jpn_win_"):
                tex_idx[int(e["name"][-8:-6])] = i
        touched = sorted({s["page"] for s in slots} | {g["page"] for g in rerender})
        imgs = {}
        for pg in touched:
            tex = gui.read(tex_idx[pg])
            if tex[:4] != b"TEX\0":
                raise ValueError("TEX 아님")
            h8, h12 = struct.unpack_from("<II", tex, 8)
            w, h = (h8 >> 6) & 0x1FFF, (h8 >> 19) & 0x1FFF
            fmt, data_off = (h12 >> 8) & 0xFF, struct.unpack_from("<I", tex, 16)[0]
            if (h8 & 0x3F) != 1 or fmt not in (0x17, 0x18, 0x2A, 0x2B) or len(tex) - data_off != w * h:
                raise ValueError(f"예상과 다른 TEX 형식(page {pg}, fmt 0x{fmt:X})")
            before = Image.open(io.BytesIO(dds_from_bc3(w, h, tex[data_off:]))).convert("RGBA")
            imgs[pg] = dict(tex=bytearray(tex), off=data_off, w=w, before=before, after=before.copy(),
                            colors=detect_colors(before))
        for g, ch in zip(slots, need):
            pi = imgs[g["page"]]
            bg, fg = pi["colors"]
            sz = render_glyph(pi["after"], g, ch, font_path, a.font_size, a.x_offset, a.y_offset, bg, fg)
            struct.pack_into("<I", gfd, g["offset"], ord(ch))
            mapping.append(dict(new=ch, old=chr(g["codepoint"]), page=g["page"], x=g["x"], y=g["y_base"],
                                w=g["width"], h=g["height"], size=sz, uses=used_hangul[ch]))
        for g in rerender:
            pi = imgs[g["page"]]
            bg, fg = pi["colors"]
            render_glyph(pi["after"], g, chr(g["codepoint"]), font_path, a.font_size, a.x_offset, a.y_offset, bg, fg)
        for pg, pi in imgs.items():
            body = bytearray(pi["tex"][pi["off"]:])
            nblk = patch_bc3(body, pi["w"], pi["before"], pi["after"])
            gui.replace(tex_idx[pg], bytes(pi["tex"][:pi["off"]]) + bytes(body))
            pi["final"] = Image.open(io.BytesIO(dds_from_bc3(pi["w"], len(body) // pi["w"], bytes(body)))).convert("RGBA")
            log(f"  page {pg}: 블록 {nblk}개 재인코딩")
        recs = sorted((bytes(gfd[toff + i * 16: toff + i * 16 + 16]) for i in range(gcount)),
                      key=lambda r: struct.unpack_from("<I", r)[0])
        gfd[toff:] = b"".join(recs)
        gui.replace(gi, bytes(gfd))
        new_files[gui_rel] = gui.save()
        for m in mapping:
            log(f"  {m['new']} ← {m['old']} (page {m['page']}, x{m['x']} y{m['y']}, {m['size']}px, 사용 {m['uses']}회)")

    # 4) 검증
    log("[4/5] 검증")
    errors = []
    for rel, blob in new_files.items():
        arc = Arc(blob)
        for i, e in enumerate(arc.entries):
            arc.read(i)  # 압축·크기 검사
            if e["crc"] == GMD_CRC and rel != gui_rel:
                rows = lookup[rel].get(norm(e["name"] + ".gmd"))
                if rows:
                    g = Gmd(arc.read(i))
                    if apply_csv_to_gmd(g, rows):
                        errors.append(f"문장 불일치: {rel} {e['name']}")
    if gui_rel in new_files or need or rerender:
        garc = Arc(new_files.get(gui_rel) or (payload_root / Path(shipped[gui_rel]["path"])).read_bytes())
        gd = garc.read(garc.find(GFD_CRC, "ui\\00_font\\ddo_font_jpn_win")[0])
        cps = [struct.unpack_from("<I", gd, len(gd) - gcount * 16 + i * 16)[0] for i in range(gcount)]
        if len(set(cps)) != len(cps):
            errors.append("GFD 코드포인트 중복")
        if any(x > y for x, y in zip(cps, cps[1:])):
            errors.append("GFD 정렬 오류")
        miss = [c for c in used_hangul if ord(c) not in set(cps)]
        if miss:
            errors.append("폰트에 없는 한글: " + "".join(miss))
        log(f"  폰트: 필요 {len(used_hangul):,} / 누락 {len(miss)} / 중복 {len(cps) - len(set(cps))}")
    for e in errors:
        log("  [실패] " + e)
    if errors:
        log("결과: FAIL (패키지를 만들지 않았습니다)")
        return 1

    # 5) 패키지
    log("[5/5] 패키지 생성")
    shutil.copytree(base_pkg, out_pkg)
    for rel, blob in new_files.items():
        f = shipped[rel]
        dst = out_pkg / "payload" / Path(f["path"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(blob)
        f["patched_sha256"] = sha(blob)
        f["size"] = len(blob)
    manifest["version"] = a.version
    manifest["created_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    manifest["candidate_csv_sha256"] = sha(Path(a.new_csv))
    manifest["build_note"] = f"incremental build from {base_pkg.name}"
    manifest["file_count"] = len(manifest["files"])
    (out_pkg / "package_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_pkg / "VERSION").write_text(a.version + "\n", encoding="utf-8")
    if a.readme_file:
        (out_pkg / "README_KO.txt").write_text(Path(a.readme_file).read_text(encoding="utf-8-sig"), encoding="utf-8-sig")
    if a.readme_note:
        readme = out_pkg / "README_KO.txt"
        txt = readme.read_text(encoding="utf-8-sig")
        readme.write_text(txt.rstrip() + "\n\n" + a.readme_note.replace("\\n", "\n") + "\n", encoding="utf-8-sig")
    sums = out_pkg / "SHA256SUMS.txt"
    if sums.exists():
        lines = []
        for line in sums.read_text(encoding="utf-8-sig").splitlines():
            if " *" not in line:
                continue
            rp = line.split(" *", 1)[1]
            lines.append(f"{sha(out_pkg / Path(rp))} *{rp}")
        listed = {l.split(" *", 1)[1].lower() for l in lines}
        for f in manifest["files"]:
            rp = "payload/" + f["path"]
            if rp.lower() not in listed:
                lines.append(f"{sha(out_pkg / Path(rp))} *{rp}")
        sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (out_pkg / "font_added_glyphs.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["new", "replaced", "page", "x", "y", "w", "h", "font_px", "uses"])
        for m in mapping:
            w.writerow([m[k] for k in ("new", "old", "page", "x", "y", "w", "h", "size", "uses")])
    if mapping:
        cell = 40
        sheet = Image.new("RGBA", (cell * 10, cell * ((len(mapping) + 9) // 10)), (40, 40, 40, 255))
        for n, (g, m) in enumerate(zip(slots, mapping)):
            img = imgs[g["page"]]["final"]
            crop = img.crop((g["x"], g["y_base"], g["x"] + g["width"], g["y_base"] + g["height"] + g["vertical_offset"]))
            sheet.paste(crop, ((n % 10) * cell + 2, (n // 10) * cell + 2))
        sheet.save(out_pkg / "font_added_glyphs_preview.png")
    log(f"  바뀐 파일 {len(new_files)}개: " + ", ".join(sorted(new_files)))
    log("결과: PASS")
    (out_pkg / "build_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8-sig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
