"""FOLGENSCHWER #12 (Muster mit neuem Hook) – Was wäre, wenn es ab morgen keine Gesetze mehr gäbe?

Neue Hook-Regeln (aus der YouTube-Auswertung von #10):
- Stimme startet mit der krassesten Folge, nicht mit der Frage (≤ 3 s).
- Frame 0 ist schon in Bewegung: Push-in, Blaulicht geht aus, Feuerschein, Blitz.
- Im Hook nur 2–3 große Wörter, kein „WAS WÄRE, WENN“-Kicker.
- Outro-Frage passt zum Thema (mehr Kommentare).
"""
import math, os, sys
from functools import lru_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import Image, ImageDraw
import kr, lib
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 42.0
CHORDS = [(110.0, 130.8, 164.8), (98.0, 116.5, 146.8), (103.8, 123.5, 155.6), (87.3, 110.0, 130.8)]
SOURCES = "Beispiele: Polizeistreik Montreal 1969 · Drachten (NL) ohne Ampeln · Somalia 1991–2012"
BLUE = (60, 120, 255)

SEGS = [
    dict(scene="hook", say="Keine Gesetze mehr – nach sechzehn Stunden wird geplündert. Wirklich passiert.", min=3.0, stamp="AB MORGEN", tplus=False, nosub=True, shake=1.0, flash0=0.0),
    dict(scene="ampel", say="Nach einer Stunde: Ampeln sind nur noch Deko. Überraschung: Ohne Ampeln kann es sogar sicherer werden.", min=4.8, stamp="1 STUNDE", node=True),
    dict(scene="montreal", say="Nach sechzehn Stunden: So lange streikte neunzehnhundertneunundsechzig die Polizei in Montreal. Plünderungen, Banküberfälle, Brände.", min=5.6, stamp="16 STUNDEN", node=True, shake=0.4),
    dict(scene="vertrag", say="Nach einer Woche: Verträge sind nur noch Papier. Dein Gehalt? Muss dir keiner mehr zahlen.", min=4.8, stamp="1 WOCHE", node=True),
    dict(scene="regeln", say="Nach einem Monat: Nachbarn tun sich zusammen – und erfinden eigene Regeln.", min=4.4, stamp="1 MONAT", node=True),
    dict(scene="twist", say="Und das Krasse: Somalia hatte über zwanzig Jahre lang keine funktionierende Regierung.", min=5.0, stamp="ECHT PASSIERT", tplus=False, node=True, twist=True, shake=0.5),
    dict(scene="outro", say="Welches Gesetz würdest du als Erstes vermissen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

# ---------- Stadt ----------
@lru_cache(None)
def skyline():
    r = np.random.default_rng(21); layers = []
    for depth, (ybase, hmin, hmax, wmin, wmax) in enumerate(((1250, 120, 420, 50, 110), (1300, 80, 300, 60, 130))):
        top = np.full(W, 99999.0, np.float32); x = -20
        while x < W + 20:
            w = r.uniform(wmin, wmax); h = r.uniform(hmin, hmax)
            top[max(0, int(x)):max(0, int(x + w))] = ybase - h; x += w + r.uniform(0, 8)
        win = r.random((H, W)) < 0.012
        layers.append((ybase, top, win))
    return layers

def city(rel, fire=0.0, lights=1.0, police=0.0, zoom=0.0):
    bg = kr.vgrad((6, 8, 24), (30, 22, 44), gamma=1.3); bg += lib.stars(rel * 2, 0, 0.25)
    if fire > 0:
        fl = 0.8 + 0.2 * math.sin(rel * 13) * math.sin(rel * 7.3)
        bg += kr.radial(300, 1300, 520, (255, 110, 30), 1.0 * fire * fl) + kr.radial(820, 1320, 420, (255, 80, 20), 0.8 * fire * fl)
        r = np.random.default_rng(int(rel * 6)); n = 220
        kr.splat(bg, r.uniform(0, W, n), 1300 - ((r.uniform(0, 900, n) + rel * 140) % 900), np.array([1.0, 0.6, 0.2]) * r.uniform(0.2, 1.0, n)[:, None] * fire, 3)
    yy = np.arange(H)[:, None]
    for k, (ybase, top, win) in enumerate(skyline()):
        m = (yy > top[None, :]) & (yy <= ybase + 400)
        col = np.array((14, 14, 28) if k == 0 else (6, 6, 14), np.float32) / 255
        bg[m] = col + (np.array([0.35, 0.12, 0.02], np.float32) * fire * (0.5 if k else 0.3))
        w = win & m
        bg[w] = np.array([1.0, 0.82, 0.45], np.float32) * lights
    bg[1500:] = np.array([0.02, 0.02, 0.04], np.float32)
    if police > 0:
        ph = (rel * 4) % 1
        bg += kr.radial(120, 260, 380, (255, 40, 40), police * (1.6 if ph < 0.5 else 0.2))
        bg += kr.radial(960, 260, 380, BLUE, police * (0.2 if ph < 0.5 else 1.6))
    if zoom > 0:    # Push-in um die Bildmitte
        k = 1 + zoom; cx, cy = W / 2, 1000
        ys = np.clip(((np.arange(H) - cy) / k + cy).astype(np.int32), 0, H - 1); xs = np.clip(((np.arange(W) - cx) / k + cx).astype(np.int32), 0, W - 1)
        bg = bg[ys][:, xs]
    return bg

# ---------- Hook: Blaulicht geht aus, Feuerschein kommt, Push-in ab Frame 0 ----------
def sc_hook(rel, ln, i):
    pol = 1.0 - eio((rel - 0.5) / 0.7)
    return city(rel, fire=0.35 + 0.65 * eo(rel / 1.5), lights=0.6, police=pol, zoom=0.04 + 0.10 * eo(rel / ln))
def ov_hook(img, rel, ln, i):
    a = 1.0 if rel < ln - 0.25 else clamp((ln - rel) / 0.25)
    p = bo(rel / 0.25)
    text_fx(img, (510, 520), "KEINE", F("Black", 150 * (0.85 + 0.15 * p)), fill=AMBER, alpha=a, shadow=1.0)
    text_fx(img, (510, 685), "GESETZE", F("Black", 190 * (0.85 + 0.15 * p)), fill=WHITE, glow=RED, glow_r=26, alpha=a, shadow=1.0)
    if rel > 0.6:
        text_fx(img, (510, 820), "POLIZEI: AUS", F("Black", 52), fill=RED, tracking=6, alpha=a * clamp((rel - 0.6) / 0.2))

def sc_ampel(rel, ln, i): return city(rel, 0.0, 0.8)
def ov_ampel(img, rel, ln, i):
    lib.heads(img, rel, "VERKEHR", "AMPELN = DEKO", glow=AMBER, sub="in Drachten (NL) fielen die Ampeln weg – und die Unfälle gingen zurück", sub_t=1.6)
    d = ImageDraw.Draw(img, "RGBA"); x, y = 760, 760
    d.rectangle([x - 10, y + 300, x + 10, y + 620], fill=(40, 44, 60, 255))
    d.rounded_rectangle([x - 70, y, x + 70, y + 310], 30, fill=(20, 22, 32, 255), outline=(90, 95, 120, 255), width=5)
    on = (rel * 1.6) % 1 < 0.5
    for k, col in enumerate((RED, AMBER, (80, 230, 120))):
        lit = (k == 1 and on)
        c = col if lit else tuple(int(v * 0.18) for v in col)
        d.ellipse([x - 45, y + 20 + k * 95, x + 45, y + 110 + k * 95], fill=c + (255,))
    if rel > 1.0:
        text_fx(img, (x, y - 50), "DEKO", F("Black", 48), fill=AMBER, glow=AMBER, glow_r=12, alpha=clamp((rel - 1.0) / 0.3))
    lib.paste_emoji(img, "🚗", 150, 300 + 80 * math.sin(rel * 2), 1320)

def sc_montreal(rel, ln, i): return city(rel, fire=0.4 + 0.6 * eo(rel / 3), lights=0.5)
def ov_montreal(img, rel, ln, i):
    lib.heads(img, rel, "MONTREAL 1969", "16 STUNDEN OHNE POLIZEI", glow=ORANGE, sub="Plünderungen, Banküberfälle, Brände – an einem einzigen Tag")
    for k, (ch, x, y, t) in enumerate((("🏦", 250, 900, 1.2), ("🛒", 520, 960, 1.7), ("🔥", 790, 900, 2.2))):
        if rel > t: lib.paste_emoji(img, ch, 130 * (0.7 + 0.3 * bo((rel - t) / 0.3)), x, y, alpha=clamp((rel - t) / 0.2))

def sc_vertrag(rel, ln, i):
    bg = kr.vgrad((14, 16, 30), (6, 6, 14)); bg += kr.radial(540, 1000, 500, (60, 50, 110), 0.4); return bg
def ov_vertrag(img, rel, ln, i):
    lib.heads(img, rel, "VERTRÄGE", "NUR NOCH PAPIER", glow=CYAN, sub="Gehalt, Miete, Kaufvertrag – niemand kann es mehr einklagen")
    k = eio((rel - 1.2) / 1.2)
    paper = Image.new("RGBA", (460, 600), (0, 0, 0, 0)); pd = ImageDraw.Draw(paper)
    pd.rectangle([0, 0, 459, 599], fill=(240, 236, 225, 255))
    pd.text((230, 70), "VERTRAG", font=F("Black", 56), fill=(30, 30, 40), anchor="mm")
    for j in range(9): pd.line([50, 150 + j * 42, 410 - (j % 3) * 40, 150 + j * 42], fill=(150, 150, 160), width=6)
    pd.line([60, 540, 220, 540], fill=(30, 30, 40), width=4); pd.text((70, 515), "Unterschrift", font=F("Medium", 22), fill=(80, 80, 90))
    m1 = Image.new("L", paper.size, 0); ImageDraw.Draw(m1).polygon([(0, 0), (260, 0), (200, 300), (240, 600), (0, 600)], fill=255)
    m2 = Image.new("L", paper.size, 0); ImageDraw.Draw(m2).polygon([(260, 0), (460, 0), (460, 600), (240, 600), (200, 300)], fill=255)
    for m, dx, ang in ((m1, -60 * k, 8 * k), (m2, 60 * k, -8 * k)):
        part = Image.new("RGBA", paper.size, (0, 0, 0, 0)); part.paste(paper, (0, 0), m)
        part = part.rotate(ang, expand=True, resample=Image.BICUBIC)
        img.paste(part, (int(500 - part.width / 2 + dx), int(1000 - part.height / 2 + 20 * k)), part)

def sc_regeln(rel, ln, i): return city(rel, 0.1, 0.9)
def ov_regeln(img, rel, ln, i):
    lib.heads(img, rel, "NACHBARSCHAFTEN", "NEUE REGELN", glow=(120, 230, 150), sub="Menschen organisieren sich – und schreiben ihre eigenen Regeln")
    d = ImageDraw.Draw(img, "RGBA"); r = np.random.default_rng(4)
    pts = [(r.uniform(140, 860), r.uniform(800, 1250)) for _ in range(14)]
    k = eo((rel - 0.6) / 2.5); n = int(len(pts) * k)
    for a in range(n):
        for b in range(a + 1, n):
            if math.dist(pts[a], pts[b]) < 300: d.line([pts[a], pts[b]], fill=(120, 230, 150, 160), width=4)
    for a in range(n):
        x, y = pts[a]; d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(120, 230, 150, 255))
    if rel > 2.2: lib.paste_emoji(img, "📜", 140, 260, 1180, alpha=clamp((rel - 2.2) / 0.3))

def sc_twist(rel, ln, i):
    bg = kr.vgrad((24, 12, 8), (8, 4, 4)); bg += kr.radial(540, 1000, 600, (200, 100, 40), 0.35); return bg
def ov_twist(img, rel, ln, i):
    lib.heads(img, rel, "UND DAS KRASSE:", "21 JAHRE", glow=ORANGE, big_col=ORANGE, sub="Somalia: 1991 bis 2012 ohne funktionierende Regierung", sub_t=1.1, size=170)
    d = ImageDraw.Draw(img, "RGBA"); x0, x1, y = 150, 870, 1000
    d.rounded_rectangle([x0, y - 24, x1, y + 24], 24, fill=(40, 30, 30, 255), outline=(255, 255, 255, 120), width=3)
    k = eio((rel - 0.8) / 2.0)
    d.rounded_rectangle([x0, y - 24, x0 + max(48, (x1 - x0) * k), y + 24], 24, fill=ORANGE + (255,))
    text_fx(img, (x0, y + 70), "1991", F("Black", 40), fill=WHITE, anchor="lm")
    text_fx(img, (x1, y + 70), "2012", F("Black", 40), fill=WHITE, anchor="rm", alpha=clamp(k * 3 - 2))
    text_fx(img, (500, 1180), f"Jahr {int(1991 + 21 * k)}", F("Black", 56), fill=AMBER)

def sc_outro(rel, ln, i): return city(rel + 4, 0.2, 0.7) * 0.6
def ov_outro(img, rel, ln, i): lib.outro(img, rel, "Welches Gesetz würdest du", "zuerst vermissen?", emoji="⚖️")

SCENES = dict(hook=sc_hook, ampel=sc_ampel, montreal=sc_montreal, vertrag=sc_vertrag, regeln=sc_regeln, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, ampel=ov_ampel, montreal=ov_montreal, vertrag=ov_vertrag, regeln=ov_regeln, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
