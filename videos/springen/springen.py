"""FOLGENSCHWER #08 – Was wäre, wenn alle Menschen gleichzeitig springen?"""
import math, os, sys
from functools import lru_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(130.8, 164.8, 196.0), (146.8, 185.0, 220.0), (123.5, 155.6, 185.0), (110.0, 138.6, 164.8)]
SOURCES = "Rechnung: 8,1 Mrd. Menschen · Ø 62 kg · 50 cm Sprung · 4 Personen pro m²"
GREEN = (120, 230, 140)

SEGS = [
    dict(scene="hook", say="Alle acht Milliarden Menschen springen gleichzeitig. Was passiert mit der Erde?", min=3.8, stamp="JETZT", nosub=True),
    dict(scene="treffen", say="Erst mal müssen alle an einen Ort. Dicht gedrängt passen wir alle aufs Saarland.", min=4.8, stamp="VORHER", tplus=False, node=True),
    dict(scene="sprung", say="Drei, zwei, eins – Sprung! Die Erde bewegt sich. Um weniger als die Breite eines Atoms.", min=5.0, stamp="0,5 SEK.", node=True, shake=0.3),
    dict(scene="landung", say="Nach einer Sekunde: Alle landen, die Erde rückt zurück. Das war's.", min=4.2, stamp="1 SEKUNDE", node=True, shake=0.8),
    dict(scene="twist", say="Und das Krasse: Alle Menschen zusammen würden in einen Würfel passen, fast so hoch wie das höchste Gebäude der Welt.", min=5.4, stamp="FAKT", tplus=False, node=True, twist=True, shake=0.5),
    dict(scene="outro", say="Welches Szenario soll als Nächstes kommen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

_r = np.random.default_rng(3); NP = 5000
P_x = _r.uniform(-60, W + 60, NP); P_d = _r.random(NP) ** 0.7          # Tiefe 0 = hinten, 1 = vorne
P_ph = _r.uniform(0, 0.25, NP); P_col = _r.choice(np.array([[1, .45, .2], [.3, .85, 1], [1, .85, .3], [.6, 1, .6], [1, .5, .8], [.9, .9, 1]]), NP)

_rr = np.random.default_rng(8)
FIG = []
for row in range(14):
    d = row / 13; y = 1095 + d ** 1.5 * 430; sz = 6 + d * 34; n = int(70 - 50 * d)
    for k in range(n):
        x = _rr.uniform(-30, W + 30)
        FIG.append((d, x, y, sz, tuple(int(c) for c in _rr.choice(np.array([[255, 115, 50], [80, 210, 255], [255, 215, 80], [150, 255, 150], [255, 120, 200], [230, 230, 255]]))), _rr.uniform(0, 0.25)))
FIG.sort(key=lambda f: f[0])

def crowd(img, rel, jump=None):
    """Menschenmenge als Figuren (hinten klein, vorne groß). jump: Zeitpunkt des Sprungs."""
    d = ImageDraw.Draw(img)
    for dep, x, y, sz, col, ph in FIG:
        h = 0.0
        if jump is not None:
            t = rel - jump - ph * 0.15
            if 0 < t < 0.9: h = math.sin(t / 0.9 * math.pi) * (10 + 90 * dep)
        shade = 0.35 + 0.65 * dep
        c = tuple(int(v * shade) for v in col); skin = tuple(int(v * shade) for v in (235, 190, 150))
        yb = y - h
        d.rounded_rectangle([x - sz * 0.45, yb - sz * 1.9, x + sz * 0.45, yb], radius=max(1, int(sz * 0.3)), fill=c)
        d.ellipse([x - sz * 0.33, yb - sz * 2.6, x + sz * 0.33, yb - sz * 1.95], fill=skin)

def ground(rel, light=1.0):
    bg = kr.vgrad((8, 14, 44), (150, 90, 90), gamma=1.5) * light
    bg[1080:] = kr.vgrad((60, 80, 60), (20, 30, 24))[1080:]
    return bg

def sc_hook(rel, ln, i): return ground(rel)
def ov_hook(img, rel, ln, i):
    crowd(img, rel, 1.2); lib.hook_text(img, rel, ln, "ALLE MENSCHEN", "GLEICHZEITIG", "SPRINGEN?")

def sc_treffen(rel, ln, i):
    bg = kr.vgrad((10, 18, 40), (6, 10, 22)); return bg
def ov_treffen(img, rel, ln, i):
    lib.heads(img, rel, "ERST MAL TREFFEN", "8,1 MRD. AUF 2.025 KM²", glow=CYAN, sub="4 Menschen pro Quadratmeter – wie in einem vollen Konzert")
    d = ImageDraw.Draw(img, "RGBA")
    k = eo((rel - 0.6) / 1.5)
    # Flächenvergleich: Saarland 2.570 km² vs. benötigte 2.025 km² (Seitenlängen ∝ Wurzel)
    s1 = 420; s2 = s1 * math.sqrt(2025 / 2570)
    x0, y0 = 500 - s1 / 2, 760
    d.rectangle([x0, y0, x0 + s1, y0 + s1], fill=(40, 120, 70, 200), outline=(255, 255, 255, 200), width=4)
    text_fx(img, (500, y0 + s1 + 40), "SAARLAND · 2.570 km²", F("Black", 32), fill=GREEN, tracking=2)
    if k > 0:
        ss_ = s2 * k
        d.rectangle([x0 + 10, y0 + 10, x0 + 10 + ss_, y0 + 10 + ss_], fill=ORANGE + (200,))
        if k > 0.7:
            text_fx(img, (x0 + 10 + ss_ / 2, y0 - 15 + ss_ / 2), "ALLE", F("Black", 40), fill=WHITE, alpha=(k - 0.7) / 0.3)
            text_fx(img, (x0 + 10 + ss_ / 2, y0 + 35 + ss_ / 2), "MENSCHEN", F("Black", 40), fill=WHITE, alpha=(k - 0.7) / 0.3)

def sc_sprung(rel, ln, i):
    bg = lib.space_bg(rel)
    dy = -14 * math.sin(clamp((rel - 1.5) / 0.9) * math.pi)
    er, ea, _ = lib.earth(300, spin=1.0 + rel * 0.05, light=(0.6, -0.4, 0.7))
    kr.blit(bg, er, ea, 540, 1010 + dy)
    return bg
def ov_sprung(img, rel, ln, i):
    lib.heads(img, rel, "DIE ERDE BEWEGT SICH", "0,00000000000004 m", glow=CYAN, sub="weniger als die Breite eines einzigen Atoms", size=96, t0=1.4)
def sc_landung(rel, ln, i): return ground(rel)
def ov_landung(img, rel, ln, i):
    crowd(img, rel + 0.9, 1.0)
    lib.heads(img, rel, "ALLE LANDEN", "DAS WAR'S", glow=GREEN, sub="die Erde rückt genauso viel zurück – Sprung neutralisiert", t0=0.5)

def sc_twist(rel, ln, i):
    bg = kr.vgrad((10, 18, 50), (110, 80, 110), gamma=1.3)
    bg[1300:] = np.array([0.12, 0.14, 0.12], np.float32)
    return bg
def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "WÜRFEL MIT 800 M", glow=ORANGE, big_col=ORANGE, sub="so viel Platz bräuchten alle 8,1 Mrd. Menschen", sub_t=1.2)
    d = ImageDraw.Draw(img, "RGBA")
    base = 1300; hpx = 430; k = eo((rel - 0.8) / 1.4)
    s = hpx * k
    if s > 4:
        x0 = 140
        d.polygon([(x0, base), (x0 + s, base), (x0 + s, base - s), (x0, base - s)], fill=(255, 112, 38, 235))
        o = s * 0.35
        d.polygon([(x0, base - s), (x0 + o, base - s - o * 0.6), (x0 + s + o, base - s - o * 0.6), (x0 + s, base - s)], fill=(255, 170, 110, 235))
        d.polygon([(x0 + s, base), (x0 + s + o, base - o * 0.6), (x0 + s + o, base - s - o * 0.6), (x0 + s, base - s)], fill=(200, 80, 25, 235))
        text_fx(img, (x0 + s / 2, base - s / 2), "8,1 MRD.", F("Black", 40), fill=WHITE, alpha=k)
    # Turm-Silhouette (828 m) zum Vergleich
    tx = 860; th = hpx * 828 / 808
    d.polygon([(tx - 40, base), (tx + 40, base), (tx + 18, base - th * 0.5), (tx + 8, base - th * 0.85), (tx + 2, base - th), (tx - 2, base - th), (tx - 8, base - th * 0.85), (tx - 18, base - th * 0.5)], fill=(25, 30, 45, 255))
    text_fx(img, (tx, base + 40), "828 m", F("Black", 30), fill=WHITE)
    text_fx(img, (140 + 215, base + 40), "807 m", F("Black", 30), fill=WHITE, alpha=k)

def sc_outro(rel, ln, i): return ground(rel) * 0.7
def ov_outro(img, rel, ln, i):
    crowd(img, rel, 0.3); lib.outro(img, rel, "Welches Szenario", "kommt als Nächstes?")

SCENES = dict(hook=sc_hook, treffen=sc_treffen, sprung=sc_sprung, landung=sc_landung, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, treffen=ov_treffen, sprung=ov_sprung, landung=ov_landung, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
