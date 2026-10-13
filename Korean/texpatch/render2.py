import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD = '/usr/share/fonts/opentype/noto/'
SERIF = FD + 'NotoSerifCJK-Black.ttc'
SERIFB = FD + 'NotoSerifCJK-Bold.ttc'
SANS = FD + 'NotoSansCJK-Bold.ttc'
SANSM = FD + 'NotoSansCJK-Medium.ttc'


def text_layer(txt, font, size, target_h, max_w, spacing=0):
    f = ImageFont.truetype(font, size, index=1)
    # measure with optional letter spacing
    chars = list(txt)
    widths = [f.getlength(c) for c in chars]
    W = int(sum(widths) + spacing * (len(chars) - 1)) + 20
    H = size * 2
    lay = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(lay)
    x = 10
    for c, w in zip(chars, widths):
        d.text((x, size // 2), c, font=f, fill=255)
        x += w + spacing
    a = np.array(lay)
    ys, xs = np.where(a > 20)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray(a)
    h = a.shape[0]
    sc = target_h / h
    w = max(1, round(a.shape[1] * sc))
    nh = max(1, round(h * sc))
    if w > max_w:
        w = max_w  # condense horizontally
    return np.array(im.resize((w, nh), Image.LANCZOS)).astype(np.float32) / 255.0


def sample_style(img, box, opaque_bg=None):
    A = np.array(img).astype(np.float32)
    x0, y0, x1, y1 = box
    c = A[y0:y1 + 1, x0:x1 + 1]
    rgb = c[..., :3]
    lum = rgb.mean(2)
    if opaque_bg is None:
        v = c[..., 3] / 255 * lum
    else:
        v = lum
    nz = v[v > 10]
    core = v >= np.percentile(nz, 70)
    ys = np.where(core.any(1))[0]
    h = len(lum)
    top = rgb[: h // 3][core[: h // 3]]
    bot = rgb[2 * h // 3:][core[2 * h // 3:]]
    mid = rgb[core]
    tc = top.mean(0) if len(top) else mid.mean(0)
    bc = bot.mean(0) if len(bot) else mid.mean(0)
    return tc, bc


def erase(img, box, pad, opaque_bg=None, inpaint=False):
    x0, y0, x1, y1 = box
    A = np.array(img)
    if inpaint:
        mask = np.zeros(A.shape[:2], np.uint8)
        mask[y0 - pad:y1 + pad + 1, x0 - pad:x1 + pad + 1] = 255
        rgb = cv2.inpaint(np.ascontiguousarray(A[..., :3]), mask, 5, cv2.INPAINT_TELEA)
        A[..., :3] = rgb
    elif opaque_bg is not None:
        A[y0 - pad:y1 + pad + 1, x0 - pad:x1 + pad + 1] = opaque_bg
    else:
        A[y0 - pad:y1 + pad + 1, x0 - pad:x1 + pad + 1] = 0
    return Image.fromarray(A)


def draw(img, core, cx, cy, top_c, bot_c, halo_c=None, halo_a=0.0, halo_r=2.0,
         outline_c=None, outline_a=0.0, opaque_bg=None):
    h, w = core.shape
    P = 8
    L = np.zeros((h + 2 * P, w + 2 * P), np.float32)
    L[P:P + h, P:P + w] = core
    Li = Image.fromarray((L * 255).astype(np.uint8))
    grad = np.linspace(0, 1, h + 2 * P)[:, None, None]
    col = np.array(top_c)[None, None] * (1 - grad) + np.array(bot_c)[None, None] * grad
    layers = []
    if halo_c is not None and halo_a > 0:
        g = np.array(Li.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(halo_r))).astype(np.float32) / 255
        layers.append((np.clip(g * 1.8, 0, 1) * halo_a, np.array(halo_c, np.float32)))
    if outline_c is not None and outline_a > 0:
        o = np.array(Li.filter(ImageFilter.MaxFilter(3))).astype(np.float32) / 255
        layers.append((o * outline_a, np.array(outline_c, np.float32)))
    X = max(0, int(round(cx - (w + 2 * P) / 2)))
    Y = int(round(cy - (h + 2 * P) / 2))
    A = np.array(img).astype(np.float32)
    reg = A[Y:Y + h + 2 * P, X:X + w + 2 * P]
    rgb = reg[..., :3] / 255
    al = reg[..., 3] / 255
    for a, c in layers + [(L, None)]:
        cc = (col if c is None else np.broadcast_to(c, rgb.shape)) / 255
        if opaque_bg is not None:
            rgb = rgb * (1 - a[..., None]) + cc * a[..., None]
        else:
            na = a + al * (1 - a)
            rgb = (cc * a[..., None] + rgb * al[..., None] * (1 - a[..., None])) / np.maximum(na[..., None], 1e-5)
            al = na
    reg[..., :3] = np.clip(rgb * 255, 0, 255)
    if opaque_bg is None:
        reg[..., 3] = np.clip(al * 255, 0, 255)
    A[Y:Y + h + 2 * P, X:X + w + 2 * P] = reg
    return Image.fromarray(A.astype(np.uint8))
