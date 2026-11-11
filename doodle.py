"""3D-Doodle-Bausteine für FOLGENSCHWER: dicke zitternde Konturen ("Line Boil" mit 12 fps),
extrudierte Formen mit dunkler Seitenfläche, Figuren mit Augen, 3D-Text, ständig bewegte Kamera.
Gezeichnet wird in doppelter Auflösung (Kantenglättung) und dann aufs Bild gelegt."""
import math
import numpy as np
from PIL import Image, ImageDraw
import kr
from kr import W, H, F

INK = (22, 16, 34)
SS = 2   # Supersampling

def boil(t, fps=12): return int(t * fps)
def dark(c, k=0.55): return tuple(int(v * k) for v in c[:3])
def light(c, k=0.45): return tuple(int(v + (255 - v) * k) for v in c[:3])

class Layer:
    def __init__(self, t, zoom=1.0, pan=(0, 0), rot=0.0, cx=540, cy=1000):
        self.im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
        self.t = t; self.z = zoom; self.pan = pan; self.rot = math.radians(rot); self.cx = cx; self.cy = cy
    # Kamera-Transformation (1x-Koordinaten) -> Supersampling-Koordinaten
    def p(self, x, y):
        x -= self.cx; y -= self.cy
        c, s = math.cos(self.rot), math.sin(self.rot)
        x, y = x * c - y * s, x * s + y * c
        return ((x * self.z + self.cx + self.pan[0]) * SS, (y * self.z + self.cy + self.pan[1]) * SS)
    def s(self, v): return v * self.z * SS
    def jit(self, pts, amp=2.2, seed=0):
        r = np.random.default_rng(seed * 7919 + boil(self.t))
        return [self.p(x + r.normal(0, amp), y + r.normal(0, amp)) for x, y in pts]
    def poly(self, pts, col, depth=(12, 12), seed=0, outline=7, hi=True):
        dx, dy = depth
        if dx or dy:   # Extrusion
            back = [(x + dx, y + dy) for x, y in pts]
            n = len(pts)
            for k in range(n):
                a, b = pts[k], pts[(k + 1) % n]
                q = self.jit([a, b, (b[0] + dx, b[1] + dy), (a[0] + dx, a[1] + dy)], seed=seed + k)
                self.d.polygon(q, fill=dark(col))
            self.d.polygon(self.jit(back, seed=seed + 99), fill=dark(col))
        fp = self.jit(pts, seed=seed)
        self.d.polygon(fp, fill=col[:3] + (255,))
        if outline > 0: self.d.line(fp + [fp[0]], fill=INK, width=max(1, int(self.s(outline))), joint="curve")
        if hi and len(pts) >= 2:
            a, b = pts[0], pts[1]
            self.d.line(self.jit([(a[0] + 10, a[1] + 10), (a[0] + (b[0] - a[0]) * 0.5, a[1] + (b[1] - a[1]) * 0.5 + 10)], 1.5, seed + 3), fill=light(col, 0.6) + (230,), width=int(self.s(5)))
    def box(self, x, y, w, h, col, depth=(14, 12), seed=0, outline=7):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], col, depth, seed, outline)
    def circ(self, cx, cy, r, col, depth=(8, 8), seed=0, outline=6, n=22):
        pts = [(cx + math.cos(k / n * 2 * math.pi) * r, cy + math.sin(k / n * 2 * math.pi) * r) for k in range(n)]
        if depth != (0, 0):
            q = self.jit([(x + depth[0], y + depth[1]) for x, y in pts], seed=seed + 50); self.d.polygon(q, fill=dark(col))
        fp = self.jit(pts, seed=seed); self.d.polygon(fp, fill=col[:3] + (255,))
        if outline > 0: self.d.line(fp + [fp[0]], fill=INK, width=max(1, int(self.s(outline))))
    def line(self, pts, col=INK, w=7, seed=0, amp=2.0):
        self.d.line(self.jit(pts, amp, seed), fill=col, width=int(self.s(w)), joint="curve")
    def text(self, x, y, txt, size, col, depth=10, anchor="mm", seed=0, stroke=7, weight="Black"):
        f = F(weight, max(8, size * self.z * SS)); px, py = self.p(x, y)
        r = np.random.default_rng(seed * 31 + boil(self.t)); jx, jy = r.normal(0, 1.2 * SS, 2)
        for k in range(int(depth), 0, -2):
            self.d.text((px + k * SS * 0.9 + jx, py + k * SS * 0.9 + jy), txt, font=f, fill=dark(col, 0.45), anchor=anchor, stroke_width=int(self.s(stroke)), stroke_fill=INK)
        self.d.text((px + jx, py + jy), txt, font=f, fill=col[:3], anchor=anchor, stroke_width=int(self.s(stroke)), stroke_fill=INK)
    def paste_to(self, img):
        small = self.im.resize((W, H), Image.LANCZOS)
        img.paste(small, (0, 0), small)

