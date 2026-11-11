"""Thumbnail: Was wäre, wenn du nie wieder schläfst? (1080x1920 für Shorts + 1280x720)"""
import math, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image, ImageDraw
import kr, lib
from kr import W, H, F, text_fx, WHITE, ORANGE, AMBER, CYAN, RED

def room(warp=0.5):
    bg = kr.vgrad((20, 14, 50), (4, 5, 14))
    bg += kr.radial(540, 980, 520, (120, 60, 200), 0.45)
    bg += kr.radial(540, 980, 300, (255, 90, 60), 0.25)
    bg += lib.stars(0, 0, 0.3)
    yy, xx = np.ogrid[0:H, 0:W]
    w = (np.sin(xx / 55 + 1.3) * np.cos(yy / 75 - 0.7)) * warp
    bg += w[..., None] * np.array([0.5, 0.2, 0.7], np.float32) * 0.35
    return bg

def clock(img, cx, cy, r):
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(3): d.ellipse([cx - r - 30 - k * 22, cy - r - 30 - k * 22, cx + r + 30 + k * 22, cy + r + 30 + k * 22], outline=ORANGE + (90 - k * 25,), width=6)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 12, 28, 235), outline=CYAN + (255,), width=12)
    for k in range(12):
        an = k * math.pi / 6; r1 = r - 26; r2 = r - (80 if k % 3 == 0 else 52)
        d.line([cx + r1 * math.sin(an), cy - r1 * math.cos(an), cx + r2 * math.sin(an), cy - r2 * math.cos(an)], fill=WHITE + (255,), width=14 if k % 3 == 0 else 7)
    for ang, ln, wd, col in ((math.radians(95), r * 0.5, 22, WHITE), (math.radians(-60), r * 0.78, 14, ORANGE)):
        d.line([cx, cy, cx + ln * math.sin(ang), cy - ln * math.cos(ang)], fill=col + (255,), width=wd)
    d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=ORANGE + (255,))

def battery(img, x, y, s=1.0):
    d = ImageDraw.Draw(img, "RGBA"); w, h = 150 * s, 270 * s
    d.rounded_rectangle([x - w / 2, y, x + w / 2, y + h], int(24 * s), outline=WHITE + (255,), width=int(9 * s))
    d.rectangle([x - 30 * s, y - 22 * s, x + 30 * s, y], fill=WHITE + (255,))
    d.rounded_rectangle([x - w / 2 + 14 * s, y + h - 14 * s - 30 * s, x + w / 2 - 14 * s, y + h - 14 * s], int(10 * s), fill=RED + (255,))
    text_fx(img, (x, y + h / 2 - 10 * s), "1%", F("Black", 64 * s), fill=RED, glow=RED, glow_r=12)

# --- Hochformat 1080x1920 (Shorts) ---
img = kr.post(room(), 0.0)
text_fx(img, (540, 330), "NIE WIEDER", F("Black", 150), fill=WHITE)
text_fx(img, (540, 500), "SCHLAFEN?", lib.fit_font("SCHLAFEN?", 190, 980), fill=ORANGE, glow=ORANGE, glow_r=30)
clock(img, 540, 1010, 300)
lib.paste_emoji(img, "😵‍💫", 230, 540, 1010)
clock_only = img.copy()
battery(img, 875, 1150, 0.8)
d = ImageDraw.Draw(img, "RGBA")
d.rounded_rectangle([170, 1440, 910, 1580], 70, fill=(8, 10, 22, 230), outline=ORANGE + (255,), width=8)
text_fx(img, (540, 1512), "264 STUNDEN WACH", F("Black", 66), fill=WHITE)
img.save(os.path.join(ROOT, "thumbnails", "nie_schlafen_1080x1920.jpg"), quality=94)

# --- Querformat 1280x720 (für lange Videos / Community) ---
q = Image.new("RGB", (1280, 720))
bgq = kr.post(room(), 0.0).crop((0, 600, 1080, 1208)).resize((1280, 720), Image.LANCZOS)
q.paste(bgq, (0, 0))
text_fx(q, (370, 230), "NIE WIEDER", F("Black", 96), fill=WHITE)
text_fx(q, (370, 355), "SCHLAFEN?", lib.fit_font("SCHLAFEN?", 120, 640), fill=ORANGE, glow=ORANGE, glow_r=24)
qq = ImageDraw.Draw(q, "RGBA")
qq.rounded_rectangle([90, 470, 650, 570], 50, fill=(8, 10, 22, 230), outline=ORANGE + (255,), width=6)
text_fx(q, (370, 520), "264 STUNDEN WACH", F("Black", 48), fill=WHITE)
cl = Image.new("RGB", (W, H)); 
sub = clock_only.crop((180, 650, 900, 1370)).resize((440, 440), Image.LANCZOS)
m = Image.new("L", (440, 440), 0); ImageDraw.Draw(m).ellipse([0, 0, 439, 439], fill=255)
q.paste(sub, (800, 140), m)
q.save(os.path.join(ROOT, "thumbnails", "nie_schlafen_1280x720.jpg"), quality=94)
print("ok")
