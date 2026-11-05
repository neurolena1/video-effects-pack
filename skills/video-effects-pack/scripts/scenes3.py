"""
scenes3.py - 5 more effects (43-47): VARIETIES of effects the skill already has (orbit, green screen, checklist, headline storm, phone mock-up).
They look different from the older versions, so they live next to them as separate effects:
  43 iconsaround   - glossy coloured icons around the head      (older, minimal version: 'orbit')
  44 greenbg       - flat green background with a white sticker outline and tracking markers   (older: 'greenscreen')
  45 checklist2    - card with a title and a list; ticks are drawn one by one                  (older: 'checklistpop')
  46 headlinestorm2- coloured plates + lightning + camera shake                                (older: 'headlinestorm')
  47 phonemock2    - the video shrinks into a smartphone on a cream background with coloured blocks (older: 'phonemock')
All of them are intro effects: they play once from --start (the duration is built in), then the picture goes back to normal.
Colours come from the style palette (--style); if the style has no real accent colours (the built-in 'minimal' is grey),
a neutral colourful default (coral pink / amber / blue) is used, so these effects do not turn grey.
"""
import math
import numpy as np
import cv2
import scenes as S
from scenes import (pal, lerp, clamp01, ease, smooth, back_out, blit, put_text, text_width, text_layer, rrect_layer, disk_layer,
                    soft_shadow2, face, matte, zoom_at, opt, items_opt, lang)
from scenes2 import _Ov, _rr_path

def _F(): return S.F
def _on(col): return S._on(col)
def _mix(a, b, k): return S._mix(a, b, k)

from scenes2 import _acc as _pop          # accent colours: from the style, or a neutral colourful default if the style is grey

# ============================================================================= 43 icons around me (glossy)
_GI = {}
def _glyph(kind, S_):
    """white glyph mask (S x S, float 0..1) and a 'hole' mask (parts cut out of the glyph), drawn on a big canvas"""
    g = np.zeros((S_, S_), np.uint8); h = np.zeros((S_, S_), np.uint8)
    P_ = lambda pts: (np.asarray(pts, np.float64) * S_ * 16).astype(np.int32).reshape(-1, 1, 2)
    def poly(m, pts): cv2.fillPoly(m, [P_(pts)], 255, cv2.LINE_AA, 4)
    def circ(m, x, y, r): cv2.circle(m, (int(x * S_ * 16), int(y * S_ * 16)), int(r * S_ * 16), 255, -1, cv2.LINE_AA, 4)
    def rect(m, x0, y0, x1, y1, rad=0.0):
        r = rad * S_
        cv2.rectangle(m, (int(x0 * S_ + r), int(y0 * S_)), (int(x1 * S_ - r), int(y1 * S_)), 255, -1)
        cv2.rectangle(m, (int(x0 * S_), int(y0 * S_ + r)), (int(x1 * S_), int(y1 * S_ - r)), 255, -1)
        for (cx, cy) in ((x0 * S_ + r, y0 * S_ + r), (x1 * S_ - r, y0 * S_ + r), (x0 * S_ + r, y1 * S_ - r), (x1 * S_ - r, y1 * S_ - r)):
            cv2.circle(m, (int(cx), int(cy)), int(r), 255, -1, cv2.LINE_AA)
    if kind == "music":
        cv2.ellipse(g, (int(0.38 * S_), int(0.69 * S_)), (int(0.125 * S_), int(0.092 * S_)), -22, 0, 360, 255, -1, cv2.LINE_AA)
        rect(g, 0.485, 0.27, 0.54, 0.69, 0.0)
        poly(g, [(0.50, 0.27), (0.50, 0.36), (0.74, 0.47), (0.74, 0.37)])
    elif kind == "image":
        rect(g, 0.20, 0.24, 0.80, 0.76, 0.06); rect(h, 0.245, 0.285, 0.755, 0.715, 0.035)
        g2 = np.zeros_like(g); poly(g2, [(0.27, 0.70), (0.43, 0.46), (0.55, 0.62), (0.63, 0.52), (0.73, 0.70)]); circ(g2, 0.66, 0.36, 0.06)
        h = cv2.bitwise_and(h, cv2.bitwise_not(g2))
    elif kind == "chat":
        rect(g, 0.19, 0.25, 0.81, 0.63, 0.10); poly(g, [(0.33, 0.60), (0.33, 0.80), (0.52, 0.60)])
        for x in (0.36, 0.50, 0.64): circ(h, x, 0.44, 0.04)
    elif kind == "play":
        poly(g, [(0.36, 0.27), (0.36, 0.73), (0.76, 0.50)])
    elif kind == "bars":
        rect(g, 0.25, 0.54, 0.37, 0.75, 0.025); rect(g, 0.44, 0.34, 0.56, 0.75, 0.025); rect(g, 0.63, 0.44, 0.75, 0.75, 0.025)
    elif kind == "doc":
        poly(g, [(0.30, 0.21), (0.57, 0.21), (0.72, 0.37), (0.72, 0.79), (0.30, 0.79)])
        for y in (0.52, 0.62, 0.71): rect(h, 0.38, y - 0.017, 0.64, y + 0.017, 0.012)
        poly(h, [(0.57, 0.21), (0.57, 0.37), (0.72, 0.37)])
    elif kind == "spark":
        pts = []
        for i in range(8):
            a = math.radians(-90 + i * 45); r = 0.31 if i % 2 == 0 else 0.075
            pts.append((0.46 + r * math.cos(a), 0.54 + r * math.sin(a)))
        poly(g, pts)
        pts = []
        for i in range(8):
            a = math.radians(-90 + i * 45); r = 0.10 if i % 2 == 0 else 0.03
            pts.append((0.73 + r * math.cos(a), 0.27 + r * math.sin(a)))
        poly(g, pts)
    elif kind == "bolt":
        poly(g, [(0.56, 0.17), (0.31, 0.55), (0.48, 0.55), (0.42, 0.84), (0.70, 0.43), (0.52, 0.43)])
    return g.astype(np.float32) / 255.0, h.astype(np.float32) / 255.0

