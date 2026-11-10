"""FOLGENSCHWER – gemeinsame Engine für alle „Was wäre, wenn …?“-Videos.

Ein Video ist eine Datei videos/<name>.py, die SEGS, SCENES und ein paar Konstanten definiert und
am Ende `kr.run(globals())` aufruft. Die Engine übernimmt: Stimme (ElevenLabs + Cache), Timing,
Zeitleisten-UI (T+ … und Kettenglieder), Karaoke-Untertitel, Übergänge, Bloom/Grain/Vignette,
prozedurale Musik + SFX, paralleles Rendern und Lautheit.
"""
import base64, hashlib, json, math, os, subprocess, sys, wave
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- Pillow ≥ 12 ignoriert Alpha in Textfarben -> Maskenweg (wie bei ZahlenBlitz)
_orig_text = ImageDraw.ImageDraw.text
def _alpha_text(self, xy, text, fill=None, font=None, anchor=None, *args, stroke_width=0, stroke_fill=None, **kw):
    fa = fill[3] if isinstance(fill, tuple) and len(fill) == 4 else 255
    sa = stroke_fill[3] if isinstance(stroke_fill, tuple) and len(stroke_fill) == 4 else 255
    if (fa >= 255 and (not stroke_width or sa >= 255)) or self._image.mode != "RGB" or kw.get("embedded_color"):
        return _orig_text(self, xy, text, fill, font, anchor, *args, stroke_width=stroke_width, stroke_fill=stroke_fill, **kw)
    if fa <= 1 and (not stroke_width or sa <= 1): return
    img = self._image
    x0, y0, x1, y1 = self.textbbox(xy, text, font=font, anchor=anchor, stroke_width=stroke_width)
    x0, y0, x1, y1 = int(x0) - 2, int(y0) - 2, int(x1) + 3, int(y1) + 3
    if x1 <= 0 or y1 <= 0 or x0 >= img.width or y0 >= img.height: return
    pos = (xy[0] - x0, xy[1] - y0)
    layers = ([(stroke_width, stroke_fill, sa)] if stroke_width and stroke_fill is not None else []) + [(0, fill, fa)]
    for width, col, al in layers:
        if col is None or al <= 1: continue
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).text(pos, text, fill=255, font=font, anchor=anchor, stroke_width=width, stroke_fill=255)
        if al < 255: m = m.point(lambda v, k=al / 255: int(v * k))
        img.paste(tuple(col[:3]), (x0, y0, x1, y1), m)
ImageDraw.ImageDraw.text = _alpha_text

W, H, FPS, SR = 1080, 1920, 30, 48000
ROOT = os.path.dirname(os.path.abspath(__file__))
VOICE_ID = "ML23UVoFL5mI6APbRAeR"   # Kanalstimme ab Video #02 (pro Video überschreibbar: VOICE_ID im Video-Skript)
MODEL_ID = "eleven_multilingual_v2"
VOICE_SETTINGS = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}

# Markenfarben
WHITE = (246, 247, 252); INK = (3, 5, 12)
ORANGE = (255, 112, 38); AMBER = (255, 190, 70); CYAN = (80, 228, 255); RED = (255, 64, 72)
SUB_CX, SUB_W, SUB_Y = 500, 830, 1395

# ---------- Mathe ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def bo(x): x = clamp(x); c = 1.7; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def ss(a, b, x): x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def mix(a, b, t): t = clamp(t); return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))
def de(v, dec=0): return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------- Schrift ----------
@lru_cache(None)
def F(w, s): return ImageFont.truetype(os.path.join(ROOT, "fonts", f"Inter-{w}.otf"), max(6, int(round(s))))
@lru_cache(None)
def emoji(ch, size):
    f = ImageFont.truetype(os.path.join(ROOT, "fonts", "NotoColorEmoji.ttf"), 109)
    im = Image.new("RGBA", (150, 150), (0, 0, 0, 0)); ImageDraw.Draw(im).text((75, 75), ch, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox()); k = size / max(im.size)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)

