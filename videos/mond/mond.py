"""FOLGENSCHWER #1 – Was wäre, wenn der Mond verschwindet?

Vorschau (0 Credits):  python3 mond.py out/mond.mp4 --preview 0 2 6 12 ...
Stumm rendern:         python3 mond.py out/mond.mp4
Mit Stimme:            KR_VOICE=1 python3 mond.py out/mond.mp4   (holt nur fehlende Abschnitte, Rest aus voice_cache/)
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kr
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, mix, WHITE, ORANGE, AMBER, CYAN, RED, INK

MAX_LEN = 44.0
VOICE_ID = "TUKJhQmz3RPYBNAgC5A1"   # #01 wurde noch mit der ZahlenBlitz-Stimme vertont
# Akkorde (Hz): düster-filmisch in d-Moll
CHORDS = [(146.8, 174.6, 220.0), (116.5, 174.6, 233.1), (130.8, 196.0, 261.6), (110.0, 164.8, 220.0)]
SOURCES = "Quellen: NASA · Laskar et al. 1993 (Nature) · Harrison et al. 1984 (Science)"

SEGS = [
    dict(key="hook", scene="hook", say="Der Mond ist weg. Einfach so. Was passiert jetzt?", min=3.6, stamp="0 SEK.", nosub=True, flash0=0.0, shake=1.0),
    dict(key="nacht", scene="nacht", say="Sekunde eins: Die Nächte werden bis zu hundertmal dunkler.", min=4.2, stamp="1 SEKUNDE", node=True),
    dict(key="flut", scene="flut", say="Nach sechs Stunden: Die Flut bleibt fast aus. Ebbe und Flut schrumpfen um mehr als die Hälfte.", min=5.0, stamp="6 STUNDEN", node=True),
    dict(key="koralle", scene="koralle", say="Nach einem Monat: Korallen warten vergeblich. Viele laichen nur nach dem Vollmond.", min=4.8, stamp="1 MONAT", node=True),
    dict(key="achse", scene="achse", say="Nach Millionen Jahren: Die Erdachse gerät ins Taumeln. Jahreszeiten könnten extrem werden.", min=5.0, stamp="MIO. JAHRE", node=True),
    dict(key="twist", scene="twist", say="Und das Krasse: Der Mond haut wirklich ab. Drei Komma acht Zentimeter. Jedes Jahr.", min=5.2, stamp="HEUTE", node=True, twist=True, shake=0.7),
    dict(key="outro", scene="outro", say="Was soll als Nächstes verschwinden? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

# ---------- Assets (einmal pro Prozess) ----------
def _earth_tex():
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
    night = np.asarray(Image.fromarray((night * 120).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 60
    return tex.astype(np.float32), clouds, night * 0.6

def _moon_tex():
    w, h = 768, 384
    n = kr.fnoise(w, h, 7, seed=31, base=4); mare = kr.fnoise(w, h, 4, seed=33, base=3)
    g = 0.58 + 0.22 * (n - 0.5) - 0.2 * ss(0.5, 0.65, mare)
    im = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8), "L"); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    for _ in range(260):
        x, y = rng.uniform(0, w), rng.uniform(30, h - 30); r = rng.uniform(2, 14) ** 1.15
        d.ellipse([x - r, y - r, x + r, y + r], outline=int(185 + 40 * rng.random()), width=max(1, int(r / 5)))
        d.ellipse([x - r * 0.8, y - r * 0.8 + r * 0.15, x + r * 0.8, y + r * 0.8 + r * 0.15], fill=int(95 + 40 * rng.random()))
    im = im.filter(ImageFilter.GaussianBlur(0.7))
    t = np.asarray(im, np.float32) / 255
    return np.stack([t * 1.0, t * 0.98, t * 0.95], -1).astype(np.float32)

EARTH, CLOUDS, NIGHT = _earth_tex()
MOON = _moon_tex()
SANDN = (0.38 + 0.18 * kr.fnoise(W, H, 6, seed=44, base=16)).astype(np.float32)
RIDGES = {k: kr.fnoise(W, 4, 6, seed=40 + k, base=3, persist=0.55)[1] for k in (1, 2)}
STARS = kr.starfield(W + 300, H + 300, 1700, seed=2)
STARS2 = kr.starfield(W + 300, H + 300, 600, seed=9, big=12)

def stars(dx=0.0, dy=0.0, k=1.0):
    a = STARS[int(150 + dy) % 300:int(150 + dy) % 300 + H, int(150 + dx) % 300:int(150 + dx) % 300 + W]
    b = STARS2[int(150 + dy * 0.4) % 300:int(150 + dy * 0.4) % 300 + H, int(150 + dx * 0.4) % 300:int(150 + dx * 0.4) % 300 + W]
    return (a * 0.8 + b * 0.6) * k

def space_bg(t, dx=0, dy=0):
    bg = kr.vgrad((4, 6, 16), (10, 8, 26), gamma=1.2)
    bg += kr.radial(820, 520, 520, (60, 40, 120), 0.35) + kr.radial(200, 1500, 600, (20, 60, 110), 0.3)
    bg += stars(dx + t * 6, dy + t * 2)
    return bg

# Partikel für das Zerbröseln des Mondes
_rng = np.random.default_rng(12)
NP = 2600
P_ang = _rng.uniform(0, 2 * math.pi, NP); P_rad = np.sqrt(_rng.random(NP))
P_vel = _rng.uniform(80, 520, NP) * (0.4 + P_rad); P_dir = P_ang + _rng.normal(0, 0.6, NP)
P_col = np.clip(np.stack([np.full(NP, 1.0), _rng.uniform(0.55, 0.95, NP), _rng.uniform(0.3, 0.8, NP)], -1) * _rng.uniform(0.4, 1.4, NP)[:, None], 0, 2)

# ---------- Szenen (liefern float-Bild HxWx3) ----------
def sc_hook(rel, ln, i):
    cam = 1.0 + 0.04 * rel
    bg = space_bg(rel)
    # Erde unten links, groß angeschnitten
    er, ea, _ = kr.sphere(330 * cam, EARTH, spin=1.2 + rel * 0.08, tilt=-18, night=NIGHT, clouds=CLOUDS, cspin=rel * 0.03, light=(0.8, -0.45, 0.4))
    kr.blit(bg, er, ea, 330, 1230)
    # Mond: zerfällt ab 0,15 s
    mx, my, mr = 760, 900, 130 * cam
    k = clamp((rel - 0.3) / 0.5)
    if k < 1:
        mrgb, ma, _ = kr.sphere(mr, MOON, spin=0.3, light=(0.8, -0.45, 0.4), atm=None)
        crack = kr.radial(mx, my, mr * 1.25, (255, 120, 40), 0.25 + 1.1 * eo((rel - 0.1) / 0.25))
        kr.blit(bg, mrgb * (1 - k), ma * (1 - k), mx, my); bg += crack * (1 - k)
    if rel > 0.3:
        tt = rel - 0.3
        x = mx + np.cos(P_ang) * P_rad * mr + np.cos(P_dir) * P_vel * (1 - np.exp(-tt * 1.4)) * 1.2
        y = my + np.sin(P_ang) * P_rad * mr + np.sin(P_dir) * P_vel * (1 - np.exp(-tt * 1.4)) * 1.2
        fade = max(0.0, 1 - tt / 3.2)
        kr.splat(bg, x, y, P_col * 0.9 * fade, 2)
        # Schockwelle
        rr = 140 + tt * 900
        if tt < 0.9:
            yy, xx = np.ogrid[0:H, 0:W]; d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
            bg += (np.exp(-((d - rr) / 18) ** 2) * (1 - tt / 0.9) * 0.9)[..., None] * np.array([1.0, 0.6, 0.3], np.float32)
        bg += kr.radial(mx, my, 260, (255, 170, 90), 2.2 * math.exp(-tt * 5))
    return bg

def ov_hook(img, rel, ln, i):
    a = 1.0 if rel < ln - 0.3 else clamp((ln - rel) / 0.3)
    text_fx(img, (510, 452), "WAS WÄRE, WENN", F("Black", 52), fill=CYAN, tracking=8, alpha=a)
    text_fx(img, (510, 552), "DER MOND", F("Black", 120), fill=WHITE, alpha=a)
    text_fx(img, (510, 670), "VERSCHWINDET?", F("Black", 90), fill=ORANGE, glow=ORANGE, glow_r=22, alpha=a)

def sc_nacht(rel, ln, i):
    dark = eio((rel - 0.15) / 1.3)        # Mondlicht weg
    sky = kr.vgrad(mix((26, 44, 86), (2, 3, 9), dark), mix((70, 96, 140), (6, 8, 20), dark), gamma=0.9)
    sky += stars(rel * 4, 0, 0.35 + 0.9 * dark)
    sky += kr.radial(780, 640, 300, (150, 180, 230), 0.7 * (1 - dark))
    # Berge: fraktale Silhouetten, Kanten vom Mondlicht gesäumt
    yy = np.arange(H)[:, None]
    for seed, base, amp, col in ((1, 1120, 260, (14, 18, 34)), (2, 1215, 150, (5, 7, 14))):
        rg = base - amp * (RIDGES[seed] - 0.35)
        m = (yy > rg[None, :]) & (yy < 1300)
        sky[m] = np.array(col, np.float32) / 255 * (1 + 1.4 * (1 - dark))
        rim = (yy - rg[None, :] >= 0) & (yy - rg[None, :] < 3) & (yy < 1300)
        sky[rim] += np.array([0.55, 0.65, 0.85], np.float32) * (1 - dark) * 0.7
    # See mit Spiegelung
    top = 1300
    refl = sky[top - (np.arange(H - top)) // 1 - 1][:, :, :] * 0.45
    ripple = (np.sin(np.arange(H - top)[:, None] * 0.35 + rel * 3) * 4).astype(np.int32)
    xi = np.clip(np.arange(W)[None, :] + ripple, 0, W - 1)
    sky[top:] = refl[np.arange(H - top)[:, None], xi] + np.array([0.01, 0.02, 0.05], np.float32)
    # Geister-Umriss, wo der Mond war
    return sky

def ov_nacht(img, rel, ln, i):
    d = ImageDraw.Draw(img, "RGBA"); dark = eio((rel - 0.15) / 1.3)
    a = int(160 * dark)
    for k in range(0, 360, 12):
        a0 = math.radians(k); a1 = math.radians(k + 6)
        d.arc([780 - 85, 640 - 85, 780 + 85, 640 + 85], k, k + 6, fill=(255, 255, 255, a), width=3)
    text_fx(img, (780, 760), "HIER WAR DER MOND", F("Bold", 24), fill=(220, 225, 240), tracking=3, alpha=dark * 0.85)
    p = bo((rel - 0.5) / 0.4)
    text_fx(img, (500, 440), "DIE NÄCHTE", F("Black", 46), fill=CYAN, tracking=6, alpha=clamp(rel / 0.3))
    if rel > 0.5:
        text_fx(img, (500, 545), "100× DUNKLER", F("Black", 110 * (0.7 + 0.3 * p)), fill=WHITE, glow=CYAN, glow_r=20, alpha=clamp((rel - 0.5) / 0.2))
    # Lux-Anzeige
    lux = math.exp(math.log(0.2) * (1 - dark) + math.log(0.002) * dark)
    text_fx(img, (500, 1222), f"{kr.de(lux, 3)} LUX", F("Black", 40), fill=AMBER, alpha=clamp(rel / 0.4))
    text_fx(img, (500, 1268), "Vollmond ≈ 0,2 Lux · Sternenlicht ≈ 0,002 Lux", F("Medium", 24), fill=(210, 215, 230), alpha=clamp(rel / 0.4) * 0.9)

def sc_flut(rel, ln, i):
    bg = kr.vgrad((3, 5, 14), (12, 18, 40)); bg += stars(rel * 3, 0, 0.8)
    A = 120 - 70 * eio((rel - 0.9) / 1.6)       # Amplitude schrumpft
    lvl = 1010 - A * math.sin(rel * 2 * math.pi / 2.6 + 1.2)
    xs = np.arange(W, dtype=np.float32)
    surf = lvl + 7 * np.sin(xs * 0.021 + rel * 3.1) + 4 * np.sin(xs * 0.047 - rel * 4.3)
    beach = 1420 - (xs - 380) * 0.78; beach = np.where(xs < 380, 2000, beach)
    yy = np.arange(H, dtype=np.float32)[:, None]
    water = (yy > surf[None, :]) & (yy < beach[None, :])
    depth = np.clip((yy - surf[None, :]) / 600, 0, 1)
    wc = np.stack([0.02 + 0.05 * (1 - depth), 0.10 + 0.25 * (1 - depth), 0.22 + 0.35 * (1 - depth)], -1)
    bg = np.where(water[..., None], wc, bg)
    foam = (np.abs(yy - surf[None, :]) < 3) & (yy < beach[None, :])
    bg[foam] = np.array([0.75, 0.9, 1.0], np.float32)
    sand = yy >= beach[None, :]
    sc = kr.vgrad((120, 100, 70), (40, 32, 22))
    bg = np.where(sand[..., None], sc * SANDN[..., None], bg)
    bg[np.abs(yy - beach[None, :]) < 2.5] = np.array([0.55, 0.45, 0.3], np.float32)
    return bg.astype(np.float32)

def ov_flut(img, rel, ln, i):
    d = ImageDraw.Draw(img, "RGBA")
    # Pegel
    px = 640; d.rectangle([px - 7, 760, px + 7, 1260], fill=(230, 230, 240, 230))
    for k in range(11):
        y = 780 + k * 46; d.line([px + 7, y, px + 30, y], fill=(230, 230, 240, 220), width=3)
    old = 1010 - 120
    for x in range(140, 900, 34): d.line([x, old, x + 18, old], fill=ORANGE + (230,), width=4)
    text_fx(img, (150, old - 30), "FLUT FRÜHER", F("Black", 30), fill=ORANGE, anchor="lm", tracking=2)
    A = 120 - 70 * eio((rel - 0.9) / 1.6); new = 1010 - A
    if rel > 0.9:
        for x in range(140, 900, 34): d.line([x, new, x + 18, new], fill=CYAN + (230,), width=4)
        text_fx(img, (150, new + 32), "OHNE MOND", F("Black", 30), fill=CYAN, anchor="lm", tracking=2, alpha=clamp((rel - 0.9) / 0.4))
    text_fx(img, (500, 440), "EBBE & FLUT", F("Black", 46), fill=CYAN, tracking=6, alpha=clamp(rel / 0.3))
    if rel > 0.6:
        p = bo((rel - 0.6) / 0.4)
        text_fx(img, (500, 545), "MEHR ALS HALBIERT", F("Black", 88 * (0.7 + 0.3 * p)), fill=WHITE, glow=ORANGE, glow_r=18, alpha=clamp((rel - 0.6) / 0.2))
    text_fx(img, (500, 640), "nur die Sonne zieht noch am Meer", F("SemiBold", 30), fill=(215, 220, 235), alpha=clamp((rel - 1.2) / 0.4))

def _coral_layer():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); rng = np.random.default_rng(5)
    def branch(x, y, ang, ln, wdt, col, depth):
        if depth == 0 or ln < 8: return
        x2 = x + math.cos(ang) * ln; y2 = y + math.sin(ang) * ln
        d.line([x, y, x2, y2], fill=col, width=int(wdt)); d.ellipse([x2 - wdt / 2, y2 - wdt / 2, x2 + wdt / 2, y2 + wdt / 2], fill=col)
        for s in (-1, 1):
            branch(x2, y2, ang + s * rng.uniform(0.25, 0.6), ln * rng.uniform(0.68, 0.82), wdt * 0.72, col, depth - 1)
    cols = [(255, 120, 140, 255), (255, 170, 90, 255), (190, 110, 255, 255), (90, 210, 200, 255)]
    for k in range(9):
        x = 60 + k * 120 + rng.uniform(-30, 30); y = 1380 + rng.uniform(-30, 40)
        branch(x, y, -math.pi / 2 + rng.uniform(-0.3, 0.3), rng.uniform(70, 120), rng.uniform(14, 22), cols[k % 4], 6)
    a = np.asarray(im, np.float32) / 255
    return a[..., :3] * a[..., 3:], a[..., 3]
CORAL = None
def sc_koralle(rel, ln, i):
    global CORAL
    if CORAL is None: CORAL = _coral_layer()
    bg = kr.vgrad((10, 60, 110), (2, 8, 22), gamma=0.8)
    xs = np.arange(W, dtype=np.float32)[None, :]; yy = np.arange(H, dtype=np.float32)[:, None]
    rays = sum(np.exp(-((xs - (cx + (yy - 400) * sl) - 30 * math.sin(rel * 0.8 + cx)) / wd) ** 2) for cx, sl, wd in ((260, 0.25, 40), (520, 0.1, 60), (760, -0.15, 35), (900, -0.3, 50)))
    bg += (rays * np.exp(-(yy - 400) / 900) * 0.10)[..., None] * np.array([0.5, 0.9, 1.0], np.float32)
    crgb, ca = CORAL
    sh = 0.35 + 0.15 * math.sin(rel * 2)
    bg = bg * (1 - ca[..., None]) + crgb * sh
    # Plankton-Drift + "wartende" Laichpakete (glühen, steigen aber nicht auf)
    r = np.random.default_rng(3); n = 220
    px = (r.uniform(0, W, n) + rel * r.uniform(-20, 20, n)) % W; py = (r.uniform(500, 1500, n) - rel * r.uniform(5, 30, n))
    kr.splat(bg, px, py, np.array([0.25, 0.45, 0.5]) * r.uniform(0.3, 1, n)[:, None], 2)
    r2 = np.random.default_rng(8); m = 90
    ex = r2.uniform(80, 1000, m); ey = r2.uniform(1180, 1380, m) + np.sin(rel * 2 + r2.uniform(0, 6, m)) * 4
    pulse = 0.5 + 0.5 * np.sin(rel * 4 + r2.uniform(0, 6, m))
    kr.splat(bg, ex, ey, np.array([1.0, 0.5, 0.6]) * pulse[:, None] * 0.9, 3)
    return bg

def ov_koralle(img, rel, ln, i):
    d = ImageDraw.Draw(img, "RGBA")
    # Mondphasen-Kalender: alle leer, Vollmond fehlt
    n = 7; cx0 = 500 - 3 * 108; y = 820
    for k in range(n):
        x = cx0 + k * 108; a = clamp((rel - 0.2 - k * 0.07) / 0.25)
        if a <= 0: continue
        for s in range(0, 360, 20): d.arc([x - 36, y - 36, x + 36, y + 36], s, s + 10, fill=(255, 255, 255, int(150 * a)), width=3)
        if k == 3:
            d.ellipse([x - 44, y - 44, x + 44, y + 44], outline=RED + (int(255 * a),), width=5)
            d.line([x - 26, y - 26, x + 26, y + 26], fill=RED + (int(255 * a),), width=6); d.line([x - 26, y + 26, x + 26, y - 26], fill=RED + (int(255 * a),), width=6)
    text_fx(img, (500, 900), "VOLLMOND-SIGNAL FEHLT", F("Black", 30), fill=RED, tracking=3, alpha=clamp((rel - 0.7) / 0.3))
    text_fx(img, (500, 440), "KORALLEN", F("Black", 46), fill=CYAN, tracking=6, alpha=clamp(rel / 0.3))
    if rel > 0.5:
        p = bo((rel - 0.5) / 0.4)
        text_fx(img, (500, 545), "WARTEN VERGEBLICH", F("Black", 86 * (0.7 + 0.3 * p)), fill=WHITE, glow=(255, 110, 150), glow_r=18, alpha=clamp((rel - 0.5) / 0.2))

def sc_achse(rel, ln, i):
    bg = space_bg(rel * 0.5)
    bg += kr.radial(-220, 1000, 560, (255, 190, 110), 1.1) + kr.radial(-220, 1000, 220, (255, 240, 200), 1.8)
    er, ea, _ = kr.sphere(290, EARTH, spin=rel * 0.9, tilt=tilt_at(rel), night=NIGHT, clouds=CLOUDS, cspin=rel * 0.2, light=(-0.95, 0.0, 0.3))
    kr.blit(bg, er, ea, 540, 1000)
    return bg

def tilt_at(rel):
    k = eio((rel - 0.7) / 1.0)
    return 23.4 + k * (42 * math.sin((rel - 0.7) * 2.1) + 18 * (1 - math.cos((rel - 0.7) * 1.3)))

def ov_achse(img, rel, ln, i):
    d = ImageDraw.Draw(img, "RGBA"); tl_ = tilt_at(rel); a = math.radians(tl_)
    cx, cy, L = 540, 1000, 360
    dx, dy = math.sin(a) * L, -math.cos(a) * L
    for w, al in ((16, 50), (8, 110), (4, 255)):
        d.line([cx - dx, cy - dy, cx + dx, cy + dy], fill=CYAN + (al,), width=w)
    d.line([cx, cy - L - 10, cx, cy - L + 60], fill=(255, 255, 255, 120), width=3)
    d.arc([cx - 150, cy - 150, cx + 150, cy + 150], -90 - abs(tl_) if tl_ > 0 else -90, -90 if tl_ > 0 else -90 - tl_, fill=AMBER + (230,), width=6)
    text_fx(img, (885, 760), f"{abs(tl_):.0f}°", F("Black", 64), fill=AMBER, glow=AMBER, glow_r=14)
    text_fx(img, (500, 440), "DIE ERDACHSE", F("Black", 46), fill=CYAN, tracking=6, alpha=clamp(rel / 0.3))
    if rel > 0.5:
        p = bo((rel - 0.5) / 0.4)
        text_fx(img, (500, 545), "TAUMELT 0–85°", F("Black", 100 * (0.7 + 0.3 * p)), fill=WHITE, glow=CYAN, glow_r=18, alpha=clamp((rel - 0.5) / 0.2))
    text_fx(img, (500, 640), "laut Simulationen · heute stabil bei ≈ 23,4°", F("SemiBold", 30), fill=(215, 220, 235), alpha=clamp((rel - 0.9) / 0.4))

def sc_twist(rel, ln, i):
    bg = space_bg(rel)
    er, ea, _ = kr.sphere(170, EARTH, spin=2.5 + rel * 0.4, tilt=-23, night=NIGHT, clouds=CLOUDS, cspin=rel * 0.05, light=(0.3, -0.5, 0.8))
    kr.blit(bg, er, ea, 220, 960)
    mx = 800 + 70 * eo(rel / 4)
    mr, ma, _ = kr.sphere(56, MOON, spin=0.3, light=(0.3, -0.5, 0.8), atm=None)
    kr.blit(bg, mr, ma, mx, 960)
    # Laser-Messstrahl
    k = (rel * 1.4) % 1.0
    yy, xx = np.ogrid[0:H, 0:W]
    beam = np.exp(-((yy - 960) / 2.5) ** 2) * ((xx > 390) & (xx < mx - 56)) * 0.6
    bg += beam[..., None] * np.array([0.3, 1.0, 0.45], np.float32)
    px = 390 + (mx - 56 - 390) * k
    bg += kr.radial(px, 960, 22, (120, 255, 150), 1.5)
    return bg

def ov_twist(img, rel, ln, i):
    d = ImageDraw.Draw(img, "RGBA")
    mx = 800 + 70 * eo(rel / 4)
    y = 1100
    d.line([220, y, mx, y], fill=(255, 255, 255, 160), width=3)
    for x in (220, mx): d.line([x, y - 14, x, y + 14], fill=(255, 255, 255, 200), width=3)
    text_fx(img, ((220 + mx) / 2, y + 36), "384.400 km", F("Bold", 30), fill=WHITE)
    a = clamp((rel - 1.2) / 0.3)
    d.line([800, y - 40, mx, y - 40], fill=ORANGE + (int(255 * a),), width=6)
    text_fx(img, (500, 440), "UND DAS KRASSE:", F("Black", 46), fill=CYAN, tracking=6, alpha=clamp(rel / 0.3))
    if rel > 0.4:
        p = bo((rel - 0.4) / 0.4)
        text_fx(img, (500, 545), "ER HAUT AB", F("Black", 120 * (0.7 + 0.3 * p)), fill=WHITE, glow=ORANGE, glow_r=22, alpha=clamp((rel - 0.4) / 0.2))
    if rel > 1.4:
        p = bo((rel - 1.4) / 0.4)
        text_fx(img, (500, 690), "+3,8 CM / JAHR", F("Black", 84 * (0.7 + 0.3 * p)), fill=ORANGE, glow=ORANGE, glow_r=16, alpha=clamp((rel - 1.4) / 0.2))
    text_fx(img, (500, 1235), "gemessen per Laser – Apollo-Spiegel auf dem Mond", F("SemiBold", 28), fill=(160, 255, 180), alpha=clamp((rel - 0.8) / 0.4))

def sc_outro(rel, ln, i):
    bg = space_bg(rel + 20)
    er, ea, _ = kr.sphere(420, EARTH, spin=3.5 + rel * 0.06, tilt=-23, night=NIGHT, clouds=CLOUDS, cspin=rel * 0.02, light=(0.6, -0.6, 0.5))
    kr.blit(bg, er, ea, 540, 1750)
    return bg

def ov_outro(img, rel, ln, i):
    a = clamp(rel / 0.3)
    d = ImageDraw.Draw(img, "RGBA")
    # Logo: drei Kettenglieder
    cx, y = 500, 470
    for k, x in enumerate((cx - 70, cx, cx + 70)):
        if k % 2 == 0: d.rounded_rectangle([x - 46, y - 24, x + 46, y + 24], 24, outline=ORANGE + (int(255 * a),), width=10)
        else: d.rounded_rectangle([x - 16, y - 40, x + 16, y + 40], 16, outline=(255, 255, 255, int(255 * a)), width=10)
    text_fx(img, (500, 580), "FOLGENSCHWER", F("Black", 84), fill=WHITE, alpha=a, tracking=2)
    text_fx(img, (500, 760), "Was soll als Nächstes", F("Black", 64), fill=WHITE, alpha=clamp((rel - 0.3) / 0.3))
    text_fx(img, (500, 845), "verschwinden?", F("Black", 80), fill=ORANGE, glow=ORANGE, glow_r=18, alpha=clamp((rel - 0.5) / 0.3))
    if rel > 0.8:
        e = kr.emoji("💬", 110); img.paste(e, (int(500 - e.width / 2), 940), e)

SCENES = dict(hook=sc_hook, nacht=sc_nacht, flut=sc_flut, koralle=sc_koralle, achse=sc_achse, twist=sc_twist, outro=sc_outro)
OVERLAYS = dict(hook=ov_hook, nacht=ov_nacht, flut=ov_flut, koralle=ov_koralle, achse=ov_achse, twist=ov_twist, outro=ov_outro)

def overlay(img, rel, ln, i):
    OVERLAYS[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
