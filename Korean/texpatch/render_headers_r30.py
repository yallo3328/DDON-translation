import sys
sys.path.insert(0, '/tmp/claude-0/tp2')
from render2 import *

# ---------- word_ID_jpn (already has the 7 menu headers in Korean) ----------
src0 = Image.open('/tmp/claude-0/texpatch/word_ID_jpn_ko.png').convert('RGBA')
im = src0.copy()
# (box, text, font, max_w, pad, halo(color,alpha,r) or None, outline)
W0 = [
    ((2, 174, 57, 187), '참가 장소', SANS, 64, 2, None),
    ((160, 341, 184, 354), 'D급', SANS, 30, 2, None),
    ((160, 365, 183, 378), 'C급', SANS, 30, 2, None),
    ((161, 389, 183, 402), 'B급', SANS, 30, 2, None),
    ((160, 413, 183, 426), 'A급', SANS, 30, 2, None),
    ((160, 437, 182, 450), 'S급', SANS, 30, 2, None),
    ((92, 562, 158, 574), '치장 장비', SANS, 70, 2, None),
    ((223, 534, 411, 553), '황금석으로 포인트 배가 추첨!', SANSM, 205, 2, None),
    ((243, 566, 396, 585), '폰 원정대를 파견한다', SANSM, 160, 2, None),
    ((289, 599, 349, 617), '참가한다', SANSM, 70, 2, None),
    ((245, 630, 394, 649), '가까운 지역으로 이동', SANSM, 160, 2, None),
    ((482, 598, 673, 616), '도미니언 포인트 숍', SANSM, 195, 2, None),
    ((516, 631, 635, 648), '퀵 파티', SANSM, 125, 2, None),
]
for box, txt, font, mw, pad, halo in W0:
    tc, bc = sample_style(src0, box)
    x0, y0, x1, y1 = box
    im = erase(im, box, pad)
    core = text_layer(txt, font, 40, (y1 - y0 + 1) * 0.92, mw)
    im = draw(im, core, (x0 + x1) / 2, (y0 + y1) / 2, tc, bc, halo_c=(0, 0, 0), halo_a=0.55, halo_r=1.0)

# gold title logo: spaced letters
box = (606, 694, 992, 718)
tc, bc = sample_style(src0, box)
im = erase(im, box, 3)
core = text_layer('드래곤즈 도그마 온라인', SERIF, 40, 25, 386, spacing=14)
im = draw(im, core, (606 + 992) / 2, 706, tc, bc, halo_c=(0, 0, 0), halo_a=0.7, halo_r=1.2)

# ornamented gold headers
for box, txt in [((831, 132, 948, 161), '습득 시련'), ((832, 311, 949, 339), '승격 시험')]:
    tc, bc = sample_style(src0, box)
    im = erase(im, box, 2)
    core = text_layer(txt, SERIF, 48, box[3] - box[1] + 1, 150)
    im = draw(im, core, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, tc, bc,
              halo_c=(40, 25, 5), halo_a=0.85, halo_r=1.0)

# banner text
box = (585, 205, 724, 229)
tc, bc = sample_style(src0, box)
im = erase(im, box, 2, inpaint=True)
core = text_layer('영령의 가호', SERIF, 48, 25, 150)
im = draw(im, core, (585 + 724) / 2 + 3, 217, (200, 190, 160), (120, 110, 90), halo_c=(0, 0, 0), halo_a=0.8, halo_r=1.2)
im.save('/tmp/claude-0/tp2/word_ID_jpn_ko2.png')

# ---------- word01_ID_jpn ----------
src1 = Image.open('/tmp/claude-0/tp2/word01_raw.png').convert('RGBA')
im1 = src1.copy()
BG = (20, 20, 20, 255)
W1 = [
    ((34, 222, 93, 241), '생명력', 80),
    ((35, 253, 92, 272), '모험력', 80),
    ((32, 284, 92, 303), '마법력', 80),
    ((43, 317, 81, 336), '공격력', 80),
    ((10, 350, 115, 369), '용력 계승', 118),
    ((11, 379, 117, 396), '황금석 구매', 118),
    ((30, 404, 97, 427), '획득률', 90),
    ((139, 222, 239, 241), '전우의 서약', 110),
    ((147, 257, 252, 276), '전투 기술 계승', 140),
    ((319, 257, 424, 276), '절기 계승', 120),
]
im1 = erase(im1, (2, 216, 123, 432), 0)
im1 = erase(im1, (128, 216, 448, 284), 0)
for box, txt, mw in W1:
    x0, y0, x1, y1 = box
    bold = txt == '황금석 구매'
    core = text_layer(txt, SANS if bold else SANSM, 40, (y1 - y0 + 1) * 0.9, mw)
    im1 = draw(im1, core, (x0 + x1) / 2, (y0 + y1) / 2, (255, 255, 255), (235, 235, 235), halo_c=(0, 0, 0), halo_a=0.85, halo_r=1.3)
im1.save('/tmp/claude-0/tp2/word01_ID_jpn_ko.png')


def view(img, box, s, out, bg=(40, 40, 40, 255)):
    c = img.crop(box)
    b = Image.new('RGBA', c.size, bg)
    b.alpha_composite(c)
    return b.resize((c.width * s, c.height * s), Image.NEAREST)


def compare(a, b, box, s, out):
    A = view(a, box, s, out); B = view(b, box, s, out)
    sh = Image.new('RGBA', (A.width, A.height * 2 + 10), (90, 0, 0, 255))
    sh.paste(A, (0, 0)); sh.paste(B, (0, A.height + 10))
    sh.convert('RGB').save(out)


compare(src0, im, (0, 120, 1024, 730), 1, '/tmp/claude-0/tp2/cmp_w0.png')
compare(src0, im, (440, 120, 1024, 350), 2, '/tmp/claude-0/tp2/cmp_w0_head.png')
compare(src0, im, (0, 520, 700, 660), 2, '/tmp/claude-0/tp2/cmp_w0_small.png')
compare(src1, im1, (0, 210, 450, 440), 2, '/tmp/claude-0/tp2/cmp_w1.png')
