"""KETTENREAKTION #04 – Was wäre, wenn die Sonne ausgeht?"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 44.0
CHORDS = [(110.0, 130.8, 164.8), (98.0, 116.5, 146.8), (87.3, 110.0, 130.8), (82.4, 98.0, 123.5)]
SOURCES = "Quellen: NASA · Stevenson 1999 (Nature) · Temperaturen = Modell-Schätzungen"
ICE = (170, 225, 255)

SEGS = [
    dict(scene="hook", say="Die Sonne geht aus. Jetzt. Wie lange merken wir nichts?", min=3.6, stamp="0 SEK.", nosub=True, shake=0.8),
    dict(scene="licht", say="Acht Minuten lang: gar nichts. So lange braucht ihr letztes Licht bis zu uns.", min=4.6, stamp="8 MINUTEN", node=True),
    dict(scene="kalt", say="Nach einer Woche: im Schnitt minus achtzehn Grad. Pflanzen bekommen kein Licht mehr.", min=4.6, stamp="1 WOCHE", node=True),
    dict(scene="eis", say="Nach einem Jahr: minus siebzig Grad. Die Ozeane frieren zu – aber nur oben.", min=4.6, stamp="1 JAHR", node=True),
    dict(scene="ende", say="Nach Millionen Jahren: Nur die Wärme aus dem Erdinneren bleibt. Minus zweihundertvierzig Grad.", min=4.8, stamp="MIO. JAHRE", node=True),
    dict(scene="twist", say="Und das Krasse: Die Sonne stirbt wirklich. In etwa fünf Milliarden Jahren bläht sie sich zum Roten Riesen auf.", min=5.4, stamp="ZUKUNFT", tplus=False, node=True, twist=True, shake=0.6),
    dict(scene="outro", say="Was soll als Nächstes ausgehen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

def sun(bg, R, cx, cy, rel, k=1.0, col=(255, 170, 70), glow=1.0):
    if k <= 0.01: return
    s, a, _ = kr.sphere(R, lib.sun_tex(), spin=rel * 0.05, light=(0, 0, 1), terminator=2.0, atm=col, atm_k=1.6)
    kr.blit(bg, s * k, a * min(1, k * 1.5), cx, cy)
    bg += kr.radial(cx, cy, R * 1.8, col, 0.45 * k * glow) + kr.radial(cx, cy, R * 4, col, 0.1 * k * glow)

def sc_hook(rel, ln, i):
    bg = lib.space_bg(rel)
    k = 1 - eio((rel - 0.3) / 0.45)
    sun(bg, 250, 560, 1000, rel, k)
    if rel > 0.3:
        lib.ring(bg, 560, 1000, 250 + (rel - 0.3) * 700, 16, (255, 190, 120), max(0, 1 - (rel - 0.3) / 1.2))
    er, ea, _ = lib.earth(110, spin=rel * 0.2, light=(0.6, -0.4, 0.7 * k + 0.05), clouds=True)
    kr.blit(bg, er * (0.3 + 0.7 * k), ea, 200, 1360)
    return bg

def ov_hook(img, rel, ln, i): lib.hook_text(img, rel, ln, "DIE SONNE", "AUSGEHT?")

def sc_licht(rel, ln, i):
    bg = lib.space_bg(rel * 0.5)
    # dunkler Sonnenrest links, Lichtfront wandert zur Erde rechts
    front = 120 + (820 - 120) * clamp(rel / (ln - 0.3))
    xs = np.arange(W, dtype=np.float32)[None, :]; yy = np.arange(H, dtype=np.float32)[:, None]
    band = (xs > 120) & (xs < front) & (np.abs(yy - 1000) < 70 * (1 + (xs - 120) / 900))
    bg += (band * 0.10)[..., None] * np.array([1.0, 0.8, 0.5], np.float32)
    bg += (np.exp(-((xs - front) / 10) ** 2) * (np.abs(yy - 1000) < 140) * 1.2)[..., None] * np.array([1.0, 0.85, 0.6], np.float32)
    er, ea, _ = lib.earth(110, spin=rel * 0.2, light=(-0.9, -0.2, 0.4))
    kr.blit(bg, er, ea, 880, 1000)
    sun(bg, 70, 120, 1000, rel, 0.06, (255, 120, 60))
    return bg

def ov_licht(img, rel, ln, i):
    lib.heads(img, rel, "DAS LETZTE LICHT", None, glow=AMBER)
    left = 500 * (1 - clamp(rel / (ln - 0.3)))
    m, s = int(left // 60), int(left % 60)
    text_fx(img, (500, 560), f"{m}:{s:02d}", F("Black", 150), fill=AMBER, glow=ORANGE, glow_r=22)
    text_fx(img, (500, 665), "Minuten, bis es auf der Erde dunkel wird", F("SemiBold", 31), fill=(215, 220, 235))
    text_fx(img, (500, 1230), "150 Mio. km · Lichtgeschwindigkeit", F("Bold", 26), fill=(200, 205, 225), tracking=2)

def thermo(img, temp, x=880, y0=760, y1=1240, tmin=-250, tmax=20):
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x - 20, y0, x + 20, y1], 20, fill=(20, 26, 50, 220), outline=(255, 255, 255, 160), width=3)
    f = (temp - tmin) / (tmax - tmin); ty = y1 - (y1 - y0) * clamp(f)
    d.rounded_rectangle([x - 10, ty, x + 10, y1 - 6], 10, fill=ICE + (255,))
    d.ellipse([x - 34, y1 - 20, x + 34, y1 + 48], fill=ICE + (255,), outline=(255, 255, 255, 180), width=3)

def sc_kalt(rel, ln, i):
    bg = lib.space_bg(rel * 0.4)
    fz = eio(rel / 3.5) * 0.45
    er, ea, _ = lib.earth(300, spin=1.5 + rel * 0.08, light=(0.2, -0.3, 1.0), frozen=fz)
    kr.blit(bg, er * 0.18, ea, 480, 1010)   # nur Restlicht der Sterne
    return bg

def ov_kalt(img, rel, ln, i):
    t = 15 - 33 * eo(rel / 3.0)
    lib.heads(img, rel, "DIE ERDE KÜHLT AUS", f"{t:.0f} °C".replace("-", "−"), glow=CYAN, big_col=ICE, sub="Durchschnitt – Pflanzen stoppen die Photosynthese", size=130, t0=0.2)
    thermo(img, t)

def sc_eis(rel, ln, i):
    bg = kr.vgrad((4, 6, 14), (2, 4, 10)); bg += lib.stars(rel * 2, 0, 0.6)
    top = 900; thick = 40 + 220 * eio(rel / 3.5)
    yy = np.arange(H, dtype=np.float32)[:, None]; xs = np.arange(W, dtype=np.float32)[None, :]
    ice = (yy > top) & (yy < top + thick + 12 * np.sin(xs * 0.02))
    water = yy >= top + thick + 12 * np.sin(xs * 0.02)
    bg = np.where(water[..., None], kr.vgrad((10, 40, 80), (2, 8, 20)), bg)
    ic = kr.vgrad((200, 230, 250), (120, 170, 210))
    n = lib.ridge(77)
    bg = np.where(ice[..., None], ic * (0.85 + 0.15 * n[None, :, None]), bg).astype(np.float32)
    bg += kr.radial(540, 1900, 400, (255, 120, 40), 0.5 + 0.1 * math.sin(rel * 3))
    r = np.random.default_rng(3); m = 150
    kr.splat(bg, r.uniform(0, W, m) + 10 * np.sin(rel + r.uniform(0, 6, m)), 1900 - ((r.uniform(0, 700, m) + rel * 80) % 700), np.array([0.3, 0.5, 0.7]) * 0.5, 2)
    return bg

def ov_eis(img, rel, ln, i):
    t = -18 - 55 * eo(rel / 3.0)
    lib.heads(img, rel, "DIE OZEANE FRIEREN ZU", f"{t:.0f} °C".replace("-", "−"), glow=CYAN, big_col=ICE, sub="das Eis isoliert: darunter bleibt das Wasser flüssig", size=130, t0=0.2)
    text_fx(img, (120, 870), "EIS", F("Black", 34), fill=WHITE, anchor="lm", tracking=4)
    text_fx(img, (120, 1250), "FLÜSSIGES WASSER", F("Black", 34), fill=CYAN, anchor="lm", tracking=4, alpha=clamp((rel - 0.8) / 0.3))

def sc_ende(rel, ln, i):
    bg = lib.space_bg(rel * 0.3, tint=(30, 30, 60))
    er, ea, _ = lib.earth(300, spin=2.2 + rel * 0.02, light=(0.2, -0.3, 1.0), frozen=1.0, night=False)
    kr.blit(bg, er * 0.16, ea, 540, 1010)
    bg += kr.radial(540, 1010, 300, (255, 90, 40), 0.06 + 0.03 * math.sin(rel * 2))
    return bg

def ov_ende(img, rel, ln, i):
    t = -73 - 167 * eo(rel / 3.2)
    lib.heads(img, rel, "NUR DAS ERDINNERE WÄRMT", f"{t:.0f} °C".replace("-", "−"), glow=CYAN, big_col=ICE, sub="Schätzung – Kälterekord auf der Erde heute: −89 °C", size=130, t0=0.2)
    thermo(img, t)

def sc_twist(rel, ln, i):
    bg = lib.space_bg(rel)
    R = 80 + 520 * eio((rel - 0.4) / 3.5)
    sun(bg, R, 540, 1250, rel, 0.55, (230, 60, 40), 0.5)
    for k, (dist, rp) in enumerate(((180, 8), (260, 12), (350, 13), (470, 10))):
        a = rel * (0.9 - k * 0.15) + k * 1.7
        x = 540 + math.cos(a) * dist; y = 1250 + math.sin(a) * dist * 0.35
        if dist > R * 1.02:
            bg += kr.radial(x, y, rp, (180, 200, 255), 1.6 if k != 2 else 2.2)
    return bg

def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "IN 5 MRD. JAHREN", glow=RED, big_col=WHITE, sub="wird die Sonne zum Roten Riesen – Merkur und Venus verglühen", sub_t=1.3)

def sc_outro(rel, ln, i):
    bg = lib.space_bg(rel + 20)
    sun(bg, 300, 540, 1950, rel, 0.7, glow=0.6)
    return bg

def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Was soll als Nächstes", "ausgehen?")

SCENES = dict(hook=sc_hook, licht=sc_licht, kalt=sc_kalt, eis=sc_eis, ende=sc_ende, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, licht=ov_licht, kalt=ov_kalt, eis=ov_eis, ende=ov_ende, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
