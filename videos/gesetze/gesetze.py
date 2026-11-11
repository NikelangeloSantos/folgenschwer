"""FOLGENSCHWER #12 – Was wäre, wenn es ab morgen keine Gesetze mehr gäbe?  (3D-Doodle-Version)

Hook-Regeln: krasseste Folge zuerst, Frame 0 in Bewegung, 2–3 riesige Wörter, Themenfrage im Outro.
Doodle-Regeln: alles zittert (Line Boil), Kamera bewegt sich immer, pro Kettenglied 2–3 schnelle Unterschnitte (Beats).
Flache Vorversion: gesetze_v1_flat.py
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from PIL import Image
import kr, lib, doodle as dd
from doodle import INK
from kr import W, H, F, text_fx, eo, eio, bo, ss, clamp, WHITE, ORANGE, AMBER, CYAN, RED

MAX_LEN = 42.0
CHORDS = [(110.0, 130.8, 164.8), (98.0, 116.5, 146.8), (103.8, 123.5, 155.6), (87.3, 110.0, 130.8)]
SOURCES = "Beispiele: Polizeistreik Montreal 1969 · Drachten (NL) ohne Ampeln · Somalia 1991–2012"
BLUE = (70, 130, 255); GREEN = (110, 220, 120); PINK = (255, 110, 170); YEL = (255, 210, 60); PAPER = (245, 238, 220)
BEAN = [(255, 140, 60), (90, 200, 255), (255, 210, 70), (150, 230, 120), (255, 120, 180), (190, 150, 255)]

SEGS = [
    dict(scene="hook", say="Keine Gesetze mehr – nach sechzehn Stunden wird geplündert. Wirklich passiert.", min=3.0, stamp="AB MORGEN", tplus=False, nosub=True, shake=1.0),
    dict(scene="ampel", say="Nach einer Stunde: Ampeln sind nur noch Deko. Überraschung: Ohne Ampeln kann es sogar sicherer werden.", min=4.8, stamp="1 STUNDE", node=True),
    dict(scene="montreal", say="Nach sechzehn Stunden: So lange streikte neunzehnhundertneunundsechzig die Polizei in Montreal. Plünderungen, Banküberfälle, Brände.", min=5.6, stamp="16 STUNDEN", node=True, shake=0.4),
    dict(scene="vertrag", say="Nach einer Woche: Verträge sind nur noch Papier. Dein Gehalt? Muss dir keiner mehr zahlen.", min=4.8, stamp="1 WOCHE", node=True),
    dict(scene="regeln", say="Nach einem Monat: Nachbarn tun sich zusammen – und erfinden eigene Regeln.", min=4.4, stamp="1 MONAT", node=True),
    dict(scene="twist", say="Und das Krasse: Somalia hatte über zwanzig Jahre lang keine funktionierende Regierung.", min=5.0, stamp="ECHT PASSIERT", tplus=False, node=True, twist=True, shake=0.5),
    dict(scene="outro", say="Welches Gesetz würdest du als Erstes vermissen? Schreib's in die Kommentare!", min=3.6, nosub=True, noui=True, nosrc=True),
]

# ---------- Hintergründe: knallige Verläufe, Licht wandert ----------
def grad(rel, top, bot, glow, gx=540, gy=1050):
    bg = kr.vgrad(top, bot, gamma=1.2)
    bg += kr.radial(gx + 120 * math.sin(rel * 0.9), gy + 80 * math.cos(rel * 0.7), 620, glow, 0.55)
    return bg

def cam(rel, beat_t=0.0, base=1.0, sway=1.0):
    """Ständig bewegte Kamera + Zoom-Punch beim Beat-Wechsel."""
    punch = 0.22 * math.exp(-max(0, rel - beat_t) * 7) if rel >= beat_t else 0
    z = base + 0.04 * math.sin(rel * 1.3) + punch
    return dict(zoom=z, pan=(18 * math.sin(rel * 0.8) * sway, 12 * math.cos(rel * 1.1) * sway), rot=2.2 * math.sin(rel * 0.9) * sway)

def beat(rel, cuts):
    k = 0
    for j, c in enumerate(cuts):
        if rel >= c: k = j
    return k, cuts[k]

def title(img, rel, kicker, big, col=WHITE, t0=0.35, size=104, sub=None, sub_t=1.2):
    """Kicker + 3D-Doodle-Kernaussage (bleibt ruhig stehen, damit man sie lesen kann)."""
    text_fx(img, (500, 440), kicker, F("Black", 44), fill=CYAN, tracking=6, alpha=clamp(rel / 0.25))
    if big and rel > t0:
        L = dd.Layer(rel); p = bo((rel - t0) / 0.35)
        f = lib.fit_font(big, size, 880); sz = f.size * (0.6 + 0.4 * p)
        L.text(500, 552 + 4 * math.sin(rel * 3), big, sz, col, depth=12, seed=7, stroke=6)
        L.paste_to(img)
    if sub: text_fx(img, (500, 650), sub, lib.fit_font(sub, 30, 900, "Bold"), fill=WHITE, alpha=clamp((rel - sub_t) / 0.3), shadow=1.0)

# ---------- HOOK ----------
def sc_hook(rel, ln, i):
    bg = grad(rel, (30, 8, 40), (90, 20, 30), (255, 80, 40))
    ph = (rel * 5) % 1; on = 1 - eio((rel - 0.6) / 0.4)
    bg += kr.radial(200, 300, 420, (255, 40, 40), on * (1.4 if ph < 0.5 else 0.2)) + kr.radial(880, 300, 420, BLUE, on * (0.2 if ph < 0.5 else 1.4))
    return bg

SHARDS = [(np.random.default_rng(k).uniform(-1, 1, 2), np.random.default_rng(k + 50).uniform(14, 40), np.random.default_rng(k + 99).uniform(-6, 6)) for k in range(22)]
def ov_hook(img, rel, ln, i):
    L = dd.Layer(rel, **cam(rel, 0.0, 1.02))
    dd.scribbles(L, 3, n=16, alpha=70)
    if rel < 1.7:
        # Polizeiauto, Sirene geht aus
        x = 540 + 30 * math.sin(rel * 6)
        dd.car(L, x, 1250, 420, (240, 240, 250), 1, spin=rel * 12)
        on = rel < 0.7; ph = (rel * 5) % 1
        L.box(x - 70, 1090, 140, 40, (255, 60, 60) if on and ph < 0.5 else (70, 120, 255) if on else (110, 110, 120), (8, 6), 4)
        if not on:
            dd.burst(L, x + 140, 1040, 70 * bo((rel - 0.7) / 0.25), YEL, 8)
            L.text(x + 140, 1040, "AUS", 34, RED, 0, seed=9, stroke=3)
    else:
        # Paragraph zerspringt
        k = clamp((rel - 2.0) / 1.2)
        if k <= 0:
            s = 360 * (0.7 + 0.3 * bo((rel - 1.7) / 0.3)); L.text(540, 1080, "§", s, YEL, depth=22, seed=11, stroke=10)
        else:
            dd.burst(L, 540, 1080, 220 * (1 - k) + 60, (255, 240, 200), 12, 12)
            for j, (d, sz, sp) in enumerate(SHARDS):
                x = 540 + d[0] * 600 * eo(k); y = 1080 + d[1] * 500 * eo(k) + 300 * k * k
                a = sp * k; c, s_ = math.cos(a), math.sin(a)
                pts = [(x + c * dx - s_ * dy, y + s_ * dx + c * dy) for dx, dy in ((-sz, -sz * 0.6), (sz, -sz * 0.2), (0, sz))]
                L.poly(pts, YEL, (6, 6), 20 + j, 4, hi=False)
        for fx, fs, sd in ((180, 160, 1), (420, 210, 2), (690, 190, 3), (900, 150, 4)):
            dd.flame(L, fx, 1520, fs * clamp((rel - 1.7) / 0.5), sd)
    L.paste_to(img)
    # Riesen-Text ab Frame 0
    T = dd.Layer(rel); p = bo(rel / 0.25); a = 1.0 if rel < ln - 0.25 else clamp((ln - rel) / 0.25)
    if a > 0:
        T.text(510, 500 + 6 * math.sin(rel * 5), "KEINE", 150 * (0.8 + 0.2 * p), YEL, depth=14, seed=1, stroke=9)
        T.text(510, 680 + 6 * math.sin(rel * 5 + 1), "GESETZE", 180 * (0.8 + 0.2 * p), WHITE, depth=18, seed=2, stroke=10)
        T.paste_to(img)

# ---------- 1 STUNDE: Ampel-Chaos -> Drachten ----------
def sc_ampel(rel, ln, i): return grad(rel, (20, 30, 70), (60, 30, 90), (120, 80, 255))
def ov_ampel(img, rel, ln, i):
    b, bt = beat(rel, [0.0, 2.6])
    L = dd.Layer(rel, **cam(rel, bt))
    dd.scribbles(L, 5, n=12, alpha=60)
    L.box(-100, 1300, 1300, 260, (70, 70, 90), (0, 0), 30, 0)          # Straße
    for k in range(8): L.box(-60 + ((k * 170 + rel * 300) % 1360) - 100, 1415, 90, 14, (240, 240, 240), (0, 0), 31 + k, 0)
    # Ampel
    x = 800
    L.box(x - 12, 1000, 24, 310, (60, 60, 80), (6, 4), 40, 5)
    L.box(x - 75, 720, 150, 300, (40, 42, 60), (14, 10), 41, 7)
    for k, col in enumerate((RED, YEL, GREEN)):
        lit = ((int(rel * 7) + k) % 3 == 0) if b == 0 else (k == 1 and (rel * 2) % 1 < 0.5)
        L.circ(x, 785 + k * 90, 36, col if lit else dd.dark(col, 0.3), (0, 0), 42 + k, 5)
    if b == 0:
        for k in range(4):
            sp = 520 + k * 90; xx = ((rel * sp + k * 380) % 1600) - 300
            flip = k % 2 == 1
            dd.car(L, W - xx if flip else xx, 1360 + (k % 2) * 110, 230, BEAN[k], 60 + k, flip, rel * 20)
        dd.burst(L, 300, 1000, 80 + 10 * math.sin(rel * 20), YEL, 70)
        L.text(300, 1000, "HUPP!", 34, RED, 0, seed=71, stroke=4)
    else:
        r = rel - bt
        for k in range(3): dd.bean(L, 120 + k * 150 + r * 80, 1330, 170, BEAN[k + 2], 80 + k, walk=r * 2, look=(1, 0))
        dd.car(L, 640 + 20 * math.sin(r), 1440, 240, BEAN[0], 90, False, r * 3)
        L.text(330, 900, "UNFÄLLE", 56, WHITE, 8, seed=91, stroke=6)
        L.poly([(520, 840), (580, 840), (580, 960 + 40 * eo(r)), (620, 960 + 40 * eo(r)), (550, 1050 + 40 * eo(r)), (480, 960 + 40 * eo(r)), (520, 960 + 40 * eo(r))], GREEN, (10, 10), 92, 6)
    L.paste_to(img)
    title(img, rel, "VERKEHR", "AMPELN = DEKO" if rel < 2.6 else "WENIGER UNFÄLLE?!", YEL if rel < 2.6 else GREEN,
          sub="Drachten (NL) schaffte Ampeln ab – es krachte seltener" if rel >= 2.6 else None, sub_t=2.9)

# ---------- 16 STUNDEN: Montreal ----------
def sc_montreal(rel, ln, i):
    fl = 0.8 + 0.2 * math.sin(rel * 13) * math.sin(rel * 7.3)
    bg = grad(rel, (40, 10, 30), (120, 30, 10), (255, 110, 30))
    bg += kr.radial(540, 1500, 700, (255, 100, 20), 0.6 * fl)
    return bg
def ov_montreal(img, rel, ln, i):
    b, bt = beat(rel, [0.0, 1.8, 3.6])
    L = dd.Layer(rel, **cam(rel, bt))
    dd.scribbles(L, 7, (255, 200, 120), n=14, alpha=70, drift=(10, -60))
    r = rel - bt
    if b == 0:   # Zeitung fliegt rein
        s = eo(r / 0.6); a = (1 - s) * 2.5
        c, s_ = math.cos(a), math.sin(a); cx, cy = 540, 1060; w, h = 320 * (0.4 + 0.6 * s), 360 * (0.4 + 0.6 * s)
        pts = [(cx + c * dx - s_ * dy, cy + s_ * dx + c * dy) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
        L.poly(pts, PAPER, (16, 16), 100, 8)
        if s > 0.8:
            L.text(540, 790, "MONTREAL 1969", 54, INK, 0, seed=101, stroke=0)
            L.text(540, 890, "POLIZEI", 96, RED, 6, seed=102, stroke=5); L.text(540, 995, "STREIKT!", 96, RED, 6, seed=103, stroke=5)
            for k in range(5): L.box(320, 1080 + k * 50, 440 - (k % 2) * 120, 18, (150, 150, 160), (0, 0), 104 + k, 0)
    elif b == 1:  # Läden, Leute tragen Kisten weg
        for k in range(4):
            x = 60 + k * 250; L.box(x, 860, 220, 380, BEAN[k], (16, 12), 110 + k, 7)
            L.box(x + 30, 960, 160, 160, (180, 220, 255), (0, 0), 120 + k, 5)
            L.line([(x + 40, 980), (x + 110, 1060), (x + 90, 1100), (x + 170, 1110)], INK, 5, 130 + k)
            dd.flame(L, x + 110, 860, 90 + 20 * k % 3, 140 + k)
        for k in range(3):
            xx = ((r * 420 + k * 380) % 1400) - 200
            dd.bean(L, xx, 1420, 230, BEAN[(k + 3) % 6], 150 + k, walk=r * 3 + k, arms_up=0.8,
                    carry=lambda L_, x_, y_, k=k: L_.box(x_ - 60, y_ - 90, 120, 90, (210, 170, 110), (10, 8), 160 + k, 5))
    else:        # Bank, Geld fliegt
        L.poly([(220, 900), (540, 760), (860, 900)], (200, 200, 215), (14, 10), 170, 7)
        L.box(240, 900, 600, 400, (220, 220, 235), (16, 12), 171, 7)
        for k in range(4): L.box(290 + k * 140, 950, 50, 300, (180, 180, 200), (6, 4), 172 + k, 5)
        L.text(540, 860, "BANK", 50, INK, 0, seed=176, stroke=0)
        rr = np.random.default_rng(3)
        for k in range(14):
            vx, vy = rr.uniform(-1, 1), rr.uniform(-1.4, -0.4); tt = (r * 0.8 + k * 0.07) % 1.2
            dd.bill(L, 540 + vx * 520 * tt, 1100 + vy * 600 * tt + 500 * tt * tt, 110, tt * 6 * vx, 180 + k)
        dd.flame(L, 150, 1500, 220, 190); dd.flame(L, 930, 1500, 200, 191)
    L.paste_to(img)
    title(img, rel, "MONTREAL 1969", "16 STD. OHNE POLIZEI", ORANGE, sub="Plünderungen, Banküberfälle, Brände – an einem Tag", sub_t=1.9)

# ---------- 1 WOCHE: Verträge ----------
def sc_vertrag(rel, ln, i): return grad(rel, (14, 30, 60), (40, 20, 70), (80, 200, 255))
def ov_vertrag(img, rel, ln, i):
    b, bt = beat(rel, [0.0, 1.5, 3.0])
    L = dd.Layer(rel, **cam(rel, bt)); dd.scribbles(L, 9, n=12, alpha=60)
    r = rel - bt
    if b < 2:
        k = 0 if b == 0 else eio(r / 0.7)
        for half, sgn in ((0, -1), (1, 1)):
            dx = sgn * 220 * k; rot = sgn * 0.35 * k
            x0 = 330 if half == 0 else 540; x1 = 540 if half == 0 else 750
            pts = [(x0, 760), (x1 + (0 if half else 25), 760), (x1 - 20, 1000), (x1 + 15, 1260), (x0, 1260)] if half == 0 else [(x0 + 25, 760), (x1, 760), (x1, 1260), (x0 + 15, 1260), (x0 - 20, 1000)]
            cx, cy = (x0 + x1) / 2, 1010; c, s_ = math.cos(rot), math.sin(rot)
            pts = [(cx + dx + c * (x - cx) - s_ * (y - cy), cy + s_ * (x - cx) + c * (y - cy) + 60 * k) for x, y in pts]
            L.poly(pts, PAPER, (12, 12), 200 + half, 7, hi=False)
        if k < 0.1:
            L.text(540, 820, "VERTRAG", 60, INK, 0, seed=210, stroke=0)
            for j in range(6): L.box(370, 880 + j * 45, 340 - (j % 3) * 60, 14, (160, 160, 170), (0, 0), 211 + j, 0)
            sig = [(390 + j * 9, 1190 + 18 * math.sin(j * 0.9)) for j in range(int(30 * clamp(rel / 1.2)))]
            if len(sig) > 1: L.line(sig, (40, 60, 200), 5, 220, 0.8)
        if b == 1: dd.burst(L, 540, 1000, 120 * (1 - eo(r / 0.6)) + 20, YEL, 230); L.text(540, 1000, "RATSCH!", 46 * (1 - eo(r / 0.8)) + 1, RED, 0, seed=231, stroke=4)
    else:
        L.box(330, 1050, 420, 240, (150, 90, 50), (16, 12), 240, 7)
        L.poly([(330, 1050), (750, 1050), (700, 960), (380, 960)], (180, 115, 65), (0, 0), 241, 7)
        for k in range(6):
            tt = (r * 0.9 + k * 0.15) % 1.2
            dd.bill(L, 540 + (k - 2.5) * 70 * tt * 3, 1000 - 700 * tt, 120, tt * 3 * (k - 2.5), 250 + k)
        dd.bean(L, 820, 1450, 260, BEAN[1], 260, arms_up=0.6, look=(-1, -1))
        for k in range(3): L.text(760 + k * 60, 1130 - 30 * math.sin(rel * 4 + k), "?", 70, YEL, 6, seed=270 + k, stroke=5)
    L.paste_to(img)
    title(img, rel, "VERTRÄGE", "NUR NOCH PAPIER" if rel < 3.0 else "GEHALT? WEG!", CYAN if rel < 3.0 else YEL,
          sub="niemand kann es mehr einklagen", sub_t=1.6)

# ---------- 1 MONAT: neue Regeln ----------
def sc_regeln(rel, ln, i): return grad(rel, (10, 40, 40), (20, 30, 70), (80, 255, 160))
HOUSES = [(120, 1180), (330, 1120), (560, 1190), (790, 1130), (230, 1400), (680, 1400)]
def ov_regeln(img, rel, ln, i):
    b, bt = beat(rel, [0.0, 2.2])
    L = dd.Layer(rel, **cam(rel, bt)); dd.scribbles(L, 11, n=12, alpha=60)
    r = rel - bt
    for k, (x, y) in enumerate(HOUSES):
        L.box(x - 70, y - 120, 140, 120, BEAN[k], (12, 10), 300 + k, 6)
        L.poly([(x - 85, y - 120), (x, y - 200), (x + 85, y - 120)], dd.dark(BEAN[k], 0.8), (10, 8), 310 + k, 6)
    if b == 0:
        n = int(len(HOUSES) * eo(r / 1.8)) + 1
        for a in range(min(n, len(HOUSES))):
            for c in range(a + 1, min(n, len(HOUSES))):
                if math.dist(HOUSES[a], HOUSES[c]) < 420: L.line([(HOUSES[a][0], HOUSES[a][1] - 60), (HOUSES[c][0], HOUSES[c][1] - 60)], GREEN, 6, 320 + a * 10 + c)
        for k in range(min(n, 5)): dd.bean(L, HOUSES[k][0] + 60, HOUSES[k][1] + 40, 140, BEAN[(k + 2) % 6], 330 + k, arms_up=0.4 * math.sin(rel * 4 + k))
    else:
        k = clamp(r / 1.0)
        for j, (d, sz, sp) in enumerate(SHARDS):
            x = 540 + d[0] * 600 * (1 - eo(k)); y = 900 + d[1] * 500 * (1 - eo(k))
            if k < 1:
                a = sp * (1 - k); c, s_ = math.cos(a), math.sin(a)
                L.poly([(x + c * dx - s_ * dy, y + s_ * dx + c * dy) for dx, dy in ((-sz, -sz * 0.6), (sz, -sz * 0.2), (0, sz))], YEL, (6, 6), 340 + j, 4, hi=False)
        if k >= 1:
            dd.burst(L, 540, 900, 180 + 10 * math.sin(rel * 8), (255, 250, 210), 360, 12)
            L.text(540, 900, "§", 300, YEL, 20, seed=361, stroke=10)
        for k2 in range(4): dd.bean(L, 200 + k2 * 220, 1330, 170, BEAN[k2], 370 + k2, arms_up=0.5 + 0.5 * math.sin(rel * 8 + k2))
    L.paste_to(img)
    title(img, rel, "NACHBARSCHAFTEN", "NEUE REGELN", GREEN, sub="Menschen schreiben sofort eigene Regeln", sub_t=1.4)

# ---------- TWIST: Somalia ----------
def sc_twist(rel, ln, i): return grad(rel, (40, 16, 8), (90, 40, 10), (255, 160, 40))
def ov_twist(img, rel, ln, i):
    L = dd.Layer(rel, **cam(rel, 0.0)); dd.scribbles(L, 13, (255, 220, 160), n=14, alpha=70)
    k = eio((rel - 0.6) / 2.4); yr = int(1991 + 21 * k)
    L.box(330, 820, 420, 460, (240, 240, 245), (18, 14), 400, 8)
    L.box(330, 820, 420, 110, RED, (0, 0), 401, 8)
    for j in range(5): L.circ(380 + j * 80, 820, 16, (200, 200, 210), (0, 0), 402 + j, 4, 10)
    flip = (rel * 9) % 1 if k < 1 else 0
    L.text(540, 875, "JAHR", 44, WHITE, 0, seed=410, stroke=4)
    L.text(540, 1100 - 30 * flip, str(yr), 150, INK, 8, seed=411, stroke=0)
    if flip > 0.05:
        L.poly([(330, 930), (750, 930), (750, 930 + 350 * (1 - flip)), (330, 930 + 350 * (1 - flip))], (255, 255, 255), (0, 0), 412, 5, hi=False)
    dd.bean(L, 860, 1460, 230, BEAN[2], 420, arms_up=0.3 + 0.2 * math.sin(rel * 3), look=(-1, -1))
    L.paste_to(img)
    title(img, rel, "UND DAS KRASSE:", "21 JAHRE", ORANGE, size=150, sub="Somalia: 1991 bis 2012 ohne funktionierende Regierung", sub_t=1.0)

def sc_outro(rel, ln, i): return grad(rel, (20, 10, 40), (40, 14, 30), (255, 110, 60)) * 0.8
def ov_outro(img, rel, ln, i):
    L = dd.Layer(rel, **cam(rel, 0.0, 1.0, 0.6)); dd.scribbles(L, 15, n=18, alpha=70)
    for k in range(5): dd.bean(L, 120 + k * 210, 1500, 200, BEAN[k], 500 + k, arms_up=0.5 + 0.5 * math.sin(rel * 6 + k), look=(0, -1))
    L.paste_to(img)
    T = dd.Layer(rel); a = clamp(rel / 0.3); p = bo(rel / 0.35)
    # Doodle-Kettenglieder (orange - weiß - orange), das mittlere springt auf
    for k, x in enumerate((390, 500, 610)):
        col = ORANGE if k != 1 else WHITE; gap = 14 * math.sin(rel * 5) if k == 1 else 0
        w, h = (120, 64) if k != 1 else (52, 110)
        T.poly([(x - w / 2, 400 - h / 2 - gap), (x + w / 2, 400 - h / 2 - gap), (x + w / 2, 400 + h / 2 + gap), (x - w / 2, 400 + h / 2 + gap)], col, (8, 8), 600 + k, 7, hi=False)
        T.poly([(x - w / 2 + 22, 400 - h / 2 + 18 - gap), (x + w / 2 - 22, 400 - h / 2 + 18 - gap), (x + w / 2 - 22, 400 + h / 2 - 18 + gap), (x - w / 2 + 22, 400 + h / 2 - 18 + gap)], (40, 20, 50), (0, 0), 610 + k, 5, hi=False)
    T.text(500, 560, "FOLGENSCHWER", 96 * (0.8 + 0.2 * p), WHITE, 14, seed=620, stroke=8)
    if rel > 0.3:
        T.text(500, 720, "Welches Gesetz würdest du", 54, WHITE, 6, seed=621, stroke=5)
        T.text(500, 810, "zuerst vermissen?", 78 * (0.8 + 0.2 * bo((rel - 0.3) / 0.35)), YEL, 10, seed=622, stroke=7)
    T.paste_to(img)
    if rel > 0.8: lib.paste_emoji(img, "⚖️", 120, 500, 960, alpha=clamp((rel - 0.8) / 0.3))

SCENES = dict(hook=sc_hook, ampel=sc_ampel, montreal=sc_montreal, vertrag=sc_vertrag, regeln=sc_regeln, twist=sc_twist, outro=sc_outro)
OV = dict(hook=ov_hook, ampel=ov_ampel, montreal=ov_montreal, vertrag=ov_vertrag, regeln=ov_regeln, twist=ov_twist, outro=ov_outro)
def overlay(img, rel, ln, i): OV[SEGS[i]["scene"]](img, rel, ln, i)

kr.run(globals())
