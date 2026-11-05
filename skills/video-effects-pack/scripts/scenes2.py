"""
scenes2.py - 12 more effects (31-42): zooms, frames, chart, split screen, magazine cover, picture-in-picture, colour/pixel/vignette/fade looks.
All of them are intro effects: they play once from --start (the duration is built in), the picture then goes back to normal.
Colours / corners / fonts come from the style palette of scenes.py (--style minimal | styles/<name>.json | path.json); accents are P["acc"].
Needs the same things as scenes.py (numpy, opencv-python, Pillow, assets/Inter-*.otf, assets/u2netp.onnx).
"""
import math
import time
import numpy as np
import cv2
import scenes as S
from scenes import (pal, lerp, clamp01, ease, smooth, back_out, blit, put_text, text_width, rrect_layer, disk_layer,
                    soft_shadow2, face, matte, zoom_at, opt, items_opt, lang)

def _F(): return S.F
_POP_DEFAULT = ((54, 90, 255), (17, 17, 17), (138, 142, 142))      # BGR: one warm red-orange accent #FF5A36 + near-black #111111 + neutral grey #8E8E8A

def _acc(P):
    """three accent colours (BGR): from the style; if the style accents are grey (built-in 'minimal') a neutral colourful default is used -
    minimal means clean shapes, not only black and grey"""
    a = P.get("acc") or ()
    if len(a) == 3 and any(max(x) - min(x) > 40 for x in a): return tuple(a)
    return _POP_DEFAULT

def _frame_cols(acc):
    """colours of the glowing frame: the style accents if there are at least two real colours, otherwise shades of the single accent"""
    real = [a for a in acc if max(a) - min(a) > 40]
    if len(real) >= 2: return tuple(real[:3])
    a = real[0] if real else acc[0]
    mx = lambda p, q, k: tuple(int(round(p[m] + (q[m] - p[m]) * k)) for m in range(3))
    return (a, mx(a, (255, 255, 255), 0.55), mx(a, (0, 0, 0), 0.30))
def _on(col): return S._on(col)
def _mix(a, b, k): return S._mix(a, b, k)

class _Ov:
    """premultiplied overlay: anti-aliased lines / polygons / circles drawn once, then composited over the frame"""
    def __init__(self, H, W):
        self.lay = np.zeros((H, W, 3), np.uint8); self.al = np.zeros((H, W), np.uint8)
    @staticmethod
    def _p(pts): return (np.asarray(pts, np.float64) * 16).astype(np.int32).reshape(-1, 1, 2)
    def line(self, pts, col, th, closed=False):
        p = self._p(pts); th = max(1, int(round(th)))
        cv2.polylines(self.lay, [p], closed, col, th, cv2.LINE_AA, 4); cv2.polylines(self.al, [p], closed, 255, th, cv2.LINE_AA, 4)
    def poly(self, pts, col):
        p = self._p(pts); cv2.fillPoly(self.lay, [p], col, cv2.LINE_AA, 4); cv2.fillPoly(self.al, [p], 255, cv2.LINE_AA, 4)
    def circle(self, x, y, r, col, th=-1):
        c_ = (int(round(x * 16)), int(round(y * 16))); rr = max(1, int(round(r * 16))); th_ = th if th < 0 else max(1, int(round(th)))
        cv2.circle(self.lay, c_, rr, col, th_, cv2.LINE_AA, 4); cv2.circle(self.al, c_, rr, 255, th_, cv2.LINE_AA, 4)
    def apply(self, img, op=1.0):
        a = self.al.astype(np.float32) / 255.0 * op
        return np.clip(img.astype(np.float32) * (1 - a[..., None]) + self.lay.astype(np.float32) * op, 0, 255).astype(np.uint8)

