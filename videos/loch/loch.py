"""KETTENREAKTION #06 – Was wäre, wenn du in ein Schwarzes Loch fällst?"""
import math, os, sys
from functools import lru_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import Image, ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(73.4, 110.0, 146.8), (69.3, 103.8, 138.6), (65.4, 98.0, 130.8), (61.7, 92.5, 123.5)]
SOURCES = "Quellen: NASA · Event Horizon Telescope (2022) · Allgemeine Relativitätstheorie"
VIOLET = (190, 140, 255)

SEGS = [
    dict(scene="hook", say="Du fällst in ein Schwarzes Loch. Was passiert mit dir?", min=3.6, stamp="START", tplus=False, nosub=True, shake=0.4),
    dict(scene="anflug", say="Im Anflug: Der Himmel verbiegt sich. Die Schwerkraft lenkt sogar Licht ab.", min=4.6, stamp="ANFLUG", tplus=False, node=True),
    dict(scene="zeit", say="Für deine Freunde draußen wirst du immer langsamer – und scheinst am Rand zu erstarren.", min=4.8, stamp="VON AUSSEN", tplus=False, node=True),
    dict(scene="horizont", say="Am Ereignishorizont: Ab hier gibt es kein Zurück. Nicht einmal Licht entkommt.", min=4.6, stamp="HORIZONT", tplus=False, node=True),
    dict(scene="spaghetti", say="Drinnen: Die Schwerkraft zieht dich in die Länge – wie Spaghetti.", min=4.4, stamp="DRINNEN", tplus=False, node=True),
    dict(scene="twist", say="Und das Krasse: In der Mitte unserer Milchstraße sitzt eins. Vier Millionen Sonnen schwer.", min=5.2, stamp="MILCHSTRASSE", tplus=False, node=True, twist=True, shake=0.6),
    dict(scene="outro", say="Welches Szenario soll als Nächstes kommen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

@lru_cache(None)
def sky_src():
    s = kr.starfield(2 * W, 2 * H, 6000, seed=31, big=80)
    s += np.asarray(Image.fromarray((kr.fnoise(2 * W // 4, 2 * H // 4, 6, seed=5, base=3) * 255).astype(np.uint8)).resize((2 * W, 2 * H)), np.float32)[..., None] / 255 * np.array([0.10, 0.05, 0.16], np.float32)
    return s.astype(np.float32)

@lru_cache(None)
def _grid():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); return xx, yy

def blackhole(cx, cy, Rs, rel, disk=1.0, rot=0.0):
    """Schwarzes Loch mit Gravitationslinse, Photonenring und Akkretionsscheibe."""
    src = sky_src(); xx, yy = _grid()
    dx = xx - cx; dy = yy - cy; r = np.sqrt(dx * dx + dy * dy) + 1e-3
    defl = (2.6 * Rs) ** 2 / r                           # Ablenkung ~ 1/r
    rs = r - defl
    sx = (cx + dx / r * rs + W + rel * 20 + rot) .astype(np.int32) % (2 * W)
    sy = (cy + dy / r * rs + H / 2).astype(np.int32) % (2 * H)
    img = src[sy, sx]
    shadow = 2.6 * Rs
    img = img * ss(shadow * 0.98, shadow * 1.04, r)[..., None]
    # Photonenring
    img += (np.exp(-((r - shadow * 1.04) / (Rs * 0.06)) ** 2) * 1.6)[..., None] * np.array([1.0, 0.8, 0.55], np.float32)
    if disk > 0:
        # Scheibe vorne (flache Ellipse) und lensierter hinterer Teil (Bogen über dem Schatten)
        ey = dy / 0.22; re = np.sqrt(dx * dx + ey * ey)
        band = ss(shadow * 1.15, shadow * 1.5, re) * (1 - ss(shadow * 2.4, shadow * 3.6, re))
        front = (dy > -2) | (r > shadow * 1.02)
        ang = np.arctan2(ey, dx)
        dop = 0.55 + 0.45 * np.cos(ang + math.pi)             # links heller (Doppler)
        swirl = 0.75 + 0.25 * np.sin(re / Rs * 3.0 - rel * 4 + ang * 3)
        hot = band * dop * swirl * front * disk
        col = np.stack([1.0 + 0 * hot, 0.55 + 0.35 * hot, 0.2 + 0.3 * hot], -1)
        img = img * (1 - np.clip(hot, 0, 1)[..., None] * 0.9) + hot[..., None] * col * 1.6
        # hinterer Teil: Bogen oben/unten um den Schatten
        arc = np.exp(-((r - shadow * 1.35) / (Rs * 0.35)) ** 2) * (dy < 0) * (0.6 + 0.4 * np.abs(dx / r)) * 0.9 * disk
        arc *= (r > shadow)
        img += arc[..., None] * np.array([1.0, 0.65, 0.3], np.float32)
        arc2 = np.exp(-((r - shadow * 1.2) / (Rs * 0.18)) ** 2) * (dy > 0) * 0.5 * disk * (r > shadow)
        img += arc2[..., None] * np.array([1.0, 0.6, 0.25], np.float32)
    return img

def sc_hook(rel, ln, i): return blackhole(540, 1080, 60 + 6 * rel, rel)
def ov_hook(img, rel, ln, i): lib.hook_text(img, rel, ln, "DU IN EIN", "SCHWARZES LOCH", "FÄLLST?")

def sc_anflug(rel, ln, i): return blackhole(540, 1020, 70 + 30 * eio(rel / ln), rel, 1.0, rot=rel * 60)
def ov_anflug(img, rel, ln, i):
    lib.heads(img, rel, "IM ANFLUG", "LICHT WIRD KRUMM", glow=VIOLET, sub="Gravitationslinse: Sterne erscheinen verzerrt und doppelt")

def sc_zeit(rel, ln, i): return blackhole(540, 1080, 100, rel, 1.0, rot=60 * 4.6)
def ov_zeit(img, rel, ln, i):
    lib.heads(img, rel, "VON AUSSEN GESEHEN", "DIE ZEIT ERSTARRT", glow=VIOLET, sub="dein Licht wird immer röter und schwächer")
    k = eo(rel / 3.6)
    x = 860 - 160 * k; y = 1080 - 30 * k
    e = kr.emoji("🧑‍🚀", 120)
    arr = np.asarray(e, np.float32); arr[..., 1] *= (1 - 0.6 * k); arr[..., 2] *= (1 - 0.8 * k); arr[..., 3] *= (1 - 0.7 * k)
    e2 = Image.fromarray(arr.astype(np.uint8), "RGBA"); img.paste(e2, (int(x - e2.width / 2), int(y - e2.height / 2)), e2)
    sec = 10 * (1 - math.exp(-rel * 0.9))
    text_fx(img, (500, 1265), f"Uhr des Astronauten: {sec:05.2f} s", F("Black", 34), fill=AMBER)

def sc_horizont(rel, ln, i):
    Rs = 100 + 170 * eio(rel / ln)
    return blackhole(540, 1150, Rs, rel, 1.0 - 0.5 * eio(rel / ln))
def ov_horizont(img, rel, ln, i):
    lib.heads(img, rel, "DER EREIGNISHORIZONT", "KEIN ZURÜCK", glow=RED, sub="die Fluchtgeschwindigkeit wäre schneller als das Licht")

def sc_spaghetti(rel, ln, i):
    bg = blackhole(540, 2400, 420, rel, 0.6) * 0.5
    bg += kr.radial(540, 1600, 700, (120, 40, 30), 0.4)
    return bg
def ov_spaghetti(img, rel, ln, i):
    lib.heads(img, rel, "DRINNEN", "SPAGHETTIFIZIERUNG", glow=ORANGE, sub="unten zieht die Schwerkraft stärker als oben")
    k = eio((rel - 0.5) / 3.0)
    e = kr.emoji("🧑‍🚀", 200)
    e = e.resize((max(10, int(e.width * (1 - 0.7 * k))), int(e.height * (1 + 2.6 * k))), Image.BICUBIC)
    img.paste(e, (int(500 - e.width / 2), int(1010 - e.height / 2 + 120 * k)), e)
    lib.paste_emoji(img, "🍝", 110, 840, 820, alpha=clamp((rel - 1.5) / 0.4))

def sc_twist(rel, ln, i):
    bg = lib.space_bg(rel)
    # Milchstraße als leuchtendes Band mit Zentrum
    xx, yy = _grid()
    band = np.exp(-((yy - 1080 + (xx - 540) * 0.25) / 120) ** 2)
    bg += band[..., None] * np.array([0.35, 0.28, 0.45], np.float32) * (0.6 + 0.4 * lib.ridge(15)[None, :, None])
    bg += kr.radial(540, 1080, 160, (255, 220, 170), 1.2)
    k = eo((rel - 1.0) / 1.2)
    if k > 0:
        lib.ring(bg, 540, 1080, 40 + 30 * (1 - k), 6, (255, 140, 60), 1.4 * k)
    return bg
def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "4 MIO. SONNEN SCHWER", glow=ORANGE, big_col=ORANGE, sub="Sagittarius A* – 2022 erstmals fotografiert", sub_t=1.3)
    d = ImageDraw.Draw(img, "RGBA"); a = clamp((rel - 1.2) / 0.3)
    d.line([480, 1040, 340, 930], fill=(255, 255, 255, int(200 * a)), width=3)
    text_fx(img, (330, 860), "SAGITTARIUS A*", F("Black", 30), fill=WHITE, anchor="mm", alpha=a, tracking=2)
    text_fx(img, (330, 900), "26.000 Lichtjahre entfernt", F("SemiBold", 24), fill=(215, 220, 235), anchor="mm", alpha=a)

def sc_outro(rel, ln, i): return blackhole(540, 1750, 80, rel + 10) * 0.9
def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welches Szenario", "kommt als Nächstes?")

SCENES = dict(hook=sc_hook, anflug=sc_anflug, zeit=sc_zeit, horizont=sc_horizont, spaghetti=sc_spaghetti, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, anflug=ov_anflug, zeit=ov_zeit, horizont=ov_horizont, spaghetti=ov_spaghetti, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
