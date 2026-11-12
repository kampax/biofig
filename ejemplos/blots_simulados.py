"""Genera imagenes SIMULADAS de dot blot (fluorescencia verde) y western blot para probar las figuras.

No son datos reales: cada imagen lleva la marca "SIMULADO". Requiere Pillow y NumPy.
Uso:  python ejemplos/blots_simulados.py   ->  static/demo/*.png
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "static" / "demo"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)


def font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def watermark(img, dark=True):
    d = ImageDraw.Draw(img)
    f = font(max(11, min(img.width, img.height) // 14))
    txt = "SIMULADO"
    w = d.textlength(txt, font=f)
    d.text((img.width - w - 6, img.height - f.size - 6), txt, font=f,
           fill=(150, 170, 160) if dark else (120, 118, 140))
    return img


def fluo_field(w, h, spots, bg=(7, 13, 10), noise=6):
    """Campo oscuro con manchas verdes gaussianas. spots: (x, y, radio, intensidad 0-1) en fracciones."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.zeros((h, w), np.float32)
    for fx, fy, fr, inten in spots:
        cx, cy, r = fx * w, fy * h, fr * min(w, h)
        # mancha irregular: suma de 3 gaussianas desplazadas
        for _ in range(3):
            ox, oy = rng.normal(0, r * 0.18, 2)
            g += inten / 3 * np.exp(-(((xx - cx - ox) ** 2) + ((yy - cy - oy) ** 2)) / (2 * (r * rng.uniform(.75, 1.05)) ** 2))
    g = np.clip(g, 0, 1.35)
    vign = 1 - 0.25 * (((xx / w - .5) ** 2 + (yy / h - .5) ** 2) * 2)
    base = np.stack([np.full((h, w), bg[0]), np.full((h, w), bg[1]), np.full((h, w), bg[2])], -1).astype(np.float32)
    base *= vign[..., None]
    base += rng.normal(0, noise, (h, w, 1))
    rgb = base.copy()
    rgb[..., 0] += g * 70
    rgb[..., 1] += g * 230
    rgb[..., 2] += g * 60
    sat = np.clip(g - 1, 0, 1)  # centro saturado casi blanco
    rgb += sat[..., None] * 140
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))


# --------------------------------------------------------------- Figura A: dot blots (un punto PMCA)
watermark(fluo_field(470, 250, [(0.26, 0.48, 0.17, 1.15), (0.62, 0.5, 0.08, 0.10)])).save(OUT / "dotblot_A.png")
watermark(fluo_field(500, 238, [(0.24, 0.5, 0.21, 1.25), (0.66, 0.52, 0.07, 0.08)])).save(OUT / "dotblot_B.png")

# --------------------------------------------------------------- Figura B (C): lavados I-V y elucion
lanes = []
intens = [(1.2, 1.0), (0.55, 0.45), (0.35, 0.3), (0.18, 0.15), (0.12, 0.1)]
for top, bot in intens:
    lanes.append(fluo_field(280, 400, [(0.32, 0.27, 0.16, top), (0.36, 0.73, 0.16, bot),
                                       (0.75, 0.3, 0.06, top * .25), (0.78, 0.7, 0.06, bot * .25)]))
strip = Image.new("RGB", (5 * 280 + 4 * 6, 400), (40, 48, 44))
for i, ln in enumerate(lanes):
    strip.paste(ln, (i * 286, 0))
watermark(strip).save(OUT / "dotblot_lavados.png")
watermark(fluo_field(290, 420, [(0.4, 0.3, 0.14, 0.28), (0.42, 0.72, 0.14, 0.22)])).save(OUT / "dotblot_elucion.png")

# --------------------------------------------------------------- Figura B (B): western blot
W, H = 330, 1000
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
img = np.empty((H, W, 3), np.float32)
img[...] = (222, 220, 232)
img -= (yy / H * 10)[..., None]
img += rng.normal(0, 2.5, (H, W, 1))
# posiciones (fraccion de alto) segun los marcadores de la figura: 150 kDa ~ .19, 52 kDa ~ .75
band_y = {"PMCA ~134 kDa": 0.25, "Tubulina ~55 kDa": 0.72}
lanes_x = [0.22, 0.5, 0.78]
bands = [  # (carril, banda, intensidad)
    (0, "PMCA ~134 kDa", 0.85), (0, "Tubulina ~55 kDa", 0.9),
    (1, "Tubulina ~55 kDa", 0.15),
    (2, "Tubulina ~55 kDa", 1.0),
]
dark = np.zeros((H, W), np.float32)
for lane, b, inten in bands:
    cx, cy = lanes_x[lane] * W, band_y[b] * H
    dark += inten * np.exp(-((xx - cx) / (W * 0.1)) ** 8) * np.exp(-((yy - cy) / 11) ** 2)
img -= dark[..., None] * np.array([150, 150, 135])
wb = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
watermark(wb, dark=False).save(OUT / "western.png")

print("Imagenes simuladas en", OUT)
for p in sorted(OUT.glob("*.png")):
    print(" ", p.name, Image.open(p).size)
