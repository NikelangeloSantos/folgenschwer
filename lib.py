"""Gemeinsame Bausteine für FOLGENSCHWER-Videos (Texturen, Hintergründe, Überschriften)."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kr
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, mix, WHITE, ORANGE, AMBER, CYAN, RED, INK

# ---------- Texturen (lazy, einmal pro Prozess) ----------
@lru_cache(None)
def earth_tex():
    w, h = 1024, 512
    n = kr.fnoise(w, h, 7, seed=3, base=3); m = kr.fnoise(w, h, 5, seed=8, base=4)
    lat = np.linspace(90, -90, h)[:, None]
    land = n > 0.53
    ocean = np.stack([0.02 + 0.06 * n, 0.10 + 0.22 * n, 0.25 + 0.35 * n], -1)
    green = np.array([0.13, 0.36, 0.14]); brown = np.array([0.55, 0.45, 0.26]); dry = np.abs(lat) < 28
    lc = green * (1 - m[..., None]) + brown * m[..., None]
    lc = np.where((dry & (m > 0.45))[..., None], np.array([0.72, 0.58, 0.36]), lc)
    tex = np.where(land[..., None], lc * (0.75 + 0.5 * (n[..., None] - 0.53)), ocean)
    ice = (np.abs(lat) > 68 + 6 * m)
    tex = np.where(ice[..., None], np.array([0.92, 0.95, 1.0]), tex)
    c = kr.fnoise(w, h, 7, seed=21, base=8, persist=0.55)
    clouds = (ss(0.52, 0.78, c) * 0.92).astype(np.float32)
    rng = np.random.default_rng(4)
    night = ((rng.random((h, w)) < 0.012) & land & ~ice).astype(np.float32) * rng.random((h, w)).astype(np.float32) * 1.6
    night = np.asarray(Image.fromarray((night * 120).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 60 * 0.6
    return tex.astype(np.float32), clouds, night, land

@lru_cache(None)
def frozen_tex():
    tex, clouds, night, land = earth_tex()
    n = kr.fnoise(1024, 512, 6, seed=70, base=6)
    ice = np.stack([0.80 + 0.15 * n, 0.88 + 0.1 * n, 0.98 + 0.02 * n], -1).astype(np.float32)
    return ice

@lru_cache(None)
def moon_tex():
    w, h = 768, 384
    n = kr.fnoise(w, h, 7, seed=31, base=4); mare = kr.fnoise(w, h, 4, seed=33, base=3)
    g = 0.58 + 0.22 * (n - 0.5) - 0.2 * ss(0.5, 0.65, mare)
    im = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8), "L"); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    for _ in range(260):
        x, y = rng.uniform(0, w), rng.uniform(30, h - 30); r = rng.uniform(2, 14) ** 1.15
        d.ellipse([x - r, y - r, x + r, y + r], outline=int(185 + 40 * rng.random()), width=max(1, int(r / 5)))
        d.ellipse([x - r * 0.8, y - r * 0.8 + r * 0.15, x + r * 0.8, y + r * 0.8 + r * 0.15], fill=int(95 + 40 * rng.random()))
    t = np.asarray(im.filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255
    return np.stack([t, t * 0.98, t * 0.95], -1).astype(np.float32)

@lru_cache(None)
def sun_tex():
    n = kr.fnoise(768, 384, 7, seed=90, base=8, persist=0.6)
    return np.stack([0.95 + 0.1 * n, 0.45 + 0.4 * n, 0.08 + 0.2 * n], -1).astype(np.float32)

@lru_cache(None)
def _stars():
    return kr.starfield(W + 300, H + 300, 1700, seed=2), kr.starfield(W + 300, H + 300, 600, seed=9, big=12)

def stars(dx=0.0, dy=0.0, k=1.0):
    A, B = _stars()
    a = A[int(150 + dy) % 300:int(150 + dy) % 300 + H, int(150 + dx) % 300:int(150 + dx) % 300 + W]
    b = B[int(150 + dy * 0.4) % 300:int(150 + dy * 0.4) % 300 + H, int(150 + dx * 0.4) % 300:int(150 + dx * 0.4) % 300 + W]
    return (a * 0.8 + b * 0.6) * k

def space_bg(t, dx=0, dy=0, tint=(60, 40, 120)):
    bg = kr.vgrad((4, 6, 16), (10, 8, 26), gamma=1.2)
    bg += kr.radial(820, 520, 520, tint, 0.35) + kr.radial(200, 1500, 600, (20, 60, 110), 0.3)
    bg += stars(dx + t * 6, dy + t * 2)
    return bg

def earth(R, spin=0.0, tilt=-23, light=(-0.7, -0.35, 0.62), clouds=True, frozen=0.0, cspin=0.0, night=True):
    tex, cl, ni, land = earth_tex()
    if frozen > 0: tex = tex * (1 - frozen) + frozen_tex() * frozen
    return kr.sphere(R, tex, spin=spin, tilt=tilt, light=light, night=ni * (1 - frozen) if night else None,
                     clouds=cl * (1 - 0.5 * frozen) if clouds else None, cspin=cspin)

# ---------- Text ----------
def fit_font(text, size, maxw=900, weight="Black"):
    f = F(weight, size)
    w = f.getlength(text)
    return F(weight, size * min(1.0, maxw / w)) if w > maxw else f

def heads(img, rel, kicker, big, glow=CYAN, sub=None, size=104, t0=0.45, big_col=WHITE, sub_t=1.1, y=(440, 548, 645)):
    """Kicker (Tracking, Cyan) + große Kernaussage mit Pop + optionale Unterzeile."""
    text_fx(img, (500, y[0]), kicker, F("Black", 46), fill=CYAN, tracking=6, alpha=clamp(rel / 0.3))
    if big and rel > t0:
        p = bo((rel - t0) / 0.4); f = fit_font(big, size * (0.7 + 0.3 * p), 900 * (0.7 + 0.3 * p))
        text_fx(img, (500, y[1]), big, f, fill=big_col, glow=glow, glow_r=20, alpha=clamp((rel - t0) / 0.2))
    if sub: text_fx(img, (500, y[2]), sub, fit_font(sub, 31, 900, "SemiBold"), fill=(215, 220, 235), alpha=clamp((rel - sub_t) / 0.4))

def hook_text(img, rel, ln, l1, l2, l3="", kick="WAS WÄRE, WENN"):
    a = 1.0 if rel < ln - 0.3 else clamp((ln - rel) / 0.3)
    text_fx(img, (510, 452), kick, F("Black", 52), fill=CYAN, tracking=8, alpha=a)
    text_fx(img, (510, 555), l1, fit_font(l1, 112, 920), fill=WHITE, alpha=a)
    if l3:
        text_fx(img, (510, 665), l2, fit_font(l2, 112, 920), fill=WHITE, alpha=a)
        text_fx(img, (510, 775), l3, fit_font(l3, 100, 920), fill=ORANGE, glow=ORANGE, glow_r=22, alpha=a)
    else:
        text_fx(img, (510, 670), l2, fit_font(l2, 100, 920), fill=ORANGE, glow=ORANGE, glow_r=22, alpha=a)

def outro(img, rel, q1, q2, emoji="💬"):
    a = clamp(rel / 0.3); d = ImageDraw.Draw(img, "RGBA")
    cx, y = 500, 470
    for k, x in enumerate((cx - 70, cx, cx + 70)):
        if k % 2 == 0: d.rounded_rectangle([x - 46, y - 24, x + 46, y + 24], 24, outline=ORANGE + (int(255 * a),), width=10)
        else: d.rounded_rectangle([x - 16, y - 40, x + 16, y + 40], 16, outline=(255, 255, 255, int(255 * a)), width=10)
    text_fx(img, (500, 580), "FOLGENSCHWER", F("Black", 84), fill=WHITE, alpha=a, tracking=2)
    text_fx(img, (500, 760), q1, fit_font(q1, 64, 900), fill=WHITE, alpha=clamp((rel - 0.3) / 0.3))
    text_fx(img, (500, 845), q2, fit_font(q2, 80, 900), fill=ORANGE, glow=ORANGE, glow_r=18, alpha=clamp((rel - 0.5) / 0.3))
    if rel > 0.8:
        e = kr.emoji(emoji, 110); img.paste(e, (int(500 - e.width / 2), 940), e)

def paste_emoji(img, ch, size, cx, cy, alpha=1.0, angle=0):
    e = kr.emoji(ch, int(size))
    if angle: e = e.rotate(angle, expand=True, resample=Image.BICUBIC)
    if alpha < 1: e.putalpha(e.getchannel("A").point(lambda v: int(v * alpha)))
    img.paste(e, (int(cx - e.width / 2), int(cy - e.height / 2)), e)

def cross(d, cx, cy, r, a=1.0, w=10):
    d.line([cx - r, cy - r, cx + r, cy + r], fill=RED + (int(255 * a),), width=w)
    d.line([cx - r, cy + r, cx + r, cy - r], fill=RED + (int(255 * a),), width=w)

# ---------- Hilfen für Hintergründe ----------
def ridge(seed, w=W):
    return kr.fnoise(w, 4, 6, seed=seed, base=3, persist=0.55)[1]

def fill_below(bg, ycurve, col, ymax=H):
    yy = np.arange(H)[:, None]
    m = (yy > ycurve[None, :]) & (yy < ymax)
    bg[m] = np.array(col, np.float32) if max(col) <= 2 else np.array(col, np.float32) / 255
    return m

def ring(bg, cx, cy, r, width, col, k=1.0):
    yy, xx = np.ogrid[0:H, 0:W]; d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    bg += (np.exp(-((d - r) / width) ** 2) * k)[..., None] * (np.array(col, np.float32) / 255)
