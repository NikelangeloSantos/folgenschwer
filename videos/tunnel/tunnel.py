"""FOLGENSCHWER #07 – Was wäre, wenn du durch ein Loch quer durch die Erde fällst?"""
import math, os, sys
from functools import lru_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(110.0, 138.6, 164.8), (98.0, 123.5, 146.8), (116.5, 146.8, 174.6), (130.8, 164.8, 196.0)]
SOURCES = "Annahmen: kein Luftwiderstand, keine Hitze · Klotz 2015 (Am. J. Phys.) · Kola-Bohrloch 1989"

SEGS = [
    dict(scene="hook", say="Ein Loch quer durch die Erde. Du springst rein. Wo kommst du raus?", min=3.8, stamp="JETZT", nosub=True, shake=0.5),
    dict(scene="minute", say="Nach einer Minute: über zweitausend Kilometer pro Stunde. Schneller als der Schall.", min=4.6, stamp="1 MINUTE", node=True),
    dict(scene="mitte", say="Nach neunzehn Minuten: der Erdmittelpunkt. Du bist schwerelos – und schneller als achtundzwanzigtausend Kilometer pro Stunde.", min=5.2, stamp="19 MINUTEN", node=True),
    dict(scene="unten", say="Nach achtunddreißig Minuten: Du kommst im Pazifik bei Neuseeland raus. Halt dich fest!", min=4.8, stamp="38 MINUTEN", node=True),
    dict(scene="zurueck", say="Sonst fällst du zurück nach Deutschland. Und wieder hin. Für immer.", min=4.2, stamp="76 MINUTEN", node=True),
    dict(scene="twist", say="Und das Krasse: Das tiefste Loch der Welt ist nur zwölf Kilometer tief. Nicht mal ein Prozent des Weges.", min=5.2, stamp="REALITÄT", tplus=False, node=True, twist=True, shake=0.6),
    dict(scene="outro", say="Welches Szenario soll als Nächstes kommen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

CX, CY, R = 540, 1050, 270

@lru_cache(None)
def section():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2) / R
    n = kr.fnoise(W, H, 5, seed=17, base=12)
    layers = [(1.00, (90, 70, 50)), (0.985, (190, 60, 30)), (0.55, (255, 140, 40)), (0.19, (255, 235, 160))]
    img = np.zeros((H, W, 3), np.float32); a = np.zeros((H, W), np.float32)
    for r_, col in layers:
        m = d <= r_
        img[m] = np.array(col, np.float32) / 255 * (0.85 + 0.25 * n[m, None]) * (0.75 + 0.45 * (1 - d[m, None] / r_) ** 0.5)
        a[m] = 1
    edge = np.clip((1 - d) * R + 0.5, 0, 1); a = a * edge
    return img * a[..., None], a

def scene(rel, pos, trail=0.0, glow=1.0):
    """pos: 0 = Oberfläche oben, 1 = Mitte, 2 = Oberfläche unten."""
    bg = lib.space_bg(rel)
    img, a = section()
    bg = bg * (1 - a[..., None]) + img * glow
    bg += kr.radial(CX, CY, R * 0.4, (255, 220, 150), 0.5)
    # Tunnel
    bg[int(CY - R - 30):int(CY + R + 30), CX - 7:CX + 7] *= 0.15
    bg[int(CY - R - 30):int(CY + R + 30), CX - 2:CX + 2] += np.array([0.3, 0.8, 1.0], np.float32) * 0.5
    y = CY - R + pos * R
    if trail > 0:
        for k in range(14):
            yt = y - k * trail * 8
            bg += kr.radial(CX, yt, 10, (120, 220, 255), 0.5 * (1 - k / 14))
    bg += kr.radial(CX, y, 26, (120, 230, 255), 2.0) + kr.radial(CX, y, 70, (80, 180, 255), 0.5)
    return bg

def labels(img, rel):
    text_fx(img, (CX + 40, CY - R - 20), "DEUTSCHLAND", F("Black", 28), fill=WHITE, anchor="lm", tracking=2)
    text_fx(img, (CX - 40, CY + R + 22), "PAZIFIK BEI NEUSEELAND", F("Black", 28), fill=WHITE, anchor="rm", tracking=2)

def sc_hook(rel, ln, i): return scene(rel, 0.02 + 0.05 * eo((rel - 0.4) / 3), 0.3)
def ov_hook(img, rel, ln, i):
    lib.hook_text(img, rel, ln, "DU DURCH DIE", "ERDE FÄLLST?")
    labels(img, rel)

def sc_minute(rel, ln, i): return scene(rel, 0.08 + 0.12 * eo(rel / ln), 0.6)
def ov_minute(img, rel, ln, i):
    v = 2119 * clamp(0.6 + rel / 2.5)
    lib.heads(img, rel, "FREIER FALL", f"{kr.de(v)} KM/H", glow=CYAN, sub="schneller als der Schall (1.235 km/h)", t0=0.2, size=120)
    labels(img, rel)

def sc_mitte(rel, ln, i): return scene(rel, 0.2 + 0.8 * eio(rel / 2.5), 1.2)
def ov_mitte(img, rel, ln, i):
    lib.heads(img, rel, "ERDMITTELPUNKT", "SCHWERELOS", glow=AMBER, sub="über 28.000 km/h · im Erdkern über 5.000 °C")
    labels(img, rel)

def sc_unten(rel, ln, i):
    p = 1.0 + 1.0 * eo(rel / 2.5)
    return scene(rel, min(p, 1.98), 0.8 * (1 - eo(rel / 2.5)))
def ov_unten(img, rel, ln, i):
    lib.heads(img, rel, "DU KOMMST RAUS", "BEI NEUSEELAND", glow=CYAN, sub="Geschwindigkeit dort: null – genau jetzt festhalten!")
    labels(img, rel)
    if rel > 2.4: lib.paste_emoji(img, "🙌", 90, CX + 120, CY + R - 10, alpha=clamp((rel - 2.4) / 0.3))

def sc_zurueck(rel, ln, i):
    ph = rel * 2.2
    return scene(rel, 1 + math.cos(ph), 0.5)
def ov_zurueck(img, rel, ln, i):
    lib.heads(img, rel, "NICHT FESTGEHALTEN?", "HIN UND HER", glow=ORANGE, sub="ohne Reibung pendelst du ewig – alle 76 Minuten einmal hin und zurück")
    labels(img, rel)

def sc_twist(rel, ln, i):
    bg = kr.vgrad((10, 12, 24), (4, 6, 14))
    return bg
def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "NUR 12 KM TIEF", glow=ORANGE, big_col=ORANGE, sub="Kola-Bohrloch, Russland – das tiefste Loch der Welt", sub_t=1.2)
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1, y = 120, 900, 900
    d.rounded_rectangle([x0, y - 34, x1, y + 34], 34, fill=(30, 36, 70, 255), outline=(255, 255, 255, 120), width=3)
    k = eo((rel - 0.9) / 1.2)
    w = max(10, (x1 - x0) * 0.0019 * k)
    d.rounded_rectangle([x0, y - 34, x0 + w + 20, y + 34], 34, fill=ORANGE + (255,))
    text_fx(img, (x0, y + 80), "OBERFLÄCHE", F("Bold", 26), fill=WHITE, anchor="lm")
    text_fx(img, (x1, y + 80), "ERDMITTELPUNKT · 6.371 km", F("Bold", 26), fill=WHITE, anchor="rm")
    text_fx(img, (x0 + 40, y - 80), "← 0,2 % geschafft", F("Black", 40), fill=ORANGE, anchor="lm", alpha=clamp((rel - 1.6) / 0.3))

def sc_outro(rel, ln, i): return scene(rel + 5, 1 + math.cos(rel * 2.2), 0.4) * 0.6
def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welches Szenario", "kommt als Nächstes?")

SCENES = dict(hook=sc_hook, minute=sc_minute, mitte=sc_mitte, unten=sc_unten, zurueck=sc_zurueck, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, minute=ov_minute, mitte=ov_mitte, unten=ov_unten, zurueck=ov_zurueck, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