# ---------- Figuren & Objekte ----------
def bean(L, x, y, s, col, seed=0, walk=0.0, arms_up=0.0, look=(0, 0), carry=None):
    """Bohnen-Figur mit Augen; walk = Phase für Beine, s = Höhe."""
    t = L.t; leg = math.sin(walk * 2 * math.pi) * s * 0.12
    L.line([(x - s * 0.12, y - s * 0.15), (x - s * 0.12 + leg, y)], INK, s * 0.07, seed + 1)
    L.line([(x + s * 0.12, y - s * 0.15), (x + s * 0.12 - leg, y)], INK, s * 0.07, seed + 2)
    w = s * 0.5; top = y - s
    L.poly([(x - w / 2, top + s * 0.25), (x - w / 2 + s * 0.08, top), (x + w / 2 - s * 0.08, top), (x + w / 2, top + s * 0.25), (x + w / 2, y - s * 0.15), (x - w / 2, y - s * 0.15)], col, (s * 0.06, s * 0.05), seed, max(3, s * 0.045))
    ay = top + s * 0.45 - arms_up * s * 0.45
    L.line([(x - w / 2, top + s * 0.5), (x - w / 2 - s * 0.18, ay)], INK, s * 0.06, seed + 3)
    L.line([(x + w / 2, top + s * 0.5), (x + w / 2 + s * 0.18, ay)], INK, s * 0.06, seed + 4)
    for ex in (-0.1, 0.1):
        L.circ(x + ex * s, top + s * 0.25, s * 0.085, (255, 255, 255), (0, 0), seed + 5, max(2, s * 0.025), 12)
        L.circ(x + ex * s + look[0] * s * 0.03, top + s * 0.26 + look[1] * s * 0.03, s * 0.035, INK, (0, 0), seed + 6, 1, 10)
    if carry: carry(L, x, top - s * 0.05)

def car(L, x, y, s, col, seed=0, flip=False, spin=0.0):
    f = -1 if flip else 1
    L.box(x - s * 0.5, y - s * 0.32, s, s * 0.22, col, (s * 0.05, s * 0.04), seed, max(3, s * 0.03))
    L.poly([(x - s * 0.25 * f, y - s * 0.32), (x - s * 0.15 * f, y - s * 0.52), (x + s * 0.22 * f, y - s * 0.52), (x + s * 0.3 * f, y - s * 0.32)], light(col, 0.2), (0, 0), seed + 9, max(3, s * 0.03))
    for wx in (-0.3, 0.3):
        L.circ(x + wx * s, y - s * 0.1, s * 0.11, (40, 40, 50), (0, 0), seed + 11, max(3, s * 0.03), 14)
        a = spin; L.line([(x + wx * s - math.cos(a) * s * 0.08, y - s * 0.1 - math.sin(a) * s * 0.08), (x + wx * s + math.cos(a) * s * 0.08, y - s * 0.1 + math.sin(a) * s * 0.08)], (200, 200, 210), s * 0.025, seed + 12)

def flame(L, x, y, s, seed=0):
    t = L.t
    for k, (col, sc) in enumerate((((255, 90, 30), 1.0), ((255, 180, 40), 0.68), ((255, 240, 150), 0.38))):
        h = s * sc * (1 + 0.15 * math.sin(t * 14 + seed + k)); w = s * sc * 0.45
        tip = (x + 0.15 * s * math.sin(t * 9 + seed), y - h)
        pts = [(x - w, y), (x - w * 0.9, y - h * 0.45), tip, (x + w * 0.9, y - h * 0.45), (x + w, y), (x, y + w * 0.3)]
        L.poly(pts, col, (0, 0), seed + k * 5, max(2, s * 0.03) if k == 0 else 0, hi=False)

def bill(L, x, y, s, ang, seed=0):
    c, sn = math.cos(ang), math.sin(ang); hw, hh = s * 0.5, s * 0.26
    pts = [(x + dx * c - dy * sn, y + dx * sn + dy * c) for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
    L.poly(pts, (110, 210, 120), (s * 0.04, s * 0.04), seed, max(2, s * 0.04), hi=False)
    L.text(x, y, "€", s * 0.35, (40, 110, 50), 0, seed=seed, stroke=0)

def burst(L, x, y, r, col, seed=0, n=10):
    pts = []
    for k in range(n * 2):
        a = k / (n * 2) * 2 * math.pi; rr = r if k % 2 == 0 else r * 0.55
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    L.poly(pts, col, (8, 8), seed, 6, hi=False)

def scribbles(L, seed, col=(255, 255, 255), n=14, alpha=60, drift=(30, -20)):
    """Hintergrund-Gekritzel (Sterne, Kringel, Punkte), langsam driftend."""
    r = np.random.default_rng(seed); t = L.t
    for k in range(n):
        x = (r.uniform(0, W) + drift[0] * t) % W; y = (r.uniform(150, H - 300) + drift[1] * t) % H; s = r.uniform(14, 34); kind = k % 3
        c = col + (alpha,)
        if kind == 0:
            pts = [(x + math.cos(a / 5 * 2 * math.pi + t) * (s if a % 2 == 0 else s * 0.45), y + math.sin(a / 5 * 2 * math.pi + t) * (s if a % 2 == 0 else s * 0.45)) for a in range(10)]
            L.d.line(L.jit(pts + [pts[0]], 1.5, k), fill=c, width=int(L.s(4)))
        elif kind == 1:
            pts = [(x + math.cos(a * 0.5) * a * 1.4, y + math.sin(a * 0.5) * a * 1.4) for a in range(0, 26)]
            L.d.line(L.jit(pts, 1.0, k), fill=c, width=int(L.s(4)))
        else:
            px, py = L.p(x, y); L.d.ellipse([px - L.s(6), py - L.s(6), px + L.s(6), py + L.s(6)], fill=c)