def _gloss_icon(kind, s, col):
    """glossy squircle: vertical colour gradient, soft top highlight, white (or dark on light colours) glyph with a small shadow"""
    key = (kind, int(s), col)
    if key in _GI: return _GI[key]
    ss = 3; N = int(s) * ss
    top = _mix(col, (255, 255, 255), 0.30); bot = _mix(col, (0, 0, 0), 0.16)
    yy = (np.arange(N, dtype=np.float32) / (N - 1))[:, None, None]
    body = (np.array(top, np.float32) * (1 - yy) + np.array(bot, np.float32) * yy) * np.ones((1, N, 1), np.float32)
    # gloss: a soft light band in the top half
    gl = np.clip(1 - np.arange(N, dtype=np.float32) / (0.50 * N), 0, 1)[:, None] ** 1.6 * 0.20
    body = body * (1 - gl[..., None]) + 255.0 * gl[..., None]
    gm, hm = _glyph(kind, N)
    gcol = np.array(_on(col) if sum(col) > 520 else (255, 255, 255), np.float32)
    gm = gm * (1 - hm)
    sh = cv2.GaussianBlur(np.roll(gm, int(0.012 * N), axis=0), (0, 0), 0.012 * N) * 0.28
    body = body * (1 - sh[..., None]) + np.array(bot, np.float32) * 0.5 * sh[..., None]
    body = body * (1 - gm[..., None]) + gcol * gm[..., None]
    sq, sa = rrect_layer(N, N, N * 0.30, (255, 255, 255))
    body = body[:sa.shape[0], :sa.shape[1]]
    rim = cv2.GaussianBlur(sa, (0, 0), 0.012 * N)
    edge = np.clip(sa - cv2.erode(sa, np.ones((int(0.02 * N) | 1,) * 2, np.uint8)), 0, 1)
    body = body * (1 - 0.12 * edge[..., None]) + 255.0 * 0.12 * edge[..., None]
    bgr = cv2.resize(np.clip(body, 0, 255).astype(np.uint8), (int(s), int(s)), interpolation=cv2.INTER_AREA)
    al = cv2.resize(sa, (int(s), int(s)), interpolation=cv2.INTER_AREA)
    _GI[key] = (bgr, np.clip(al, 0, 1).astype(np.float32))
    return _GI[key]

_ICON_KINDS = ["music", "image", "chat", "play", "bars", "doc", "spark", "bolt"]

