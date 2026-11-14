"""FOLGENSCHWER #09 – Was wäre, wenn du einen Kaugummi verschluckst?  (Shorts-optimiert, v2)

Nach den Auswertungen: 28–34 s, 3 Kettenglieder + Twist, Hook = krasseste Aussage + Slam-Text + Bewegung ab Frame 0,
hochlaufender Zähler, Themenfrage im Outro. Vorversion: kaugummi_v1.py"""
import math, os, sys
from functools import lru_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 32.0
CHORDS = [(146.8, 185.0, 220.0), (164.8, 207.7, 246.9), (130.8, 164.8, 196.0), (146.8, 174.6, 220.0)]
SOURCES = "Quellen: Mayo Clinic · Harvard Health · Milov et al. 1998 (Pediatrics)"
PINK = (255, 110, 190)

SEGS = [
    dict(scene="hook", say="Sieben Jahre im Bauch? Wir verfolgen deinen Kaugummi.", min=2.6, stamp="JETZT", nosub=True, shake=1.0, tail=0.15),
    dict(scene="speise", say="Nach zehn Sekunden: Er landet im Magen.", min=2.6, stamp="10 SEKUNDEN", node=True, tail=0.2),
    dict(scene="magen", say="Nach einer Stunde: Die Magensäure kriegt ihn nicht klein.", min=3.0, stamp="1 STUNDE", node=True, tail=0.2),
    dict(scene="raus", say="Nach zwei Tagen: Er ist wieder draußen. Ganz normal, auf dem Klo.", min=3.6, stamp="2 TAGEN", node=True, tail=0.2),
    dict(scene="twist", say="Die sieben Jahre? Ein Mythos! Gefährlich wird's nur, wenn du ständig viele schluckst.", min=4.4, stamp="FAKT", tplus=False, node=True, twist=True, shake=0.6),
    dict(scene="outro", say="Welchen Mythos sollen wir als Nächstes checken?", min=2.8, nosub=True, noui=True, nosrc=True),
]

# Weg durch den Körper (Mund → Speiseröhre → Magen → Dünndarm → Dickdarm → raus)
def _path():
    pts = [(540, 790), (540, 860), (544, 930), (560, 960), (620, 965), (660, 990), (650, 1030), (600, 1045), (560, 1040)]
    y = 1065; left = True
    for k in range(5):                    # Dünndarm-Schlingen
        xs = (420, 660) if left else (660, 420)
        pts += [(xs[0], y), (xs[1], y)]; y += 26; left = not left
    pts += [(400, 1200), (400, 1060), (690, 1060), (690, 1215), (560, 1225), (540, 1300)]
    P = np.array(pts, np.float32); seg = np.sqrt(((P[1:] - P[:-1]) ** 2).sum(1)); cum = np.concatenate([[0], np.cumsum(seg)])
    return P, cum / cum[-1]
PATH, CUM = _path()
MARK = dict(mund=0.0, magen=CUM[6], darm=CUM[9], ende=1.0)

def at(s):
    s = clamp(s); j = int(np.searchsorted(CUM, s, side="right") - 1); j = min(j, len(PATH) - 2)
    t = (s - CUM[j]) / max(1e-6, CUM[j + 1] - CUM[j]); return PATH[j] + (PATH[j + 1] - PATH[j]) * t

@lru_cache(None)
def body():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([460, 680, 620, 840], fill=(90, 170, 220, 60), outline=(150, 220, 255, 200), width=4)
    d.rounded_rectangle([515, 830, 565, 880], 10, fill=(90, 170, 220, 60))
    d.rounded_rectangle([360, 870, 720, 1330], 120, fill=(90, 170, 220, 55), outline=(150, 220, 255, 200), width=4)
    d.line([tuple(p) for p in PATH], fill=(255, 140, 170, 120), width=30, joint="curve")
    d.line([tuple(p) for p in PATH], fill=(255, 190, 210, 160), width=6, joint="curve")
    d.ellipse([560, 930, 690, 1050], outline=(255, 140, 170, 170), width=8)          # Magen-Umriss
    glow = im.filter(ImageFilter.GaussianBlur(14))
    a = np.asarray(Image.alpha_composite(glow, im), np.float32) / 255
    return a[..., :3] * a[..., 3:], a[..., 3]

def scene(rel, s, acid=0.0, trail=0.0, zoom=0.0):
    bg = kr.vgrad((14, 20, 44), (6, 8, 20)); bg += kr.radial(540, 1000, 500, (60, 40, 120), 0.4)
    rgb, a = body(); bg = bg * (1 - a[..., None] * 0.6) + rgb
    if acid > 0:
        r = np.random.default_rng(int(rel * 10)); n = 80
        kr.splat(bg, 625 + r.normal(0, 30, n), 990 + r.normal(0, 25, n), np.array([0.6, 1.0, 0.3]) * acid * 0.8, 3)
    x, y = at(s)
    for k in range(1, 7):                       # Leuchtspur hinter dem Kaugummi
        tx, ty = at(max(0.0, s - k * trail))
        if trail > 0: bg += kr.radial(tx, ty, 16, PINK, 0.7 * (1 - k / 7))
    bg += kr.radial(x, y, 24, PINK, 2.4) + kr.radial(x, y, 70, PINK, 0.6)
    # Kamera: sanftes Atmen + Zoom-Ruck am Szenenanfang, folgt leicht dem Kaugummi
    z = 1.14 + 0.03 * math.sin(rel * 1.4) + 0.20 * math.exp(-rel * 6) + zoom
    cx = 540 + (x - 540) * 0.25; cy = 1000 + (y - 1000) * 0.35
    ys = np.clip(((np.arange(H) - cy) / z + cy).astype(np.int32), 0, H - 1); xs = np.clip(((np.arange(W) - cx) / z + cx).astype(np.int32), 0, W - 1)
    return bg[ys][:, xs]

