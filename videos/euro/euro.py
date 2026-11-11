"""FOLGENSCHWER #11 – Was wäre, wenn du jeden Tag 1 € zur Seite legst?"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(130.8, 164.8, 196.0), (146.8, 185.0, 220.0), (164.8, 207.7, 246.9), (174.6, 220.0, 261.6)]
SOURCES = "Beispiel: 30,42 €/Monat · 7 % p. a. (Welt-Aktien im Schnitt, nicht garantiert) · keine Anlageberatung"
GOLD = (255, 200, 70); GREEN = (110, 230, 140)

M, RM = 365 / 12, 0.07 / 12
def fv(years): n = years * 12; return M * ((1 + RM) ** n - 1) / RM if n > 0 else 0.0
def paid(years): return M * years * 12

SEGS = [
    dict(scene="hook", say="Jeden Tag ein Euro. Klingt nach nichts. Aber was wird daraus?", min=3.8, stamp="JETZT", nosub=True),
    dict(scene="j1", say="Nach einem Jahr: dreihundertfünfundsechzig Euro. Kaum der Rede wert.", min=4.4, stamp="1 JAHR", node=True, Y=1),
    dict(scene="j10", say="Nach zehn Jahren, angelegt mit sieben Prozent im Jahr: schon über fünftausend Euro.", min=4.8, stamp="10 JAHREN", node=True, Y=10),
    dict(scene="j30", say="Nach dreißig Jahren: über siebenunddreißigtausend Euro.", min=4.4, stamp="30 JAHREN", node=True, Y=30),
    dict(scene="j50", say="Nach fünfzig Jahren: über hundertfünfundsechzigtausend Euro. Eingezahlt hast du nur achtzehntausend.", min=5.2, stamp="50 JAHREN", node=True, Y=50),
    dict(scene="twist", say="Und das Krasse: Fast neunzig Prozent davon sind Zinseszinsen. Geld, das dein Geld verdient hat.", min=5.2, stamp="ZINSESZINS", tplus=False, node=True, twist=True, shake=0.5),
    dict(scene="outro", say="Welches Szenario soll als Nächstes kommen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]
PREV = {"j1": 0, "j10": 1, "j30": 10, "j50": 30}

def bg_money(rel):
    bg = kr.vgrad((10, 24, 22), (4, 10, 12)); bg += kr.radial(540, 1000, 600, (40, 120, 80), 0.35)
    r = np.random.default_rng(5); n = 120
    kr.splat(bg, r.uniform(0, W, n), (r.uniform(0, H, n) + rel * 40) % H, np.array([1.0, 0.8, 0.3]) * r.uniform(0.1, 0.5, n)[:, None], 2)
    return bg

def chart(img, years_now, a=1.0, x0=130, x1=900, y0=1290, y1=760, ymax=170000):
    d = ImageDraw.Draw(img, "RGBA")
    d.line([x0, y0, x1, y0], fill=(255, 255, 255, int(150 * a)), width=3); d.line([x0, y0, x0, y1], fill=(255, 255, 255, int(150 * a)), width=3)
    def X(y): return x0 + (x1 - x0) * y / 50
    def Y(v): return y0 - (y0 - y1) * v / ymax
    for yr in (0, 10, 30, 50): text_fx(img, (X(yr), y0 + 28), f"{yr} J.", F("Bold", 24), fill=(210, 215, 230), alpha=a)
    pts_v = [(X(t / 4), Y(fv(t / 4))) for t in range(0, int(years_now * 4) + 1)]
    pts_p = [(X(t / 4), Y(paid(t / 4))) for t in range(0, int(years_now * 4) + 1)]
    if len(pts_v) > 1:
        d.polygon(pts_v + pts_p[::-1], fill=GOLD + (int(70 * a),))
        d.line(pts_p, fill=(255, 255, 255, int(200 * a)), width=5)
        d.line(pts_v, fill=GOLD + (int(255 * a),), width=8, joint="curve")
        x, y = pts_v[-1]; d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=GOLD + (int(255 * a),))
    text_fx(img, (x0 + 20, y1 + 10), "— mit Zinsen", F("Bold", 26), fill=GOLD, anchor="lm", alpha=a)
    text_fx(img, (x0 + 20, y1 + 48), "— nur eingezahlt", F("Bold", 26), fill=WHITE, anchor="lm", alpha=a)

def coins(img, n, cx=500, base=1240, a=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(int(n)):
        y = base - k * 18
        d.ellipse([cx - 90, y - 26, cx + 90, y + 26], fill=(200, 150, 40, int(255 * a)), outline=(255, 220, 120, int(255 * a)), width=4)
    if n >= 1:
        y = base - (int(n) - 1) * 18
        d.ellipse([cx - 90, y - 26, cx + 90, y + 26], fill=(255, 200, 70, int(255 * a)), outline=(255, 240, 170, int(255 * a)), width=4)
        text_fx(img, (cx, y), "1 €", F("Black", 34), fill=(120, 80, 10), alpha=a, shadow=0)

def sc_hook(rel, ln, i): return bg_money(rel)
def ov_hook(img, rel, ln, i):
    lib.hook_text(img, rel, ln, "DU JEDEN TAG", "1 € SPARST?")
    coins(img, 1 + min(14, rel * 5), base=1300)

def make(key):
    Y = next(s["Y"] for s in SEGS if s["scene"] == key); Y0 = PREV[key]
    def sc(rel, ln, i): return bg_money(rel)
    def ov(img, rel, ln, i):
        k = eio((rel - 0.3) / 2.4); yrs = Y0 + (Y - Y0) * k
        v = fv(yrs) if key != "j1" else paid(yrs)
        text_fx(img, (500, 440), f"EINGEZAHLT: {kr.de(paid(yrs))} €", F("Black", 40), fill=CYAN, tracking=3)
        text_fx(img, (500, 548), f"{kr.de(v)} €", F("Black", 120), fill=GOLD, glow=GOLD, glow_r=18)
        if key == "j1": coins(img, 1 + 15 * k)
        else: chart(img, yrs)
    return sc, ov
sc_j1, ov_j1 = make("j1"); sc_j10, ov_j10 = make("j10"); sc_j30, ov_j30 = make("j30"); sc_j50, ov_j50 = make("j50")

def sc_twist(rel, ln, i): return bg_money(rel) * 1.1
def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "89 % ZINSESZINS", glow=GOLD, big_col=GOLD, sub="nur 11 % hast du selbst eingezahlt", sub_t=1.2)
    d = ImageDraw.Draw(img, "RGBA"); k = eio((rel - 0.7) / 1.2)
    cx, cy, r = 500, 1020, 240
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 230))
    d.pieslice([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * 0.89 * k, fill=GOLD + (255,))
    text_fx(img, (cx + 140, cy + 40), "Zinsen", F("Black", 34), fill=(90, 60, 10), shadow=0, alpha=k)
    text_fx(img, (cx - 40, cy - 170), "du", F("Black", 30), fill=(40, 50, 70), shadow=0, alpha=k)

def sc_outro(rel, ln, i): return bg_money(rel + 5) * 0.8
def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welches Szenario", "kommt als Nächstes?")

SCENES = dict(hook=sc_hook, j1=sc_j1, j10=sc_j10, j30=sc_j30, j50=sc_j50, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, j1=ov_j1, j10=ov_j10, j30=ov_j30, j50=ov_j50, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