def _rr_path(x0, y0, x1, y1, r, step=3.0):
    """closed rounded-rectangle outline, clockwise from the top-left corner, as an (N, 2) array"""
    pts = []
    def seg(xa, ya, xb, yb):
        n = max(2, int(math.hypot(xb - xa, yb - ya) / step))
        for k in range(n): pts.append((xa + (xb - xa) * k / n, ya + (yb - ya) * k / n))
    def arc(cx, cy, a0, a1):
        n = max(4, int(r * abs(math.radians(a1 - a0)) / step))
        for k in range(n):
            a = math.radians(a0 + (a1 - a0) * k / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    seg(x0 + r, y0, x1 - r, y0); arc(x1 - r, y0 + r, -90, 0)
    seg(x1, y0 + r, x1, y1 - r); arc(x1 - r, y1 - r, 0, 90)
    seg(x1 - r, y1, x0 + r, y1); arc(x0 + r, y1 - r, 90, 180)
    seg(x0, y1 - r, x0, y0 + r); arc(x0 + r, y0 + r, 180, 270)
    return np.array(pts, np.float64)

def _dim_text(P): return P["dim"]

# ----------------------------------------------------------------------------- 03 quick zoom (RGB split + speed lines)
def fx_quickzoom(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 1.9
    if t > D: return img
    e_in = 1 - (1 - clamp01(t / 0.2)) ** 3                              # 100% -> 120% in 0.2 s, fast start
    s = 1 + 0.20 * e_in
    if t > 1.25: s = 1 + 0.20 * (1 - ease(clamp01((t - 1.25) / 0.65)))   # then a calm pull back, so the clip is not left zoomed
    out = zoom_at(img, s, W / 2.0, H / 2.0)
    amt = 18 * u * max(0.0, 1 - t / 0.5)                                 # RGB shift, fades in 0.5 s
    if amt > 0.4:
        b, g, r = cv2.split(out)
        r = cv2.warpAffine(r, np.float32([[1, 0, amt], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT101)
        b = cv2.warpAffine(b, np.float32([[1, 0, -amt], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT101)
        out = cv2.merge([b, g, r])
    k = max(0.0, 1 - t / 0.35)                                           # speed lines, fade in 0.35 s
    if k > 0.02:
        ov = _Ov(H, W); rng = np.random.default_rng(5); diag = math.hypot(W, H) / 2
        for _ in range(46):
            an = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(0.30, 0.55) * diag; r1 = r0 + rng.uniform(0.18, 0.42) * diag * (0.6 + 0.4 * (1 - k))
            ov.line([(W / 2 + r0 * math.cos(an), H / 2 + r0 * math.sin(an)), (W / 2 + r1 * math.cos(an), H / 2 + r1 * math.sin(an))], (255, 255, 255), rng.uniform(1.5, 3.5) * u)
        out = ov.apply(out, 0.55 * k)
    return out

# ----------------------------------------------------------------------------- 04 smooth zoom out
def fx_smoothzoomout(img, t, c):
    W, H = c.W, c.H
    D = 1.45
    if t > D: return img
    if t < 0.12: s = 1 + 0.20 * ease(t / 0.12)                           # short push in (the starting point of the pull back)
    else: s = 1 + 0.20 * (1 - ease(clamp01((t - 0.12) / 1.0)))           # 120% -> 100% in 1 s, smooth in and out
    return zoom_at(img, s, W / 2.0, H / 2.0)

# ----------------------------------------------------------------------------- 14 black & white frame
def fx_bwframe(img, t, c):
    D = 1.9
    if t > D: return img
    k = smooth(0.0, 0.35, t) * (1 - smooth(1.45, 1.9, t))
    if k <= 0.003: return img
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = np.clip((g - 128) * (1 + 0.10 * k) + 128, 0, 255)
    bw = cv2.cvtColor(g.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    return _F().mix(img, bw, k)

# ----------------------------------------------------------------------------- 15 pixelate (whole frame)
def fx_pixelate(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 1.8
    if t > D: return img
    if t < 0.25: b = lerp(1, 48 * u, ease(t / 0.25))
    elif t < 1.2: b = 48 * u
    else: b = lerp(48 * u, 1, ease(clamp01((t - 1.2) / 0.55)))
    b = int(b)
    if b <= 1: return img
    small = cv2.resize(img, (max(1, W // b), max(1, H // b)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_NEAREST)

# ----------------------------------------------------------------------------- 16 vignette
def fx_vignette(img, t, c):
    W, H = c.W, c.H
    D = 1.55
    if t > D: return img
    k = smooth(0.0, 0.35, t) * (1 - smooth(1.10, 1.55, t))
    if k <= 0.003: return img
    if "vig" not in c.state:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
        c.state["vig"] = np.clip((r - 0.45) / 0.60, 0, 1) ** 1.5
    v = c.state["vig"] * 0.95 * k
    ink = np.array(pal(c)["ink"], np.float32)
    return np.clip(img.astype(np.float32) * (1 - v[..., None]) + ink * v[..., None] * 0.55, 0, 255).astype(np.uint8)

# ----------------------------------------------------------------------------- 17 fade to black
def fx_fadeblack(img, t, c):
    D = 1.75
    if t > D: return img
    k = ease(clamp01(t / 0.8)) * (1 - ease(clamp01((t - 1.35) / 0.4)))   # to black in 0.8 s, short hold, back in 0.4 s
    return np.clip(img.astype(np.float32) * (1 - k), 0, 255).astype(np.uint8)

# ----------------------------------------------------------------------------- 11 split screen
def fx_splitscreen(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 1.9
    if t > D: return img
    P = pal(c); acc = _acc(P)
    e_in = ease(clamp01(t / 0.3)); e_out = ease(clamp01((t - 1.65) / 0.25)); e = e_in * (1 - e_out)
    if e <= 0.002: return img
    fb = face(img, c); fcx, fcy = fb[0] + fb[2] / 2, fb[1] + fb[3] * 0.40
    big = zoom_at(img, 1.35, fcx, fcy)
    h2 = H // 2
    out = img.copy()
    dy = int((1 - e) * h2)
    # the upper half is the normal frame, the lower half is the same frame zoomed to 135%; they slide in from the top and from the bottom
    if dy < h2:
        out[0:h2 - dy] = img[dy:h2]
        out[h2 + dy:H] = big[h2:H - dy]
    ly = h2
    ln = np.zeros((H, W), np.float32); cv2.line(ln, (0, ly), (W, ly), 1.0, max(2, int(4 * u)), cv2.LINE_AA)
    col = np.array(P["card"], np.float32)
    res = out.astype(np.float32) * (1 - ln[..., None]) + col * ln[..., None]
    res = res.astype(np.uint8)
    lab = opt(c, "text", None)
    if lab:
        tw = text_width(lab, 24 * u, "Bold") + 40 * u
        pb, pa = rrect_layer(tw, 46 * u, 23 * u * P["rad"], P["card"], P["line"], max(1, 1.5 * u))
        put_text(pb, lab, pb.shape[1] / 2.0, pb.shape[0] / 2.0, 24 * u, P["ink"], "Bold", "c")
        blit(res, pb, pa, W / 2.0, ly)
    return res

# ----------------------------------------------------------------------------- 10 video over video (delayed copy, REC window)
def fx_pipdelay(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 2.1
    hist = c.state.setdefault("hist", [])
    hist.append(img.copy())
    n = max(1, int(round(0.5 * getattr(c, "fps", 30))))
    del hist[:-(n + 1)]
    if t > D: return img
    P = pal(c); RAD = P["rad"]; acc = _acc(P)
    pop = back_out(clamp01(t / 0.28)) * (1 - ease(clamp01((t - 1.85) / 0.25)))
    if pop <= 0.02: return img
    delayed = hist[0]                                                      # the same video, 0.5 s earlier
    ww, wh = 0.50 * W, 0.50 * W * 0.88
    barh = 44 * u
    fb = face(img, c)
    cw_ = min(W, max(fb[2] * 2.7, 0.35 * W)); ch_ = cw_ * (wh - barh) / ww                # crop around the head so the chin fits
    cx_ = min(max(fb[0] + fb[2] / 2, cw_ / 2), W - cw_ / 2); cy_ = min(max(fb[1] + fb[3] * 0.62, ch_ / 2), H - ch_ / 2)
    crop = delayed[int(cy_ - ch_ / 2):int(cy_ + ch_ / 2), int(cx_ - cw_ / 2):int(cx_ + cw_ / 2)]
    if crop.size == 0: crop = delayed
    win = np.empty((int(wh), int(ww), 3), np.uint8); win[:] = P["card"]
    win[int(barh):] = cv2.resize(crop, (int(ww), int(wh - barh)), interpolation=cv2.INTER_AREA)
    win[:int(barh)] = acc[0]
    on = _on(acc[0])
    blink = 0.5 + 0.5 * math.sin(t * 9)
    cv2.circle(win, (int(26 * u), int(barh / 2)), int(8 * u), (50, 50, 235), -1, cv2.LINE_AA) if blink > 0.35 else None
    put_text(win, "REC", 46 * u, barh / 2.0, 20 * u, on, "Bold", "l")
    put_text(win, "0:%02d" % min(59, int(t * 10)), ww - 20 * u, barh / 2.0, 18 * u, on, "Medium", "r")
    wb, wa = rrect_layer(ww, wh, 14 * u * RAD, (255, 255, 255))
    bwd = 4 * u
    ia = np.zeros_like(wa)
    inner = rrect_layer(ww - 2 * bwd, wh - 2 * bwd, max(1, 12 * u * RAD), (255, 255, 255))[1]
    oy, ox = (wa.shape[0] - inner.shape[0]) // 2, (wa.shape[1] - inner.shape[1]) // 2
    ia[oy:oy + inner.shape[0], ox:ox + inner.shape[1]] = inner
    if win.shape[:2] != wa.shape[:2]: win = cv2.resize(win, (wa.shape[1], wa.shape[0]))
    full = (win.astype(np.float32) * ia[..., None] + np.array(P["ink"], np.float32) * (1 - ia[..., None])).astype(np.uint8)
    cx, cy = 0.70 * W, 0.745 * H + 0.006 * H * math.sin(t * 2.6)
    rot = 2.6 * math.sin(t * 2.0 + 0.5)
    out = img.copy()
    soft_shadow2(out, wa, cx, cy, 0, 0.012 * H, 0.014 * W, 0.30, pop, rot)
    blit(out, full, wa, cx, cy, 1.0, rot, pop)
    return out

# ----------------------------------------------------------------------------- 07 colour frame / 08 break the frame
def _frame_path(W, H, sc=1.0):
    mx, my = 0.045 * W, 0.027 * H
    pts = _rr_path(mx, my, W - mx, H - my, 0.075 * W, max(2.0, 3.0 * W / 1080.0))
    ctr = np.array([W / 2.0, H / 2.0])
    return ctr + (pts - ctr) * sc

def _runs(pts, phase, nseg):
    """cuts the closed outline into nseg equal arcs (shifted by phase, in px) -> list of (index, point array)"""
    d = np.roll(pts, -1, 0) - pts; sl = np.hypot(d[:, 0], d[:, 1]); cum = np.r_[0, np.cumsum(sl)][:-1]; tot = sl.sum()
    idx = (((cum + phase) % tot) / (tot / nseg)).astype(int) % nseg
    out = []; start = 0
    for i in range(1, len(pts) + 1):
        if i == len(pts) or idx[i] != idx[start]:
            seg = pts[start:min(len(pts), i + 1)]
            if i == len(pts): seg = np.vstack([seg, pts[0]])
            out.append((int(idx[start]), seg)); start = i
    return out

_CF_TH = 0.0085          # frame line width (fraction of W)
_CF_COLS = 0.30          # colour cycles per second along the frame

def _cf_col(s, acc, phase):
    """smooth colour at position s (0..1 along the frame) - a gradient that runs through the accent colours and loops"""
    x = ((s + phase) % 1.0) * len(acc); i = int(x) % len(acc); f = x - int(x); f = f * f * (3 - 2 * f)
    return tuple(int(round(acc[i][k] + (acc[(i + 1) % len(acc)][k] - acc[i][k]) * f)) for k in range(3))

def _halo(img, ov, sig, k):
    """soft coloured glow around everything drawn in the overlay (alpha-composited, so it is visible on light and dark pictures); works at half size"""
    H, W = img.shape[:2]
    a = cv2.resize(ov.al, (W // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    L = cv2.resize(ov.lay, (W // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.float32) * a[..., None] 
    ab = np.clip(cv2.GaussianBlur(a, (0, 0), sig / 2.0) * k, 0, 1)
    Lb = cv2.GaussianBlur(L, (0, 0), sig / 2.0) * k
    ab = cv2.resize(ab, (W, H), interpolation=cv2.INTER_LINEAR); Lb = cv2.resize(Lb, (W, H), interpolation=cv2.INTER_LINEAR)
    return img.astype(np.float32) * (1 - ab[..., None]) + Lb

def _cf_draw(img, c, P, t, pop, op):
    """the glowing frame: a thin line whose colour flows through the three accents, a bright comet running around it, soft halo outside and inside"""
    W, H = c.W, c.H; u = W / 1080.0
    acc = _frame_cols(_acc(P))
    pts = _frame_path(W, H, 0.94 + 0.06 * min(1.0, pop)); n = len(pts)
    d = np.roll(pts, -1, 0) - pts; sl = np.hypot(d[:, 0], d[:, 1]); cum = np.r_[0, np.cumsum(sl)][:-1]; tot = float(sl.sum())
    th = _CF_TH * W; ph = t * _CF_COLS; head = (t * 0.55) % 1.0
    ov = _Ov(H, W); wh = _Ov(H, W)
    step = 2
    for i in range(0, n, step):
        j = (i + step) % n
        s_ = cum[i] / tot; col = _cf_col(s_, acc, ph)
        dd = (head - s_) % 1.0                                           # distance behind the comet head
        k = (1 - dd / 0.13) ** 1.6 if dd < 0.13 else 0.0
        seg = [pts[i], pts[j] if j > i else pts[0]]
        ov.line(seg, col, th)
        if k > 0.02: wh.line(seg, tuple(int(col[m] + (255 - col[m]) * 0.85 * k) for m in range(3)), th * (1.0 + 0.5 * k))
    out = _halo(img, ov, 0.030 * W, 0.80)
    out = _halo(np.clip(out, 0, 255).astype(np.uint8), ov, 0.010 * W, 0.90)
    out = np.clip(out, 0, 255).astype(np.uint8)
    out = ov.apply(out, 1.0); out = wh.apply(out, 1.0)
    return _F().mix(img, out, op)

def fx_colorframe(img, t, c):
    W, H = c.W, c.H
    D = 1.9
    if t > D: return img
    P = pal(c)
    pop = back_out(clamp01(t / 0.2)); op = clamp01(t / 0.12) * (1 - smooth(1.6, 1.9, t))
    if op <= 0.01: return img
    return _cf_draw(img, c, P, t, pop, op)

_FB_T0 = 0.42          # the frame holds exactly like "colour frame" (33), cracks grow, then it shatters

def _fb_build(c, P):
    """the SAME frame as in colorframe (same path, same width, same flowing colours) cut into pieces"""
    W, H = c.W, c.H; u = W / 1080.0
    rng = np.random.default_rng(11)
    pts = _frame_path(W, H); n = len(pts)
    d = np.roll(pts, -1, 0) - pts; sl = np.hypot(d[:, 0], d[:, 1]); tang = d / np.maximum(sl[:, None], 1e-6)
    nrm = np.stack([tang[:, 1], -tang[:, 0]], 1)                              # outward normal
    cum = np.r_[0, np.cumsum(sl)][:-1]; tot = float(sl.sum())
    th = _CF_TH * W * 1.25
    acc = _frame_cols(_acc(P))
    ctr = np.array([W / 2.0, H / 2.0])
    base = np.linspace(0, n, 49)[:-1] + rng.uniform(-0.25, 0.25, 48) * n / 48.0
    cuts = np.sort(base.astype(int) % n); cuts = np.r_[cuts, cuts[0] + n]
    shards = []
    for gi in range(len(cuts) - 1):
        a, b = int(cuts[gi]), int(cuts[gi + 1])
        if b - a < 2: continue
        ids = np.unique(np.linspace(a, b, min(6, max(2, b - a + 1))).astype(int))
        idm = ids % n
        col = _cf_col(cum[idm[len(idm) // 2]] / tot, acc, _FB_T0 * _CF_COLS)
        poly = np.vstack([pts[idm] + nrm[idm] * th / 2, (pts[idm] - nrm[idm] * th / 2)[::-1]])
        g = poly.mean(0)
        dirv = (g - ctr) / max(1e-6, np.hypot(*(g - ctr))); ra = rng.uniform(0, 6.283)
        dirv = 0.5 * dirv + 0.5 * np.array([math.cos(ra), math.sin(ra)])
        shards.append(dict(pc=poly - g, g=g, col=col, v=dirv * rng.uniform(0.22, 0.65) * W + np.array([0, -0.22 * H * rng.random()]),
                           w=rng.uniform(-8, 8), ph=rng.uniform(0, 6.28), fl=rng.uniform(4, 9)))
    conf = []
    for _ in range(70):
        j = rng.integers(0, n); g = pts[j]; dirv = (g - ctr) / max(1e-6, np.hypot(*(g - ctr)))
        if rng.random() < 0.5: dirv = -dirv
        conf.append(dict(g=g.copy(), v=dirv * rng.uniform(0.25, 0.8) * W + rng.normal(0, 0.2 * W, 2) + np.array([0, -0.25 * H * rng.random()]),
                         s=rng.uniform(0.008, 0.017) * W, w=rng.uniform(-8, 8), ci=int(rng.integers(0, 4)), d=rng.uniform(0.0, 0.15)))
    cracks = []
    for _ in range(11):
        j = rng.integers(0, n); p0 = pts[j]; inward = -nrm[j]; line = [p0 + nrm[j] * th * 0.6]
        cur = p0.copy()
        for _k in range(6):
            cur = cur + inward * rng.uniform(0.012, 0.03) * W + np.array([-inward[1], inward[0]]) * rng.normal(0, 0.012 * W); line.append(cur.copy())
        cracks.append(np.array(line))
    return dict(shards=shards, conf=conf, cracks=cracks, pts=pts, tot=tot)

def fx_framebreak(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 1.75
    if t > D: return img
    P = pal(c); acc = _acc(P)
    if "fb" not in c.state:
        c.state["fb"] = _fb_build(c, P)
    B = c.state["fb"]
    T0 = _FB_T0
    if t < T0:                                                                 # exactly the "colour frame" (33) picture, then cracks appear
        pop = back_out(clamp01(t / 0.2)); op = clamp01(t / 0.12)
        out = _cf_draw(img, c, P, t, pop, op)
        kc = clamp01((t - 0.22) / 0.20)
        if kc > 0:
            ov = _Ov(H, W); ctr = np.array([W / 2.0, H / 2.0]); sc0 = 0.94 + 0.06 * min(1.0, pop)
            for cr in B["cracks"]:
                m = max(2, int(1 + kc * (len(cr) - 1)))
                q = ctr + (cr[:m] - ctr) * sc0
                ov.line(q, (255, 255, 255), 3.2 * u); ov.line(q, P["ink"], 1.3 * u)
            out = ov.apply(out, 1.0)
        return out
    tb = t - T0; G = 2.4 * H
    fade = 1 - smooth(0.95, 1.32, tb)
    ov = _Ov(H, W)
    for s in B["shards"]:
        pos = s["g"] + s["v"] * tb + np.array([0, 0.5 * G * tb * tb])
        a = s["w"] * tb; sx = math.cos(s["ph"] + s["fl"] * tb)
        R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        ov.poly((s["pc"] * np.array([sx, 1.0])) @ R.T + pos, s["col"])
    cols = [acc[0], acc[1 % len(acc)], acc[2 % len(acc)], P["card"]]
    cf = _Ov(H, W)
    for f in B["conf"]:
        te = tb - f["d"]
        if te <= 0: continue
        pos = f["g"] + f["v"] * te + np.array([0, 0.5 * 0.9 * G * te * te]); a = f["w"] * te; s_ = f["s"]
        sq = np.array([[-s_, -s_], [s_, -s_], [s_, s_], [-s_, s_]]) * np.array([math.cos(3 * te + f["ci"]), 1.0])
        R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        cf.poly(sq @ R.T + pos, cols[f["ci"] % 4])
    gl = _halo(img, ov, 0.014 * W, 0.85 * fade)                                 # the glow of the flying pieces fades out
    out = np.clip(gl, 0, 255).astype(np.uint8)
    out = ov.apply(out, fade); out = cf.apply(out, fade)
    kw = clamp01(tb / 0.55)
    if kw < 1:                                                                  # shock wave
        ov2 = _Ov(H, W); ov2.circle(W / 2.0, H / 2.0, ease(kw) * 0.62 * math.hypot(W, H), P["card"], max(2, 7 * u * (1 - kw)))
        out = ov2.apply(out, 0.55 * (1 - kw))
    return out

# ----------------------------------------------------------------------------- 09 draw a growth chart
_GC_VALS = [0, 10, 18, 30, 52, 62, 88, 120]

def fx_growthchart(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 2.3
    if t > D: return img
    P = pal(c); acc = _acc(P); RAD = P["rad"]; ink = P["ink"]
    cw, chh = int(0.88 * W), int(0.20 * H)
    title = str(opt(c, "text", None) or ("РОСТ" if lang(c) == "ru" else "GROWTH"))
    if "gc" not in c.state:
        card = np.empty((chh, cw, 3), np.uint8); card[:] = P["card"]
        px0, px1, py0, py1 = 0.105 * cw, 0.955 * cw, 0.30 * chh, 0.82 * chh
        for k in range(4):
            y = int(py1 - (py1 - py0) * k / 3.0); cv2.line(card, (int(px0), y), (int(px1), y), P["line"], max(1, int(1.5 * u)), cv2.LINE_AA)
            put_text(card, str(40 * k), px0 - 12 * u, y, 15 * u, P["dim"], "Medium", "r")
        put_text(card, title.upper(), 26 * u, 0.15 * chh, 21 * u, ink, "Bold", "l", spacing=0.08)
        put_text(card, ("условный пример" if lang(c) == "ru" else "sample data").upper(), cw - 22 * u, chh - 0.075 * chh, 13 * u, P["dim"], "Medium", "r", spacing=0.06)
        ba, aa = rrect_layer(cw, chh, 16 * u * RAD, (255, 255, 255))
        c.state["gc"] = (card, aa, (px0, px1, py0, py1))
    base, aa, (px0, px1, py0, py1) = c.state["gc"]
    card = base.copy()
    inn = back_out(clamp01(t / 0.3)); op = clamp01(t / 0.16) * (1 - smooth(2.0, 2.3, t))
    p = ease(clamp01((t - 0.35) / 1.25))
    n = len(_GC_VALS)
    xs = [px0 + (px1 - px0) * i / (n - 1) for i in range(n)]; ys = [py1 - (py1 - py0) * v / 120.0 for v in _GC_VALS]
    allp = np.array(list(zip(xs, ys)))
    seglen = np.hypot(*np.diff(allp, axis=0).T); tot = seglen.sum(); goal = p * tot
    path = [allp[0]]; acc_l = 0.0
    for i in range(n - 1):
        if acc_l + seglen[i] <= goal: path.append(allp[i + 1]); acc_l += seglen[i]
        else:
            f = (goal - acc_l) / max(1e-6, seglen[i]); path.append(allp[i] + (allp[i + 1] - allp[i]) * f); break
    path = np.array(path)
    if len(path) >= 2:
        fill = card.copy(); poly = np.vstack([path, [path[-1][0], py1], [path[0][0], py1]]).astype(np.int32)
        cv2.fillPoly(fill, [poly], acc[0], cv2.LINE_AA); card = cv2.addWeighted(fill, 0.16, card, 0.84, 0)
        cv2.polylines(card, [(path * 16).astype(np.int32).reshape(-1, 1, 2)], False, acc[0] if acc[0] != P["card"] else ink, max(2, int(4 * u)), cv2.LINE_AA, 4)
        for i, (lbl_i, txt_) in enumerate(((4, "52"), (6, "88"))):
            if goal >= seglen[:lbl_i].sum():
                cv2.circle(card, (int(xs[lbl_i]), int(ys[lbl_i])), int(5 * u), ink, -1, cv2.LINE_AA)
                put_text(card, txt_, xs[lbl_i], ys[lbl_i] - 18 * u, 16 * u, ink, "Bold", "c")
        ex, ey = path[-1]; r = 6 * u * (1 + 0.35 * math.sin(t * 11))
        cv2.circle(card, (int(ex), int(ey)), int(r), acc[0] if acc[0] != P["card"] else ink, -1, cv2.LINE_AA)
    val = int(round(120 * p))
    pw = 150 * u; pb, pa = rrect_layer(pw, 44 * u, 8 * u * RAD, acc[0])
    put_text(pb, "+%d%%" % val, pw / 2.0, pb.shape[0] / 2.0, 24 * u, _on(acc[0]), "Bold", "c")
    blit(card, pb, pa, cw - 22 * u - pw / 2.0, 0.15 * chh)
    out = img.copy()
    cx, cy = 0.5 * W, 0.715 * H + (1 - inn) * 0.05 * H
    soft_shadow2(out, aa, cx, cy, 0, 0.008 * H, 0.012 * W, 0.22 * op, 1.0)
    blit(out, card, aa, cx, cy, op, 0, 1.0)
    return out

# ----------------------------------------------------------------------------- 12 magazine cover ("I am on the cover")
_MONTHS = ["ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"]
_MONTHS_EN = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
def _lum(col): return 0.114 * col[0] + 0.587 * col[1] + 0.299 * col[2]

# ----------------------------------------------------------------------------- magazine cover (38)
def _tw(txt, size, weight, spacing=0.0):
    f = S.font(size, weight)
    return sum(f.getlength(ch) + spacing * size for ch in txt) if spacing else f.getlength(txt)

def _caph(size, weight):
    b = S.font(size, weight).getbbox("H"); return float(b[3] - b[1])

def _fit(txt, max_w, size, weight, spacing=0.0, min_frac=0.55):
    """largest size <= `size` at which txt fits max_w; if even min_frac*size is too wide the text is shortened with an ellipsis"""
    if not txt: return txt, size
    w = _tw(txt, size, weight, spacing); sz = size * min(1.0, max_w / max(1.0, w))
    if sz < size * min_frac:
        sz = size * min_frac
        while len(txt) > 1 and _tw(txt + "…", sz, weight, spacing) > max_w: txt = txt[:-1]
        txt = txt.rstrip() + "…"
    return txt, sz

_MAG_KEYS = ("head1", "head2", "big", "biglabel", "sub1", "sub2", "issue", "date")      # order of --items
def _mag_fields(c):
    """all texts of the cover. --text = masthead, --items = head1|head2|big|biglabel|sub1|sub2|issue|date (separator , or |),
    --opt key=value for any of them by name; '-' (or an empty value) hides an element"""
    o = getattr(c, "opts", {}) or {}
    it = items_opt(c, [])
    now = time.localtime()
    if lang(c) == "ru":
        dflt = dict(name="ЖУРНАЛ", head1="ВИДЕО И", head2="МОНТАЖ", big="15+", biglabel="ЭФФЕКТОВ", sub1="СЕКРЕТЫ МОНТАЖА",
                    sub2="ТИТРЫ · ГРАФИКА · ПЕРЕХОДЫ", issue="ВЫПУСК № 1", date="%s %d" % (_MONTHS[now.tm_mon - 1], now.tm_year))
    else:
        dflt = dict(name="MAGAZINE", head1="VIDEO &", head2="EDITING", big="15+", biglabel="EFFECTS", sub1="EDITING SECRETS",
                    sub2="TITLES · GRAPHICS · TRANSITIONS", issue="ISSUE NO. 1", date="%s %d" % (_MONTHS_EN[now.tm_mon - 1], now.tm_year))
    out = {}
    for key in ("name",) + _MAG_KEYS:
        v = o.get("text") if key == "name" else None
        if key in o and o[key] is not None: v = o[key]
        if v is None and key != "name" and _MAG_KEYS.index(key) < len(it): v = it[_MAG_KEYS.index(key)]
        v = dflt[key] if v is None or str(v).strip() == "" and key in ("name",) else str(v).strip()
        out[key] = "" if v in ("-", "—") else v.upper()
    bc = str(o.get("barcode") or "on").strip().lower()
    out["barcode"] = bc not in ("off", "no", "0", "-", "нет", "выкл")
    return out

def _mag_layout(img, c, cw, chh, u, P, acc):
    st = c.state
    if "mag" in st: return st["mag"]
    W, H = c.W, c.H
    F_ = _mag_fields(c)
    s = max(cw / float(W), chh / float(H)); bw, bh = int(round(W * s)), int(round(H * s))
    fb = face(img, c); m = matte(img, c)
    rows = np.where((m > 0.5).sum(1) >= 0.01 * W)[0]
    ht = float(rows[0]) * s if len(rows) else (fb[1] - 0.6 * fb[3]) * s            # top of the hair in the scaled frame
    y0 = int(min(max(0, ht - 0.19 * chh), bh - chh))
    x0 = int(min(max(0, (fb[0] + fb[2] * 0.5) * s - cw / 2.0), bw - cw))
    hair = ht - y0; chin = (fb[1] + fb[3]) * s - y0
    mx = 0.055 * cw; white = P["card"]
    bigcol = max(list(acc), key=_lum); bigcol = bigcol if _lum(bigcol) > 150 else white
    items = []                                      # dict(blk, kind, txt, x, y, size, weight, anchor, spacing, col, op)
    def T(blk, txt, x, y, size, weight, anchor, col, spacing=0.0, op=1.0):
        if txt: items.append(dict(blk=blk, kind="t", txt=txt, x=x, y=y, size=size, weight=weight, anchor=anchor, spacing=spacing, col=col, op=op))
    # --- top strip: issue / date
    sz_s = 22 * u; y_s = 0.034 * chh
    iss, szi = _fit(F_["issue"], 0.46 * cw, sz_s, "Medium", 0.08); dat, szd = _fit(F_["date"], 0.46 * cw, sz_s, "Medium", 0.08)
    T(0, iss, mx, y_s, szi, "Medium", "l", white, 0.08); T(0, dat, cw - mx, y_s, szd, "Medium", "r", white, 0.08)
    # --- masthead: sits in the band between the strip and the top of the hair
    band_top = y_s + 0.030 * chh; band_bot = hair - 0.018 * chh; overlap = False
    if band_bot - band_top < 0.055 * chh: band_bot = band_top + 0.085 * chh; overlap = True              # no room: the head stands in front of the title
    if F_["name"]:
        szw = 400.0; szw = szw * 0.90 * cw / max(1.0, _tw(F_["name"], szw, "Black"))
        szh = (band_bot - band_top) / (_caph(100, "Black") / 100.0)
        nm, szn = _fit(F_["name"], 0.90 * cw, min(szw, szh), "Black")
        T(0, nm, cw / 2.0, (band_top + band_bot) / 2.0, szn, "Black", "c", white)
    # --- footer: two lines of small text on the left, barcode on the right
    foot_bot = chh - 0.045 * chh; bc_w, bc_h = (0.19 * cw, 0.062 * chh) if F_["barcode"] else (0.0, 0.0)
    sub_w = cw - 2 * mx - (bc_w + 0.05 * cw if bc_w else 0.0)
    s1, sz1 = _fit(F_["sub1"], sub_w, 30 * u, "Bold", 0.08); s2, sz2 = _fit(F_["sub2"], sub_w, 23 * u, "Medium", 0.06)
    y2 = foot_bot - _caph(sz2, "Medium") / 2.0 if s2 else foot_bot
    y1 = (y2 - (_caph(sz2, "Medium") / 2.0 + 14 * u if s2 else 0) - _caph(sz1, "Bold") / 2.0) if s1 else y2
    T(3, s1, mx, y1, sz1, "Bold", "l", white, 0.08); T(3, s2, mx, y2, sz2, "Medium", "l", white, 0.06, 0.85)
    foot_top = min([foot_bot - bc_h if bc_w else foot_bot] + ([y1 - _caph(sz1, "Bold") / 2.0] if s1 else []))
    bar = dict(x=cw - mx - bc_w / 2.0, y=foot_bot - bc_h / 2.0, w=bc_w, h=bc_h) if bc_w else None
    # --- middle block: big number (left) + cover line (right), below the chin, bottom-aligned above the footer
    mid_bot = foot_top - 0.040 * chh; avail_top = max(0.60 * chh, chin + 0.05 * chh)
    big, h1, h2 = F_["big"], F_["head1"], F_["head2"]; lab = F_["biglabel"] if big else ""            # a label without a number makes no sense
    best = None
    for f in np.arange(1.0, 0.49, -0.05):
        szb = 0.21 * cw * f; szl = 30 * u * f
        bt, szb = _fit(big, 0.5 * cw, szb, "Black", 0.0, 0.35) if big else ("", szb); lt, szl = _fit(lab, 0.5 * cw, szl, "Bold", 0.12) if lab else ("", szl)
        left_w = max(_tw(bt, szb, "Black") if bt else 0, _tw(lt, szl, "Bold", 0.12) if lt else 0)
        gap = 0.05 * cw if left_w else 0.0
        right_w = cw - 2 * mx - left_w - gap
        hs = 0.068 * cw * f; pad = 0.42 * hs
        t1, s1_ = _fit(h1, right_w, hs, "Black") if h1 else ("", hs)
        t2, s2_ = _fit(h2, right_w - 2 * pad, hs, "Black") if h2 else ("", hs)
        if t1 and t2: s1_ = s2_ = min(s1_, s2_)
        ch_l = (_caph(szb, "Black") if bt else 0) + (14 * u * f + _caph(szl, "Bold") if lt and bt else _caph(szl, "Bold") if lt else 0)
        plate_h = 1.55 * s2_ if t2 else 0.0
        ch_r = (_caph(s1_, "Black") if t1 else 0) + (16 * u * f if t1 and t2 else 0) + plate_h
        best = (f, szb, szl, bt, lt, left_w, t1, s1_, t2, s2_, pad, plate_h, ch_l, ch_r)
        if mid_bot - max(ch_l, ch_r) >= avail_top: break
    f, szb, szl, bt, lt, left_w, t1, s1_, t2, s2_, pad, plate_h, ch_l, ch_r = best
    if bt or lt:
        yl = mid_bot
        if lt: T(2, lt, mx, yl - _caph(szl, "Bold") / 2.0, szl, "Bold", "l", bigcol, 0.12); yl -= _caph(szl, "Bold") + 14 * u * f
        if bt: T(2, bt, mx - 0.01 * szb, yl - _caph(szb, "Black") / 2.0, szb, "Black", "l", white)
    plate = None; xr = cw - mx
    if t2:
        pw = _tw(t2, s2_, "Black") + 2 * pad
        plate = dict(x=xr - pw / 2.0, y=mid_bot - plate_h / 2.0, w=pw, h=plate_h, txt=t2, size=s2_)
    if t1:
        y1c = mid_bot - plate_h - (16 * u * f if t2 else 0) - _caph(s1_, "Black") / 2.0
        T(1, t1, xr, y1c, s1_, "Black", "r", white)
    L = dict(s=s, bw=bw, bh=bh, x0=x0, y0=y0, hair=hair, chin=chin, overlap=overlap, items=items, plate=plate, bar=bar, mid_top=mid_bot - max(ch_l, ch_r),
             mid_bot=mid_bot, foot_top=foot_top, f=f, F=F_)
    st["mag"] = L
    return L

def fx_magazine(img, t, c):
    W, H = c.W, c.H; u = W / 1080.0
    D = 2.15
    if t > D: return img
    P = pal(c); acc = _acc(P); RAD = P["rad"]
    k = smooth(0.0, 0.18, t) * (1 - smooth(1.85, 2.1, t))
    if k <= 0.003: return img
    e_in = back_out(clamp01((t - 0.02) / 0.45)); e_out = ease(clamp01((t - 1.72) / 0.38))
    cw, chh = int(0.89 * W), int(0.73 * H)
    L = _mag_layout(img, c, cw, chh, u, P, acc)
    x0, y0 = L["x0"], L["y0"]
    big = cv2.resize(img, (L["bw"], L["bh"]), interpolation=cv2.INTER_AREA)
    vid = big[y0:y0 + chh, x0:x0 + cw]
    m = cv2.resize(matte(img, c), (L["bw"], L["bh"]), interpolation=cv2.INTER_AREA)[y0:y0 + chh, x0:x0 + cw][..., None]
    ink = np.array(P["ink"], np.float32)
    # --- dark gradient under the title; head (if it reaches into the title band) stays in front
    gy = np.clip(1 - np.arange(chh, dtype=np.float32) / (0.34 * chh), 0, 1)[:, None, None] * 0.58
    card = (vid.astype(np.float32) * (1 - gy) + ink * gy).astype(np.uint8)
    def rv(t0): a = smooth(t0, t0 + 0.30, t); return a, (1 - a) * 18 * u                  # reveal: alpha, rise in px
    def draw(blk):
        a, dy = rv((0.16, 0.46, 0.58, 0.70)[blk])
        for it in L["items"]:
            if it["blk"] == blk and a > 0.01:
                put_text(card, it["txt"], it["x"], it["y"] + dy, it["size"], it["col"], it["weight"], it["anchor"], op=a * it["op"], spacing=it["spacing"])
        return a, dy
    draw(0)
    card = (card.astype(np.float32) * (1 - m) + vid.astype(np.float32) * m).astype(np.uint8) if L["overlap"] else card
    # --- dark gradient under the cover lines (so white text reads on the light sweater)
    g0 = 0.50 * chh; gb = np.clip((np.arange(chh, dtype=np.float32) - g0) / (chh - g0), 0, 1)[:, None, None]; gb = (gb * gb * (3 - 2 * gb)) * 0.66
    card = (card.astype(np.float32) * (1 - gb) + ink * gb).astype(np.uint8)
    a1, dy1 = draw(1)
    if L["plate"] and a1 > 0.01:
        p = L["plate"]; tb, ta = rrect_layer(p["w"], p["h"], 5 * u * RAD, acc[0])
        put_text(tb, p["txt"], tb.shape[1] / 2.0, tb.shape[0] / 2.0, p["size"], _on(acc[0]), "Black", "c")
        blit(card, tb, ta, p["x"], p["y"] + dy1, a1)
    draw(2)
    a3, dy3 = draw(3)
    if L["bar"] and a3 > 0.01:
        b = L["bar"]; bw_, bh_ = int(b["w"]), int(b["h"])
        pb = np.full((bh_, bw_, 3), 255, np.uint8); rng = np.random.default_rng(3); xx = 5 * u
        while xx < bw_ - 6 * u:
            w_ = rng.choice([1, 2, 3]) * max(1.0, 1.4 * u); cv2.rectangle(pb, (int(xx), int(4 * u)), (int(xx + w_), bh_ - int(4 * u)), (20, 20, 22), -1); xx += w_ + rng.choice([1, 2]) * 1.4 * u
        blit(card, pb, np.ones((bh_, bw_), np.float32), b["x"], b["y"] + dy3, a3)
    # --- backdrop and card placement
    bg = np.empty((H, W, 3), np.uint8); bg[:] = P["bg"]
    ba, aa = rrect_layer(cw, chh, 6 * u * RAD, (255, 255, 255))
    off = (1 - e_in) * 0.95 * H + e_out * 0.95 * H
    rot = lerp(7.0, -2.4, e_in) + e_out * 5.0
    cx, cy = 0.5 * W, 0.50 * H + off
    soft_shadow2(bg, aa, cx, cy, 0.006 * W, 0.012 * H, 0.014 * W, 0.30, 1.0, rot)
    blit(bg, card, aa, cx, cy, 1.0, rot, 1.0)
    return _F().mix(img, bg, k)

# ----------------------------------------------------------------------------- registry
def build(fx_mod):
    def e(fn, ru, alias, dur, desc): return dict(fn=fn, ru=ru, alias=alias, kind="intro", dur=dur, desc=desc)
    return {
        "quickzoom":    e(fx_quickzoom, "резкое приближение", ["quick zoom", "быстрый наезд", "зум с сдвигом цвета"], 1.9, "быстрый наезд 100%→120% за 0.2 с, цветовые каналы разъезжаются (до 18 px, 0.5 с), радиальные линии скорости (0.35 с), затем плавный возврат"),
        "smoothzoomout": e(fx_smoothzoomout, "плавное отдаление", ["smooth zoom out", "отъезд", "плавный отъезд"], 1.45, "камера возвращается с 120% до 100% за 1 с с плавным разгоном и торможением (в ролике идёт сразу после «резкого приближения»)"),
        "colorframe":   e(fx_colorframe, "цветная рамка", ["color frame", "рамка", "цветная окантовка"], 1.9, "поверх видео выскакивает тонкая светящаяся рамка: цвет плавно перетекает по трём акцентам, по рамке бежит яркая комета, мягкое свечение снаружи и внутри (цвета из стиля)"),
        "framebreak":   e(fx_framebreak, "разбить рамку", ["break frame", "разбитая рамка", "осколки"], 1.75, "та же светящаяся рамка, что в «цветной рамке» (33), держится 0.42 с, трескается и рассыпается на ~48 светящихся кусков того же цвета: вращение, переворот, падение; следом конфетти и круговая волна"),
        "growthchart":  e(fx_growthchart, "рисуем график", ["draw graph", "график", "график роста"], 2.3, "карточка с осями и сеткой, линия роста рисуется слева направо с заливкой, подписи значений, счётчик +N% до 120, пульсирующая точка; заголовок через --text"),
        "splitscreen":  e(fx_splitscreen, "сплит-экран", ["split screen", "разделённый экран", "двойной экран"], 1.9, "экран делится по горизонтали: сверху обычный кадр, снизу тот же кадр в 135%; половины выезжают сверху и снизу за 0.3 с, между ними линия; подпись на линии через --text"),
        "magazine":     e(fx_magazine, "я на обложке", ["magazine cover", "обложка журнала", "обложка"], 2.15, "видео превращается в обложку журнала: выпуск и дата сверху, название над причёской, число с подписью и строка с плашкой ниже подбородка, две мелкие строки и штрихкод внизу; ничего не налезает на лицо; все тексты меняются: --text (название), --items (по порядку: строка1|строка2|число|подпись|низ1|низ2|выпуск|дата), --opt ключ=значение, «-» скрывает"),
        "pipdelay":     e(fx_pipdelay, "видео поверх видео", ["video in video", "окно с задержкой", "картинка в картинке"], 2.1, "в правом нижнем углу окно с отметкой REC, в нём то же видео с задержкой 0.5 с (голова и подбородок целиком), окно чуть наклонено и плавает"),
        "bwframe":      e(fx_bwframe, "чёрно-белый кадр", ["black and white", "ч/б", "чёрно-белое", "черно-белый"], 1.9, "цвет уходит за 0.35 с (контраст чуть выше), держится, возвращается за 0.45 с"),
        "pixelate":     e(fx_pixelate, "пикселизация", ["pixelate", "мозаика кадра", "пиксели"], 1.8, "весь кадр превращается в мозаику: блок растёт 1→48 px за 0.25 с, держится, возвращается за 0.55 с"),
        "vignette":     e(fx_vignette, "виньетка", ["vignette", "затемнение краёв"], 1.55, "края кадра затемняются радиальным градиентом: появляется 0.35 с, держится ~0.75 с, уходит за 0.45 с"),
        "fadeblack":    e(fx_fadeblack, "плавное затемнение", ["fade to black", "уход в чёрный", "затемнение"], 1.75, "экран уходит в чёрный за 0.8 с, короткая пауза, быстрый возврат за 0.4 с"),
    }