def gum_label(img, s, rel, txt=None):
    x, y = at(s)
    if txt: text_fx(img, (x + 60, y - 10), txt, F("Black", 28), fill=PINK, anchor="lm", tracking=2)

def slam(img, xy, txt, size, col, t, glow=None):
    """Text knallt rein: startet riesig und landet mit Nachfedern."""
    k = clamp(t / 0.22); sc = 1 + 0.32 * (1 - eo(k)) + 0.05 * math.sin(t * 22) * math.exp(-t * 7)
    text_fx(img, xy, txt, lib.fit_font(txt, size * sc, 1040), fill=col, glow=glow, glow_r=24, alpha=1.0, shadow=1.0)

def sc_hook(rel, ln, i): return scene(rel, MARK["magen"] * 0.75 * eio(rel / ln), trail=0.012, zoom=0.05)
def ov_hook(img, rel, ln, i):
    a = 1.0 if rel < ln - 0.2 else clamp((ln - rel) / 0.2)
    if a > 0.05:
        slam(img, (510, 470), "7 JAHRE", 200, AMBER, rel, glow=AMBER)
        if rel >= 0.1: slam(img, (510, 640), "IM BAUCH?", 130, WHITE, rel - 0.1)

def sc_speise(rel, ln, i): return scene(rel, MARK["magen"] * (0.75 + 0.25 * eio(rel / 1.4)), trail=0.01)
def ov_speise(img, rel, ln, i):
    lib.heads(img, rel, "RUNTERGESCHLUCKT", "AB IN DEN MAGEN", glow=PINK, t0=0.15)
    sec = min(10, int(rel / max(0.1, ln - 0.6) * 10) + 1)
    text_fx(img, (500, 650), f"Sekunde {sec}", F("Black", 44), fill=PINK)

def sc_magen(rel, ln, i):
    s = MARK["magen"] + 0.006 * math.sin(rel * 6)
    return scene(rel, s, acid=0.6 + 0.4 * math.sin(rel * 7) ** 2)
def ov_magen(img, rel, ln, i):
    lib.heads(img, rel, "MAGENSÄURE", "UNVERDAULICH", glow=(140, 255, 90), t0=0.15)
    mn = min(60, int(rel / max(0.1, ln - 0.5) * 60))
    text_fx(img, (500, 650), f"Minute {mn} – immer noch da", F("Black", 40), fill=(170, 255, 120))

def sc_raus(rel, ln, i): return scene(rel, MARK["magen"] + (1 - MARK["magen"]) * eio(rel / max(0.5, ln - 0.9)), trail=0.012)
def ov_raus(img, rel, ln, i):
    lib.heads(img, rel, "DURCH DEN DARM", "WIEDER DRAUSSEN", glow=CYAN, t0=0.15)
    hr = min(48, int(rel / max(0.1, ln - 0.9) * 48))
    text_fx(img, (500, 650), f"Stunde {hr}", F("Black", 44), fill=CYAN)
    if rel > ln - 1.2: lib.paste_emoji(img, "🚽", 130 * (0.7 + 0.3 * bo((rel - ln + 1.2) / 0.3)), 820, 1260)

def sc_twist(rel, ln, i):
    bg = kr.vgrad((24, 10, 30), (8, 4, 14)); bg += kr.radial(540, 1000, 500 + 40 * math.sin(rel * 3), (200, 60, 120), 0.4); return bg
def ov_twist(img, rel, ln, i):
    d = ImageDraw.Draw(img, "RGBA")
    text_fx(img, (500, 440), "DIE 7 JAHRE?", F("Black", 46), fill=CYAN, tracking=6, alpha=clamp(rel / 0.2))
    if rel > 0.7: slam(img, (500, 560), "MYTHOS!", 170, RED, rel - 0.7, glow=RED)
    k = eo(rel / 0.4)
    text_fx(img, (500, 930 + 6 * math.sin(rel * 4)), "7 JAHRE", F("Black", 150), fill=WHITE, alpha=k)
    if rel > 0.7:
        a = clamp((rel - 0.7) / 0.2); d.line([190, 990, 810, 870], fill=RED + (int(255 * a),), width=20)
    if rel > 1.3: slam(img, (500, 1120), "1–3 TAGE", 110, CYAN, rel - 1.3, glow=CYAN)
    text_fx(img, (500, 1250), "nur wer ständig viele schluckt, riskiert einen Darmverschluss", lib.fit_font("nur wer ständig viele schluckt, riskiert einen Darmverschluss", 30, 900, "Bold"), fill=WHITE, alpha=clamp((rel - 2.0) / 0.3), shadow=1.0)

def sc_outro(rel, ln, i): return scene(rel, 0.5 + 0.5 * math.sin(rel * 1.5), trail=0.01) * 0.5
def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welchen Mythos sollen wir", "als Nächstes checken?", emoji="🤔")

SCENES = dict(hook=sc_hook, speise=sc_speise, magen=sc_magen, raus=sc_raus, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, speise=ov_speise, magen=ov_magen, raus=ov_raus, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
