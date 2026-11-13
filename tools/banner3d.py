"""FOLGENSCHWER – YouTube-Banner 2560x1440 im Stil des 3D-Pastell-Logos (SDF-Raymarching).
Fallende Pastell-Dominos (Kettenreaktion) -> Schriftzug -> gespaltenes F. Alles Wichtige liegt in der
Safe Area 1546x423 (Mitte).  python3 tools/banner3d.py [breite]   (Standard 1920, wird auf 2560 skaliert)"""
import math, os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
WR = int(sys.argv[1]) if len(sys.argv) > 1 else 1920
HR = WR * 1440 // 2560
f32 = np.float32
def norm(v): return v / np.linalg.norm(v)

# Welt: 163 px (bei 2560) = 1 Einheit; Streifenmitte = y 0
FX = 3.75                                           # F rechts in der Safe Area
YAW = math.radians(-27); CY, SY = math.cos(YAW), math.sin(YAW)
BOXES = [(-0.42, 0.0, 0.19, 0.96), (0.10, 0.77, 0.71, 0.19), (0.0, 0.05, 0.56, 0.16)]
def sd_f(q):
    d2 = None
    for cx, cy, hx, hy in BOXES:
        ax = np.abs(q[:, 0] - cx) - hx; ay = np.abs(q[:, 1] - cy) - hy
        d = np.sqrt(np.maximum(ax, 0) ** 2 + np.maximum(ay, 0) ** 2) + np.minimum(np.maximum(ax, ay), 0)
        d2 = d if d2 is None else np.minimum(d2, d)
    d2 = d2 - 0.035; wz = np.abs(q[:, 2]) - 0.30
    return np.minimum(np.maximum(d2, wz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(wz, 0) ** 2) - 0.045
DIR = norm(np.array([1.3, 1.45])); NRM = np.array([-DIR[1], DIR[0]]); P0 = np.array([0.0, 0.18])
def crack(q):
    u = (q[:, 0] - P0[0]) * DIR[0] + (q[:, 1] - P0[1]) * DIR[1]
    s = (q[:, 0] - P0[0]) * NRM[0] + (q[:, 1] - P0[1]) * NRM[1]
    return s + 0.085 * (np.abs(((u * 2.6 + 0.3) % 1.0) - 0.5) * 2 - 0.5)
GAP = 0.022; OFF = np.array([NRM[0] * 0.055 - 0.01, NRM[1] * 0.055 + 0.03, -0.03], f32)
FLOOR_Y = -1.045

PASTEL = np.array([[0.45, 0.92, 0.78], [1.0, 0.86, 0.45], [0.66, 0.56, 1.0], [1.0, 0.46, 0.58], [0.45, 0.76, 1.0]], f32)
# Dominos: von weit links (schon gefallen) bis kurz vor dem Schriftzug (kippt gerade)
PHI = math.radians(40); EX, EZ = math.cos(PHI), math.sin(PHI)      # Kette läuft schräg von hinten links nach vorne rechts
OX, OZ = -2.75, 0.75                                               # letzter (noch stehender) Stein
DOM = []
sp = 0.0; k = 0
while sp > -11.5:
    prog = 1 + sp / 11.5                                           # 1 vorne … 0 hinten
    ang = 0.0 if k < 1 else math.radians(min(78, 6 + 10 * k))
    DOM.append((sp, ang, k % 5)); sp -= 0.56 + 0.05 * min(k, 8); k += 1
TH, HH, DZ = 0.10, 0.66, 0.40                      # halbe Dicke, halbe Höhe, halbe Tiefe
_r = np.random.default_rng(6)
DEB = [(_r.uniform(-7.5, 5.5), _r.uniform(-0.6, 2.2), _r.uniform(-1.2, 0.9), _r.uniform(0.035, 0.085), k % 5) for k in range(26)]
DEB += [(FX + (P0 + DIR * u)[0] * 0.9 + _r.normal(0, 0.06), (P0 + DIR * u)[1] + _r.normal(0, 0.06), _r.uniform(-0.1, 0.7), _r.uniform(0.03, 0.06), k % 3) for k, u in enumerate(np.linspace(-1.1, 1.1, 8))]

def f_local(p):
    x_ = (p[:, 0] - FX) * CY + p[:, 2] * SY; z_ = -(p[:, 0] - FX) * SY + p[:, 2] * CY
    return np.stack([x_, p[:, 1], z_], 1)

def sdf(p, want=False):
    q = f_local(p)
    s1 = crack(q); a = np.maximum(sd_f(q), s1 + GAP)
    q2 = q - OFF; s2 = crack(q2); b = np.maximum(sd_f(q2), GAP - s2)
    dF = np.minimum(a, b)
    dD = np.full(len(p), 1e9, f32); iD = np.zeros(len(p), np.int32)
    near = p[:, 0] < -1.4
    if near.any():
        pn = p[near]; best = np.full(len(pn), 1e9, f32); bi = np.zeros(len(pn), np.int32)
        cxl = (pn[:, 0] - OX) * EX + (pn[:, 2] - OZ) * EZ; czl = -(pn[:, 0] - OX) * EZ + (pn[:, 2] - OZ) * EX
        for (dx, ang, cid) in DOM:
            px = cxl - (dx + TH); py = pn[:, 1] - FLOOR_Y               # Drehpunkt: vordere untere Kante
            c, s_ = math.cos(ang), math.sin(ang)
            lx = px * c - py * s_; ly = px * s_ + py * c                 # Stein kippt nach vorne (+x der Kette)
            ex = np.abs(lx + TH) - (TH - 0.03); ey = np.abs(ly - HH) - (HH - 0.03); ez = np.abs(czl) - (DZ - 0.03)
            d = np.sqrt(np.maximum(ex, 0) ** 2 + np.maximum(ey, 0) ** 2 + np.maximum(ez, 0) ** 2) + np.minimum(np.maximum(np.maximum(ex, ey), ez), 0) - 0.03
            m = d < best; best = np.where(m, d, best); bi = np.where(m, cid, bi)
        dD[near] = best; iD[near] = bi
    dE = np.full(len(p), 1e9, f32); iE = np.zeros(len(p), np.int32)
    for (ex_, ey_, ez_, r, cid) in DEB:
        e = np.maximum(np.maximum(np.abs(p[:, 0] - ex_), np.abs(p[:, 1] - ey_)), np.abs(p[:, 2] - ez_)) - r * 0.72
        e = np.maximum(e, np.sqrt((p[:, 0] - ex_) ** 2 + (p[:, 1] - ey_) ** 2 + (p[:, 2] - ez_) ** 2) - r)
        m = e < dE; dE = np.where(m, e, dE); iE = np.where(m, cid, iE)
    fl = p[:, 1] - FLOOR_Y
    out = np.minimum(np.minimum(np.minimum(dF, dD), dE), fl) * 0.85
    if not want: return out
    st = np.stack([dF, dE, fl, dD], 1); mat = st.argmin(1)        # 0 F, 1 Splitter, 2 Boden, 3 Domino
    cut = (((a <= b) & (np.abs(s1 + GAP) < 0.03)) | ((b < a) & (np.abs(GAP - s2) < 0.03))) & (mat == 0)
    return out, mat, cut, np.where(mat == 3, iD, iE), q

def march(ro, rd, steps=120, tmax=40.0):
    t = np.full(len(ro), 0.01, f32); alive = np.ones(len(ro), bool); hit = np.zeros(len(ro), bool)
    for _ in range(steps):
        idx = np.nonzero(alive)[0]
        if len(idx) == 0: break
        d = sdf(ro[idx] + rd[idx] * t[idx, None]); h = d < 0.0015
        hit[idx[h]] = True; alive[idx[h]] = False
        t[idx] += np.where(h, 0, d).astype(f32)
        alive[idx[t[idx] > tmax]] = False
    return t, hit

cam = np.array([-0.6, 1.0, 17.0], f32); tgt = np.array([0.0, 0.02, 0.0], f32)
fw = norm(tgt - cam); rt = norm(np.cross(fw, [0, 1, 0])); up = np.cross(rt, fw)
ys, xs = np.mgrid[0:HR, 0:WR].astype(f32)
half_w = (2560 / 2 / 163) / 17.0
u = (xs + 0.5 - WR / 2) / (WR / 2) * half_w; v = -(ys + 0.5 - HR / 2) / (WR / 2) * half_w
rd = (fw[None, :] + u.reshape(-1, 1) * rt[None, :] + v.reshape(-1, 1) * up[None, :]).astype(f32)
rd /= np.linalg.norm(rd, axis=1, keepdims=True); ro = np.broadcast_to(cam, rd.shape).astype(f32)

sx = (xs - WR / 2) / (WR / 2); sy = (ys - HR / 2) / (HR / 2)
g = np.clip((sy + 1) / 2, 0, 1)[..., None]
top = np.array([0.05, 0.03, 0.16], f32); mid = np.array([0.40, 0.20, 0.52], f32); bot = np.array([0.74, 0.40, 0.52], f32)
bgc = np.where(g < 0.56, top + (mid - top) * (g / 0.56) ** 1.3, mid + (bot - mid) * ((g - 0.56) / 0.44))
for cx_, k_ in ((0.47, 0.42), (-0.55, 0.22)):          # Lichtschein hinter F, Titel und Dominos
    rr = np.sqrt(((sx - cx_) * 1.78) ** 2 + (sy + 0.05) ** 2); ang = np.arctan2(sy + 0.05, (sx - cx_) * 1.78)
    rays = (0.5 + 0.5 * np.sin(ang * 9 + 1.3 * np.sin(ang * 3))) ** 3
    bgc = bgc + (np.exp(-(rr / 0.55) ** 2) * (0.55 + 0.35 * rays))[..., None] * np.array([1.0, 0.72, 0.62], f32) * k_
bgc = bgc * (1 - 0.7 * np.clip((np.sqrt((sx * 0.9) ** 2 + sy ** 2) - 0.6) / 0.8, 0, 1) ** 1.3)[..., None]
bgc = bgc.reshape(-1, 3).astype(f32)

print("march …", WR, HR); t, hit = march(ro, rd)
col = bgc.copy(); emis = np.zeros((WR * HR, 3), f32)
idx = np.nonzero(hit)[0]; p = ro[idx] + rd[idx] * t[idx, None]
_, mat, cut, cid, q = sdf(p, True)
n = np.zeros_like(p)
for k in range(3):
    dp = np.zeros(3, f32); dp[k] = 0.002; n[:, k] = sdf(p + dp) - sdf(p - dp)
n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
L1 = norm(np.array([0.72, 0.62, 0.48])).astype(f32); L2 = norm(np.array([-0.85, 0.35, -0.55])).astype(f32)
print("shadow …")
sh = np.ones(len(p), f32); ts = np.full(len(p), 0.03, f32); po = p + n * 0.012
for _ in range(44):
    d = sdf(po + L1[None, :] * ts[:, None]); sh = np.minimum(sh, np.clip(9.0 * d / ts, 0, 1)); ts += np.clip(d, 0.015, 0.3).astype(f32)
ao = np.ones(len(p), f32)
for k in range(1, 5):
    hh = 0.06 * k; ao -= (hh - sdf(p + n * hh)) * (0.5 / k)
ao = np.clip(ao, 0.25, 1)
alb = np.empty((len(p), 3), f32)
front = np.clip(n[:, 2] * CY + n[:, 0] * -SY, 0, 1)[:, None]
alb[:] = np.array([0.98, 0.36, 0.50], f32) * (1 - front) + np.array([1.0, 0.56, 0.58], f32) * front
m1 = (mat == 1) | (mat == 3); alb[m1] = PASTEL[cid[m1]]
alb[mat == 2] = np.array([0.40, 0.30, 0.64], f32)
dif1 = np.clip(n @ L1, 0, 1) * sh; dif2 = np.clip(n @ L2, 0, 1)
vdir = -rd[idx]; hlf = L1[None, :] + vdir; hlf /= np.linalg.norm(hlf, axis=1, keepdims=True)
spec = np.clip((n * hlf).sum(1), 0, 1) ** 40 * sh; fres = (1 - np.clip((n * vdir).sum(1), 0, 1)) ** 3
c = alb * (dif1[:, None] * np.array([1.0, 0.90, 0.80], f32) * 1.15 + dif2[:, None] * np.array([0.30, 0.95, 0.85], f32) * 1.0
           + ao[:, None] * np.array([0.34, 0.26, 0.62], f32) * 0.30)
c += spec[:, None] * 0.30 + fres[:, None] * np.array([0.5, 0.95, 0.9], f32) * 0.30 * (mat != 2)[:, None]
gl = np.exp(-np.abs(crack(q)) / 0.09)[:, None] * (mat == 0)[:, None]
c += gl * np.array([1.0, 0.40, 0.22], f32) * 0.40
em = np.zeros((len(p), 3), f32); em[cut] = np.array([1.0, 0.30, 0.14], f32) * 2.4
c = np.where(cut[:, None], em + np.array([1.0, 0.75, 0.35], f32) * 0.5, c)
fog = np.clip((t[idx] - 16.0) / 9.0, 0, 1)[:, None]
c = np.where((mat == 2)[:, None], c * (1 - fog) + bgc[idx] * fog, c)
col[idx] = c; emis[idx] = em

img = col.reshape(HR, WR, 3); E = emis.reshape(HR, WR, 3)
def blur(a, r):
    im = Image.fromarray((np.clip(a / 4, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)); return np.asarray(im, f32) / 255 * 4
img = img + blur(E, WR / 220) * 0.55 + blur(E, WR / 60) * 0.30 + blur(np.clip(img - 1.0, 0, 4), WR / 200) * 0.3
rng = np.random.default_rng(2)
for _ in range(260):
    x, y = rng.uniform(0, WR), rng.uniform(0, HR); r = rng.uniform(1.0, 3.0) * WR / 2560; a = rng.uniform(0.05, 0.22)
    x0, x1, y0, y1 = int(max(0, x - 3 * r)), int(min(WR, x + 3 * r + 1)), int(max(0, y - 3 * r)), int(min(HR, y + 3 * r + 1))
    yy, xx = np.mgrid[y0:y1, x0:x1]
    img[y0:y1, x0:x1] += (np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r)) * a)[..., None] * np.array([1.0, 0.95, 0.85], f32)
