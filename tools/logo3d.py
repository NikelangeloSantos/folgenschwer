"""FOLGENSCHWER-Logo: 3D, pastell, dramatisch. Echter 3D-Render (SDF-Raymarching in numpy).
Ein pastellfarbenes, extrudiertes F wird von einem glühenden Riss gespalten; Splitter schweben,
hartes Seitenlicht, langer Schatten, Lichtkegel von hinten.  python3 tools/logo3d.py [größe]"""
import math, os, sys
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1600
f32 = np.float32

def norm(v): return v / np.linalg.norm(v)
YAW = math.radians(-27); CY, SY = math.cos(YAW), math.sin(YAW)
def to_obj(p):
    x = p[:, 0] * CY + p[:, 2] * SY; z = -p[:, 0] * SY + p[:, 2] * CY
    return np.stack([x, p[:, 1], z], 1)

BOXES = [(-0.42, 0.0, 0.19, 0.96), (0.10, 0.77, 0.71, 0.19), (0.0, 0.05, 0.56, 0.16)]
def sd_f(q):
    d2 = None
    for cx, cy, hx, hy in BOXES:
        ax = np.abs(q[:, 0] - cx) - hx; ay = np.abs(q[:, 1] - cy) - hy
        d = np.sqrt(np.maximum(ax, 0) ** 2 + np.maximum(ay, 0) ** 2) + np.minimum(np.maximum(ax, ay), 0)
        d2 = d if d2 is None else np.minimum(d2, d)
    d2 = d2 - 0.035
    wz = np.abs(q[:, 2]) - 0.30
    return np.minimum(np.maximum(d2, wz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(wz, 0) ** 2) - 0.045

DIR = norm(np.array([1.3, 1.45])); NRM = np.array([-DIR[1], DIR[0]]); P0 = np.array([0.0, 0.18])
def crack(q):
    u = (q[:, 0] - P0[0]) * DIR[0] + (q[:, 1] - P0[1]) * DIR[1]
    s = (q[:, 0] - P0[0]) * NRM[0] + (q[:, 1] - P0[1]) * NRM[1]
    tri = np.abs(((u * 2.6 + 0.3) % 1.0) - 0.5) * 2 - 0.5
    return s + 0.085 * tri
GAP = 0.022; OFF = np.array([NRM[0] * 0.055 - 0.01, NRM[1] * 0.055 + 0.03, -0.03], f32)

_r = np.random.default_rng(4)
DEB = []
for k in range(11):
    u = _r.uniform(-1.25, 1.25); c = P0 + DIR * u + NRM * _r.normal(0.03, 0.06)
    DEB.append((c[0] + _r.normal(0, 0.05), c[1] + _r.normal(0, 0.05), _r.uniform(-0.2, 0.75), _r.uniform(0.028, 0.07), k % 3))
PASTEL = np.array([[0.62, 0.95, 0.84], [1.0, 0.93, 0.62], [0.78, 0.70, 1.0]], f32)   # Mint, Butter, Flieder
FLOOR_Y = -1.045

def sdf(p, want_mat=False):
    q = to_obj(p)
    s1 = crack(q); a = np.maximum(sd_f(q), s1 + GAP)                 # unteres Stück
    q2 = q - OFF; s2 = crack(q2); b = np.maximum(sd_f(q2), GAP - s2)  # oberes Stück, leicht versetzt
    d = np.minimum(a, b)
    dd = None; did = None
    for k, (x, y, z, r, cid) in enumerate(DEB):
        e = np.maximum(np.maximum(np.abs(q[:, 0] - x), np.abs(q[:, 1] - y)), np.abs(q[:, 2] - z)) - r * 0.72
        e = np.maximum(e, np.sqrt((q[:, 0] - x) ** 2 + (q[:, 1] - y) ** 2 + (q[:, 2] - z) ** 2) - r)
        if dd is None: dd = e; did = np.full(len(e), cid)
        else:
            m = e < dd; dd = np.where(m, e, dd); did = np.where(m, cid, did)
    fl = p[:, 1] - FLOOR_Y
    out = np.minimum(np.minimum(d, dd), fl) * 0.85
    if not want_mat: return out
    mat = np.zeros(len(p), np.int32)                 # 0 = F, 1 = Splitter, 2 = Boden
    mat[(dd < d) & (dd < fl)] = 1; mat[(fl < d) & (fl < dd)] = 2
    cutA = (a <= b) & (np.abs(s1 + GAP) < 0.03); cutB = (b < a) & (np.abs(GAP - s2) < 0.03)
    return out, mat, (cutA | cutB) & (mat == 0), did, q

def march(ro, rd, steps=110, tmax=14.0):
    t = np.full(len(ro), 0.01, f32); alive = np.ones(len(ro), bool); hit = np.zeros(len(ro), bool)
    for _ in range(steps):
        idx = np.nonzero(alive)[0]
        if len(idx) == 0: break
        d = sdf(ro[idx] + rd[idx] * t[idx, None])
        h = d < 0.0012
        hit[idx[h]] = True; alive[idx[h]] = False
        t[idx] += np.where(h, 0, d).astype(f32)
        far = t[idx] > tmax; alive[idx[far]] = False
    return t, hit

# ---------- Kamera (tief, leicht von unten = dramatisch) ----------
cam = np.array([-0.55, -0.42, 5.6], f32); tgt = np.array([0.02, 0.06, 0.0], f32)
fw = norm(tgt - cam); rt = norm(np.cross(fw, [0, 1, 0])); up = np.cross(rt, fw)
ys, xs = np.mgrid[0:N, 0:N].astype(f32)
u = (xs + 0.5 - N / 2) / (N / 2) * 0.305; v = -(ys + 0.5 - N / 2) / (N / 2) * 0.305
rd = (fw[None, :] + u.reshape(-1, 1) * rt[None, :] + v.reshape(-1, 1) * up[None, :]).astype(f32)
rd /= np.linalg.norm(rd, axis=1, keepdims=True)
ro = np.broadcast_to(cam, rd.shape).astype(f32)

# ---------- Hintergrund: Pastell-Verlauf, Lichtkegel von hinten, dunkle Ränder ----------
sx = (xs - N / 2) / (N / 2); sy = (ys - N / 2) / (N / 2)
g = np.clip((sy + 1) / 2, 0, 1)[..., None]
top = np.array([0.07, 0.05, 0.20], f32); mid = np.array([0.56, 0.30, 0.62], f32); bot = np.array([0.86, 0.50, 0.56], f32)
bgc = np.where(g < 0.62, top + (mid - top) * (g / 0.62) ** 1.4, mid + (bot - mid) * ((g - 0.62) / 0.38))
rr = np.sqrt((sx + 0.05) ** 2 + (sy + 0.12) ** 2); ang = np.arctan2(sy + 0.12, sx + 0.05)
rays = (0.5 + 0.5 * np.sin(ang * 9 + 1.3 * np.sin(ang * 3))) ** 3
bgc = bgc + (np.exp(-(rr / 0.62) ** 2) * (0.55 + 0.35 * rays))[..., None] * np.array([1.0, 0.72, 0.62], f32) * 0.55
bgc = bgc * (1 - 0.8 * np.clip((np.sqrt(sx ** 2 + sy ** 2) - 0.45) / 0.9, 0, 1) ** 1.3)[..., None]
bgc = bgc.reshape(-1, 3).astype(f32)

print("march …"); t, hit = march(ro, rd)
col = bgc.copy(); emis = np.zeros((N * N, 3), f32)
idx = np.nonzero(hit)[0]; p = ro[idx] + rd[idx] * t[idx, None]
_, mat, cut, did, q = sdf(p, True)
e = 0.0015; n = np.zeros_like(p)
for k in range(3):
    dp = np.zeros(3, f32); dp[k] = e
    n[:, k] = sdf(p + dp) - sdf(p - dp)
n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9

L1 = norm(np.array([0.72, 0.62, 0.48])).astype(f32); L2 = norm(np.array([-0.85, 0.35, -0.55])).astype(f32)
print("shadow …")
sh = np.ones(len(p), f32); ts = np.full(len(p), 0.03, f32); po = p + n * 0.01
for _ in range(48):
    d = sdf(po + L1[None, :] * ts[:, None]); sh = np.minimum(sh, np.clip(9.0 * d / ts, 0, 1)); ts += np.clip(d, 0.012, 0.25).astype(f32)
ao = np.ones(len(p), f32)
for k in range(1, 6):
    hh = 0.05 * k; ao -= (hh - sdf(p + n * hh)) * (0.5 / k)
ao = np.clip(ao, 0.25, 1)

alb = np.empty((len(p), 3), f32)
front = np.clip(n[:, 2] * CY + n[:, 0] * -SY, 0, 1)[:, None]            # Vorderfläche heller
alb[:] = np.array([0.98, 0.36, 0.50], f32) * (1 - front) + np.array([1.0, 0.56, 0.58], f32) * front
alb[mat == 1] = PASTEL[did[mat == 1]]
fog = np.clip((t[idx] - 5.0) / 6.0, 0, 1)[:, None]
alb[mat == 2] = np.array([0.50, 0.40, 0.72], f32)

dif1 = np.clip(n @ L1, 0, 1) * sh; dif2 = np.clip(n @ L2, 0, 1)
vdir = -rd[idx]; hlf = L1[None, :] + vdir; hlf /= np.linalg.norm(hlf, axis=1, keepdims=True)
spec = np.clip((n * hlf).sum(1), 0, 1) ** 40 * sh
fres = (1 - np.clip((n * vdir).sum(1), 0, 1)) ** 3
c = alb * (dif1[:, None] * np.array([1.0, 0.90, 0.80], f32) * 1.15 + dif2[:, None] * np.array([0.30, 0.95, 0.85], f32) * 1.0
           + ao[:, None] * np.array([0.34, 0.26, 0.62], f32) * 0.30)
c += spec[:, None] * 0.30 + fres[:, None] * np.array([0.5, 0.95, 0.9], f32) * 0.30 * (mat != 2)[:, None]
# Rissflächen glühen; Glut strahlt auf nahe Flächen
glow_near = np.exp(-np.abs(crack(q)) / 0.09)[:, None] * (mat != 2)[:, None]
c += glow_near * np.array([1.0, 0.40, 0.22], f32) * 0.40
em = np.zeros((len(p), 3), f32); em[cut] = np.array([1.0, 0.30, 0.14], f32) * 2.4
c = np.where(cut[:, None], em + np.array([1.0, 0.75, 0.35], f32) * 0.5, c)
# Boden blendet in den Hintergrund
c = np.where((mat == 2)[:, None], c * (1 - fog) + bgc[idx] * fog, c)
col[idx] = c; emis[idx] = em

img = col.reshape(N, N, 3); E = emis.reshape(N, N, 3)
def blur(a, r):
    im = Image.fromarray((np.clip(a / 4, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, f32) / 255 * 4
img = img + blur(E, N / 60) * 0.55 + blur(E, N / 16) * 0.30 + blur(np.clip(img - 1.0, 0, 4), N / 60) * 0.3
rng = np.random.default_rng(2)                       # schwebender Staub im Gegenlicht
for _ in range(140):
    x, y = rng.uniform(0, N, 2); r = rng.uniform(1.2, 3.5) * N / 1600; a = rng.uniform(0.05, 0.22)
    x0, x1, y0, y1 = int(max(0, x - 3 * r)), int(min(N, x + 3 * r + 1)), int(max(0, y - 3 * r)), int(min(N, y + 3 * r + 1))
    yy, xx = np.mgrid[y0:y1, x0:x1]
    img[y0:y1, x0:x1] += (np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r)) * a)[..., None] * np.array([1.0, 0.95, 0.85], f32)
img = 1 - np.exp(-img * 1.05)                          # Tonemapping
img = np.clip(img, 0, 1) ** (1 / 2.0)
img = img * img * (3 - 2 * img) * 0.6 + img * 0.4          # mehr Kontrast
m_ = img.mean(-1, keepdims=True); img = np.clip(m_ + (img - m_) * 1.25, 0, 1)   # Sättigung
out = Image.fromarray((img * 255).astype(np.uint8))
os.makedirs(os.path.join(ROOT, "brand"), exist_ok=True)
for s in (1024, 800):
    out.resize((s, s), Image.LANCZOS).save(os.path.join(ROOT, "brand", f"logo3d_{s}x{s}.png"), optimize=True)
print("ok")
