"""FOLGENSCHWER #09 – Was wäre, wenn du einen Kaugummi verschluckst?"""
import math, os, sys
from functools import lru_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(146.8, 185.0, 220.0), (164.8, 207.7, 246.9), (130.8, 164.8, 196.0), (146.8, 174.6, 220.0)]
SOURCES = "Quellen: Mayo Clinic · Harvard Health · Milov et al. 1998 (Pediatrics)"
PINK = (255, 110, 190)

SEGS = [
    dict(scene="hook", say="Du verschluckst deinen Kaugummi. Bleibt der jetzt wirklich sieben Jahre im Bauch?", min=3.8, stamp="JETZT", nosub=True),
    dict(scene="speise", say="Nach zehn Sekunden: Er rutscht durch die Speiseröhre in den Magen.", min=4.2, stamp="10 SEKUNDEN", node=True),
    dict(scene="magen", say="Nach einer Stunde: Die Magensäure kann die Kaumasse nicht auflösen.", min=4.4, stamp="1 STUNDE", node=True),
    dict(scene="darm", say="Nach ein paar Stunden: Er rutscht einfach weiter in den Darm – wie ein Maiskorn.", min=4.6, stamp="4 STUNDEN", node=True),
    dict(scene="raus", say="Nach ein bis drei Tagen: wieder draußen. Ganz normal, auf dem Klo.", min=4.4, stamp="2 TAGEN", node=True),
    dict(scene="twist", say="Und das Krasse: Die sieben Jahre sind ein Mythos. Gefährlich wird's nur, wenn man ständig sehr viele schluckt.", min=5.4, stamp="FAKT", tplus=False, node=True, twist=True, shake=0.5),
    dict(scene="outro", say="Welches Szenario soll als Nächstes kommen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
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

def scene(rel, s, acid=0.0):
    bg = kr.vgrad((14, 20, 44), (6, 8, 20)); bg += kr.radial(540, 1000, 500, (60, 40, 120), 0.4)
    rgb, a = body(); bg = bg * (1 - a[..., None] * 0.6) + rgb
    if acid > 0:
        r = np.random.default_rng(int(rel * 10)); n = 80
        kr.splat(bg, 625 + r.normal(0, 30, n), 990 + r.normal(0, 25, n), np.array([0.6, 1.0, 0.3]) * acid * 0.8, 3)
    x, y = at(s)
    bg += kr.radial(x, y, 22, PINK, 2.2) + kr.radial(x, y, 60, PINK, 0.5)
    return bg

def gum_label(img, s, rel, txt=None):
    x, y = at(s)
    if txt: text_fx(img, (x + 60, y - 10), txt, F("Black", 28), fill=PINK, anchor="lm", tracking=2)

def sc_hook(rel, ln, i): return scene(rel, 0.03 * eo((rel - 1.5) / 2))
def ov_hook(img, rel, ln, i):
    lib.hook_text(img, rel, ln, "DU KAUGUMMI", "VERSCHLUCKST?")
    text_fx(img, (780, 760), "7 JAHRE?", F("Black", 56), fill=AMBER, glow=AMBER, glow_r=14, alpha=clamp((rel - 0.6) / 0.3))

def sc_speise(rel, ln, i): return scene(rel, MARK["magen"] * eio((rel - 0.3) / 2.6))
def ov_speise(img, rel, ln, i):
    lib.heads(img, rel, "SPEISERÖHRE", "AB IN DEN MAGEN", glow=PINK, sub="Schlucken dauert nur ein paar Sekunden")

def sc_magen(rel, ln, i):
    s = MARK["magen"] + 0.006 * math.sin(rel * 3)
    return scene(rel, s, acid=0.5 + 0.5 * math.sin(rel * 5) ** 2)
def ov_magen(img, rel, ln, i):
    lib.heads(img, rel, "MAGENSÄURE", "UNVERDAULICH", glow=(140, 255, 90), sub="die Kaumasse ist eine Art Kunststoff – Säure kriegt sie nicht klein")

def sc_darm(rel, ln, i): return scene(rel, MARK["magen"] + (0.8 - MARK["magen"]) * eio((rel - 0.4) / 3.5))
def ov_darm(img, rel, ln, i):
    lib.heads(img, rel, "VERDAUUNG", "EINFACH WEITER", glow=PINK, sub="der Darm schiebt ihn mit allem anderen weiter – wie ein Maiskorn")

def sc_raus(rel, ln, i): return scene(rel, 0.8 + 0.2 * eio((rel - 0.3) / 2.2))
def ov_raus(img, rel, ln, i):
    lib.heads(img, rel, "1 BIS 3 TAGE", "WIEDER DRAUSSEN", glow=CYAN, sub="ganz normal – auf dem Klo")
    if rel > 2.2: lib.paste_emoji(img, "🚽", 120, 820, 1250, alpha=clamp((rel - 2.2) / 0.3))

def sc_twist(rel, ln, i):
    bg = kr.vgrad((24, 10, 30), (8, 4, 14)); bg += kr.radial(540, 1000, 500, (200, 60, 120), 0.35); return bg
def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "DIE 7 JAHRE?", "MYTHOS!", glow=RED, big_col=RED, sub="nur wer ständig sehr viele schluckt, riskiert einen Darmverschluss", sub_t=1.3, size=150)
    d = ImageDraw.Draw(img, "RGBA")
    k = eo((rel - 0.6) / 0.6)
    text_fx(img, (500, 980), "7 JAHRE", F("Black", 150), fill=WHITE, alpha=k)
    if rel > 1.0:
        a = clamp((rel - 1.0) / 0.3); d.line([200, 1040, 800, 920], fill=RED + (int(255 * a),), width=18)
    text_fx(img, (500, 1180), "→ 1 bis 3 Tage", F("Black", 60), fill=CYAN, alpha=clamp((rel - 1.6) / 0.3))

def sc_outro(rel, ln, i): return scene(rel, 0.5 + 0.5 * math.sin(rel)) * 0.5
def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welches Szenario", "kommt als Nächstes?")

SCENES = dict(hook=sc_hook, speise=sc_speise, magen=sc_magen, darm=sc_darm, raus=sc_raus, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, speise=ov_speise, magen=ov_magen, darm=ov_darm, raus=ov_raus, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
