"""KETTENREAKTION #03 – Was wäre, wenn alle Insekten verschwinden?"""
import math, os, sys
from functools import lru_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(130.8, 155.6, 196.0), (116.5, 146.8, 174.6), (103.8, 130.8, 155.6), (98.0, 123.5, 146.8)]
SOURCES = "Quellen: Klein et al. 2007 (Proc. R. Soc. B) · Nyffeler et al. 2018 · Hallmann et al. 2017 (PLOS ONE)"
GREEN = (120, 230, 120)

SEGS = [
    dict(scene="hook", say="Alle Insekten sind weg. Jedes einzelne. Was passiert jetzt?", min=3.6, stamp="0 SEK.", nosub=True),
    dict(scene="voegel", say="Nach einer Woche: Vögel hungern. Sie fressen sonst bis zu fünfhundert Millionen Tonnen Insekten im Jahr.", min=4.8, stamp="1 WOCHE", node=True),
    dict(scene="mist", say="Nach einem Monat: Mist und tote Tiere verrotten kaum noch. Die Müllabfuhr der Natur fehlt.", min=4.6, stamp="1 MONAT", node=True),
    dict(scene="bluete", say="Im Frühling: kaum Obst. Drei Viertel unserer wichtigsten Nutzpflanzen brauchen Bestäuber.", min=4.8, stamp="6 MONATE", node=True),
    dict(scene="schoko", say="Nach einem Jahr: Schokolade wird knapp. Kakao wird fast nur von winzigen Mücken bestäubt.", min=4.8, stamp="1 JAHR", node=True),
    dict(scene="twist", say="Und das Krasse: Es passiert schon. In deutschen Schutzgebieten schrumpfte die Insektenmasse in siebenundzwanzig Jahren um drei Viertel.", min=5.4, stamp="HEUTE", node=True, twist=True, shake=0.6),
    dict(scene="outro", say="Welches Szenario soll als Nächstes kommen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

@lru_cache(None)
def meadow_layers():
    """Wiese mit Blumen: farbig und entsättigt (RGB premultiplied + Alpha)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = np.random.default_rng(11)
    for k in range(1600):
        x = r.uniform(-20, W + 20); base = r.uniform(1150, 1560); h = r.uniform(60, 220) * (base - 1000) / 500
        bend = r.uniform(-30, 30); g = int(r.uniform(60, 130))
        d.line([x, base, x + bend, base - h], fill=(20, g, 40, 255), width=int(r.uniform(2, 5)))
    cols = [(255, 90, 120), (255, 200, 60), (190, 120, 255), (255, 255, 255), (255, 140, 60)]
    for k in range(240):
        x = r.uniform(0, W); y = r.uniform(1100, 1500); s = r.uniform(8, 20) * (y - 950) / 450
        c = cols[k % 5]
        for a in range(6):
            ang = a * math.pi / 3; px = x + math.cos(ang) * s; py = y + math.sin(ang) * s * 0.7
            d.ellipse([px - s * 0.7, py - s * 0.5, px + s * 0.7, py + s * 0.5], fill=c + (255,))
        d.ellipse([x - s * 0.5, y - s * 0.4, x + s * 0.5, y + s * 0.4], fill=(255, 220, 80, 255))
    d.rectangle([0, 1560, W, H], fill=(10, 30, 16, 255))
    a = np.asarray(im, np.float32) / 255
    rgb = a[..., :3] * a[..., 3:]; al = a[..., 3]
    grey = rgb.mean(-1, keepdims=True) * np.array([0.8, 0.75, 0.6], np.float32)
    return rgb, grey, al

def meadow(bg, wither=0.0, light=1.0):
    rgb, grey, al = meadow_layers()
    col = rgb * (1 - wither) + grey * wither
    return bg * (1 - al[..., None]) + col * light

def dusk(rel):
    bg = kr.vgrad((8, 10, 34), (120, 60, 70), gamma=1.6)
    bg += kr.radial(760, 1180, 300, (255, 150, 90), 0.45)
    bg += lib.stars(rel * 3, 0, 0.6)
    return bg

_r = np.random.default_rng(5); NI = 1800
I_x = _r.uniform(0, W, NI); I_y = _r.uniform(700, 1500, NI); I_ph = _r.uniform(0, 6.3, NI); I_sp = _r.uniform(0.5, 2, NI)

def swarm(bg, rel, alive):
    x = I_x + 30 * np.sin(rel * I_sp + I_ph); y = I_y + 20 * np.cos(rel * I_sp * 1.3 + I_ph)
    tw = 0.5 + 0.5 * np.sin(rel * 8 * I_sp + I_ph)
    kr.splat(bg, x, y, np.array([0.9, 1.0, 0.3]) * (tw * alive)[:, None] * 2.6, 4)

def sc_hook(rel, ln, i):
    bg = dusk(rel)
    k = clamp((rel - 0.35) / 1.4)
    alive = np.clip(1 - k * 2 + _r.random(NI) * 0, 0, 1) * (I_ph / 6.3 > k)
    swarm(bg, rel, alive.astype(np.float32))
    if 0.35 < rel < 2.0:
        gone = (I_ph / 6.3 <= k) & (I_ph / 6.3 > k - 0.08)
        kr.splat(bg, I_x[gone], I_y[gone], np.array([1.0, 1.0, 1.0]) * 2.0, 3)
    return meadow(bg, 0.0, 0.4)

def ov_hook(img, rel, ln, i): lib.hook_text(img, rel, ln, "ALLE INSEKTEN", "VERSCHWINDEN?")

def sc_voegel(rel, ln, i):
    bg = kr.vgrad((60, 110, 170), (200, 210, 190), gamma=1.1)
    return meadow(bg, 0.15, 0.9)

def ov_voegel(img, rel, ln, i):
    lib.heads(img, rel, "VÖGEL HUNGERN", "500 MIO. TONNEN", glow=AMBER, sub="Insekten fressen Vögel sonst pro Jahr")
    d = ImageDraw.Draw(img, "RGBA"); r = np.random.default_rng(9)
    for k in range(14):
        x0 = r.uniform(-200, 600); y0 = r.uniform(760, 1050); s = r.uniform(18, 34)
        x = x0 + rel * r.uniform(150, 260) * 1.5; y = y0 - rel * 30 + 8 * math.sin(rel * 6 + k)
        flap = 0.5 * math.sin(rel * 10 + k)
        d.line([x - s, y - s * flap, x, y + s * 0.2, x + s, y - s * flap], fill=(15, 18, 30, 255), width=5, joint="curve")
    lib.paste_emoji(img, "🪺", 150, 790, 1180)
    text_fx(img, (790, 1275), "LEER", F("Black", 32), fill=RED, tracking=4, alpha=clamp((rel - 1.2) / 0.3))

def sc_mist(rel, ln, i):
    bg = kr.vgrad((90, 120, 150), (170, 160, 130), gamma=1.0)
    bg = meadow(bg, 0.45, 0.8)
    return bg

def ov_mist(img, rel, ln, i):
    lib.heads(img, rel, "DIE MÜLLABFUHR FEHLT", "NICHTS RÄUMT AUF", glow=AMBER, sub="Käfer, Fliegen und Maden zersetzen sonst Mist und Kadaver")
    r = np.random.default_rng(4); n = int(4 + 22 * eo(rel / 3.5))
    for k in range(n):
        lib.paste_emoji(img, "🍂" if k % 3 else "💩" if k % 6 == 0 else "🍂", r.uniform(70, 110), r.uniform(150, 900), 1240 - (k // 6) * 40 + r.uniform(-20, 20), angle=r.uniform(-40, 40))
    d = ImageDraw.Draw(img, "RGBA")
    lib.paste_emoji(img, "🪲", 120, 860, 860, alpha=0.9); lib.cross(d, 860, 860, 60, clamp((rel - 0.8) / 0.3))

def sc_bluete(rel, ln, i):
    k = eio((rel - 0.6) / 2.5)
    bg = kr.vgrad((70, 130, 200), (210, 220, 200), gamma=1.0)
    bg = bg * (1 - 0.35 * k) + 0.35 * k * bg.mean(-1, keepdims=True)
    return meadow(bg, k, 1.0)

def ov_bluete(img, rel, ln, i):
    lib.heads(img, rel, "OBST & GEMÜSE", "75 % DER NUTZPFLANZEN", glow=GREEN, sub="brauchen Bestäuber – zumindest teilweise")
    d = ImageDraw.Draw(img, "RGBA")
    for k, ch in enumerate("🍎🍓🍒🥒🍉"):
        x = 160 + k * 170; y = 820; a = clamp((rel - 0.3 - k * 0.12) / 0.25)
        if a <= 0: continue
        lib.paste_emoji(img, ch, 120 * (0.6 + 0.4 * bo(a)), x, y, alpha=a)
        lib.cross(d, x, y, 50, clamp((rel - 1.5 - k * 0.15) / 0.25), 9)

def sc_schoko(rel, ln, i):
    bg = kr.vgrad((40, 20, 14), (12, 6, 4)); bg += kr.radial(540, 950, 520, (160, 80, 40), 0.7)
    r = np.random.default_rng(2); n = 300
    kr.splat(bg, r.uniform(0, W, n), (r.uniform(0, H, n) + rel * 60) % H, np.array([0.5, 0.3, 0.15]) * r.uniform(0.2, 1, n)[:, None], 2)
    return bg

def ov_schoko(img, rel, ln, i):
    lib.heads(img, rel, "UND DANN:", "SCHOKOLADE WIRD KNAPP", glow=ORANGE, sub="Kakaoblüten werden fast nur von winzigen Gnitzen bestäubt")
    k = eo((rel - 1.2) / 0.6)
    lib.paste_emoji(img, "🍫", 330, 500 - 40 * k, 1010, angle=8 * k)
    if k > 0:
        d = ImageDraw.Draw(img, "RGBA")
        d.line([520, 860, 480, 950, 540, 1020, 490, 1100, 530, 1170], fill=(20, 10, 6, int(255 * k)), width=10)

def sc_twist(rel, ln, i):
    bg = kr.vgrad((10, 14, 30), (4, 6, 14)); bg += kr.radial(540, 1000, 600, (40, 90, 60), 0.5)
    return bg

def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "−76 %", glow=RED, big_col=RED, sub="Fluginsekten-Biomasse in deutschen Schutzgebieten, 1989–2016", sub_t=1.3, size=140)
    d = ImageDraw.Draw(img, "RGBA")
    y0 = 1260; hmax = 440; bw = 220
    k = eio((rel - 0.8) / 1.8)
    h1 = hmax; h2 = hmax * (1 - 0.76 * k)
    d.rounded_rectangle([200, y0 - h1, 200 + bw, y0], 18, fill=GREEN + (230,))
    d.rounded_rectangle([580, y0 - h2, 580 + bw, y0], 18, fill=RED + (230,))
    text_fx(img, (310, y0 - h1 + 40), "100 %", F("Black", 46), fill=(10, 30, 16), shadow=0)
    text_fx(img, (690, y0 - h2 - 34), f"{100 - 76 * k:.0f} %", F("Black", 46), fill=WHITE)
    text_fx(img, (310, y0 + 38), "1989", F("Black", 36), fill=WHITE); text_fx(img, (690, y0 + 38), "2016", F("Black", 36), fill=WHITE)
    # Insekten-Glyphen fallen weg
    r = np.random.default_rng(6)
    for k2 in range(10):
        if (k2 / 10) > 1 - 0.76 * k: continue
        lib.paste_emoji(img, "🐝" if k2 % 2 else "🦋", 54, 640 + (k2 % 3) * 55, y0 - 40 - (k2 // 3) * 60)

def sc_outro(rel, ln, i):
    bg = dusk(rel + 5)
    return meadow(bg, 0.6, 0.6)

def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welches Szenario", "kommt als Nächstes?")

SCENES = dict(hook=sc_hook, voegel=sc_voegel, mist=sc_mist, bluete=sc_bluete, schoko=sc_schoko, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, voegel=ov_voegel, mist=ov_mist, bluete=ov_bluete, schoko=ov_schoko, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