# ---------- Prozedurale Texturen ----------
def fnoise(w, h, octaves=6, seed=0, base=4, persist=0.5):
    """Fraktales Value-Noise 0..1, horizontal nahtlos (für Kugeltexturen)."""
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw = base * 2 ** o; gh = max(2, gw // 2 + 1)
        g = rng.random((gh, gw)).astype(np.float32); g = np.concatenate([g, g, g], 1)
        im = Image.fromarray(g, "F").resize((3 * w, h), Image.BICUBIC)
        out += np.asarray(im)[:, w:2 * w] * amp; tot += amp; amp *= persist
    out /= tot; out = (out - out.min()) / (out.max() - out.min() + 1e-9)
    return out

def starfield(w, h, n=1500, seed=1, big=40):
    rng = np.random.default_rng(seed)
    im = Image.new("RGB", (w, h), (0, 0, 0)); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h); b = rng.random() ** 3
        c = mix((255, 236, 210), (200, 225, 255), rng.random())
        c = tuple(int(v * (0.25 + 0.75 * b)) for v in c); r = 0.6 + 1.3 * b
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    glow = Image.new("RGB", (w, h), (0, 0, 0)); g = ImageDraw.Draw(glow)
    for _ in range(big):
        x, y = rng.uniform(0, w), rng.uniform(0, h); r = rng.uniform(4, 9)
        g.ellipse([x - r, y - r, x + r, y + r], fill=(170, 200, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    return np.clip(np.asarray(im, np.float32) / 255 + np.asarray(glow, np.float32) / 255 * 0.8, 0, 1)

@lru_cache(None)
def _sgrid(S, R):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    x = (xx + 0.5 - S / 2) / R; y = (yy + 0.5 - S / 2) / R
    return x, y, x * x + y * y

def sphere(R, tex, spin=0.0, tilt=0.0, light=(-0.7, -0.35, 0.62), night=None, clouds=None, cspin=0.0,
           atm=(90, 170, 255), atm_k=1.0, terminator=0.18):
    """Beleuchtete Kugel aus equirektangulärer Textur. Liefert (rgb float SxSx3, alpha SxS), S = 2,5·R."""
    R = float(R); S = int(2.5 * R) | 1
    x, y, r2 = _sgrid(S, R)
    ins = r2 < 1.0
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    a = math.radians(tilt); ca, sa = math.cos(a), math.sin(a)
    xr = x * ca + y * sa; yr = -x * sa + y * ca
    lat = np.arcsin(np.clip(-yr, -1, 1)); lon = np.arctan2(xr, z)
    th, tw = tex.shape[:2]
    v = np.clip(((0.5 - lat / math.pi) * th).astype(np.int32), 0, th - 1)
    u = (((lon + spin) / (2 * math.pi)) % 1.0 * tw).astype(np.int32) % tw
    col = tex[v, u]
    L = np.array(light, np.float32); L /= np.linalg.norm(L)
    dot = x * L[0] + y * L[1] + z * L[2]
    lit = ss(-terminator, terminator * 1.6, dot)
    rgb = col * (0.025 + 0.975 * lit[..., None]) * (0.75 + 0.25 * z[..., None])
    if clouds is not None:
        uc = (((lon + spin + cspin) / (2 * math.pi)) % 1.0 * tw).astype(np.int32) % tw
        ca_ = clouds[v, uc][..., None]
        rgb = rgb * (1 - ca_) + ca_ * (0.02 + 0.98 * lit[..., None]) * np.float32(0.95)
    if night is not None:
        nl = night[v, u][..., None] * (1 - lit[..., None]) ** 2
        rgb = rgb + nl * np.array([1.0, 0.62, 0.25], np.float32)
    rr = np.sqrt(r2)
    alpha = np.clip((1 - rr) * R + 0.5, 0, 1)
    if atm is not None:
        ac = np.array(atm, np.float32) / 255
        lit_dir = np.clip(x * L[0] + y * L[1] + 0.3, 0, 1) * 0.85 + 0.15
        rim_in = np.where(ins, ss(0.75, 1.0, rr) ** 2 * 0.55, 0)
        rim_out = np.where(~ins, np.exp(-((rr - 1) / 0.045) ** 2 * 0.5) * 0.9, 0)
        g = (rim_in + rim_out) * lit_dir * atm_k
        rgb = rgb * (alpha[..., None]) + g[..., None] * ac
        alpha = np.clip(alpha + rim_out * lit_dir * atm_k, 0, 1)
        return rgb, alpha, True
    return rgb * alpha[..., None], alpha, True

def blit(canvas, rgb, alpha, cx, cy, additive_rgb=True):
    """Premultiplied-RGB an Mittelpunkt (cx, cy) einsetzen."""
    S = rgb.shape[0]; x0 = int(round(cx - S / 2)); y0 = int(round(cy - S / 2))
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + S), min(H, y0 + S)
    if xa >= xb or ya >= yb: return
    sr = rgb[ya - y0:yb - y0, xa - x0:xb - x0]; sa = alpha[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
    dst = canvas[ya:yb, xa:xb]
    dst *= (1 - np.clip(sa, 0, 1)); dst += sr

def splat(canvas, xs, ys, col, size=1):
    """Partikel additiv zeichnen (xs, ys Arrays, col (n,3) oder (3,))."""
    xs = np.asarray(xs); ys = np.asarray(ys)
    col = np.broadcast_to(np.asarray(col, np.float32), (len(xs), 3))
    for dx in range(size):
        for dy in range(size):
            xi = (xs + dx).astype(np.int32); yi = (ys + dy).astype(np.int32)
            ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
            np.add.at(canvas, (yi[ok], xi[ok]), col[ok])

def vgrad(top, bot, h=H, w=W, gamma=1.0):
    t = (np.linspace(0, 1, h, dtype=np.float32) ** gamma)[:, None, None]
    a = np.array(top, np.float32) / 255; b = np.array(bot, np.float32) / 255
    return np.broadcast_to(a + (b - a) * t, (h, w, 3)).copy()

def radial(cx, cy, r, col, k=1.0, w=W, h=H):
    yy, xx = np.ogrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    g = np.exp(-d * d) * k
    return g[..., None].astype(np.float32) * (np.array(col, np.float32) / 255)

# ---------- Text-Helfer ----------
def text_fx(img, xy, text, font, fill=WHITE, anchor="mm", alpha=1.0, glow=None, glow_r=18, shadow=0.7, tracking=0, stroke=0):
    """Text mit weichem Schatten (Lesbarkeit) und optionalem Glow. img: PIL RGB."""
    if alpha <= 0.01 or not text: return
    d0 = ImageDraw.Draw(img)
    if tracking:
        widths = [font.getlength(c) + tracking for c in text]; tot = sum(widths) - tracking
        bb = d0.textbbox((0, 0), text, font=font, anchor="ls"); asc = -bb[1]
        if anchor[0] == "m": x = xy[0] - tot / 2
        elif anchor[0] == "r": x = xy[0] - tot
        else: x = xy[0]
        y = xy[1] + (asc / 2 if anchor[1] == "m" else 0)
        parts = []
        for c, wd in zip(text, widths): parts.append((c, (x, y))); x += wd
        anc = "ls"
    else:
        parts = [(text, xy)]; anc = anchor
    pad = glow_r * 2 + 10
    bbs = [d0.textbbox(p, c, font=font, anchor=anc, stroke_width=stroke) for c, p in parts]
    x0 = int(min(b[0] for b in bbs)) - pad; y0 = int(min(b[1] for b in bbs)) - pad
    x1 = int(max(b[2] for b in bbs)) + pad; y1 = int(max(b[3] for b in bbs)) + pad
    m = Image.new("L", (x1 - x0, y1 - y0), 0); md = ImageDraw.Draw(m)
    for c, p in parts: md.text((p[0] - x0, p[1] - y0), c, font=font, fill=255, anchor=anc, stroke_width=stroke, stroke_fill=255)
    region = (x0, y0, x1, y1)
    if shadow:
        sh = m.filter(ImageFilter.GaussianBlur(max(6, font.size // 7))).point(lambda v: int(min(255, v * 1.6) * shadow * alpha))
        img.paste(INK, region, sh)
    if glow:
        gl = m.filter(ImageFilter.GaussianBlur(glow_r))
        base = img.crop(region); arr = np.asarray(base, np.float32)
        ga = np.asarray(gl, np.float32)[..., None] / 255 * alpha * 1.3
        arr = np.clip(arr + ga * np.array(glow, np.float32), 0, 255).astype(np.uint8)
        img.paste(Image.fromarray(arr), region)
    mm = m if alpha >= 0.99 else m.point(lambda v: int(v * alpha))
    img.paste(tuple(int(c) for c in fill[:3]), region, mm)

def text_w(text, font, tracking=0):
    return sum(font.getlength(c) + tracking for c in text) - tracking if tracking else font.getlength(text)

# ---------- Stimme ----------
class Video:
    pass
V = Video()

def _vid(): return getattr(V, "VOICE_ID", VOICE_ID)
def _hash(text): return hashlib.sha1(f"{_vid()}|{MODEL_ID}|{json.dumps(VOICE_SETTINGS, sort_keys=True)}|{text}".encode()).hexdigest()[:16]
def fetch_voice(text):
    cache = os.path.join(V.dir, "voice_cache"); os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, _hash(text) + ".json")
    if os.path.exists(path): return json.load(open(path))
    if os.environ.get("KR_VOICE") != "1": return None
    import requests
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{_vid()}/with-timestamps",
                      params={"output_format": "mp3_44100_128"},
                      headers={"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "proxy-injected"), "Content-Type": "application/json"},
                      json={"text": text, "model_id": MODEL_ID, "voice_settings": VOICE_SETTINGS}, timeout=120)
    if r.status_code != 200: raise SystemExit(f"ElevenLabs-Fehler {r.status_code}: {r.text[:300]}")
    data = r.json(); json.dump(data, open(path, "w")); return data

def decode_mp3(b64, tempo=1.0):
    flt = "areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.08,areverse" + (f",atempo={tempo:.4f}" if abs(tempo - 1) > 1e-3 else "")
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-af", flt, "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                       input=base64.b64decode(b64), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).astype(np.float64)

def words_from_alignment(al, tempo):
    words, cur, t0, t1 = [], "", None, None
    for c, a, b in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if c.isspace():
            if cur: words.append((cur, t0 / tempo, t1 / tempo)); cur = ""
        else:
            if not cur: t0 = a
            cur += c; t1 = b
    if cur: words.append((cur, t0 / tempo, t1 / tempo))
    return words

def estimate_words(text, dur):
    ws = text.split(); tot = sum(len(w) + 2 for w in ws); t = 0.1; out = []
    for w in ws:
        d = (dur - 0.2) * (len(w) + 2) / tot; out.append((w, t, t + d * 0.92)); t += d
    return out

def squeeze(a, ws, keep=0.22):
    out, nw, shift, pos = [], [], 0.0, 0
    for k, (w, t0, t1) in enumerate(ws):
        if k > 0:
            pe = ws[k - 1][2]
            if t0 - pe > keep + 0.05:
                c0 = int((pe + keep / 2) * SR); c1 = int((t0 - keep / 2) * SR)
                if c1 > c0 > pos: out.append(a[pos:c0]); pos = c1; shift += (c1 - c0) / SR
        nw.append((w, t0 - shift, t1 - shift))
    out.append(a[pos:]); return np.concatenate(out), nw

TL = None
def tl():
    global TL
    if TL is not None: return TL
    S = V.SEGS
    voices = [fetch_voice(s["say"]) for s in S]
    have = all(v is not None for v in voices)
    if have:
        def make(tempo):
            res = [squeeze(decode_mp3(v["audio_base64"], tempo), words_from_alignment(v["alignment"], tempo)) for v in voices]
            return [r[0] for r in res], [r[1] for r in res]
        a1, _ = make(1.0)
        need = sum(max(s["min"], len(a) / SR + s.get("tail", 0.25)) for s, a in zip(S, a1))
        tempo = min(1.15, max(1.0, need / V.MAX_LEN))
        audio, words = make(tempo); durs = [len(a) / SR for a in audio]
    else:
        tempo = 1.0; audio = None
        durs = [len(s["say"]) / 15.5 for s in S]
        words = [estimate_words(s["say"], d) for s, d in zip(S, durs)]
    lens = [max(s["min"], d + s.get("tail", 0.25)) for s, d in zip(S, durs)]
    starts = list(np.cumsum([0] + lens[:-1]))
    TL = dict(starts=starts, lens=lens, words=words, audio=audio, total=float(sum(lens)), tempo=tempo, voiced=have)
    return TL

def seg_at(t):
    T = tl()
    for i in range(len(V.SEGS) - 1, -1, -1):
        if t >= T["starts"][i]: return i
    return 0

# ---------- Zeitleiste (Markenzeichen: T+ … und Kettenglieder) ----------
def chain_ui(img, t, i, rel):
    S = V.SEGS; seg = S[i]
    if seg.get("noui"): return
    T = tl()
    nodes = [k for k, s in enumerate(S) if s.get("node")]
    n = len(nodes); x0, x1, y = 150, 870, 335
    xs = [x0 + (x1 - x0) * k / (n - 1) for k in range(n)]
    cur = max([k for k, nd in enumerate(nodes) if nd <= i], default=-1)
    # Fortschritt innerhalb der Kette (Glied zwischen Knoten füllt sich beim Wechsel)
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(n - 1):
        a, b = xs[k], xs[k + 1]
        fill = 1.0 if k < cur else 0.0
        if k == cur - 1: fill = eo(rel / 0.45)
        links = 5
        for j in range(links):
            lx = a + (b - a) * (j + 0.5) / links; on = (j + 0.5) / links <= fill
            col = ORANGE + (235,) if on else (255, 255, 255, 70)
            if j % 2 == 0: d.rounded_rectangle([lx - 15, y - 8, lx + 15, y + 8], 8, outline=col, width=4)
            else: d.line([lx - 9, y, lx + 9, y], fill=col, width=4)
    for k, x in enumerate(xs):
        on = k <= cur; pulse = (k == cur) * (1 - eo(rel / 0.6))
        r = 13 + 10 * pulse
        if on:
            d.ellipse([x - r - 6, y - r - 6, x + r + 6, y + r + 6], fill=ORANGE + (int(60 + 120 * pulse),))
            d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=ORANGE + (255,), outline=(255, 230, 200, 255), width=3)
        else:
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(10, 14, 28, 200), outline=(255, 255, 255, 110), width=3)
    # T+ Pille
    stamp = seg.get("stamp") or next((S[k].get("stamp") for k in range(i, -1, -1) if S[k].get("stamp")), "")
    if not stamp: return
    pop = bo(rel / 0.35) if seg.get("stamp") else 1.0
    f = F("Black", 50 * (0.85 + 0.15 * pop)); ft = F("Black", 50 * (0.85 + 0.15 * pop))
    pre = "T+ " if seg.get("tplus", True) else ""
    w1 = text_w(pre, ft); w2 = text_w(stamp, f); tw_ = w1 + w2
    cx, cy = 510, 250; px = tw_ / 2 + 36
    d.rounded_rectangle([cx - px, cy - 42, cx + px, cy + 42], 42, fill=(8, 10, 22, 205), outline=ORANGE + (255,), width=4)
    if pre: d.text((cx - tw_ / 2, cy), pre, font=ft, fill=ORANGE, anchor="lm")
    d.text((cx - tw_ / 2 + w1, cy), stamp, font=f, fill=WHITE, anchor="lm")

# ---------- Untertitel ----------
def subtitles(img, t):
    T = tl(); i = seg_at(t)
    if V.SEGS[i].get("nosub"): return
    rel = t - T["starts"][i]; words = []
    for w in T["words"][i]:
        if w[0] in ("–", "-", "…") and words: words[-1] = (words[-1][0] + " " + w[0], words[-1][1], w[2])
        else: words.append(w)
    if not words or rel < words[0][1] - 0.05 or rel > words[-1][2] + 0.4: return
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or w[0][-1] in ".,:!?–": chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    ch = next((c for c in chunks if c[0][1] - 0.05 <= rel <= c[-1][2] + 0.25), None)
    if ch is None: ch = max((c for c in chunks if c[0][1] <= rel), key=lambda c: c[0][1], default=None)
    if not ch: return
    d = ImageDraw.Draw(img)
    f = F("Black", 54); sp = f.getlength(" ") + 14
    texts = [w[0].upper() for w in ch]; widths = [f.getlength(x) for x in texts]
    lines, line, lw = [], [], 0
    for k, wd in enumerate(widths):
        if line and lw + sp + wd > SUB_W: lines.append(line); line, lw = [], 0
        line.append(k); lw += (sp if len(line) > 1 else 0) + wd
    if line: lines.append(line)
    y = SUB_Y - (len(lines) - 1) * 34
    for ln in lines:
        tot = sum(widths[k] for k in ln) + sp * (len(ln) - 1); shrink = min(1.0, SUB_W / tot)
        x = SUB_CX - tot * shrink / 2
        for k in ln:
            w, a0, a1 = ch[k]; active = a0 <= rel <= a1 + 0.05
            ff = F("Black", 54 * shrink * (1.06 if active else 1.0))
            d.text((x + widths[k] * shrink / 2, y), texts[k], font=ff, fill=AMBER if active else WHITE, anchor="mm", stroke_width=6, stroke_fill=INK)
            x += (widths[k] + sp) * shrink
        y += 68

# ---------- Post-Processing ----------
_GRAIN = None
def post(arr, t, flash=0.0, shake=(0, 0)):
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(5)
        _GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
        yy, xx = np.ogrid[0:H, 0:W]
        d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
        globals()["_VIG"] = (1 - 0.55 * ss(0.55, 1.25, d)).astype(np.float32)[..., None]
    # Bloom
    bright = np.clip(arr - 0.55, 0, 4)
    small = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8)).reduce(6).filter(ImageFilter.GaussianBlur(7))
    bl = np.asarray(small.resize((W, H), Image.BILINEAR), np.float32) / 255
    arr = arr + bl * 0.9 + flash
    arr = arr * _VIG
    g = _GRAIN[int(t * FPS) % 6]
    arr = arr + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None] * 0.010
    arr = 1 - np.exp(-np.clip(arr, 0, None) * 1.45)   # weiches Tonemapping
    out = (np.clip(arr / (1 - math.exp(-1.45)), 0, 1) * 255).astype(np.uint8)
    if shake != (0, 0): out = np.roll(out, (int(shake[1]), int(shake[0])), (0, 1))
    return Image.fromarray(out)

