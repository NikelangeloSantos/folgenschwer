"""FOLGENSCHWER #10 – Was wäre, wenn du nie wieder schläfst?"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(110.0, 130.8, 164.8), (103.8, 123.5, 155.6), (98.0, 116.5, 146.8), (92.5, 110.0, 138.6)]
SOURCES = "Quellen: Dawson & Reid 1997 (Nature) · Guinness World Records · Schlafforschung"
VIOLET = (190, 140, 255)

SEGS = [
    dict(scene="hook", say="Du schläfst nie wieder. Keine Minute. Was macht das mit dir?", min=3.8, stamp="JETZT", nosub=True),
    dict(scene="h17", say="Nach siebzehn Stunden wach: Du reagierst wie mit einem halben Promille im Blut.", min=4.6, stamp="17 STUNDEN", node=True),
    dict(scene="h24", say="Nach vierundzwanzig Stunden: wie mit einem Promille. Fahruntauglich.", min=4.4, stamp="24 STUNDEN", node=True),
    dict(scene="d3", say="Nach drei Tagen: Du siehst Dinge, die nicht da sind. Halluzinationen.", min=4.6, stamp="3 TAGEN", node=True, shake=0.3),
    dict(scene="d11", say="Nach elf Tagen: Weltrekord. So lange blieb Randy Gardner neunzehnhundertvierundsechzig wach.", min=5.0, stamp="11 TAGEN", node=True),
    dict(scene="twist", say="Und das Krasse: Solche Rekorde nimmt Guinness heute nicht mehr an. Viel zu gefährlich.", min=5.0, stamp="FAKT", tplus=False, node=True, twist=True, shake=0.5),
    dict(scene="outro", say="Welches Szenario soll als Nächstes kommen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

def room(rel, dark=1.0, warp=0.0):
    bg = kr.vgrad((14, 16, 40), (4, 5, 14))
    bg += kr.radial(840, 760, 220, (120, 150, 230), 0.25)          # Fenster-Mondlicht
    bg += lib.stars(rel * 2, 0, 0.25)
    if warp > 0:
        yy, xx = np.ogrid[0:H, 0:W]
        w = (np.sin(xx / 60 + rel * 3) * np.cos(yy / 80 - rel * 2)) * warp
        bg += w[..., None] * np.array([0.5, 0.2, 0.7], np.float32) * 0.5
    return bg * dark

def clock(img, rel, speed, cx=500, cy=1010, r=230, a=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], outline=(255, 255, 255, int(70 * a)), width=4)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 14, 30, int(200 * a)), outline=CYAN + (int(220 * a),), width=6)
    for k in range(12):
        an = k * math.pi / 6; r1 = r - 18; r2 = r - (46 if k % 3 == 0 else 32)
        d.line([cx + r1 * math.sin(an), cy - r1 * math.cos(an), cx + r2 * math.sin(an), cy - r2 * math.cos(an)], fill=(255, 255, 255, int(220 * a)), width=7 if k % 3 == 0 else 4)
    hm = rel * speed
    for ang, ln, wd, col in ((hm / 12 * 2 * math.pi, r * 0.5, 12, WHITE), (hm * 2 * math.pi, r * 0.78, 8, ORANGE)):
        d.line([cx, cy, cx + ln * math.sin(ang), cy - ln * math.cos(ang)], fill=col + (int(255 * a),), width=wd)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=ORANGE + (int(255 * a),))

def battery(img, level, x=820, y=780, a=1.0):
    d = ImageDraw.Draw(img, "RGBA"); w, h = 90, 170
    d.rounded_rectangle([x - w / 2, y, x + w / 2, y + h], 16, outline=(255, 255, 255, int(220 * a)), width=5)
    d.rectangle([x - 18, y - 14, x + 18, y], fill=(255, 255, 255, int(220 * a)))
    col = (110, 230, 120) if level > 0.5 else AMBER if level > 0.25 else RED
    fh = (h - 16) * clamp(level)
    d.rounded_rectangle([x - w / 2 + 8, y + h - 8 - fh, x + w / 2 - 8, y + h - 8], 10, fill=col + (int(255 * a),))
    text_fx(img, (x, y + h + 36), f"{level * 100:.0f} %", F("Black", 34), fill=col, alpha=a)

def sc_hook(rel, ln, i): return room(rel)
def ov_hook(img, rel, ln, i):
    lib.hook_text(img, rel, ln, "DU NIE WIEDER", "SCHLÄFST?")
    clock(img, rel, 6, cy=1060, r=200)

def sc_h17(rel, ln, i): return room(rel)
def ov_h17(img, rel, ln, i):
    lib.heads(img, rel, "REAKTION WIE MIT", "0,5 PROMILLE", glow=AMBER, sub="Forscher verglichen Wachsein mit Alkohol im Blut")
    clock(img, rel, 3, cx=430); battery(img, 0.6 - 0.1 * eo(rel / 3))
    if rel > 1.2: lib.paste_emoji(img, "🍺", 100, 820, 1120, alpha=clamp((rel - 1.2) / 0.3))

def sc_h24(rel, ln, i): return room(rel, 0.9)
def ov_h24(img, rel, ln, i):
    lib.heads(img, rel, "VIERUNDZWANZIG STUNDEN", "1 PROMILLE", glow=ORANGE, sub="so solltest du nicht mehr Auto fahren")
    clock(img, rel, 3, cx=430); battery(img, 0.4 - 0.12 * eo(rel / 3))
    if rel > 1.2: lib.paste_emoji(img, "🍻", 110, 820, 1120, alpha=clamp((rel - 1.2) / 0.3))

def sc_d3(rel, ln, i): return room(rel, 0.9, warp=0.4 + 0.4 * math.sin(rel * 2) ** 2)
def ov_d3(img, rel, ln, i):
    lib.heads(img, rel, "DEIN GEHIRN SPINNT", "HALLUZINATIONEN", glow=VIOLET, sub="Schatten bewegen sich, Muster wabern, Gedanken reißen ab")
    clock(img, rel, 5, cx=430, a=0.7 + 0.3 * math.sin(rel * 7) ** 2); battery(img, 0.18)
    for k in range(3):
        a = clamp(math.sin(rel * 1.7 + k * 2.1)) * 0.8
        lib.paste_emoji(img, "👁️", 70, 230 + k * 300, 1260 - 40 * k, alpha=a)

def sc_d11(rel, ln, i): return room(rel, 0.95)
def ov_d11(img, rel, ln, i):
    lib.heads(img, rel, "WELTREKORD 1964", "264 STUNDEN WACH", glow=AMBER, sub="Randy Gardner, 17 Jahre alt – danach schlief er 14 Stunden am Stück")
    clock(img, rel, 4, cx=430); battery(img, 0.05)
    if rel > 1.4: lib.paste_emoji(img, "🏆", 110, 820, 1120, alpha=clamp((rel - 1.4) / 0.3))

def sc_twist(rel, ln, i):
    bg = kr.vgrad((30, 8, 12), (10, 3, 6)); bg += kr.radial(540, 1000, 500, (200, 40, 40), 0.35); return bg
def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "ZU GEFÄHRLICH", glow=RED, big_col=RED, sub="Guinness nimmt Schlafentzug-Rekorde nicht mehr an", sub_t=1.2, size=120)
    k = eo((rel - 0.8) / 0.5)
    lib.paste_emoji(img, "⛔", 260 * (0.7 + 0.3 * bo(k)), 500, 1010, alpha=k)

def sc_outro(rel, ln, i): return room(rel + 3, 0.7)
def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welches Szenario", "kommt als Nächstes?")

SCENES = dict(hook=sc_hook, h17=sc_h17, h24=sc_h24, d3=sc_d3, d11=sc_d11, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, h17=ov_h17, h24=ov_h24, d3=ov_d3, d11=ov_d11, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