img = 1 - np.exp(-img * 1.05); img = np.clip(img, 0, 1) ** (1 / 2.0)
img = img * img * (3 - 2 * img) * 0.6 + img * 0.4
m_ = img.mean(-1, keepdims=True); img = np.clip(m_ + (img - m_) * 1.25, 0, 1)
base = Image.fromarray((img * 255).astype(np.uint8)).resize((2560, 1440), Image.LANCZOS)
base.save(os.path.join(ROOT, "brand", "banner3d_2560x1440_ohne_text.jpg"), quality=94)
print("ok")

# ---------- Schriftzug in der Safe Area (zwischen Dominos und F) ----------
def F_(w, sz): return ImageFont.truetype(os.path.join(ROOT, "fonts", f"Inter-{w}.otf"), sz)
img2 = base.copy()
txt = "FOLGENSCHWER"; f = F_("Black", 108); tr = 4
ws = [f.getlength(ch) + tr for ch in txt]; tot = sum(ws) - tr
cx, y = 1318, 735
def draw_text(dr, dx, dy, fill):
    xx = cx - tot / 2 + dx
    for ch, wd in zip(txt, ws): dr.text((xx, y + dy), ch, font=f, fill=fill, anchor="ls"); xx += wd
sh = Image.new("L", img2.size, 0); draw_text(ImageDraw.Draw(sh), 14, 22, 255)
img2.paste((40, 16, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.8)))
d2 = ImageDraw.Draw(img2)
for k in range(12, 0, -1): draw_text(d2, k * 0.9, k * 0.9, (214, 96, 128))      # Extrusion in Rosé
draw_text(d2, 0, 0, (255, 244, 236))
f2 = F_("Bold", 46); sub = "Was wäre, wenn …?"
m2 = Image.new("L", img2.size, 0); ImageDraw.Draw(m2).text((cx, y + 62), sub, font=f2, fill=255, anchor="mm")
img2.paste((40, 16, 70), (0, 0), m2.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(min(255, v * 1.5))))
img2.paste((150, 240, 215), (0, 0), m2)
img2.save(os.path.join(ROOT, "brand", "banner3d_2560x1440.jpg"), quality=94)
print("text", int(cx - tot / 2), int(cx + tot / 2))