# ---------- Frame ----------
def frame(t):
    T = tl(); i = seg_at(t); rel = t - T["starts"][i]; seg = V.SEGS[i]
    scene = V.SCENES[seg["scene"]]
    arr = scene(rel, T["lens"][i], i)
    # Übergang: kurze Überblendung aus der vorigen Szene + Blitz
    flash = 0.0; tr = 0.22
    if i > 0 and rel < tr and not seg.get("cut"):
        prev = V.SCENES[V.SEGS[i - 1]["scene"]](T["lens"][i - 1] - 0.001, T["lens"][i - 1], i - 1)
        k = eio(rel / tr); arr = prev * (1 - k) + arr * k
    if i > 0: flash += 0.22 * max(0, 1 - rel / 0.18)
    flash += seg.get("flash0", 0) * max(0, 1 - rel / 0.3) if i == 0 else 0
    sh = seg.get("shake", 0) * max(0, 1 - rel / 0.5)
    shake = (math.sin(t * 90) * sh * 14, math.cos(t * 77) * sh * 14)
    img = post(arr, t, flash, shake)
    if hasattr(V, "overlay"): V.overlay(img, rel, T["lens"][i], i)
    chain_ui(img, t, i, rel)
    subtitles(img, t)
    if V.SOURCES and not seg.get("nosrc"):
        text_fx(img, (500, 1478), V.SOURCES, F("Medium", 21), fill=(200, 205, 220), alpha=0.75, shadow=0.6)
    return img

