#!/usr/bin/env python3
"""
scenes.py - 10 "scene" effects (Orbit, Chat, Snap Zoom, Checklist Pop, Headline Storm, Paper Cutout, Liquid Glass, Green Screen, Digital Zoom, Phone Mockup) in a minimal look; the minimal ones (chat, checklistpop, headlinestorm, orbit, papercutout, phonemock) use a monochrome palette.
Imported by fx.py (build(fx) returns the registry entries). Every effect plays ONCE from --start for its own duration.
Texts can be customised: --text "MAIN TEXT" and --items "one,two,three".
Needs: numpy, opencv-python, Pillow (text), assets/Inter-*.otf, assets/u2netp.onnx (person cut-out, OpenCV DNN).
All geometry is expressed as fractions of the frame (W, H) measured on the 576x1024 original.
"""
import math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

F = None                                   # the fx module (helpers), set in build()
ORANGE = (34, 87, 255)                     # BGR of #FF5722
BLUE = (255, 79, 30)                       # BGR of #1E4FFF
NAVY = (10, 8, 6)


# ----------------------------------------------------------------------------- styles (palettes)
# --style NAME picks one; add your own brand by copying a block. Colours are BGR. rad = corner factor (1 = rounded, 0 = square).
STYLES = {
    "minimal": dict(
        ink=(26, 26, 28), card=(252, 252, 252), line=(222, 222, 222), bg=(238, 238, 236), surface=(240, 240, 240), dim=(170, 170, 170), rad=1.0,
        icon={"spark": ((252, 252, 252), (26, 26, 28)), "wave": ((252, 252, 252), (26, 26, 28)), "play": ((252, 252, 252), (26, 26, 28)),
              "burst": ((252, 252, 252), (26, 26, 28)), "cc": ((252, 252, 252), (26, 26, 28)), "aa": ((252, 252, 252), (26, 26, 28)), "cut": ((252, 252, 252), (26, 26, 28))},
        check=((26, 26, 28), (255, 255, 255)), tag_light=((24, 24, 26), (255, 255, 255)), tag_dark=((240, 240, 240), (20, 20, 22)),
        acc=((26, 26, 28), (150, 150, 152), (90, 90, 92)), paper=(224, 234, 240), p_strip=(250, 250, 250), p_disc=(30, 30, 32), p_star=(30, 30, 32), p_dot_a=(150, 150, 152), p_dot_b=(30, 30, 32), p_sticker=(252, 252, 252), p_tear=(36, 36, 40)),
}
_cur_style = ["minimal"]

def _hex(h):
    h = h.strip().lstrip("#")
    if len(h) == 3: h = "".join(ch * 2 for ch in h)
    return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))          # RGB hex in the file -> BGR for OpenCV

def _mix(a, b, k): return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))
def _on(col):                                                              # readable text colour on top of a fill
    lum = 0.114 * col[0] + 0.587 * col[1] + 0.299 * col[2]
    return (20, 20, 22) if lum > 140 else (250, 250, 250)

def _style_from_brand(b):
    """builds a full scene palette from a SHORT brand file (styles/<name>.json or any path):
       paper, card, ink + up to three accents (+ optional line, dim, surface, corners 0..1, fonts).  Everything else is derived."""
    g = lambda k, d: _hex(b[k]) if b.get(k) else d
    ink = g("ink", (26, 26, 28)); paper = g("paper", (238, 238, 236)); card = g("card", _mix(paper, (255, 255, 255), 0.6))
    a1 = g("accent1", ink); a2 = g("accent2", a1); a3 = g("accent3", a1)
    P = dict(ink=ink, card=card, bg=paper, paper=paper, surface=g("surface", _mix(card, ink, 0.06)), line=g("line", _mix(paper, ink, 0.2)),
             dim=g("dim", _mix(paper, ink, 0.5)), rad=float(b.get("corners", 1.0)),
             icon={"spark": (a1, _on(a1)), "wave": (a2, _on(a2)), "play": (a3, _on(a3)), "burst": (card, ink), "cc": (card, ink), "aa": (card, ink), "cut": (card, ink)},
             check=(a1, _on(a1)), tag_light=(a1, _on(a1)), tag_dark=(a3, _on(a3)),
             p_strip=card, p_disc=a1, p_star=a3, p_dot_a=a2, p_dot_b=ink, p_sticker=card, p_tear=a2, acc=(a1, a2, a3))
    if b.get("fonts"): P["fonts"] = dict(b["fonts"])
    return P