def fx_iconsaround(img, t, c):
    W, H = c.W, c.H
    D = 2.0
    if t > D: return img
    P = pal(c); pop = _pop(P)
    fb = face(img, c)
    fcx = fb[0] + fb[2] / 2.0; fcy = fb[1] + fb[3] / 2.0
    g = clamp01((fb[2] / W - 0.30) / 0.20)                         # 0: far face, 1: close-up
    cx = fcx; cy = fcy + 0.16 * fb[3]
    rx = float(np.clip(0.85 * fb[2] + 0.11 * W, 0.37 * W, 0.44 * W))
    rx = max(0.22 * W, min(rx, cx - 0.085 * W, W - 0.085 * W - cx))
    ry = max(0.075 * H, 0.36 * rx)
    s = int(0.108 * W * (1 + 0.12 * g))
    cols = [pop[0], pop[1], pop[2], _mix(pop[0], pop[2], 0.5), pop[2], pop[0], pop[1], _mix(pop[1], pop[0], 0.5)]
    tilt = -10.0; ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    th0 = math.radians(200) + 2 * math.pi * t / 3.6
    fade = 1 - smooth(1.72, 1.98, t)
    items = []
    n = len(_ICON_KINDS)
    for i, k in enumerate(_ICON_KINDS):
        th = th0 + 2 * math.pi * i / n
        z = math.sin(th)
        ex, ey = rx * math.cos(th), ry * z
        life = back_out(clamp01((t - 0.05 * i) / 0.30)) * fade
        x = cx + ex * ct - ey * st; y = cy + ex * st + ey * ct + 0.004 * H * math.sin(2.4 * t + i)
        items.append((z, x, y, k, cols[i], life))
    items.sort(key=lambda a: a[0])
    back = img.copy(); fronts = []
    for z, x, y, k, col, life in items:
        sc_ = (0.80 + 0.20 * (z + 1) / 2) * life
        if sc_ <= 0.06: continue
        b, a = _gloss_icon(k, s, col)
        if z < 0:
            soft_shadow2(back, a, x, y, 0, 0.007 * H, 0.010 * W, 0.30, sc_)
            blit(back, b, a, x, y, 1.0, 0, sc_)
        else: fronts.append((b, a, x, y, sc_))
    m = matte(img, c)[..., None]
    out = (back.astype(np.float32) * (1 - m) + img.astype(np.float32) * m).astype(np.uint8)
    for b, a, x, y, sc_ in fronts:
        soft_shadow2(out, a, x, y, 0, 0.008 * H, 0.011 * W, 0.34, sc_)
        blit(out, b, a, x, y, 1.0, 0, sc_)
    return out

# ============================================================================= 44 green background + sticker
_GREEN = (64, 200, 38)     # BGR of a clean saturated green

def _green_base(c):
    W, H = c.W, c.H; u = W / 1080.0
    yy = (np.arange(H, dtype=np.float32) / H)[:, None, None]
    base = np.empty((H, W, 3), np.float32)
    top = np.array(_mix(_GREEN, (255, 255, 255), 0.10), np.float32); bot = np.array(_mix(_GREEN, (0, 0, 0), 0.10), np.float32)
    base[:] = top * (1 - yy) + bot * yy
    ov = _Ov(H, W); step = 34 * u
    for j in range(int(H / step) + 2):
        for i in range(int(W / step) + 2):
            ov.circle(i * step + (step / 2 if j % 2 else 0), j * step, 1.5 * u, (255, 255, 255))
    base = ov.apply(base.astype(np.uint8), 0.18).astype(np.float32)
    ov = _Ov(H, W)                                                  # faint diagonal stripes in two corners
    for k in range(-40, 60):
        x0 = k * 22 * u
        ov.line([(x0, 0), (x0 - 0.30 * H, 0.30 * H)], (0, 90, 0), 5 * u)
        ov.line([(W - x0, H), (W - x0 + 0.30 * H, H - 0.30 * H)], (0, 90, 0), 5 * u)
    mk = np.zeros((H, W), np.float32)
    yy2, xx2 = np.mgrid[0:H, 0:W].astype(np.float32)
    mk = np.clip(1 - (xx2 / W + yy2 / H) / 0.55, 0, 1) + np.clip(1 - ((W - xx2) / W + (H - yy2) / H) / 0.55, 0, 1)
    al = (ov.al.astype(np.float32) / 255.0) * np.clip(mk, 0, 1) * 0.16
    base = base * (1 - al[..., None]) + np.array((10, 110, 10), np.float32) * al[..., None]
    rng = np.random.default_rng(11)
    base += rng.normal(0, 3.0, (H, W, 1)).astype(np.float32)
    return np.clip(base, 0, 255).astype(np.uint8)

def _marks(c):
    """tracking markers: fixed spots (as fractions of the frame) with real X/Y labels of where they sit"""
    return [(0.13, 0.27, 0.00), (0.87, 0.36, 0.12), (0.12, 0.60, 0.24), (0.88, 0.69, 0.36)]