# ---------- Sound ----------
def ev(n, k): return np.exp(-np.arange(n) / SR * k)
def sine(f, n): return np.sin(2 * np.pi * f * np.arange(n) / SR)
def smooth(x, k): return np.convolve(x, np.ones(k) / k, "same")

def soundtrack():
    T = tl(); total = T["total"]; n = int(SR * (total + 0.6)); L = np.zeros(n); R = np.zeros(n)
    rng = np.random.default_rng(11); S = T["starts"]; segs = V.SEGS
    def put(s, t, pan=0.0, g=1.0):
        i = int(t * SR); j = min(n, i + len(s))
        if j > i >= 0: L[i:j] += s[:j - i] * g * (1 - max(0, pan)); R[i:j] += s[:j - i] * g * (1 + min(0, pan))
    def boom(dur=1.6, g=1.0):
        m = int(SR * dur); f = 32 + 90 * np.exp(-np.arange(m) / SR * 9)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * ev(m, 2.2)
        nz = smooth(rng.standard_normal(m), 30) * ev(m, 9) * 0.6
        return (b + nz) * g
    def whoosh(dur=0.6, g=1.0):
        m = int(SR * dur); x = rng.standard_normal(m); out = np.zeros(m); k0 = 60
        env = np.sin(np.pi * np.linspace(0, 1, m) ** 1.6) ** 2
        for j, kk in enumerate((80, 30, 10, 4)):
            seg = smooth(x, kk) * (0.4 + j * 0.25); w = np.clip(np.linspace(-1 + j * 0.5, 1 + j * 0.5, m), 0, 1)
            out += seg * w
        return out * env * g
    def clink(f0=1750, g=1.0):
        m = int(SR * 0.7); s = sum(sine(f0 * p, m) * ev(m, 6 + 4 * k) / (k + 1) for k, p in enumerate((1, 2.76, 5.4, 8.93)))
        return s * g
    def tick(hi=True):
        m = int(SR * 0.03); return np.diff(rng.standard_normal(m + 1)) * ev(m, 160) * 0.5 + sine(3200 if hi else 2200, m) * ev(m, 120) * 0.4
    # Drohnen-Bett mit Akkorden je Segment
    for k, s in enumerate(segs):
        t0 = S[k]; dur = T["lens"][k] + 0.6; m = int(SR * dur)
        chord = s.get("chord", V.CHORDS[k % len(V.CHORDS)])
        env = np.minimum(1, np.arange(m) / (SR * 0.35)) * np.minimum(1, (m - np.arange(m)) / (SR * 0.5))
        tt = np.arange(m) / SR; pad = np.zeros(m)
        for fq in chord:
            for det in (-0.6, 0.6):
                ph = 2 * np.pi * (fq + det) * tt
                pad += (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * tt + fq))
        pad = smooth(pad, 6) / (len(chord) * 2)
        sub = sine(chord[0] / 2, m) * 0.6
        g = s.get("music", 1.0)
        put(pad * env * 0.06 * g, t0, -0.2); put(np.roll(pad, 900) * env * 0.06 * g, t0, 0.2); put(sub * env * 0.08 * g, t0)
    # Uhr-Ticken: Puls der Zeitleiste
    t = S[1] if len(S) > 1 else 0.0; tw = next((S[k] for k, s in enumerate(segs) if s.get("twist")), total)
    j = 0
    while t < tw - 0.2:
        put(tick(j % 2 == 0), t, 0.3 if j % 2 else -0.3, 0.22); t += 0.5; j += 1
    # Übergänge
    for k in range(1, len(segs)):
        put(whoosh(0.55, 0.22), S[k] - 0.45)
        put(boom(1.4, 0.55 if not segs[k].get("twist") else 0.95), S[k])
        if segs[k].get("node"): put(clink(1600 + 90 * k, 0.05), S[k] + 0.05, 0.25)
    # Hook: Einschlag + Funkeln
    put(boom(2.4, 1.0), 0.0)
    m = int(SR * 2.4); sp = np.diff(rng.standard_normal(m + 1)) * (rng.random(m) > 0.995) * ev(m, 1.4)
    put(smooth(sp, 3) * 0.6, 0.15, -0.3); put(smooth(np.roll(sp, 999), 3) * 0.6, 0.15, 0.3)
    # Riser vor dem Twist
    tws = [S[k] for k, s in enumerate(segs) if s.get("twist")]
    for t0 in tws:
        m = int(SR * 2.0); put(np.sin(2 * np.pi * np.cumsum(np.linspace(80, 900, m)) / SR) * np.linspace(0, 1, m) ** 2.5 * 0.05, t0 - 2.0)
        put(whoosh(2.0, 0.25) * np.linspace(0, 1, int(SR * 2.0)) ** 2, t0 - 2.0)
    if hasattr(V, "extra_sfx"): V.extra_sfx(put, dict(boom=boom, whoosh=whoosh, clink=clink, tick=tick, sine=sine, ev=ev, smooth=smooth, rng=rng), S)
    music = np.stack([L, R], 1)
    if T["audio"] is not None:
        vo = np.zeros(n)
        for k, a in enumerate(T["audio"]):
            i = int(S[k] * SR); j = min(n, i + len(a)); vo[i:j] += a[:j - i]
        env = smooth(np.abs(vo), 2400); env = env / (env.max() + 1e-9)
        duck = 1 - 0.6 * np.clip(env * 4, 0, 1)
        vo = np.convolve(vo, [1, -0.97], "same") * 0.9 + vo * 0.1
        vo = np.tanh(vo * 2.2) / 2.2 * 1.6
        music = music * duck[:, None] * 0.85 + vo[:, None]
    st = np.tanh(music * 1.1) * 0.9
    return (st * 32767).astype(np.int16)

