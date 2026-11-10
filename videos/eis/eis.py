"""KETTENREAKTION #05 – Was wäre, wenn alles Eis der Erde schmilzt?"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(98.0, 146.8, 196.0), (110.0, 164.8, 220.0), (87.3, 130.8, 174.6), (116.5, 174.6, 233.1)]
SOURCES = "Quellen: USGS · IPCC AR6 (2021) · Höhen ≈ Stadtmitte, ohne Deiche"

SEGS = [
    dict(scene="hook", say="Alles Eis der Erde schmilzt. Was steht dann unter Wasser?", min=3.6, stamp="+0 METER", tplus=False, nosub=True, shake=0.5),
    dict(scene="malediven", say="Plus ein Meter: Die Malediven verlieren den Großteil ihres Landes.", min=4.4, stamp="+1 METER", tplus=False, node=True),
    dict(scene="holland", say="Plus zehn Meter: Amsterdam und Rotterdam sind weg.", min=4.2, stamp="+10 METER", tplus=False, node=True),
    dict(scene="hamburg", say="Plus zwanzig Meter: Hamburg und Bremen stehen größtenteils unter Wasser.", min=4.4, stamp="+20 METER", tplus=False, node=True),
    dict(scene="berlin", say="Plus siebzig Meter – so viel wäre es am Ende: Sogar Berlin liegt unter Wasser.", min=4.8, stamp="+70 METER", tplus=False, node=True),
    dict(scene="twist", say="Und das Krasse: Ein Teil passiert wirklich. Bis 2100 könnte das Meer um fast einen Meter steigen.", min=5.4, stamp="BIS 2100", tplus=False, node=True, twist=True, shake=0.6),
    dict(scene="outro", say="Welches Szenario soll als Nächstes kommen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

# Szene: Querschnitt. Boden (Höhe E) mit Skyline, Wasser steigt von L0 auf L1. scale = px pro Meter.
LV = dict(
    malediven=dict(E=0.6, L0=0.0, L1=1.0, s=260, kind="insel", label="MALEDIVEN: meist < 1 m"),
    holland=dict(E=0.0, L0=1.0, L1=10.0, s=26, kind="stadt", label="AMSTERDAM ≈ 0 m"),
    hamburg=dict(E=6.0, L0=10.0, L1=20.0, s=14, kind="stadt", label="HAMBURG ≈ 6 m"),
    berlin=dict(E=34.0, L0=20.0, L1=70.0, s=5.2, kind="turm", label="BERLIN ≈ 34 m"),
)
BASE = 1330   # y für 0 m

def sky(rel):
    bg = kr.vgrad((20, 40, 80), (120, 150, 180), gamma=1.0); bg += lib.stars(rel * 2, 0, 0.15)
    return bg

def skyline(seed, x0, x1, ytop, kind):
    r = np.random.default_rng(seed); top = np.full(W, 99999.0, np.float32); x = x0
    if kind == "insel":
        xs = np.arange(W)
        hump = ytop - 30 * np.exp(-((xs - 560) / 220) ** 2)
        top = np.where((xs > 260) & (xs < 860), hump, top)
        for px in (380, 470, 650, 720):
            top[px - 26:px + 26] = np.minimum(top[px - 26:px + 26], ytop - r.uniform(50, 110))
        return top
    while x < x1:
        w = r.uniform(30, 70); h = r.uniform(60, 240) if kind == "stadt" else r.uniform(40, 140)
        top[int(x):int(x + w)] = ytop - h; x += w + r.uniform(2, 10)
    if kind == "turm":   # Fernsehturm-artige Silhouette
        top[555:565] = ytop - 360; top[530:590] = np.minimum(top[530:590], ytop - 250)
    return top

def level_scene(key, rel):
    p = LV[key]; s = p["s"]
    bg = sky(rel)
    L = p["L0"] + (p["L1"] - p["L0"]) * eio((rel - 0.3) / 2.6)
    yground = BASE - p["E"] * s
    yy = np.arange(H, dtype=np.float32)[:, None]; xs = np.arange(W, dtype=np.float32)
    ground = np.full(W, yground, np.float32)
    ground = np.where(xs < 200, BASE + 40, ground)   # Meer links
    lib.fill_below(bg, ground, (40, 36, 30))
    top = skyline(7 + len(key), 230, 900, yground, p["kind"])
    m = (yy > top[None, :]) & (yy <= yground + 1)
    bg[m] = np.array([0.03, 0.035, 0.06], np.float32)
    win = (np.random.default_rng(1).random((H, W)) < 0.03) & m
    bg[win] = np.array([1.0, 0.85, 0.5], np.float32)
    wy = BASE - L * s + 5 * np.sin(xs * 0.03 + rel * 3)
    water = yy > wy[None, :]
    depth = np.clip((yy - wy[None, :]) / 600, 0, 1)
    wc = np.stack([0.02 + 0.06 * (1 - depth), 0.15 + 0.25 * (1 - depth), 0.3 + 0.35 * (1 - depth)], -1)
    bg = np.where(water[..., None], bg * 0.35 + wc * 0.75, bg).astype(np.float32)
    bg[np.abs(yy - wy[None, :]) < 3] = np.array([0.8, 0.95, 1.0], np.float32)
    return bg, L

def level_overlay(img, key, rel, kicker, big, sub):
    p = LV[key]; s = p["s"]
    lib.heads(img, rel, kicker, big, glow=CYAN, sub=sub)
    L = p["L0"] + (p["L1"] - p["L0"]) * eio((rel - 0.3) / 2.6)
    d = ImageDraw.Draw(img, "RGBA")
    # Pegel rechts
    x = 950; top_m = (BASE - 700) / s
    d.line([x, 700, x, BASE], fill=(255, 255, 255, 180), width=3)
    step = [0.25, 0.5, 1, 2, 5, 10, 20][[0.25, 0.5, 1, 2, 5, 10, 20].index(min([0.25, 0.5, 1, 2, 5, 10, 20], key=lambda v: abs(top_m / v - 5)))]
    v = 0.0
    while v <= top_m + 1e-6:
        y = BASE - v * s; d.line([x - 14, y, x, y], fill=(255, 255, 255, 180), width=3)
        text_fx(img, (x - 22, y), (f"{v:g} m").replace(".", ","), F("Bold", 22), fill=(220, 225, 240), anchor="rm", shadow=0.8)
        v += step
    y = BASE - L * s
    text_fx(img, (60, y - 34), f"+{L:.1f} m".replace(".", ",") if L < 10 else f"+{L:.0f} m", F("Black", 44), fill=CYAN, anchor="lm", glow=CYAN, glow_r=10)
    text_fx(img, (560, BASE - p["E"] * s + 40), p["label"], F("Black", 30), fill=WHITE, tracking=2)

def sc_hook(rel, ln, i):
    bg = kr.vgrad((30, 60, 110), (150, 190, 220)); bg += lib.stars(rel, 0, 0.1)
    xs = np.arange(W, dtype=np.float32); yy = np.arange(H, dtype=np.float32)[:, None]
    melt = eio((rel - 0.3) / 3.0)
    # Eisberg: mehrere Gipfel, Facetten-Schattierung, Teil unter Wasser
    sc = 1 - 0.55 * melt
    prof = np.zeros(W, np.float32)
    for cx, hh, ww in ((470, 520, 260), (650, 380, 200), (330, 260, 170), (780, 220, 150)):
        prof = np.maximum(prof, hh * sc * np.clip(1 - np.abs(xs - cx) / (ww * (1 - 0.2 * melt)), 0, 1) ** 1.15)
    prof *= (0.9 + 0.1 * lib.ridge(12))
    berg = 1250 - prof
    m = (yy > berg[None, :]) & (yy < 1250) & (prof[None, :] > 1)
    grad = np.gradient(prof)[None, :, None]
    ice = kr.vgrad((245, 252, 255), (160, 205, 235)) * (0.85 + np.clip(grad * 0.08, -0.25, 0.2))
    bg = np.where(m[..., None], ice, bg).astype(np.float32)
    wy = 1250 - 40 * melt + 6 * np.sin(xs * 0.03 + rel * 3)
    water = yy > wy[None, :]
    bg = np.where(water[..., None], kr.vgrad((20, 90, 150), (4, 20, 50)), bg).astype(np.float32)
    under = (yy >= 1250) & (yy < 1250 + prof[None, :] * 1.6) & (prof[None, :] > 1)
    bg = np.where(under[..., None], bg * 0.55 + np.array([0.25, 0.55, 0.7], np.float32) * 0.45, bg).astype(np.float32)
    bg[np.abs(yy - wy[None, :]) < 3] = np.array([0.85, 0.95, 1.0], np.float32)
    r = np.random.default_rng(4); n = 120
    dx = r.uniform(300, 820, n); dy = (r.uniform(0, 1, n) + rel * 0.8) % 1
    kr.splat(bg, dx, np.interp(dx, xs, berg) + dy * (1250 - np.interp(dx, xs, berg)), np.array([0.6, 0.85, 1.0]) * 0.8 * (melt > 0.02), 3)
    return bg

def ov_hook(img, rel, ln, i): lib.hook_text(img, rel, ln, "ALLES EIS", "SCHMILZT?")

def make(key, kicker, big, sub):
    def sc(rel, ln, i): return level_scene(key, rel)[0]
    def ov(img, rel, ln, i): level_overlay(img, key, rel, kicker, big, sub)
    return sc, ov

sc_mal, ov_mal = make("malediven", "DIE MALEDIVEN", "LAND UNTER", "rund 80 % des Landes liegen weniger als 1 m über dem Meer")
sc_hol, ov_hol = make("holland", "DIE NIEDERLANDE", "AMSTERDAM & ROTTERDAM", "ein Viertel des Landes liegt heute schon unter dem Meeresspiegel")
sc_ham, ov_ham = make("hamburg", "NORDDEUTSCHLAND", "HAMBURG & BREMEN", "große Teile beider Städte liegen unter 20 m")
sc_ber, ov_ber = make("berlin", "AM ENDE: RUND 70 M", "SOGAR BERLIN", "auch Köln (≈ 53 m) wäre weg – München (≈ 520 m) nicht")

def sc_twist(rel, ln, i):
    bg = kr.vgrad((8, 14, 30), (4, 8, 18)); bg += kr.radial(540, 1000, 600, (30, 80, 140), 0.5)
    return bg

def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "≈ 1 METER BIS 2100", glow=ORANGE, big_col=ORANGE, sub="möglich bei hohen Emissionen – alles Eis bräuchte Jahrtausende", sub_t=1.3)
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1, y0, y1 = 150, 900, 1270, 760   # Jahre 1900..2100, 0..1,1 m
    def X(yr): return x0 + (x1 - x0) * (yr - 1900) / 200
    def Y(m): return y0 - (y0 - y1) * m / 1.1
    d.line([x0, y0, x1, y0], fill=(255, 255, 255, 150), width=3); d.line([x0, y0, x0, y1], fill=(255, 255, 255, 150), width=3)
    for yr in (1900, 2000, 2100): text_fx(img, (X(yr), y0 + 30), str(yr), F("Bold", 26), fill=(215, 220, 235))
    for m in (0.5, 1.0):
        d.line([x0, Y(m), x1, Y(m)], fill=(255, 255, 255, 50), width=2)
        text_fx(img, (x0 - 14, Y(m)), f"{m:g} m".replace(".", ","), F("Bold", 24), fill=(215, 220, 235), anchor="rm")
    k = eio((rel - 0.6) / 2.2)
    pts = [(X(1900 + t), Y(0.20 * (t / 118) ** 1.4)) for t in range(0, 119, 4)]
    n = max(2, int(len(pts) * clamp(k * 2)))
    d.line(pts[:n], fill=CYAN + (255,), width=7, joint="curve")
    if k > 0.5:
        kk = (k - 0.5) * 2; ye = 2018 + 82 * kk
        hi = [(X(2018 + t), Y(0.20 + 0.81 * (t / 82) ** 1.6)) for t in range(0, int(82 * kk) + 1, 2)]
        lo = [(X(2018 + t), Y(0.20 + 0.43 * (t / 82) ** 1.4)) for t in range(0, int(82 * kk) + 1, 2)]
        if len(hi) > 1: d.polygon(hi + lo[::-1], fill=ORANGE + (110,)); d.line(hi, fill=ORANGE + (255,), width=5)
    text_fx(img, (X(1960), Y(0.30)), "gemessen", F("Bold", 26), fill=CYAN, alpha=clamp(k * 3))
    text_fx(img, (X(2075), Y(1.05)), "Prognose", F("Bold", 26), fill=ORANGE, alpha=clamp((k - 0.6) * 3))

def sc_outro(rel, ln, i): return level_scene("berlin", 3.5 + rel * 0.0)[0] * 0.6

def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welches Szenario", "kommt als Nächstes?")

SCENES = dict(hook=sc_hook, malediven=sc_mal, holland=sc_hol, hamburg=sc_ham, berlin=sc_ber, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, malediven=ov_mal, holland=ov_hol, hamburg=ov_ham, berlin=ov_ber, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
