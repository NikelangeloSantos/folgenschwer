"""FOLGENSCHWER #02 – Was wäre, wenn die Erde aufhört, sich zu drehen?"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(110.0, 164.8, 220.0), (98.0, 146.8, 196.0), (116.5, 174.6, 233.1), (130.8, 196.0, 261.6)]
SOURCES = "Quellen: NASA · Esri/W. Fraczek (Simulation) · Stephenson et al. 2016 (Proc. R. Soc. A)"

SEGS = [
    dict(scene="hook", say="Die Erde hört auf, sich zu drehen. Sofort. Was passiert?", min=3.6, stamp="JETZT", nosub=True, shake=0.4),
    dict(scene="wind", say="Sekunde eins: Alles fliegt weiter – am Äquator mit über sechzehnhundert Kilometern pro Stunde.", min=4.6, stamp="1 SEKUNDE", node=True, shake=1.0),
    dict(scene="tsunami", say="Nach einer Stunde: Die Ozeane schwappen weiter. Riesige Tsunamis rollen über die Küsten.", min=4.8, stamp="1 STUNDE", node=True),
    dict(scene="tag", say="Nach sechs Monaten: Immer noch Tag. Ein Tag dauert jetzt ein ganzes Jahr.", min=4.6, stamp="6 MONATEN", node=True),
    dict(scene="ozean", say="Am Ende: Die Meere fließen zu den Polen. Am Äquator taucht ein Riesen-Kontinent auf.", min=4.8, stamp="AM ENDE", tplus=False, node=True),
    dict(scene="twist", say="Und das Krasse: Die Erde bremst wirklich. Pro Jahrhundert wird jeder Tag knapp zwei Millisekunden länger.", min=5.2, stamp="HEUTE", node=True, twist=True, shake=0.6),
    dict(scene="outro", say="Was soll als Nächstes stoppen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

def spin_at(rel):
    stop = 0.35
    if rel < stop: return 1.0 + 4.0 * rel
    return 1.0 + 4.0 * stop + 0.04 * math.sin((rel - stop) * 18) * math.exp(-(rel - stop) * 5)

_r = np.random.default_rng(3); NP = 1400
P_y = _r.uniform(-1, 1, NP) ** 3 * 120; P_v = _r.uniform(300, 1400, NP); P_side = np.where(_r.random(NP) < 0.5, -1, 1); P_d = _r.uniform(0, 0.4, NP)

def sc_hook(rel, ln, i):
    bg = lib.space_bg(rel)
    bg += kr.radial(-200, 700, 600, (255, 200, 120), 0.6)
    er, ea, _ = lib.earth(320, spin=spin_at(rel), tilt=0, light=(-0.8, -0.3, 0.5), cspin=0.0)
    kr.blit(bg, er, ea, 540, 1110)
    if rel > 0.35:
        tt = rel - 0.35 - P_d; ok = tt > 0
        x = 540 + P_side * (300 + P_v * np.clip(tt, 0, None)); y = 1110 + P_y + 20 * np.sin(tt * 3)
        a = np.clip(1 - tt / 2.5, 0, 1)[:, None] * ok[:, None]
        kr.splat(bg, x, y, np.array([0.8, 0.9, 1.0]) * a, 2)
        bg += kr.radial(540, 1110, 420, (120, 180, 255), 1.0 * math.exp(-(rel - 0.35) * 4))
    return bg

def ov_hook(img, rel, ln, i):
    lib.hook_text(img, rel, ln, "DIE ERDE", "ANHÄLT?")
    if rel > 0.35:
        text_fx(img, (540, 1480 - 30), "STOPP", F("Black", 40), fill=RED, tracking=10, alpha=clamp(1.2 - (rel - 0.35)))

STREAK = None
def sc_wind(rel, ln, i):
    bg = kr.vgrad((40, 70, 130), (230, 160, 110), gamma=1.3)
    rg = 1180 - 120 * (lib.ridge(5) - 0.3)
    lib.fill_below(bg, rg, (18, 16, 24))
    r = np.random.default_rng(1); n = 900
    y0 = r.uniform(300, 1400, n); sp = r.uniform(1500, 3500, n); ph = r.uniform(0, W, n)
    for k in range(10):
        x = (ph + sp * rel - k * 9) % (W + 200) - 100
        kr.splat(bg, x, y0, np.array([0.9, 0.95, 1.0]) * (0.4 * (1 - k / 10)), 3)
    return bg

def ov_wind(img, rel, ln, i):
    lib.heads(img, rel, "AM ÄQUATOR", "1.670 KM/H", glow=ORANGE, sub="alles, was lose ist, fliegt mit dem alten Schwung weiter")
    for k, (ch, y, s, d) in enumerate((("🚗", 900, 150, 0.0), ("🌳", 1060, 180, 0.35), ("🐄", 780, 140, 0.7), ("🏠", 1150, 160, 1.1), ("⛵", 960, 130, 1.5), ("🚌", 840, 150, 1.9), ("🌲", 1100, 170, 2.3), ("🐑", 1000, 120, 2.7))):
        t = rel - d
        if t < 0: continue
        x = -150 + t * 1100;
        if x > W + 150: continue
        lib.paste_emoji(img, ch, s, x, y - 60 * math.sin(t * 2), angle=-t * 160)

def sc_tsunami(rel, ln, i):
    bg = kr.vgrad((20, 26, 50), (70, 60, 90)); bg += lib.stars(rel * 2, 0, 0.3)
    xs = np.arange(W, dtype=np.float32)
    # Skyline rechts
    sky = np.full(W, 1260.0, np.float32); r = np.random.default_rng(2); x = 620
    while x < W:
        w = r.uniform(40, 90); h = r.uniform(80, 330); sky[int(x):int(x + w)] = 1260 - h; x += w + r.uniform(4, 14)
    lib.fill_below(bg, sky, (10, 12, 22), 1262)
    win = (np.random.default_rng(3).random((H, W)) < 0.004)
    yy = np.arange(H)[:, None]
    bg[win & (yy > sky[None, :] + 10) & (yy < 1255)] = np.array([1.0, 0.8, 0.4], np.float32)
    # Welle wandert von links nach rechts und türmt sich auf
    xc = -200 + 520 * eo(rel / 4.2); A = 180 + 300 * eio(rel / 3.5)
    d = (xs - xc)
    surf = 1280 - A * np.where(d < 0, np.exp(-(d / 420) ** 2), np.exp(-(d / 130) ** 2)) + 6 * np.sin(xs * 0.03 + rel * 5)
    water = yy > surf[None, :]
    depth = np.clip((yy - surf[None, :]) / 500, 0, 1)
    wc = np.stack([0.02 + 0.08 * (1 - depth), 0.12 + 0.3 * (1 - depth), 0.25 + 0.4 * (1 - depth)], -1)
    bg = np.where(water[..., None], wc, bg).astype(np.float32)
    crest = np.abs(yy - surf[None, :]) < 5
    bg[crest] = np.array([0.9, 0.97, 1.0], np.float32)
    rr = np.random.default_rng(4); n = 600
    fx = xc + rr.normal(60, 50, n); fy = np.interp(np.clip(fx, 0, W - 1), xs, surf) - rr.uniform(0, 60, n)
    kr.splat(bg, fx + rr.normal(0, 8, n) * rel, fy, np.array([0.7, 0.8, 0.9]) * 0.5, 2)
    return bg

def ov_tsunami(img, rel, ln, i):
    lib.heads(img, rel, "DIE OZEANE", "RIESEN-TSUNAMIS", glow=CYAN, sub="das Wasser hat noch den alten Schwung")

def sc_tag(rel, ln, i):
    bg = lib.space_bg(rel * 0.3)
    bg += kr.radial(-220, 1000, 560, (255, 190, 110), 1.1) + kr.radial(-220, 1000, 220, (255, 240, 200), 1.8)
    er, ea, _ = lib.earth(300, spin=2.6, tilt=0, light=(-0.95, 0.0, 0.3), cspin=rel * 0.02)
    kr.blit(bg, er, ea, 560, 1000)
    return bg

def ov_tag(img, rel, ln, i):
    lib.heads(img, rel, "EIN TAG", "1 TAG = 1 JAHR", glow=AMBER)
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1, y = 120, 880, 1300; mid = (x0 + x1) / 2
    d.rounded_rectangle([x0, y - 16, mid, y + 16], 16, fill=AMBER + (230,))
    d.rounded_rectangle([mid, y - 16, x1, y + 16], 16, fill=(30, 36, 70, 230), outline=(255, 255, 255, 90), width=2)
    p = eo(rel / 3.5); px = x0 + (mid - x0 - 10) * p
    d.ellipse([px - 22, y - 22, px + 22, y + 22], fill=(255, 255, 255, 255))
    text_fx(img, ((x0 + mid) / 2, y - 48), "6 MONATE HELL", F("Black", 30), fill=AMBER, tracking=2)
    text_fx(img, ((mid + x1) / 2, y - 48), "6 MONATE NACHT", F("Black", 30), fill=(170, 190, 255), tracking=2)
    text_fx(img, (500, 645), f"Tag {int(1 + 182 * p)} – die Sonne steht noch", F("SemiBold", 31), fill=(215, 220, 235), alpha=clamp((rel - 1.0) / 0.4))

GN = (0.8 + 0.3 * kr.fnoise(1024, 512, 4, seed=61, base=4)[..., None]).astype(np.float32)
def sc_ozean(rel, ln, i):
    bg = lib.space_bg(rel * 0.3)
    tex, _, _, land = lib.earth_tex()
    k = eio((rel - 0.6) / 3.2)
    h_, w_ = tex.shape[:2]
    lat = np.abs(np.linspace(90, -90, h_))[:, None]
    lim = 35 * k
    newland = (lat < lim)
    sea = np.array([0.04, 0.16, 0.38], np.float32); ground = np.array([0.55, 0.45, 0.28], np.float32)
    m = tex.copy()
    m = np.where((newland & ~land)[..., None], ground * GN, m)
    m = np.where(((lat > 90 - 50 * k) & land)[..., None], sea, m)
    im = (np.asarray(__import__("PIL").Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((900, 450)), np.float32) / 255)
    x0, y0 = 90, 760
    bg[y0:y0 + 450, x0:x0 + 900] = im
    return bg

def ov_ozean(img, rel, ln, i):
    lib.heads(img, rel, "DIE MEERE", "FLIEHEN ZU DEN POLEN", glow=CYAN, sub="die Wölbung am Äquator (21 km) hält sie nicht mehr")
    d = ImageDraw.Draw(img, "RGBA"); d.rectangle([90, 760, 990, 1210], outline=(255, 255, 255, 140), width=3)
    d.line([90, 985, 990, 985], fill=ORANGE + (200,), width=3)
    text_fx(img, (110, 1240), "ÄQUATOR = ORANGE LINIE · Simulation", F("Bold", 24), fill=(210, 215, 230), anchor="lm", tracking=2)

def sc_twist(rel, ln, i):
    bg = lib.space_bg(rel)
    er, ea, _ = lib.earth(200, spin=2.0 + rel * 0.25, tilt=-23, light=(0.3, -0.5, 0.8), cspin=rel * 0.05)
    kr.blit(bg, er, ea, 400, 900)
    mr, ma, _ = kr.sphere(60, lib.moon_tex(), spin=0.3, light=(0.3, -0.5, 0.8), atm=None)
    kr.blit(bg, mr, ma, 830, 790)
    return bg

def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "+1,8 MILLISEKUNDEN", glow=ORANGE, big_col=ORANGE, sub="pro Jahrhundert – Ebbe und Flut bremsen die Erde", sub_t=1.4)
    d = ImageDraw.Draw(img, "RGBA")
    text_fx(img, (500, 1165), "TAGESLÄNGE IN 100 JAHREN", F("Bold", 26), fill=(210, 215, 230), tracking=3, alpha=clamp((rel - 1.0) / 0.3))
    text_fx(img, (500, 1235), "24:00:00,0018", F("Black", 70), fill=WHITE, glow=CYAN, glow_r=12, alpha=clamp((rel - 1.0) / 0.3))

def sc_outro(rel, ln, i):
    bg = lib.space_bg(rel + 20)
    er, ea, _ = lib.earth(420, spin=3.5 + rel * 0.06, tilt=-23, light=(0.6, -0.6, 0.5), cspin=rel * 0.02)
    kr.blit(bg, er, ea, 540, 1750)
    return bg

def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Was soll als Nächstes", "stoppen?")

SCENES = dict(hook=sc_hook, wind=sc_wind, tsunami=sc_tsunami, tag=sc_tag, ozean=sc_ozean, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, wind=ov_wind, tsunami=ov_tsunami, tag=ov_tag, ozean=ov_ozean, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