def fx_greenbg(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 2.1
    if t > D: return img
    k = smooth(0.0, 0.14, t) * (1 - smooth(1.88, 2.1, t))
    if k <= 0.002: return img
    if "gbase" not in c.state: c.state["gbase"] = _green_base(c)
    bg = c.state["gbase"].astype(np.float32)
    # soft light blobs drifting over the green
    sw, sh_ = W // 4, H // 4
    yy, xx = np.mgrid[0:sh_, 0:sw].astype(np.float32)
    blob = np.zeros((sh_, sw), np.float32)
    for i, (bx, by, br) in enumerate(((0.25, 0.22, 0.34), (0.80, 0.55, 0.40), (0.35, 0.88, 0.32))):
        px = (bx + 0.05 * math.sin(0.8 * t + i * 2)) * sw; py = (by + 0.04 * math.cos(0.7 * t + i)) * sh_
        blob += np.exp(-(((xx - px) / (br * sw)) ** 2 + ((yy - py) / (br * sw)) ** 2) * 1.6)
    blob = cv2.resize(np.clip(blob, 0, 1), (W, H), interpolation=cv2.INTER_CUBIC)[..., None] * 0.22
    bg = bg * (1 - blob) + 255.0 * blob
    bg = np.clip(bg, 0, 255).astype(np.uint8)
    ov = _Ov(H, W)
    for j in range(3):                                              # rounded frames growing from the centre and fading
        ph = (t * 0.45 + j / 3.0) % 1.0
        sc_ = 0.30 + 0.85 * ph
        w_, h_ = 0.90 * W * sc_, 0.52 * H * sc_
        path = _rr_path(W / 2 - w_ / 2, H * 0.47 - h_ / 2, W / 2 + w_ / 2, H * 0.47 + h_ / 2, 0.07 * W * sc_, 4 * u)
        al = math.sin(math.pi * ph) ** 1.3 * 0.34
        o2 = _Ov(H, W); o2.line(path, (255, 255, 255), 3.5 * u, True); bg = o2.apply(bg, al)
    # tracking markers
    for i, (mx, my, t0) in enumerate(_marks(c)):
        life = back_out(clamp01((t - 0.15 - t0) / 0.28))
        if life <= 0.02: continue
        x = (mx + 0.008 * math.sin(2.2 * t + i * 1.7)) * W; y = (my + 0.006 * math.cos(1.9 * t + i)) * H
        r = 0.020 * W * life
        o2 = _Ov(H, W)
        o2.circle(x, y, r, (255, 255, 255), max(2, int(2.5 * u)))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            o2.line([(x + dx * r * 1.15, y + dy * r * 1.15), (x + dx * r * 2.0, y + dy * r * 2.0)], (255, 255, 255), max(2, 2.5 * u))
        bg = o2.apply(bg, 0.92)
        lab = "X%.2f Y%.2f" % (x / W, y / H)
        put_text(bg, lab, x, y + r * 3.1, 0.0185 * W, (255, 255, 255), "Bold", "c", op=clamp01(life), spacing=0.04)
    # sticker: wobbly white outline around the matte
    m = matte(img, c)
    ms = cv2.resize((m > 0.5).astype(np.uint8), (W // 3, H // 3), interpolation=cv2.INTER_NEAREST)
    dist = cv2.distanceTransform(1 - ms, cv2.DIST_L2, 3)
    rng = np.random.default_rng(int(t * 9))
    wob = cv2.resize(rng.standard_normal((11, 6)).astype(np.float32), (W // 3, H // 3), interpolation=cv2.INTER_CUBIC)
    r0 = 0.018 * W / 3.0
    r_ = r0 + wob * 0.0045 * W / 3.0
    so = np.clip((r_ - dist) / 1.6 + 0.5, 0, 1)
    so = cv2.resize(so, (W, H), interpolation=cv2.INTER_CUBIC)
    so = np.clip(np.maximum(so, m), 0, 1).astype(np.float32)
    sh = cv2.GaussianBlur(cv2.warpAffine(so, np.float32([[1, 0, 0.004 * W], [0, 1, 0.008 * W]]), (W, H)), (0, 0), 0.007 * W) * 0.26
    out = bg.astype(np.float32) * (1 - sh[..., None]) + np.array((10, 70, 10), np.float32) * sh[..., None]
    out = out * (1 - so[..., None]) + 255.0 * so[..., None]
    out = out * (1 - m[..., None]) + img.astype(np.float32) * m[..., None]
    return _F().mix(img, np.clip(out, 0, 255).astype(np.uint8), k)

# ============================================================================= 45 checklist card
def _tick(cv, cx, cy, r, prog, col, th):
    """check mark drawn progressively (prog 0..1)"""
    p0 = (cx - 0.42 * r, cy + 0.02 * r); p1 = (cx - 0.10 * r, cy + 0.36 * r); p2 = (cx + 0.48 * r, cy - 0.34 * r)
    d1 = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); d2 = math.hypot(p2[0] - p1[0], p2[1] - p1[1]); tot = d1 + d2
    L = prog * tot
    pts = [p0]
    if L <= d1: f = L / d1; pts.append((p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f))
    else:
        pts.append(p1); f = (L - d1) / d2; pts.append((p1[0] + (p2[0] - p1[0]) * f, p1[1] + (p2[1] - p1[1]) * f))
    o = _Ov(cv.shape[0], cv.shape[1]); o.line(pts, col, th); return o

def fx_checklist2(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 2.0
    if t > D: return img
    P = pal(c); pop = _pop(P); RAD = P["rad"]
    items = items_opt(c, ["ТИТРЫ", "ПЕРЕХОДЫ", "ГРАФИКА"] if lang(c) == "ru" else ["TITLES", "TRANSITIONS", "GRAPHICS"])[:5]
    title = opt(c, "text", "СПИСОК С ГАЛОЧКАМИ" if lang(c) == "ru" else "CHECKLIST")
    n = len(items)
    cw = int(0.66 * W); rowh = int(0.047 * H); ch = int(rowh * n + 0.018 * H)
    pad = int(0.035 * W)
    t_on = [0.50 + 0.40 * i for i in range(n)]
    # canvas with the card
    CW, CH = cw + 2 * pad, ch + 2 * pad
    cb, ca = rrect_layer(cw, ch, 0.012 * W * RAD, P["card"], P["line"], max(1.0, 1.6 * u))
    cv = np.zeros((CH, CW, 3), np.uint8); cv[pad:pad + ch, pad:pad + cw] = cb
    A = np.zeros((CH, CW), np.float32); A[pad:pad + ch, pad:pad + cw] = ca
    card = cv[pad:pad + ch, pad:pad + cw]                     # view
    rows_vis = clamp01((t - 0.12) / 0.2)
    done_f = 0.0
    for i, name in enumerate(items):
        yc = int(0.009 * H + rowh * (i + 0.5)); xr = int(0.058 * cw); rr = 0.0195 * W
        tt = t - t_on[i]
        if i > 0:
            cv2.line(card, (int(0.04 * cw), int(0.009 * H + rowh * i)), (int(0.96 * cw), int(0.009 * H + rowh * i)), P["line"], max(1, int(1.5 * u)), cv2.LINE_AA)
        done = clamp01(tt / 0.2)
        if rows_vis <= 0.01: continue
        txt_col = _mix(_mix(P["ink"], P["card"], 0.55), P["ink"], done)
        o = _Ov(ch, cw)
        if done <= 0:
            o.circle(xr, yc, rr, _mix(P["card"], P["ink"], 0.35), max(2, int(2.6 * u))); cv[pad:pad + ch, pad:pad + cw] = o.apply(card, 1.0)
        else:
            pc = P["ink"]
            o.circle(xr, yc, rr * (0.55 + 0.45 * back_out(clamp01(tt / 0.16))), pc); card[:] = o.apply(card, 1.0)
            tk = _tick(card, xr, yc, rr, ease(clamp01((tt - 0.05) / 0.16)), _on(pc), max(2, int(3.2 * u)))
            card[:] = tk.apply(card, 1.0)
            done_f += ease(clamp01(tt / 0.3))
        put_text(card, name, 0.14 * cw, yc, 0.041 * W, txt_col, "Bold", "l", op=rows_vis)
        put_text(card, "%02d" % (i + 1), cw - 0.045 * cw, yc, 0.016 * W, _mix(P["card"], P["ink"], 0.45), "Medium", "r", op=rows_vis, spacing=0.06)
    # progress line along the bottom edge
    pw_ = int(cw * done_f / n)
    if pw_ > 1:
        cv2.rectangle(card, (0, ch - max(3, int(5 * u))), (pw_, ch), pop[0], -1)
    cv[pad:pad + ch, pad:pad + cw] = card
    # burst marks around each tick the moment it lands
    ovb = _Ov(CH, CW); any_b = False
    for i in range(n):
        tt = t - t_on[i] - 0.10
        if 0 < tt < 0.34:
            f = ease(tt / 0.34); xr = pad + 0.058 * cw; yc = pad + 0.009 * H + rowh * (i + 0.5)
            for k in range(7):
                a = math.radians(-70 + k * 40 + 12); r0 = 0.024 * W * (1 + 0.5 * f); r1 = r0 + 0.012 * W * (1 - f * 0.4)
                ovb.line([(xr + r0 * math.cos(a), yc + r0 * math.sin(a)), (xr + r1 * math.cos(a), yc + r1 * math.sin(a))], pop[0], max(2, 3 * u)); any_b = True
    if any_b:
        cv = ovb.apply(cv, 1.0); A = np.maximum(A, ovb.al.astype(np.float32) / 255.0 * 0.9)
    out = img.copy()
    top_y = 0.857 * H - ch                                          # bottom of the card stays put
    cxm = 0.5 * W; cym = top_y + ch / 2.0
    pin = back_out(clamp01(t / 0.26)); pout = 1 - smooth(1.72, 1.98, t)
    sc_ = pin * (0.9 + 0.1 * pout) if pout < 1 else pin
    op = clamp01(pin * 1.4) * pout
    if sc_ > 0.02 and op > 0.01:
        soft_shadow2(out, A, cxm, cym, 0, 0.007 * H, 0.012 * W, 0.20 * op, sc_)
        blit(out, cv, A, cxm, cym, op, 0, sc_)
    # title plate above the card
    tsz = 0.040 * W; tw = text_width(title, tsz, "Black")
    tpw = int(max(tw + 0.07 * W, 0.45 * W)); tph = int(0.046 * H)
    tb, ta = rrect_layer(tpw, tph, 0.010 * W * RAD, P["card"], P["line"], max(1.0, 1.6 * u))
    put_text(tb, title, tpw / 2.0, tph / 2.0, tsz, P["ink"], "Black", "c")
    tin = back_out(clamp01((t - 0.08) / 0.26))
    if tin > 0.02 and op > 0.01:
        ty = top_y - 0.014 * H - tph / 2.0
        soft_shadow2(out, ta, cxm, ty, 0, 0.005 * H, 0.008 * W, 0.18 * op, tin)
        blit(out, tb, ta, cxm, ty, op, 0, tin)
    return out

# ============================================================================= 46 headline storm with lightning
_HS2_TEXT = ["МОНТАЖ НАЧАЛСЯ", "ЭТО ВИДЕО", "ЕЩЁ ОДИН ЭФФЕКТ", "СМОТРИ ДО КОНЦА", "БЕЗ ТАЙМЛАЙНА", "ВСЁ ПО ПРОМПТУ", "ГОТОВО"]
_HS2_TEXT_EN = ["EDITING STARTED", "THIS VIDEO", "ONE MORE EFFECT", "WATCH TILL THE END", "NO TIMELINE", "ALL BY PROMPT", "DONE"]
# (colour: 0 pink 1 yellow 2 blue 3 white, centre x frac, anchor, dy (fraction of face height / of H), angle, side, t0, front)
_HS2 = [(0, 0.46, "top", -0.72, -3.0, "L", 0.00, False),
        (2, 0.74, "top", 0.18, 3.0, "R", 0.08, False),
        (1, 0.26, "top", 0.62, -4.0, "L", 0.16, False),
        (3, 0.40, "chin", 0.050, -2.0, "L", 0.24, True),
        (1, 0.64, "chin", 0.105, 2.5, "R", 0.32, True),
        (2, 0.45, "chin", 0.160, -2.0, "L", 0.40, True),
        (0, 0.70, "top", 1.05, 3.0, "R", 0.20, False)]

def _plate(text, fill, W, H, P, RAD):
    """a headline plate: flat fill, hairline outline, no hard offset shadow (the soft shadow is added when it is placed)"""
    u = W / 1080.0
    fs = 0.040 * W; tw = text_width(text, fs, "Black")
    pw = int(tw + 0.075 * W); ph = int(0.080 * W)
    r = 0.012 * W * RAD
    edge = P["ink"] if fill != P["ink"] else _mix(P["ink"], (255, 255, 255), 0.25)
    body, ba = rrect_layer(pw, ph, r, fill, edge, max(1, int(1.6 * u)))
    put_text(body, text, pw / 2.0, ph / 2.0, fs, _on(fill), "Black", "c")
    return body, ba

def _bolt(rng, W, H, x0, y_end):
    """jagged lightning polyline from the top edge down to y_end"""
    pts = [(x0, -0.02 * H)]
    x, y = x0, -0.02 * H
    while y < y_end:
        y += rng.uniform(0.030, 0.060) * H; x += rng.uniform(-0.055, 0.055) * W
        pts.append((x, y))
    return pts

def fx_headlinestorm2(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 2.1
    if t > D: return img
    P = pal(c); pop = _pop(P); RAD = P["rad"]
    fills = [pop[0], P["card"], P["ink"], P["surface"]]
    texts = [s.strip().upper() for s in items_opt(c, _HS2_TEXT if lang(c) == "ru" else _HS2_TEXT_EN)]
    if "pl" not in c.state:
        c.state["pl"] = [_plate(texts[i % len(texts)], fills[sp[0]], W, H, P, RAD) for i, sp in enumerate(_HS2)]
    fb = face(img, c); fh = fb[3]
    dim = 0.26 * smooth(0.22, 0.42, t) * (1 - smooth(1.55, 1.85, t))
    base = (img.astype(np.float32) * (1 - dim)).astype(np.uint8)
    back = base.copy(); front = []
    out_k = smooth(1.82, 2.05, t)
    for i, (ci, cxf, anc, dy, ang, side, t0, isf) in enumerate(_HS2):
        body, al = c.state["pl"][i]
        u_ = ease(clamp01((t - t0) / 0.40))
        if u_ <= 0.001: continue
        ph_ = body.shape[0]
        if anc == "chin": yy = min(0.93 * H, fb[1] + fb[3] + dy * H)
        else: yy = fb[1] + dy * fh
        yy = max(0.08 * H, min(0.95 * H, yy)) + 0.004 * H * math.sin(2.6 * t + i)
        xrest = cxf * W
        start = (-0.9 * W) if side == "L" else (1.9 * W)
        x = lerp(start, xrest, u_) + (0.010 * W * (t - t0 - 0.4) if t - t0 > 0.4 else 0) * (1 if side == "L" else -1)
        x = lerp(x, (-0.9 * W if side == "L" else 1.9 * W), out_k)
        if isf: front.append((body, al, x, yy, ang, out_k))
        else:
            soft_shadow2(back, al, x, yy, 0, 0.003 * H, 0.004 * W, 0.15 * (1 - out_k), 1.0, ang)
            blit(back, body, al, x, yy, 1.0, ang)
    m = matte(img, c)[..., None]
    res = (back.astype(np.float32) * (1 - m) + base.astype(np.float32) * m).astype(np.uint8)
    for body, al, x, yy, ang, ok in front:
        soft_shadow2(res, al, x, yy, 0, 0.004 * H, 0.005 * W, 0.22 * (1 - ok), 1.0, ang)
        blit(res, body, al, x, yy, 1.0, ang)
    # lightning: three bolts, each with a glow and a white flash
    flash = 0.0
    for bi, tb in enumerate((0.50, 0.72, 0.95)):
        tt = t - tb
        if 0 <= tt < 0.15:
            f = 1 - tt / 0.15; rng = np.random.default_rng(100 + bi)
            x0 = (0.30 + 0.20 * bi + rng.uniform(-0.05, 0.05)) * W
            pts = _bolt(rng, W, H, x0, (0.62 + 0.08 * bi) * H)
            ov = _Ov(H, W); ov.line(pts, (255, 255, 255), max(2, 4 * u))
            for j in range(2):                                      # a couple of side branches
                k = 2 + j * 3
                if k < len(pts):
                    bx, by = pts[k]; br = [(bx, by)]
                    for _ in range(4): bx += rng.uniform(-0.05, 0.07) * W * (1 if j else -1); by += rng.uniform(0.02, 0.04) * H; br.append((bx, by))
                    ov.line(br, (255, 255, 255), max(1, 2 * u))
            core = ov.al.astype(np.float32) / 255.0
            glow = cv2.GaussianBlur(core, (0, 0), 0.012 * W) * 2.2 + cv2.GaussianBlur(core, (0, 0), 0.004 * W) * 1.2
            glow = np.clip(glow, 0, 1) * f
            res = res.astype(np.float32)
            res = res * (1 - glow[..., None]) + np.array((255, 225, 170), np.float32) * glow[..., None]
            res = np.clip(res * (1 - core[..., None] * f) + 255.0 * core[..., None] * f, 0, 255).astype(np.uint8)
            flash = max(flash, 0.34 * f ** 1.5)
    if flash > 0.01:
        res = np.clip(res.astype(np.float32) * (1 - flash) + 255.0 * flash, 0, 255).astype(np.uint8)
    # camera shake settling down
    sk = 6 * u * math.exp(-max(0.0, t - 0.45) / 0.55) * smooth(0.40, 0.50, t) * (1 - smooth(1.7, 1.9, t))
    if sk > 0.3:
        dx = sk * math.sin(2 * math.pi * 3.3 * t) ; dy = sk * 0.8 * math.sin(2 * math.pi * 4.1 * t + 1.0)
        res = cv2.warpAffine(res, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_REFLECT101)
    return res

# ============================================================================= 47 phone on cream background
def _cover(img, w, h):
    H, W = img.shape[:2]
    s = max(w / W, h / H); nw, nh = max(1, int(math.ceil(W * s))), max(1, int(math.ceil(H * s)))
    r = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    x0 = (nw - w) // 2; y0 = (nh - h) // 2
    return r[y0:y0 + h, x0:x0 + w]

def _quad(cx, cy, w, h, ang):
    a = math.radians(ang); c_, s_ = math.cos(a), math.sin(a)
    return [(cx + dx * c_ - dy * s_, cy + dx * s_ + dy * c_) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]

def fx_phonemock2(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 2.0
    if t > D: return img
    P = pal(c); pop = _pop(P); RAD = P["rad"]
    p = ease(clamp01(t / 0.40)) * (1 - ease(clamp01((t - 1.55) / 0.45)))
    if p <= 0.002: return img
    ba = clamp01((p - 0.10) / 0.55)
    # uniform neutral background (no pattern, no decorative blocks)
    bg = np.empty((H, W, 3), np.uint8); bg[:] = P["bg"]
    # phone geometry
    pw = 0.555 * W; ph = 0.64 * H; bz = 0.014 * W
    pcx, pcy = 0.5 * W, 0.505 * H
    sw, sh_ = pw - 2 * bz, ph - 2 * bz
    # shadow on the floor
    shd = np.zeros((H, W), np.float32)
    cv2.ellipse(shd, (int(pcx), int(pcy + ph / 2 + 0.012 * H)), (int(0.23 * W * p), int(0.011 * H)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    shd = cv2.GaussianBlur(shd, (0, 0), 0.012 * W) * 0.34 * ba
    bg = (bg.astype(np.float32) * (1 - shd[..., None])).astype(np.uint8)
    # caption plate above the phone: only when the user gives a text with --text (no default caption)
    cap = opt(c, "text", None)
    if cap:
        csz = 0.0285 * W; cwid = text_width(cap, csz, "Black") + 0.07 * W; chh = 0.034 * H
        cb, ca = rrect_layer(cwid, chh, 0.004 * W * RAD, P["ink"])
        put_text(cb, cap, cwid / 2.0, chh / 2.0, csz, _on(P["ink"]), "Black", "c")
        cin = back_out(clamp01((t - 0.22) / 0.26)) * clamp01(p * 1.6)
        if cin > 0.02: blit(bg, cb, ca, 0.50 * W, pcy - ph / 2 - 0.036 * H, 1.0, 0, cin)
    # the screen picture: full frame -> screen of the phone
    scw, sch = lerp(W, sw, p), lerp(H, sh_, p)
    scx, scy = lerp(W / 2.0, pcx, p), lerp(H / 2.0, pcy, p)
    bzp = bz * p
    if p > 0.05:                                                   # body (bezel) grows around the screen
        bwid, bhei = scw + 2 * bzp, sch + 2 * bzp
        bb, bal = rrect_layer(bwid, bhei, 0.115 * pw * (0.4 + 0.6 * p), P["ink"], _mix(P["ink"], (255, 255, 255), 0.30), max(1.0, 2.2 * u))
        soft_shadow2(bg, bal, scx, scy, 0, 0.010 * H, 0.020 * W, 0.28 * p)
        blit(bg, bb, bal, scx, scy)
        for sgn, (yy_, hh_) in ((-1, (-0.20, 0.05)), (1, (-0.12, 0.09))):                    # side buttons
            rb, ra = rrect_layer(max(3, 0.004 * W), hh_ * ph * p, 1.5, _mix(P["ink"], (255, 255, 255), 0.18))
            blit(bg, rb, ra, scx + sgn * (bwid / 2 + 1.0 * u), scy + yy_ * ph * p)
    vid = _cover(img, int(round(scw)), int(round(sch)))
    vb, va = rrect_layer(vid.shape[1], vid.shape[0], lerp(0.0, 0.092 * pw, p) + 0.001, (255, 255, 255))
    vid = vid[:va.shape[0], :va.shape[1]]
    blit(bg, vid, va, scx, scy)
    if p > 0.6:                                                    # dynamic-island pill
        ib, ia = rrect_layer(0.20 * pw, 0.034 * pw, 0.017 * pw, (8, 8, 10)); blit(bg, ib, ia, scx, scy - sch / 2 + 0.050 * pw, clamp01((p - 0.6) / 0.4))
    # soft gloss over the screen
    if p > 0.7:
        gl = np.zeros((H, W), np.float32)
        cv2.fillConvexPoly(gl, np.array(_quad(scx - 0.02 * W, scy, 0.12 * W, sch * 1.2, 18), np.int32), 1.0, cv2.LINE_AA)
        gl = cv2.GaussianBlur(gl, (0, 0), 0.01 * W)
        bg = np.clip(bg.astype(np.float32) + 255.0 * gl[..., None] * 0.05 * clamp01((p - 0.7) / 0.3), 0, 255).astype(np.uint8)
    return _F().mix(img, bg, 1.0) if ba >= 0.999 else _F().mix(img, bg, max(ba, clamp01(p * 4)))

# ============================================================================= registry
def build(fx_mod):
    def e(fn, ru, alias, dur, desc): return dict(fn=fn, ru=ru, alias=alias, kind="intro", dur=dur, desc=desc)
    return {
        "iconsaround":   e(fx_iconsaround, "иконки вокруг меня", ["icons around me", "глянцевые иконки", "цветные иконки"], 2.0, "8 глянцевых цветных иконок (музыка, картинка, чат, play, график, документ, искра, молния) с белыми значками кружатся по плоскому наклонному эллипсу вокруг головы, часть за человеком, часть перед ним; без пунктирного кольца; разновидность «орбиты»"),
        "greenbg":       e(fx_greenbg, "зелёный фон", ["green background", "зелёная наклейка", "зелёный стикер"], 2.1, "яркий зелёный фон с мягкими бликами, точками и растущими рамками, метки трекинга с подписями X/Y, человек с белым волнистым контуром-наклейкой; разновидность «хромакея»"),
        "checklist2":    e(fx_checklist2, "список с галочками", ["checklist card", "чек-лист с галочками", "список дел"], 2.0, "карточка с заголовком и списком из 3 пунктов внизу кадра: кружки превращаются в цветные галочки одна за другой, искры, полоса прогресса; текст через --text, пункты через --items; разновидность «всплывающего чек-листа»"),
        "headlinestorm2": e(fx_headlinestorm2, "шторм из заголовков", ["headline storm 2", "заголовки и молния", "цветные заголовки"], 2.1, "экран темнеет, три молнии со вспышкой, цветные плашки с заголовками влетают с боков (часть за человеком, часть перед ним), кадр трясётся 1.5 с; тексты через --items; разновидность «шторма заголовков»"),
        "phonemock2":    e(fx_phonemock2, "макет телефона", ["phone mockup 2", "смартфон на фоне"], 2.0, "видео за 0.4 с сжимается в экран смартфона на однородном нейтральном фоне, держится и разворачивается обратно за 0.45 с; подпись над телефоном только через --text; разновидность «телефона»"),
    }