# ---------- Rendern ----------
def encode(f0, f1, path):
    tmp = path[:-4] + ".part.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fr in range(f0, f1): p.stdin.write(frame(fr / FPS).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() != 0: raise SystemExit("ffmpeg failed")
    os.replace(tmp, path)

def run(g):
    for k, v in g.items():
        if k.isupper() or k in ("overlay", "extra_sfx"): setattr(V, k, v)
    V.dir = os.path.dirname(os.path.abspath(g["__file__"])); V.name = os.path.splitext(os.path.basename(g["__file__"]))[0]
    V.file = os.path.abspath(g["__file__"])
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    out = os.path.abspath(args[0]); wd = os.path.dirname(out); os.makedirs(wd, exist_ok=True)
    T = tl(); nf = int(round(T["total"] * FPS))
    if len(args) > 1 and args[1] == "--part": encode(int(args[2]), int(args[3]), args[4]); return
    if len(args) > 1 and args[1] == "--preview":
        for ts in args[2:]: frame(float(ts)).save(os.path.join(wd, f"pv_{V.name}_{float(ts):05.1f}.png"))
        print("Stimme:", T["voiced"], "| Tempo:", round(T["tempo"], 3), "| Länge:", round(T["total"], 1), "| Starts:", [round(s, 1) for s in T["starts"]]); return
    print("Stimme:", "ElevenLabs" if T["voiced"] else "keine (Vorschau-Timing)", "| Länge:", round(T["total"], 1), "s | Tempo:", round(T["tempo"], 3))
    k = 4; cuts = [nf * i // k for i in range(k + 1)]; parts = [os.path.join(wd, f"_{V.name}_part{i}.mp4") for i in range(k)]
    procs = [subprocess.Popen([sys.executable, V.file, out, "--part", str(cuts[i]), str(cuts[i + 1]), parts[i]]) for i in range(k)]
    pcm = soundtrack(); wav = os.path.join(wd, f"_{V.name}_audio.wav")
    with wave.open(wav, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    for p in procs:
        if p.wait() != 0: raise SystemExit("render failed")
    lst = os.path.join(wd, f"_{V.name}_list.txt")
    with open(lst, "w") as fl: fl.writelines(f"file '{p}'\n" for p in parts)
    raw = os.path.join(wd, f"_{V.name}_raw.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "pcm_s16le", "-t", f"{T['total']:.3f}", raw.replace(".mp4", ".mkv")], check=True)
    raw = raw.replace(".mp4", ".mkv")
    # 2-Pass-Lautheit auf −14 LUFS
    j = subprocess.run(["ffmpeg", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(j[j.rfind("{"):j.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", out], check=True)
    for p in parts + [wav, lst, raw]: os.remove(p)
    print("fertig:", out)