def _load_style(name):
    """--style minimal (built in) | name of styles/<name>.json next to the scripts | path to a .json brand file"""
    if name in STYLES: return STYLES[name]
    import json, os
    cands = [name, os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles", name if name.endswith(".json") else name + ".json")]
    for p in cands:
        if os.path.isfile(p):
            STYLES[name] = _style_from_brand(json.load(open(p, encoding="utf-8")))
            return STYLES[name]
    print("style '%s' not found - using minimal" % name); STYLES[name] = STYLES["minimal"]
    return STYLES[name]

def pal(c):
    """palette of the style chosen with --style (default: minimal)"""
    name = str(getattr(c, "opts", {}).get("style") or "minimal")
    _cur_style[0] = name
    return _load_style(name)

# ----------------------------------------------------------------------------- helpers
_fonts = {}
def font(size, weight="Bold"):
    key = (int(max(6, round(size))), weight, _cur_style[0])
    if key not in _fonts:
        p = None
        ff = STYLES.get(_cur_style[0], {}).get("fonts", {}).get(weight)
        if ff and not F._asset(ff) and os.path.isfile(ff): p = ff
        elif ff: p = F._asset(ff)
        p = p or F._asset("Inter-%s.otf" % weight) or F._asset("Inter-Bold.otf")
        try:
            _fonts[key] = ImageFont.truetype(p, key[0]) if p else ImageFont.load_default()
        except Exception:
            _fonts[key] = ImageFont.load_default()
    return _fonts[key]

def text_layer(txt, size, color=(255, 255, 255), weight="Bold", stroke=0, stroke_color=(0, 0, 0), spacing=0.0):
    """(bgr uint8, alpha float32) of rendered text"""
    f = font(size, weight)
    if spacing:
        widths = [f.getlength(ch) + spacing * size for ch in txt]
        l, t, r, b = f.getbbox(txt)
        w = int(sum(widths) + 8); h = int(b - t + 8 + 2 * stroke)
        im = Image.new("RGBA", (max(2, w), max(2, h)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        x = 4
        for ch, wd in zip(txt, widths):
            d.text((x, 4 - t + stroke), ch, font=f, fill=(color[2], color[1], color[0], 255)); x += wd
    else:
        l, t, r, b = f.getbbox(txt, stroke_width=stroke)
        w, h = int(r - l + 2 * stroke + 8), int(b - t + 2 * stroke + 8)
        im = Image.new("RGBA", (max(2, w), max(2, h)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((4 - l + stroke, 4 - t + stroke), txt, font=f, fill=(color[2], color[1], color[0], 255),
               stroke_width=stroke, stroke_fill=(stroke_color[2], stroke_color[1], stroke_color[0], 255))
    a = np.asarray(im)
    return np.ascontiguousarray(a[..., 2::-1]), a[..., 3].astype(np.float32) / 255.0

def text_width(txt, size, weight="Bold"):
    return font(size, weight).getlength(txt)

def blit(cv, bgr, a, x, y, op=1.0, rot=0.0, scale=1.0):
    """alpha-composite a (bgr, alpha) patch centred at (x, y); optional rotation (deg, ccw) and scale."""
    h, w = bgr.shape[:2]
    if scale != 1.0 or rot != 0.0:
        M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), rot, scale)
        cs, sn = abs(M[0, 0]), abs(M[0, 1])
        nw, nh = int(h * sn + w * cs) + 2, int(h * cs + w * sn) + 2
        M[0, 2] += nw / 2.0 - w / 2.0; M[1, 2] += nh / 2.0 - h / 2.0
        bgr = cv2.warpAffine(bgr, M, (nw, nh), flags=cv2.INTER_LINEAR)
        a = cv2.warpAffine(a, M, (nw, nh), flags=cv2.INTER_LINEAR)
        h, w = nh, nw
    x0 = int(round(x - w / 2.0)); y0 = int(round(y - h / 2.0))
    X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(cv.shape[1], x0 + w), min(cv.shape[0], y0 + h)
    if X1 <= X0 or Y1 <= Y0 or op <= 0: return cv
    sb = bgr[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32); sa = (a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * op)[..., None]
    reg = cv[Y0:Y1, X0:X1].astype(np.float32)
    cv[Y0:Y1, X0:X1] = np.clip(reg * (1 - sa) + sb * sa, 0, 255).astype(np.uint8)
    return cv

def put_text(cv, txt, x, y, size, color=(255, 255, 255), weight="Bold", anchor="c", op=1.0, rot=0.0, stroke=0, stroke_color=(0, 0, 0), scale=1.0, spacing=0.0):
    bgr, a = text_layer(txt, size, color, weight, stroke, stroke_color, spacing)
    h, w = bgr.shape[:2]
    cx = x + (w / 2.0 * scale if anchor == "l" else -w / 2.0 * scale if anchor == "r" else 0)
    return blit(cv, bgr, a, cx, y, op, rot, scale)

def rrect_layer(w, h, r, fill=(255, 255, 255), border=None, bw=0):
    """anti-aliased rounded rectangle (bgr, alpha)"""
    S = 3
    w = max(2, int(round(w))); h = max(2, int(round(h)))
    W_, H_ = w * S, h * S
    m = np.zeros((H_, W_), np.uint8); rr = int(max(0, min(r * S, W_ / 2, H_ / 2)))
    if rr > 0:
        cv2.rectangle(m, (rr, 0), (W_ - rr - 1, H_ - 1), 255, -1); cv2.rectangle(m, (0, rr), (W_ - 1, H_ - rr - 1), 255, -1)
        for cx_, cy_ in ((rr, rr), (W_ - rr - 1, rr), (rr, H_ - rr - 1), (W_ - rr - 1, H_ - rr - 1)): cv2.circle(m, (cx_, cy_), rr, 255, -1)
    else:
        m[:] = 255
    a = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    bgr = np.empty((h, w, 3), np.uint8); bgr[:] = fill
    if border is not None and bw > 0:
        k = int(bw * S) * 2 + 1
        inner = cv2.erode(m, np.ones((k, k), np.uint8))
        ia = cv2.resize(inner, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        bgr = (bgr.astype(np.float32) * ia[..., None] + np.array(border, np.float32) * (1 - ia[..., None])).astype(np.uint8)
    return bgr, a

def disk_layer(r, fill):
    n = int(2 * r + 4); bgr = np.empty((n, n, 3), np.uint8); bgr[:] = fill
    m = np.zeros((n * 3, n * 3), np.uint8); cv2.circle(m, (n * 3 // 2, n * 3 // 2), int(r * 3), 255, -1)
    return bgr, cv2.resize(m, (n, n), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0

def lerp(a, b, u): return a + (b - a) * u
def clamp01(x): return max(0.0, min(1.0, x))
def ease(x): return F.ease(x)
def smooth(a, b, t): return ease(clamp01((t - a) / max(1e-6, (b - a))))
def back_out(x, k=1.7):
    x = clamp01(x) - 1; return 1 + (k + 1) * x ** 3 + k * x ** 2
def kfs(t, pts): return F.kf(t, pts)

def soft_shadow(cv, a, x, y, dx, dy, blur, strength, scale=1.0, rot=0.0):
    """drop shadow of an alpha mask centred at (x, y) shifted by (dx, dy)"""
    sa = cv2.GaussianBlur(a, (0, 0), max(0.5, blur))
    blit(cv, np.zeros((a.shape[0], a.shape[1], 3), np.uint8), sa, x + dx, y + dy, strength, rot, scale)
    return cv

def light_bg(c):
    """flat light-grey backdrop for the minimal scenes (chat, phone)"""
    if "lightbg" not in c.state:
        bg = np.empty((c.H, c.W, 3), np.uint8); bg[:] = pal(c)["bg"]
        c.state["lightbg"] = bg
    return c.state["lightbg"].copy()

def soft_shadow2(cv, a, x, y, dx, dy, blur, strength, scale=1.0, rot=0.0):
    """like soft_shadow, but the mask is padded before blurring so the shadow is never cut at the edge of its bitmap"""
    pad = int(3 * blur) + 3
    ap = np.pad(a, ((pad, pad), (pad, pad)))
    sa = cv2.GaussianBlur(ap, (0, 0), max(0.5, blur))
    blit(cv, np.zeros((ap.shape[0], ap.shape[1], 3), np.uint8), sa, x + dx, y + dy, strength, rot, scale)
    return cv

def navy_bg(c, glow=True, orange=True):
    key = ("navybg", glow, orange)
    if key not in c.state:
        W, H = c.W, c.H
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        bg = np.empty((H, W, 3), np.float32); bg[:] = NAVY
        if glow:
            r = np.hypot((xx - W * 0.5) / (W * 0.62), (yy - H * 0.80) / (H * 0.30))
            g = np.clip(1 - r, 0, 1) ** 1.5
            bg += g[..., None] * np.array([185, 75, 12], np.float32)
        if orange:
            r2 = np.hypot((xx - W * 0.95) / (W * 0.45), (yy - H * 0.02) / (H * 0.20))
            g2 = np.clip(1 - r2, 0, 1) ** 2
            bg += g2[..., None] * np.array([6, 24, 60], np.float32)
        c.state[key] = np.clip(bg, 0, 255).astype(np.uint8)
    return c.state[key].copy()

def face(img, c):
    if "face" not in c.state:
        W, H = c.W, c.H
        if c.fixed_face is not None:
            fb = np.array([c.fixed_face[0] * W, c.fixed_face[1] * H, c.fixed_face[2] * W, c.fixed_face[3] * H], np.float32)
        else:
            fb = F.detect_face(img)
        if fb is None: fb = np.array([W * .327, H * .255, W * .352, H * .198], np.float32)
        c.state["face"] = fb
    return c.state["face"]

def face_scale(img, c):
    """how much of the original's zoom to keep: a face that is already large in the frame needs less zoom (the design assumes a face ~0.2 W wide)"""
    fb = face(img, c)
    return float(np.clip(0.21 / max(1e-3, fb[2] / c.W), 0.45, 1.0))

def matte(img, c, every=2):
    """soft person alpha (HxW float32), cached every `every` frames. u2netp via OpenCV DNN, colour-difference fallback."""
    st = c.state
    if "mt" in st and c.i - st["mt_i"] < every: return st["mt"]
    H, W = img.shape[:2]
    if "net" not in st:
        st["net"] = None
        p = F._asset("u2netp.onnx")
        if p:
            try: st["net"] = cv2.dnn.readNetFromONNX(p)
            except Exception: st["net"] = None
    if st["net"] is not None:
        x = cv2.dnn.blobFromImage(cv2.resize(img, (320, 320), interpolation=cv2.INTER_AREA), 1 / 255.0, (320, 320), (0, 0, 0), swapRB=True)
        x[0] = (x[0] - np.array([0.485, 0.456, 0.406], np.float32)[:, None, None]) / np.array([0.229, 0.224, 0.225], np.float32)[:, None, None]
        st["net"].setInput(x)
        o = st["net"].forward()[0, 0]
        o = (o - o.min()) / (o.max() - o.min() + 1e-8)
        m = cv2.resize(o, (W, H), interpolation=cv2.INTER_CUBIC)
        m = np.clip((m - 0.28) / 0.44, 0, 1)
        m = m * m * (3 - 2 * m)
    else:
        m = F.person_mask(img)
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), max(1.0, 0.0022 * W))
    if "mt" in st: m = 0.5 * st["mt"] + 0.5 * m
    st["mt"] = m.astype(np.float32); st["mt_i"] = c.i
    return st["mt"]

def over_person(bg, img, c, boost=0.0, m=None):
    if m is None: m = matte(img, c)
    m = m[..., None]
    fg = img.astype(np.float32)
    if boost: fg = fg * (1 + boost)
    return np.clip(bg.astype(np.float32) * (1 - m) + fg * m, 0, 255).astype(np.uint8)

def opt(c, key, default):
    v = getattr(c, "opts", {}).get(key)
    return v if v else default

def lang(c):
    """language of the default texts: 'en' (default) or 'ru' (--lang ru)"""
    return "ru" if str(getattr(c, "opts", {}).get("lang") or "en").lower().startswith("ru") else "en"

def items_opt(c, default):
    v = getattr(c, "opts", {}).get("items")
    sep = "|" if v and "|" in v else ","                      # "|" lets the items themselves contain commas
    return [s.strip() for s in v.split(sep) if s.strip()] if v else list(default)

def zoom_at(img, s, cx, cy, blur=0.0, n=9):
    """zoom by s about (cx, cy); blur>0 -> radial zoom blur spanning that relative scale range"""
    H, W = img.shape[:2]
    def one(sc_):
        M = np.float32([[sc_, 0, cx - sc_ * cx], [0, sc_, cy - sc_ * cy]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)
    if blur <= 0.002: return one(s)
    n = max(n, int(blur * 28) + 7)
    acc = np.zeros(img.shape, np.float32)
    for k in range(n):
        acc += one(s * (1 + blur * (k / (n - 1) - 0.5))).astype(np.float32)
    return (acc / n).astype(np.uint8)

def tint_flash(img, a, col=(255, 255, 255)):
    return F.flash(img, a, col) if a > 0.003 else img

def add_glow(canvas, mask, color, radius, strength):
    g = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), max(1.0, radius))
    out = canvas.astype(np.float32) + g[..., None] * np.array(color, np.float32) * strength
    return np.clip(out, 0, 255).astype(np.uint8)

def dashed_ellipse(cv, cx, cy, rx, ry, dash_deg=4.0, gap_deg=4.0, color=(255, 255, 255), thick=2, op=0.8, phase=0.0):
    """dashed ellipse drawn as many short arcs"""
    ov = np.zeros(cv.shape[:2], np.uint8)
    a = phase % (dash_deg + gap_deg)
    while a < 360:
        cv2.ellipse(ov, (int(cx), int(cy)), (int(rx), int(ry)), 0, a, a + dash_deg, 255, thick, cv2.LINE_AA)
        a += dash_deg + gap_deg
    al = ov.astype(np.float32) / 255.0 * op
    return (cv.astype(np.float32) * (1 - al[..., None]) + np.array(color, np.float32) * al[..., None]).astype(np.uint8)

# ----------------------------------------------------------------------------- 1. orbit
def _icon(kind, s, P=None):
    """minimal icon: tile with a hairline border and a single thin glyph (colours from the style palette)"""
    P = P or STYLES["minimal"]
    S = int(s)
    fill, ink = P["icon"][kind]
    b, a = rrect_layer(S, S, S * 0.28 * P["rad"], fill, P["line"], max(1, S * 0.022))
    h, w = b.shape[:2]; cx_, cy_ = w // 2, h // 2
    th = max(2, int(w * 0.052))
    def put(t, ta, x=cx_, y=cy_):
        t_h, t_w = t.shape[:2]; y0, x0 = y - t_h // 2, x - t_w // 2
        reg = b[max(0, y0):y0 + t_h, max(0, x0):x0 + t_w]
        t2 = t[max(0, -y0):max(0, -y0) + reg.shape[0], max(0, -x0):max(0, -x0) + reg.shape[1]]; ta2 = ta[max(0, -y0):max(0, -y0) + reg.shape[0], max(0, -x0):max(0, -x0) + reg.shape[1]]
        reg[:] = (reg * (1 - ta2[..., None]) + t2 * ta2[..., None]).astype(np.uint8)
    if kind == "spark":
        r = w * 0.27; pts = []
        for i in range(8):
            ang = math.radians(-90 + i * 45); rr = r if i % 2 == 0 else r * 0.20
            pts.append([cx_ + rr * math.cos(ang), cy_ + rr * math.sin(ang)])
        cv2.fillPoly(b, [np.array(pts, np.int32)], ink, cv2.LINE_AA)
    elif kind == "wave":
        for i, hh in enumerate((0.10, 0.20, 0.30, 0.18, 0.08)):
            x = int(w * (0.28 + 0.11 * i)); cv2.line(b, (x, int(cy_ - h * hh)), (x, int(cy_ + h * hh)), ink, th, cv2.LINE_AA)
    elif kind == "play":
        pts = np.array([[cx_ - w * .10, cy_ - h * .21], [cx_ - w * .10, cy_ + h * .21], [cx_ + w * .22, cy_]], np.int32); cv2.fillConvexPoly(b, pts, ink, cv2.LINE_AA)
    elif kind == "burst":
        for i in range(8):
            ang = math.radians(i * 45); r0, r1 = w * 0.07, w * 0.27
            cv2.line(b, (int(cx_ + r0 * math.cos(ang)), int(cy_ + r0 * math.sin(ang))), (int(cx_ + r1 * math.cos(ang)), int(cy_ + r1 * math.sin(ang))), ink, th, cv2.LINE_AA)
    elif kind == "cc":
        t, ta = text_layer("CC", w * 0.36, ink, "Bold"); put(t, ta)
    elif kind == "aa":
        t, ta = text_layer("Aa", w * 0.38, ink, "Bold"); put(t, ta)
    elif kind == "cut":
        d = w * 0.18
        cv2.line(b, (int(cx_ - d), int(cy_ - d)), (int(cx_ + d), int(cy_ + d)), ink, th, cv2.LINE_AA)
        cv2.line(b, (int(cx_ - d), int(cy_ + d)), (int(cx_ + d), int(cy_ - d)), ink, th, cv2.LINE_AA)
        cv2.circle(b, (int(cx_ - d), int(cy_ + d * 1.15)), max(2, int(w * .085)), ink, max(2, int(w * .04)), cv2.LINE_AA)
        cv2.circle(b, (int(cx_ + d), int(cy_ + d * 1.15)), max(2, int(w * .085)), ink, max(2, int(w * .04)), cv2.LINE_AA)
    return b, a

_ORBIT_BIG_RX, _ORBIT_BIG_RY = 0.44, 0.19      # ellipse half-sizes (fractions of W and H) for a close-up face; a far face keeps 0.455 W x 0.155 H
_ORBIT_TILT = -13.0       # tilt of the orbit ring in degrees (negative: the right side is higher, positive: the left side is higher)

def _orbit_ring(H, W, cx, cy, rx, ry, tilt, phase, thick, dash=3.0, gap=3.6):
    """dashed tilted ellipse as two float masks: (back half, front half). Front = lower half of the ring (sin(theta) > 0)."""
    mb = np.zeros((H, W), np.uint8); mf = np.zeros((H, W), np.uint8)
    a = phase % (dash + gap) - (dash + gap)
    while a < 360:
        m = mf if math.sin(math.radians(a + dash / 2.0)) > 0 else mb
        cv2.ellipse(m, (int(cx), int(cy)), (int(rx), int(ry)), tilt, a, a + dash, 255, thick, cv2.LINE_AA)
        a += dash + gap
    return mb.astype(np.float32) / 255.0, mf.astype(np.float32) / 255.0

def _paint_ring(cv, al, op):
    """white dashes with a faint dark edge so they read on light and dark backgrounds"""
    if op <= 0.005: return cv
    sh = cv2.GaussianBlur(al, (0, 0), 1.6) * 0.30 * op
    f = cv.astype(np.float32) * (1 - sh[..., None])
    w = al * op
    return np.clip(f * (1 - w[..., None]) + 255.0 * w[..., None], 0, 255).astype(np.uint8)

def fx_orbit(img, t, c):
    W, H = c.W, c.H
    D = 1.55
    if t > D: return img
    P = pal(c)
    kinds = ["spark", "wave", "play", "burst", "cc", "aa", "cut"]
    fb_ = face(img, c)
    # big face (close-up selfie): the ring goes AROUND THE HEAD (behind the hair, in front of the neck/chest) and the icons grow;
    # small face (full-body shot): the old low ring under the chin
    g = clamp01((fb_[2] / W - 0.40) / 0.12)
    fcx_, fcy_ = fb_[0] + fb_[2] / 2, fb_[1] + fb_[3] / 2
    cx = lerp(0.50 * W, fcx_, g)
    cy = lerp(min(0.70 * H, fb_[1] + fb_[3] * 0.5 + 0.24 * H), fcy_ + 0.06 * H, g)
    rx, ry = lerp(0.455 * W, _ORBIT_BIG_RX * W, g), lerp(0.155 * H, _ORBIT_BIG_RY * H, g)   # far face: flat ellipse; big face: bigger, so it does not squeeze the head
    rx = min(rx, cx - 0.075 * W, W - 0.075 * W - cx)                # icons must stay fully inside the frame, also when the face is off-centre
    if "icons" not in c.state:
        c.state["icons"] = {k: _icon(k, 0.113 * W * (1 + 0.18 * g), P) for k in kinds}
    tilt = _ORBIT_TILT; ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    fade_out = 1 - smooth(1.35, 1.55, t)
    ring_a = smooth(0.0, 0.3, t) * fade_out
    ring_b = ring_f = None
    if ring_a > 0.01:
        ring_b, ring_f = _orbit_ring(H, W, cx, cy, rx, ry, tilt, t * 40, max(2, int(0.0032 * W)))
    base = _paint_ring(img, ring_b, 0.90 * ring_a) if ring_b is not None else img
    th0 = math.radians(150) + 2 * math.pi * t / 2.1
    items = []
    for i, k in enumerate(kinds):
        th = th0 + 2 * math.pi * i / len(kinds)
        z = math.sin(th)                                  # +1 = front (bottom of the ellipse)
        ex, ey = rx * math.cos(th), ry * z                # point on the un-tilted ellipse
        life = back_out(clamp01((t - 0.04 * i) / 0.28)) * fade_out
        items.append((z, cx + ex * ct - ey * st, cy + ex * st + ey * ct, k, life))
    items.sort()
    back_layer = base.copy()
    fronts = []
    for z, x, y, k, life in items:
        sc_ = (0.80 + 0.20 * (z + 1) / 2) * life
        if sc_ <= 0.08: continue
        b, a = c.state["icons"][k]
        if z < 0:
            soft_shadow2(back_layer, a, x, y, 0, 0.006 * H, 0.008 * W, 0.30, sc_)
            blit(back_layer, b, a, x, y, 1.0, 0, sc_)
        else: fronts.append((b, a, x, y, sc_))
    m = matte(img, c)[..., None]
    out = (back_layer.astype(np.float32) * (1 - m) + img.astype(np.float32) * m).astype(np.uint8)
    if ring_f is not None:                                # the front half of the ring crosses IN FRONT of the body
        out = _paint_ring(out, ring_f, 0.90 * ring_a)
    for b, a, x, y, sc_ in fronts:
        soft_shadow2(out, a, x, y, 0, 0.007 * H, 0.009 * W, 0.32, sc_)
        blit(out, b, a, x, y, 1.0, 0, sc_)
    return out

# ----------------------------------------------------------------------------- 2. chat takeover
def _chat_wrap(txt, size, maxw):
    rows = []; cur = ""
    for wd in txt.split(" "):
        if cur and text_width(cur + " " + wd, size, "Medium") > maxw: rows.append(cur); cur = wd
        else: cur = (cur + " " + wd).strip()
    if cur: rows.append(cur)
    return rows or [""]

def _chat_geom(c, user_text, w, h):
    """layout of the chat thread in window pixels: request bubble on top, the attached video card BELOW it (never over the text), reply under both"""
    W = c.W; u = W / 1080.0
    fsz = 26 * u
    rows = _chat_wrap(user_text, fsz, 0.60 * w - 48 * u)
    tw = max(text_width(r, fsz, "Medium") for r in rows)
    g = dict(u=u, fsz=fsz, rows=rows, bw=tw + 48 * u, bh=len(rows) * 38 * u + 30 * u, bub_top=164 * u)
    g["card_w"] = 0.27 * W; g["card_h"] = g["card_w"] * c.H / W
    g["card_top"] = g["bub_top"] + g["bh"] + 14 * u
    g["card_x"] = w - 36 * u - g["card_w"] / 2
    g["cap_y"] = g["card_top"] + g["card_h"] + 26 * u
    g["ay"] = g["cap_y"] + 76 * u
    return g

def _chat_window(c, W, H, user_text, lines, tt, w, h):
    """window bitmap (w x h px); tt = seconds since the window opened. Minimal: white, light-grey bubble, black accents only."""
    g = _chat_geom(c, user_text, w, h); u = g["u"]
    P = pal(c); INK = P["ink"]; RAD = P["rad"]
    win = np.empty((h, w, 3), np.uint8); win[:] = P["card"]
    # header
    cv2.circle(win, (int(40 * u), int(48 * u)), int(15 * u), INK, -1, cv2.LINE_AA)
    sb, sa = _spark_glyph(8 * u, P["card"]); blit(win, sb, sa, 40 * u, 48 * u)
    put_text(win, str(opt(c, "assistant", "Assistant")), 68 * u, 48 * u, 28 * u, INK, "Bold", "l")          # --opt assistant=Name
    cv2.line(win, (0, int(96 * u)), (w, int(96 * u)), P["line"], max(1, int(1.5 * u)))
    put_text(win, "Today", w / 2.0, 130 * u, 19 * u, P["dim"], "Medium", "c")
    # user bubble (right) with the request
    bb, ba = rrect_layer(g["bw"], g["bh"], 24 * u * RAD, P["surface"])
    blit(win, bb, ba, w - 36 * u - g["bw"] / 2, g["bub_top"] + g["bh"] / 2)
    tk_ = clamp01(tt / 0.06)
    for i, ln in enumerate(g["rows"]):
        put_text(win, ln, w - 36 * u - g["bw"] + 24 * u, g["bub_top"] + 15 * u + 19 * u + i * 38 * u, g["fsz"], tuple(int(lerp(205, INK[j], tk_)) for j in range(3)), "Medium", "l")
    # attachment caption under the video card (the card itself is drawn by fx_chat)
    put_text(win, "raw.mov · 1:09", w - 36 * u, g["cap_y"], 19 * u, (170, 170, 170), "Medium", "r")
    # assistant: avatar, typing dots, "On it." and the three-step list (timings measured on the original)
    ay = g["ay"]
    ia_ = clamp01((tt - 0.17) / 0.06)
    if ia_ > 0:
        ib, ia = disk_layer(20 * u, INK); blit(win, ib, ia, 58 * u, ay, ia_)
        sb, sa = _spark_glyph(9 * u, P["card"]); blit(win, sb, sa, 58 * u, ay, ia_)
    if 0.27 < tt < 0.65:
        for i in range(3):
            ph = (tt * 7.0 - i * 0.33) % 1.0
            cv2.circle(win, (int(100 * u + i * 24 * u), int(ay - 5 * u * math.sin(ph * math.pi))), max(2, int(5 * u)), (205 - 85 * math.sin(ph * math.pi),) * 3, -1, cv2.LINE_AA)
    if tt >= 0.62:
        put_text(win, "On it.", 100 * u, ay, 27 * u, INK, "Bold", "l", op=clamp01((tt - 0.62) / 0.07))
        starts = (0.77, 0.93, 1.10); checks = (0.83, 1.03, 9.0)
        for i, nm in enumerate(lines):
            st = starts[min(i, 2)]
            uu = clamp01((tt - st) / 0.06)
            if uu <= 0.01: continue
            y = ay + (68 + 60 * i) * u; x = 58 * u
            done = tt >= checks[min(i, 2)]
            if done:
                cb, ca = disk_layer(14 * u, P["check"][0]); blit(win, cb, ca, x, y)
                tk = max(2, int(2.4 * u))
                cv2.line(win, (int(x - 6 * u), int(y + 0.5 * u)), (int(x - 1.5 * u), int(y + 5 * u)), P["check"][1], tk, cv2.LINE_AA)
                cv2.line(win, (int(x - 1.5 * u), int(y + 5 * u)), (int(x + 6.5 * u), int(y - 4.5 * u)), P["check"][1], tk, cv2.LINE_AA)
            elif tt < st + 0.07:
                cv2.circle(win, (int(x), int(y)), max(2, int(4 * u)), (200, 200, 200), -1, cv2.LINE_AA)
            else:
                a0 = (tt * 400) % 360
                cv2.ellipse(win, (int(x), int(y)), (int(12 * u), int(12 * u)), 0, a0, a0 + 270, (150, 150, 150), max(1, int(2.2 * u)), cv2.LINE_AA)
            put_text(win, nm, 100 * u, y, 25 * u, INK, "Medium", "l", op=uu * (1.0 if done or tt > st + 0.07 else 0.55))
    # input bar
    ib2, ia2 = rrect_layer(w - 72 * u, 76 * u, 38 * u * RAD, P["surface"], P["line"], max(1, 1.5 * u))
    blit(win, ib2, ia2, w / 2.0, h - 78 * u)
    put_text(win, "Reply to %s..." % str(opt(c, "assistant", "Assistant")), 72 * u, h - 78 * u, 22 * u, P["dim"], "Regular", "l")
    bx = w - 70 * u; by = h - 78 * u
    cb, ca = disk_layer(22 * u, INK); blit(win, cb, ca, bx, by); WH = P["card"]
    tk = max(2, int(2.4 * u))
    cv2.line(win, (int(bx), int(by + 8 * u)), (int(bx), int(by - 8 * u)), WH, tk, cv2.LINE_AA)
    cv2.line(win, (int(bx - 7 * u), int(by - 1 * u)), (int(bx), int(by - 8.5 * u)), WH, tk, cv2.LINE_AA)
    cv2.line(win, (int(bx + 7 * u), int(by - 1 * u)), (int(bx), int(by - 8.5 * u)), WH, tk, cv2.LINE_AA)
    return win

def fx_chat(img, t, c):
    W, H = c.W, c.H
    D = 2.03
    if t > D: return img
    u = W / 1080.0
    P = pal(c); RAD = P["rad"]
    bg = light_bg(c)
    wx0, wy0, wx1, wy1 = 0.036 * W, 0.17 * H, 0.964 * W, 0.83 * H
    ww, wh = int(wx1 - wx0), int(wy1 - wy0)
    user = opt(c, "text", "Edit this video, caption every word, then add these effects.")
    lines = items_opt(c, ["Cut the pauses", "Caption every word", "Add the effects"])[:3]
    g = _chat_geom(c, user, ww, wh)
    full = (0.5 * W, 0.5 * H, W, H)
    card = (wx0 + g["card_x"], wy0 + g["card_top"] + g["card_h"] / 2, g["card_w"], g["card_h"])
    def mixbox(a, b, v): return tuple(lerp(a[i], b[i], v) for i in range(4))
    win_a = smooth(0.20, 0.31, t) * (1 - smooth(1.62, 1.70, t))
    if t < 0.05: box = full
    elif t < 0.25: box = mixbox(full, card, ease((t - 0.05) / 0.20))
    elif t < 1.70: box = card
    elif t < 1.87: box = mixbox(card, full, ease((t - 1.70) / 0.17))
    else: box = full
    out = bg
    if win_a > 0.01:
        win = _chat_window(c, W, H, user, lines, max(0.0, t - 0.3), ww, wh)
        wb, wa = rrect_layer(ww, wh, 28 * u * RAD)
        soft_shadow2(out, wa, wx0 + wa.shape[1] / 2, wy0 + wa.shape[0] / 2, 0, 8 * u, 18 * u, 0.16 * win_a)
        wwin = win
        if wwin.shape[:2] != wa.shape[:2]: wwin = cv2.resize(wwin, (wa.shape[1], wa.shape[0]))
        blit(out, wwin, wa, wx0 + wa.shape[1] / 2, wy0 + wa.shape[0] / 2, win_a)
    bx, by, bw, bh = box
    cd = F.resize(img, bw, bh)
    f = clamp01((W - bw) / max(1.0, W - g["card_w"]))
    cb, ca = rrect_layer(cd.shape[1], cd.shape[0], 18 * u * f * RAD)
    blit(out, cd, ca[:cd.shape[0], :cd.shape[1]], bx, by)
    return out

# ----------------------------------------------------------------------------- 4. snap zoom
def fx_snapzoom(img, t, c):
    W, H = c.W, c.H
    D = 2.45
    if t > D: return img
    fb = face(img, c); cx = fb[0] + fb[2] / 2; cy = fb[1] + fb[3] * 0.45
    k = face_scale(img, c)
    s0 = F.kf(t, [(0, 2.1), (0.08, 2.1), (0.30, 1.45), (1.05, 1.58), (1.12, 1.58), (1.22, 1.95), (1.9, 2.05), (1.98, 2.05), (2.08, 1.0), (2.45, 1.0)])
    s = 1 + (s0 - 1) * k
    bl = 0.0
    if t < 0.3: bl = 0.45 * (1 - t / 0.3)
    elif 1.1 < t < 1.3: bl = 0.40 * math.sin(math.pi * (t - 1.1) / 0.2)
    elif 1.95 < t < 2.2: bl = 0.45 * math.sin(math.pi * (t - 1.95) / 0.25)
    out = zoom_at(img, s, cx, cy, bl * k)
    if bl > 0.05: out = cv2.GaussianBlur(out, (0, 0), 0.0045 * W * bl / 0.4)
    return out

# ----------------------------------------------------------------------------- 5. checklist pop
def _spark_glyph(r, col):
    n = int(2 * r + 6); b = np.zeros((n, n, 3), np.uint8); b[:] = col; a = np.zeros((n, n), np.uint8)
    for i in range(10):
        ang = math.radians(i * 36); r0, r1 = r * 0.30, r * 0.95
        cv2.line(a, (int(n / 2 + r0 * math.cos(ang)), int(n / 2 + r0 * math.sin(ang))), (int(n / 2 + r1 * math.cos(ang)), int(n / 2 + r1 * math.sin(ang))), 255, max(1, int(r * 0.14)), cv2.LINE_AA)
    return b, a.astype(np.float32) / 255.0

def fx_checklistpop(img, t, c):
    W, H = c.W, c.H
    D = 1.84
    if t > D: return img
    u = W / 1080.0
    items = items_opt(c, ["Edit", "Captions", "Effects"])[:4]
    out = img.copy()
    ph = 76 * u; pitch = 98 * u; R = 0.94 * W; y0 = 0.37 * H
    t_on = [0.22, 0.58, 0.95, 1.2]
    fade = 1 - smooth(1.62, 1.78, t)
    P = pal(c); INK = P["ink"]; RAD = P["rad"]
    if "clp" not in c.state:
        L = []
        for name in items:
            tw = text_width(name, 29 * u, "Medium"); pw = 78 * u + tw + 32 * u
            pb, pa = rrect_layer(pw, ph, ph / 2 * RAD, P["card"], P["line"], max(1.0, 1.6 * u))
            pend = pb.copy(); done = pb.copy()
            cx_, cy_ = int(24 * u + 17 * u), pb.shape[0] // 2
            cv2.circle(pend, (cx_, cy_), int(16 * u), P["dim"], max(1, int(2.2 * u)), cv2.LINE_AA)
            cv2.circle(done, (cx_, cy_), int(17 * u), P["check"][0], -1, cv2.LINE_AA)
            tk = max(2, int(2.6 * u))
            cv2.line(done, (int(cx_ - 7 * u), int(cy_ + 0.5 * u)), (int(cx_ - 2 * u), int(cy_ + 5.5 * u)), P["check"][1], tk, cv2.LINE_AA)
            cv2.line(done, (int(cx_ - 2 * u), int(cy_ + 5.5 * u)), (int(cx_ + 7.5 * u), int(cy_ - 5.5 * u)), P["check"][1], tk, cv2.LINE_AA)
            for bmp in (pend, done): put_text(bmp, name, 78 * u, pb.shape[0] / 2.0, 29 * u, INK, "Medium", "l")
            L.append((pend, done, pa))
        c.state["clp"] = L
    sb, sa = _spark_glyph(0.010 * W, P["dim"])
    for i, name in enumerate(items):
        pend, done, pa = c.state["clp"][i]
        pw = pa.shape[1]; yc = y0 + i * pitch + ph / 2; xc = R - pw / 2
        u_ = back_out(clamp01((t - t_on[i]) / 0.22))
        if u_ <= 0.01:
            blit(out, sb, sa, R - pw + 41 * u, yc, 0.9 * fade * smooth(0.0, 0.1, t))      # loading spark placeholder
            continue
        soft_shadow2(out, pa, xc, yc, 0, 7 * u, 10 * u, 0.20 * fade, u_)
        blit(out, done if t > t_on[i] + 0.28 else pend, pa, xc, yc, fade * clamp01(u_ * 1.6), 0, u_)
    return out

# ----------------------------------------------------------------------------- 6. headline storm
# (tag, text, kind, y_frac, angle, left_edge_frac (of W; negative = starts off-screen), enter_from, t_in)
_HS = [("BREAKING", "AI NOW EDITS VIDEO", "white", 0.222, -5.5, 0.01, "L", 0.00),
       ("JUST IN", "20 EFFECTS. ONE PROMPT.", "white", 0.285, 3.0, 0.30, "R", 0.14),
       ("BREAKING", "EDITORS ON NOTICE", "black", 0.345, -5.0, -0.02, "L", 0.28),
       ("", "EVERY WORD CAPTIONED", "white", 0.395, -6.5, 0.60, "R", 0.42),
       ("BREAKING", "NO TIMELINE NEEDED", "white", 0.455, 4.0, -0.35, "L", 0.52),
       ("JUST IN", "THE AI EDIT IS HERE", "black", 0.525, -3.5, 0.10, "R", 0.62),
       ("UPDATE", "MADE WITH AI", "black", 0.625, -2.5, 0.52, "R", 0.76),
       ("JUST IN", "20 EFFECTS INSIDE", "white", 0.700, 3.0, 0.52, "R", 0.88),
       ("BREAKING", "AI EDITS", "white", 0.765, -5.0, -0.04, "L", 1.0)]

_HS_FRONT = {3: 0.070, 5: 0.135, 7: 0.205}   # strips that cross IN FRONT of the person: index -> distance below the chin (fraction of H); the others fly behind

def _strip(tag, text, kind, W, H, P):
    fh = int(0.038 * H); fs = 0.040 * W
    tb_, ta_ = text_layer(text, fs, P["ink"] if kind == "white" else P["card"], "Black")
    tw_ = tb_.shape[1]
    parts = []
    x = 0
    if tag:
        tgb, tga = text_layer(tag, 0.016 * W, P["tag_light"][1] if kind == "white" else P["tag_dark"][1], "Bold", spacing=0.06)
        tw2 = tgb.shape[1] + int(0.02 * W)
        parts.append(("tag", tw2, tgb, tga)); x += tw2
    total = x + tw_ + int(0.04 * W)
    bgcol = P["card"] if kind == "white" else P["ink"]
    body = np.empty((fh, total, 3), np.uint8); body[:] = bgcol
    al = np.ones((fh, total), np.float32)
    xx = 0
    if tag:
        body[:, :x] = P["tag_light"][0] if kind == "white" else P["tag_dark"][0]
        th, tw = parts[0][2].shape[:2]; y0 = (fh - th) // 2
        body[y0:y0 + th, int(0.01 * W):int(0.01 * W) + tw] = (parts[0][2] * parts[0][3][..., None] + body[y0:y0 + th, int(0.01 * W):int(0.01 * W) + tw] * (1 - parts[0][3][..., None])).astype(np.uint8)[:, :body.shape[1] - int(0.01 * W)][:, :tw]
    th, tw = tb_.shape[:2]; y0 = (fh - th) // 2; x0 = x + int(0.02 * W)
    reg = body[max(0, y0):y0 + th, x0:x0 + tw]
    t2 = tb_[max(0, -y0):max(0, -y0) + reg.shape[0], :reg.shape[1]]; a2 = ta_[max(0, -y0):max(0, -y0) + reg.shape[0], :reg.shape[1]]
    reg[:] = (reg * (1 - a2[..., None]) + t2 * a2[..., None]).astype(np.uint8)
    return body, al

def fx_headlinestorm(img, t, c):
    W, H, sc = c.W, c.H, c.sc
    D = 2.05
    if t > D: return img
    phr = items_opt(c, [])
    strips = list(_HS)
    if phr:
        custom = [s.strip().upper() for s in phr if s.strip()]
        strips = [(s[0], custom[i % len(custom)], s[2], s[3], s[4], s[5], s[6], s[7]) for i, s in enumerate(strips)]
    if "hs" not in c.state:
        P_ = pal(c); c.state["hs"] = {i: _strip(s[0], s[1], s[2], W, H, P_) for i, s in enumerate(strips)}
    back = img.copy(); front = None
    fbh = face(img, c); dyoff = float(np.clip((fbh[1] + fbh[3] * 0.5) - 0.43 * H, -0.25 * H, 0.1 * H)) * 0.9
    out_k = smooth(1.82, 2.0, t)
    for i, (tag, text, kind, yf, ang, lf, side, t0) in enumerate(strips):
        body, al = c.state["hs"][i]
        bh_, bw_ = body.shape[:2]
        u = ease(clamp01((t - t0) / 0.42))
        if u <= 0.001: continue
        left_rest = lf * W
        start = (-1.25 * W) if side == "L" else (1.25 * W)
        left = lerp(start, left_rest, u) + (0.012 * W * (t - t0 - 0.4) if t - t0 > 0.4 else 0) * (1 if side == "L" else -1)
        left = lerp(left, (-1.4 * W if side == "L" else 1.4 * W), out_k)
        cx = left + bw_ / 2
        cy = yf * H + dyoff * (0.3 + 0.7 * min(1.0, yf / 0.5)) + 0.004 * H * math.sin(t * 3 + i)
        if i in _HS_FRONT:
            if front is None: front = []
            cy = min(0.93 * H, fbh[1] + fbh[3] + _HS_FRONT[i] * H) + 0.004 * H * math.sin(t * 3 + i)     # always under the chin, never over the face
            front.append((body, al, cx, cy, ang, out_k)); continue
        soft_shadow2(back, al, cx, cy, 0, 0.004 * H, 0.004 * W, 0.22 * (1 - out_k), 1.0, ang)
        blit(back, body, al, cx, cy, 1.0, ang)
    m = matte(img, c)[..., None]
    res = (back.astype(np.float32) * (1 - m) + img.astype(np.float32) * m).astype(np.uint8)
    for body, al, cx, cy, ang, ok in (front or []):
        soft_shadow2(res, al, cx, cy, 0, 0.005 * H, 0.006 * W, 0.28 * (1 - ok), 1.0, ang)
        blit(res, body, al, cx, cy, 1.0, ang)
    return res

# ----------------------------------------------------------------------------- 11. paper cutout
_PG = {}
def _paper_gain(W, H):
    """cached multiplicative paper texture: soft mottling + fine grain + short fibres + a faint vignette (never flat colour)"""
    k = (W, H)
    if k in _PG: return _PG[k]
    rng = np.random.default_rng(7)
    g = np.zeros((H, W), np.float32)
    for frac, amp in ((0.02, 0.016), (0.07, 0.012), (0.30, 0.008)):
        n = rng.standard_normal((max(2, int(H * frac)), max(2, int(W * frac)))).astype(np.float32)
        g += cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC) * amp
    g += cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.7) * 0.05           # fine grain
    fib = np.zeros((H, W), np.float32)
    for _ in range(int(W * H / 2600)):                                                                  # fibres
        x0, y0 = rng.uniform(0, W), rng.uniform(0, H); ln = rng.uniform(5, 20) * W / 1080.0; an = rng.uniform(0, np.pi)
        cv2.line(fib, (int(x0), int(y0)), (int(x0 + ln * np.cos(an)), int(y0 + ln * np.sin(an))), float(rng.choice([-1.0, 1.0])), 1, cv2.LINE_AA)
    g += cv2.GaussianBlur(fib, (0, 0), 0.6) * 0.07
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r2 = ((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2)
    g -= 0.10 * r2 / 0.5
    _PG[k] = (1.0 + g).astype(np.float32)
    return _PG[k]

def _shift(a, dx, dy):
    return cv2.warpAffine(a, np.float32([[1, 0, dx], [0, 1, dy]]), (a.shape[1], a.shape[0]), borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def _paper_shadow(bgf, a, W, lift=1.0):
    """two layers like a piece lying on a table: a tight dark contact shadow + a wide soft one"""
    for dx, dy, bl, st in ((0.0012 * W, 0.0022 * W, 0.0018 * W, 0.34), (0.006 * W * lift, 0.012 * W * lift, 0.011 * W * lift, 0.20)):
        sh = cv2.GaussianBlur(_shift(a, dx, dy), (0, 0), max(0.6, bl)) * st
        bgf *= (1 - sh[..., None])

def _paper_piece(bgf, a, col, gain, W, lift=1.0, shadow=True):
    """paints one paper shape: shadow, grain, a slightly darker cut edge"""
    if shadow: _paper_shadow(bgf, a, W, lift)
    er = cv2.erode(a, np.ones((3, 3), np.uint8))
    rim = cv2.GaussianBlur(np.clip(a - er, 0, 1), (0, 0), 0.8)
    colimg = np.array(col, np.float32)[None, None, :] * gain[..., None]
    colimg = colimg * (1 - 0.30 * np.clip(rim, 0, 1)[..., None])
    bgf *= (1 - a[..., None]); bgf += colimg * a[..., None]

def _torn_strip(H, W, rng, yc, ang, thick):
    """a band of paper ripped by hand: both long edges are wobbly; returns (outer white-core mask, inner coloured mask)"""
    n = 120
    xs = np.linspace(-0.08 * W, 1.08 * W, n)
    def edge(amp):
        v = cv2.resize(rng.standard_normal((1, 14)).astype(np.float32), (n, 1), interpolation=cv2.INTER_CUBIC)[0] * amp * 0.5
        return v + rng.standard_normal(n).astype(np.float32) * amp * 0.22
    slope = math.tan(math.radians(ang))
    base = yc + (xs - 0.5 * W) * slope
    t1 = base - thick / 2 + edge(0.0035 * H); t2 = base + thick / 2 + edge(0.0035 * H)
    outer = np.zeros((H, W), np.uint8)
    cv2.fillPoly(outer, [np.concatenate([np.stack([xs, t1], 1), np.stack([xs, t2], 1)[::-1]]).astype(np.int32)], 255, cv2.LINE_AA)
    # the coloured top layer is torn away a little short of the white core on both sides -> white fibrous rim
    r1 = base - thick / 2 + 0.0055 * H + edge(0.004 * H); r2 = base + thick / 2 - 0.0055 * H + edge(0.004 * H)
    inner = np.zeros((H, W), np.uint8)
    cv2.fillPoly(inner, [np.concatenate([np.stack([xs, r1], 1), np.stack([xs, r2], 1)[::-1]]).astype(np.int32)], 255, cv2.LINE_AA)
    return outer.astype(np.float32) / 255.0, inner.astype(np.float32) / 255.0

def _paper_bg(c, var):
    key = ("ppbg", var)
    if key in c.state: return c.state[key]
    W, H = c.W, c.H; P = pal(c)
    gain = _paper_gain(W, H)
    rng = np.random.default_rng(100 + var)
    def j(a, amp=0.0035): return a + rng.uniform(-1, 1) * amp * W
    bgf = np.empty((H, W, 3), np.float32); bgf[:] = np.array(P["paper"], np.float32); bgf *= gain[..., None]
    def disk(x, y, r):
        m = np.zeros((H, W), np.uint8); cv2.circle(m, (int(x * 16), int(y * 16)), int(r * 16), 255, -1, cv2.LINE_AA, 4); return m.astype(np.float32) / 255.0
    # a torn strip diagonally behind the head
    outer, inner = _torn_strip(H, W, rng, 0.455 * H, -6 + rng.uniform(-0.6, 0.6), 0.070 * H)
    _paper_piece(bgf, outer, (250, 250, 250), gain, W, 0.8)
    _paper_piece(bgf, inner, P["p_tear"], gain, W, shadow=False)
    # a big disc, a small star, two dots, one white bar
    _paper_piece(bgf, disk(j(0.795 * W), j(0.255 * H), 0.195 * W), P["p_disc"], gain, W, 1.2)
    star = np.array([[math.cos(math.radians(-90 + i * 45)) * (1 if i % 2 == 0 else 0.30), math.sin(math.radians(-90 + i * 45)) * (1 if i % 2 == 0 else 0.30)] for i in range(8)])
    sm = np.zeros((H, W), np.uint8); cv2.fillPoly(sm, [(star * 0.075 * W + [j(0.108 * W), j(0.283 * H)]).astype(np.int32)], 255, cv2.LINE_AA)
    _paper_piece(bgf, sm.astype(np.float32) / 255.0, P["p_star"], gain, W)
    _paper_piece(bgf, disk(j(0.075 * W), j(0.585 * H), 0.030 * W), P["p_dot_a"], gain, W, 0.7)
    _paper_piece(bgf, disk(j(0.915 * W), j(0.60 * H), 0.018 * W), P["p_dot_b"], gain, W, 0.7)
    ang = -9 + rng.uniform(-0.7, 0.7)
    bw_, bh_ = 0.58 * W, 0.034 * H
    bm = np.zeros((H, W), np.uint8)
    cx_, cy_ = j(0.16 * W), j(0.70 * H)
    box = cv2.boxPoints(((cx_, cy_), (bw_, bh_), ang)).astype(np.int32)
    cv2.fillPoly(bm, [box], 255, cv2.LINE_AA)
    _paper_piece(bgf, bm.astype(np.float32) / 255.0, P["p_strip"], gain, W, 0.8)
    c.state[key] = bgf
    return bgf

def fx_papercutout(img, t, c):
    W, H, sc = c.W, c.H, c.sc
    D = 1.87
    if t > D: return img
    k = smooth(0.0, 0.1, t) * (1 - smooth(1.75, 1.87, t))
    var = int(t * 10) % 3                                              # stop-motion: the paper shifts a little every 3 frames
    P = pal(c); gain = _paper_gain(W, H)
    bgf = _paper_bg(c, var).copy()
    m = matte(img, c)
    # the person is cut out with scissors: white sticker border with a wobbly, hand-cut outline
    key = ("ppwob", var)
    if key not in c.state:
        rng = np.random.default_rng(300 + var)
        f = cv2.resize(rng.standard_normal((9, 5)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        c.state[key] = f / max(1e-6, float(np.abs(f).max()))
    dist = cv2.distanceTransform((m <= 0.45).astype(np.uint8), cv2.DIST_L2, 3)
    r = 0.026 * W * (1 + 0.28 * c.state[key])
    st = cv2.GaussianBlur(np.clip(r - dist + 0.5, 0, 1), (0, 0), 1.2)
    _paper_piece(bgf, st, P["p_sticker"], gain, W, 1.0)
    outf = bgf * (1 - m[..., None]) + img.astype(np.float32) * m[..., None]
    return F.mix(img, np.clip(outf, 0, 255).astype(np.uint8), k)

# ----------------------------------------------------------------------------- 14. liquid glass
_LG = [(0.0, -0.50, 0.15), (0.27, -0.18, 0.09), (0.54, -0.10, 0.10), (0.81, 0.04, 0.07), (1.09, -0.07, 0.07), (1.50, -0.07, 0.07)]   # offsets from the face centre (x in W, y in H)
def fx_liquidglass(img, t, c):
    W, H = c.W, c.H
    D = 1.55
    if t > D: return img
    env = smooth(0.0, 0.2, t) * (1 - smooth(1.3, 1.55, t))
    fb = face(img, c)
    cx = float(np.interp(t, [p[0] for p in _LG], [p[1] for p in _LG])) * W + fb[0] + fb[2] / 2
    cy = float(np.interp(t, [p[0] for p in _LG], [p[2] for p in _LG])) * H + fb[1] + fb[3] * 0.5
    R = 0.205 * W
    x0, x1 = int(max(0, cx - R * 1.2)), int(min(W, cx + R * 1.2)); y0, y1 = int(max(0, cy - R * 1.2)), int(min(H, cy + R * 1.2))
    if x1 - x0 < 4 or y1 - y0 < 4: return img
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = (xx - cx) / R; dy = (yy - cy) / R
    r = np.sqrt(dx * dx + dy * dy)
    inside = np.clip((1 - r) * R * 0.22, 0, 1)                      # soft edge
    # lens profile: magnify in the middle (1.28x), compress strongly towards the rim (glass sphere)
    rr = np.clip(r, 0, 1.0)
    src_r = rr * (0.80 - 0.0) + 0.30 * rr ** 3 * 0 + 0.20 * rr ** 4.5 * 1.0
    src_r = np.where(r < 1.0, rr * (0.78 + 0.34 * rr ** 3.2), r)
    f = np.where(r > 1e-4, src_r / np.maximum(r, 1e-4), 1.0)
    f = np.where(r < 1.0, f, 1.0)
    sx = (cx + dx * R * f); sy = (cy + dy * R * f)
    ca_ = 0.012 * R * np.clip(r, 0, 1) ** 3
    chans = []
    for off in (-1.0, 0.0, 1.0):
        mx_ = (sx + dx * R * (ca_ / R) * off * 9).astype(np.float32); my_ = (sy + dy * R * (ca_ / R) * off * 9).astype(np.float32)
        chans.append(cv2.remap(img[..., 0 if off < 0 else (1 if off == 0 else 2)], mx_, my_, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101))
    # chans order: B from -, G centre, R from +  -> merge as BGR
    refr = np.stack(chans, axis=-1)
    # highlights: bright thin arc at the upper-left rim, darker rim at the lower right
    ang = np.arctan2(dy, dx)
    rim = np.clip(1 - np.abs(r - 0.965) / 0.035, 0, 1)
    hl = rim * np.clip(np.cos(ang + 2.3) * 0.9 + 0.1, 0, 1)
    dk = rim * np.clip(-np.cos(ang + 2.3) * 0.6, 0, 1)
    veil = 0.07 * np.clip(1 - r, 0, 1) ** 0.5
    base = img[y0:y1, x0:x1].astype(np.float32)
    lens = refr.astype(np.float32) * (1 - veil[..., None]) + 255 * veil[..., None]
    lens = lens + (hl * 140)[..., None] - (dk * 60)[..., None]
    a = (inside * env)[..., None]
    out = img.copy()
    out[y0:y1, x0:x1] = np.clip(base * (1 - a) + lens * a, 0, 255).astype(np.uint8)
    return out

# ----------------------------------------------------------------------------- 16. green screen
def _skyline(c, W, H):
    key = "skyline"
    if key in c.state: return c.state[key].copy()
    # sky: deep blue at the top -> violet -> orange at the horizon (RGB measured on the original)
    ys = np.linspace(0, 1, H, dtype=np.float32)
    stops = [(0.0, (28, 52, 205)), (0.30, (40, 62, 215)), (0.50, (110, 75, 205)), (0.62, (200, 90, 150)), (0.70, (240, 110, 95)), (0.80, (250, 140, 70)), (1.0, (250, 140, 70))]
    sky = np.zeros((H, W, 3), np.float32)
    for ch in range(3):
        col = np.interp(ys, [s[0] for s in stops], [s[1][ch] for s in stops])
        sky[..., 2 - ch] = col[:, None]
    sky = np.clip(sky, 0, 255).astype(np.uint8)
    rng = np.random.default_rng(11)
    base_y = int(0.93 * H)
    x = -int(0.02 * W)
    dark = (14, 10, 10)
    while x < W:
        bw = int(rng.uniform(0.07, 0.14) * W); bh = int(rng.uniform(0.28, 0.62) * H)
        y0 = base_y - bh
        cv2.rectangle(sky, (x, y0), (x + bw, H), dark, -1)
        if rng.random() < 0.4: cv2.rectangle(sky, (x + int(bw * 0.2), y0 - int(0.012 * H)), (x + int(bw * 0.8), y0), dark, -1)
        cols = max(2, int(bw / (0.022 * W)))
        for ci in range(cols):
            for ry in range(int(bh / (0.026 * H))):
                if rng.random() < 0.38:
                    wx = x + int(bw * (ci + 0.5) / cols); wy = y0 + int(0.015 * H) + ry * int(0.026 * H)
                    cv2.rectangle(sky, (wx - int(0.003 * W), wy - int(0.003 * W)), (wx + int(0.003 * W), wy + int(0.003 * W)), (60, 110, 255), -1)
        x += bw + int(rng.uniform(0, 0.012) * W)
    tx = int(0.69 * W)
    cv2.rectangle(sky, (tx - int(0.006 * W), int(0.18 * H)), (tx + int(0.006 * W), int(0.38 * H)), dark, -1)
    cv2.ellipse(sky, (tx, int(0.38 * H)), (int(0.03 * W), int(0.012 * H)), 0, 0, 360, dark, -1)
    cv2.rectangle(sky, (tx - int(0.012 * W), int(0.38 * H)), (tx + int(0.012 * W), int(0.46 * H)), dark, -1)
    cv2.rectangle(sky, (tx - int(0.05 * W), int(0.46 * H)), (tx + int(0.05 * W), base_y), dark, -1)
    cv2.rectangle(sky, (0, base_y), (W, H), dark, -1)
    c.state[key] = sky
    return sky.copy()

def _green_bg(c):
    if "greenbg" not in c.state:
        W, H = c.W, c.H
        xx = np.arange(W, dtype=np.float32)[None, :]; yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        fold = 0.5 + 0.5 * np.cos(2 * math.pi * xx / (0.082 * W)) * 0.6 + 0.2 * np.cos(2 * math.pi * xx / (0.041 * W) + 1.0)
        base = np.zeros((H, W, 3), np.float32)
        base[..., 1] = 120 + 70 * fold; base[..., 0] = 55 + 22 * fold; base[..., 2] = 22 + 22 * fold
        base *= (1 - 0.22 * np.abs(xx / W - 0.5) * 2)[..., None] * 1.0
        base *= (1 - 0.2 * np.clip(yy - 0.55, 0, 1))[..., None]
        c.state["greenbg"] = np.clip(base, 0, 255).astype(np.uint8)
    return c.state["greenbg"].copy()

def green_composite(img, c, sky_r=None):
    """person over the green curtain; sky_r (px) = radius of the sky reveal circle centred at the bottom"""
    W, H = c.W, c.H
    bg = _green_bg(c)
    if sky_r is not None and sky_r > 0:
        sky = _skyline(c, W, H)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        mk = (np.hypot(xx - 0.5 * W, yy - 1.05 * H) < sky_r).astype(np.float32)
        mk = cv2.GaussianBlur(mk, (0, 0), 2.5)
        bg = np.clip(bg.astype(np.float32) * (1 - mk[..., None]) + sky.astype(np.float32) * mk[..., None], 0, 255).astype(np.uint8)
    return over_person(bg, img, c)

def fx_greenscreen(img, t, c):
    W, H = c.W, c.H
    D = 2.05
    if t > D: return img
    k = smooth(0.0, 0.1, t) * (1 - smooth(1.85, 2.05, t))
    r = ease(clamp01((t - 1.1) / 0.32)) * 1.45 * H if t > 1.1 else None
    out = green_composite(img, c, r)
    return F.mix(img, out, k)

# ----------------------------------------------------------------------------- 18. digital zoom
def fx_digitalzoom(img, t, c):
    W, H, sc = c.W, c.H, c.sc
    D = 2.05
    if t > D: return img
    fb = face(img, c); cx = fb[0] + fb[2] / 2; cy = fb[1] + fb[3] * 0.45
    k = face_scale(img, c)
    s0 = F.kf(t, [(0, 1.0), (0.12, 1.0), (0.30, 1.6), (0.72, 1.6), (0.88, 2.6), (1.50, 2.62), (1.62, 2.62), (1.80, 1.0), (2.05, 1.0)])
    s = 1 + (s0 - 1) * k
    shown = 1 + (s0 - 1)
    jit = np.random.default_rng(int(t * 24)).normal(0, 1.2, 2) * (1 if 0.3 < t < 1.7 else 0) * sc
    out = zoom_at(img, s, cx + jit[0], cy + jit[1], 0.22 * math.sin(math.pi * clamp01((t - 1.62) / 0.18)) * k if 1.62 < t < 1.8 else 0.0)
    env = smooth(0.04, 0.2, t) * (1 - smooth(1.9, 2.05, t))
    col = (255, 255, 255)
    L = 0.06 * W
    ov = out.copy()
    for (x, y, sx_, sy_) in ((0.058, 0.121, 1, 1), (0.942, 0.121, -1, 1), (0.058, 0.772, 1, -1), (0.942, 0.772, -1, -1)):
        px, py = x * W, y * H
        cv2.line(ov, (int(px), int(py)), (int(px + sx_ * L), int(py)), col, max(2, int(0.004 * W)), cv2.LINE_AA)
        cv2.line(ov, (int(px), int(py)), (int(px), int(py + sy_ * L)), col, max(2, int(0.004 * W)), cv2.LINE_AA)
    cb, ca = disk_layer(0.006 * W, ORANGE); blit(ov, cb, ca, 0.074 * W, 0.1195 * H)
    put_text(ov, "REC", 0.088 * W, 0.1195 * H, 0.0155 * W, col, "Bold", "l", spacing=0.08)
    put_text(ov, "00:42:%02d" % (16 + int(t * 2) % 8), 0.942 * W, 0.1195 * H, 0.0155 * W, (235, 235, 235), "Medium", "r")
    pb, pa = rrect_layer(0.115 * W, 0.0285 * H, 0.0142 * H, (30, 30, 30))
    blit(ov, pb, pa, 0.5 * W, 0.1195 * H, 0.55)
    put_text(ov, "%.1f×" % shown, 0.5 * W, 0.1195 * H, 0.0165 * W, col, "Bold")
    if 0.2 < t < 0.8:                                                # focus box on the eyes
        fa = smooth(0.2, 0.3, t) * (1 - smooth(0.65, 0.8, t))
        bx0, by0, bx1, by1 = int(0.37 * W), int(0.305 * H), int(0.62 * W), int(0.36 * H)
        al = fa * 0.9
        for (xa, ya, xb, yb) in ((bx0, by0, bx0 + 14, by0), (bx0, by0, bx0, by0 + 14), (bx1, by0, bx1 - 14, by0), (bx1, by0, bx1, by0 + 14), (bx0, by1, bx0 + 14, by1), (bx0, by1, bx0, by1 - 14), (bx1, by1, bx1 - 14, by1), (bx1, by1, bx1, by1 - 14)):
            cv2.line(ov, (xa, ya), (xb, yb), ORANGE, 2, cv2.LINE_AA)
        ov = F.mix(out, ov, 1.0) if al >= 0.99 else ov
    return F.mix(out, ov, env)

# ----------------------------------------------------------------------------- 19. phone mockup
def fx_phonemock(img, t, c):
    W, H, sc = c.W, c.H, c.sc
    D = 1.16
    if t > D: return img
    k = ease(clamp01(t / 0.3)) * (1 - smooth(1.06, 1.16, t))
    if k <= 0.002: return img
    bg = light_bg(c)
    pw = 0.47 * W; ph = 0.49 * H
    pcx, pcy = 0.5 * W, 0.505 * H
    body_b, body_a = rrect_layer(pw, ph, 0.09 * pw, (16, 14, 14), (78, 74, 74), max(2, 0.009 * pw))
    soft_shadow2(bg, body_a, pcx, pcy, 0, 0.014 * H, 0.03 * W, 0.32)
    blit(bg, body_b, body_a, pcx, pcy)
    sw, sh_ = pw - 0.052 * pw, ph - 0.036 * pw
    ar = sw / sh_; iw = H * ar
    crop = img[:, int((W - iw) / 2):int((W + iw) / 2)] if iw <= W else img[int((H - W / ar) / 2):int((H + W / ar) / 2)]
    scr = cv2.resize(crop, (int(sw), int(sh_)), interpolation=cv2.INTER_AREA)
    sb, sa = rrect_layer(scr.shape[1], scr.shape[0], 0.075 * pw, (0, 0, 0))
    scr = scr[:sa.shape[0], :sa.shape[1]]
    sh_w, sh_h = scr.shape[1], scr.shape[0]
    # Reels-style UI measured on the original: title top-left, like / comment / share on the right, avatar + name + Follow + caption bottom-left
    put_text(scr, "Reels", 0.085 * sh_w, 0.062 * sh_h, 0.026 * W, (255, 255, 255), "Bold", "l")
    for j, (cy_, lab) in enumerate(((0.615, "12.4K"), (0.700, "3,108"))):
        cx_ = int(0.915 * sh_w); cy2 = int(cy_ * sh_h); r_ = int(0.0105 * W)
        if j == 0:
            th = np.linspace(0, 2 * np.pi, 60)
            hx = 16 * np.sin(th) ** 3; hy = -(13 * np.cos(th) - 5 * np.cos(2 * th) - 2 * np.cos(3 * th) - np.cos(4 * th))
            cv2.polylines(scr, [np.stack([cx_ + hx * r_ / 17.0, cy2 + hy * r_ / 17.0], 1).astype(np.int32)], True, (255, 255, 255), 2, cv2.LINE_AA)
        else:
            cv2.ellipse(scr, (cx_, cy2), (r_, int(r_ * 0.85)), 0, 0, 360, (255, 255, 255), 2, cv2.LINE_AA)
        put_text(scr, lab, cx_, cy2 + 0.036 * sh_h, 0.0105 * W, (255, 255, 255), "Bold", "c")
    cb, ca = disk_layer(0.0105 * W, (210, 210, 210)); blit(scr, cb, ca, 0.075 * sh_w, 0.915 * sh_h)
    put_text(scr, opt(c, "text", "yourname"), 0.135 * sh_w, 0.915 * sh_h, 0.0125 * W, (255, 255, 255), "Bold", "l")
    fb_, fa_ = rrect_layer(0.17 * sh_w, 0.028 * sh_h, 0.006 * sh_h, (255, 255, 255), (255, 255, 255), 1)
    pb_ = np.zeros_like(fb_); blit(scr, pb_, fa_ * 0.0, 0.01, 0.01)
    put_text(scr, "Follow", 0.57 * sh_w, 0.915 * sh_h, 0.0095 * W, (255, 255, 255), "Bold", "c")
    cv2.rectangle(scr, (int(0.47 * sh_w), int(0.90 * sh_h)), (int(0.67 * sh_w), int(0.93 * sh_h)), (255, 255, 255), 1, cv2.LINE_AA)
    put_text(scr, "20 video effects, all made with AI...", 0.065 * sh_w, 0.955 * sh_h, 0.0105 * W, (235, 235, 235), "Medium", "l")
    blit(bg, scr, sa[:scr.shape[0], :scr.shape[1]], pcx, pcy)
    ib, ia = rrect_layer(0.22 * pw, 0.040 * pw, 0.02 * pw, (8, 8, 8)); blit(bg, ib, ia, pcx, pcy - ph / 2 + 0.058 * pw)
    # the picture shrinks into the phone: the first moment is the full-frame rounded picture
    if t < 0.3:
        e = ease(t / 0.3)
        big = F.resize(img, lerp(W, sw, e), lerp(H, sh_, e))
        fb_, fa_ = rrect_layer(big.shape[1], big.shape[0], lerp(0.06 * W, 0.075 * pw, e))
        base = bg.copy(); blit(base, big, fa_[:big.shape[0], :big.shape[1]], lerp(0.5 * W, pcx, e), lerp(0.5 * H, pcy, e))
        return F.mix(img, base, ease(clamp01(t / 0.12)))
    return F.mix(img, bg, k) if k < 0.999 else bg

# ----------------------------------------------------------------------------- registry
def build(fx_mod):
    global F
    F = fx_mod
    def e(fn, ru, alias, dur, desc): return dict(fn=fn, ru=ru, alias=alias, kind="intro", dur=dur, desc=desc)
    return {
        "orbit":        e(fx_orbit, "орбита", ["orbit", "иконки по орбите"], 1.55, "7 минималистичных иконок (искра, волна, play, взрыв, CC, Aa, ножницы: белые плитки, тонкий чёрный значок) кружатся по пунктирному эллипсу вокруг человека, задняя половина уходит за него"),
        "chat":         e(fx_chat, "чат-захват", ["chat takeover", "чат", "окно чата"], 2.03, "видео сжимается в карточку и ложится в чат с ИИ под сообщением-запросом (светлый минималистичный чат: серый пузырь, «On it.», список с чёрными галочками, поле ответа), карточка раскрывается обратно; запрос через --text, пункты через --items"),
        "snapzoom":     e(fx_snapzoom, "щелчок-зум", ["snap zoom", "снап зум", "резкий зум"], 2.45, "три резких наезда на лицо (1.45×, 1.95×, обратно) с размытием и медленной доводкой"),
        "checklistpop": e(fx_checklistpop, "всплывающий чек-лист", ["checklist pop", "плашки с галочками"], 1.84, "белые плашки-пилюли с тонкой рамкой и чёрной галочкой выпрыгивают справа одна за другой (Edit, Captions, Effects), тень не обрезается; пункты через --items"),
        "headlinestorm": e(fx_headlinestorm, "шторм заголовков", ["headline storm", "бегущие заголовки", "новостные ленты"], 2.05, "чёрно-белые новостные ленты с тегами BREAKING / JUST IN влетают с обеих сторон: часть летит за человеком, три ленты проходят ПЕРЕД ним (под подбородком); тексты через --items"),
        "papercutout":  e(fx_papercutout, "бумажная вырезка", ["paper cutout", "наклейка", "стикер"], 1.87, "человек-наклейка с белым контуром на светлой бумаге: чёрный диск, звезда, точки, белая полоса, лёгкая покадровая дрожь"),
        "liquidglass":  e(fx_liquidglass, "жидкое стекло", ["liquid glass", "стеклянная линза"], 1.55, "большая стеклянная линза скользит по лицу, увеличивает и преломляет изображение"),
        "greenscreen":  e(fx_greenscreen, "хромакей", ["green screen", "зелёный экран"], 2.05, "зелёный занавес за человеком, затем снизу дугой раскрывается закатное небо с силуэтом города"),
        "digitalzoom":  e(fx_digitalzoom, "цифровой зум", ["digital zoom", "видоискатель"], 2.05, "видоискатель с REC, счётчиком зума и рамкой фокуса: 1.6× → 2.6× → резкий возврат"),
        "phonemock":    e(fx_phonemock, "телефон", ["phone mockup", "мокап телефона"], 1.16, "видео уменьшается в экран смартфона с интерфейсом приложения коротких видео (сердце, комментарии, подпись) на светлом фоне"),
    }
