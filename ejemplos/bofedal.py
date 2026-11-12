"""Perfil esquemático de un bofedal (humedal altoandino) con pozos de monitoreo P1-P3 y una vicuña pastoreando.

Uso:  python ejemplos/bofedal.py
Genera las ilustraciones SVG en static/demo/bofedal/ y un proyecto editable de BioFig en data/projects/.
Coordenadas de diseño en el sistema de la imagen de referencia (1280 x 609 px); el lienzo es S = 1.875 veces mayor.
"""
import json
import math
import random
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "demo" / "bofedal"
OUT.mkdir(parents=True, exist_ok=True)
W, H, S = 1280, 609, 1.875
rnd = random.Random(7)


def interp(pts, x):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1] if x > pts[-1][0] else pts[0][1]


# superficie del suelo (techo de la turba) y nivel freático
TOP_L = [(0, 290), (60, 292), (100, 288), (200, 284), (300, 290), (400, 300), (480, 315), (555, 323)]
TOP_R = [(589, 325), (650, 332), (750, 345), (850, 360), (930, 375), (985, 389)]
CH0, CH1 = 555, 589                  # canal donde está P2 (más angosto que el tubo)
WT = [(0, 374), (80, 368), (150, 378), (250, 382), (400, 386), (546, 390), (600, 394), (700, 396), (900, 396),
      (1000, 394), (1280, 392)]
WET = 390                            # superficie de la vega húmeda (derecha)


def top(x):
    if x <= CH0:
        return interp(TOP_L, x)
    if x < CH1:
        return interp(WT, x) - 4
    if x <= 985:
        return interp(TOP_R, x)
    return WET


def wt(x):
    return interp(WT, x)


def poly(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def path_along(f, x0, x1, step=4, jitter=0.0):
    pts = [(x, f(x) + (rnd.uniform(-jitter, jitter) if jitter else 0)) for x in range(int(x0), int(x1) + 1, step)]
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
       '<defs>',
       '<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
       '<stop offset="0" stop-color="#fff"/><stop offset=".78" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>',
       f'<mask id="m"><rect x="0" y="360" width="{W}" height="{H - 360}" fill="url(#fade)"/></mask>',
       '</defs>']

# ---------------------------------------------------------------- zona saturada en capas (sedimentos)
sat = [f'<g mask="url(#m)"><polygon points="{poly([(x, wt(x)) for x in range(0, W + 1, 10)] + [(W, H), (0, H)])}" fill="#e3ebf6"/>']
y = 404
bands = []
while y < 600:
    h = rnd.uniform(9, 16)
    bands.append((y, h))
    y += h + rnd.uniform(14, 24)
for i, (y, h) in enumerate(bands):  # bandas azules onduladas
    ph, amp = rnd.uniform(0, 6), rnd.uniform(1.5, 3.5)
    up = [(x, y + amp * math.sin(x / 90 + ph)) for x in range(0, W + 1, 16)]
    dn = [(x, y + h + amp * math.sin(x / 70 + ph + 1)) for x in range(W, -1, -16)]
    sat.append(f'<polygon points="{poly(up + dn)}" fill="#8ea6d3" opacity=".85"/>')
dots = []
for (y, h), (y2, _) in zip(bands, bands[1:] + [(610, 0)]):  # puntillado marrón entre bandas
    for _ in range(int((y2 - y - h) * 26)):
        x = rnd.uniform(0, W)
        yy = rnd.uniform(y + h, y2)
        if yy > wt(x) + 3:
            dots.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="{rnd.uniform(.7, 1.6):.2f}" fill="#b27a52"/>')
for _ in range(2600):  # puntillado azul en toda la zona saturada
    x, yy = rnd.uniform(0, W), rnd.uniform(395, 605)
    if yy > wt(x) + 2:
        dots.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="{rnd.uniform(.6, 1.3):.2f}" fill="#9fb8de"/>')
sat += dots + ["</g>"]
svg += sat

# ---------------------------------------------------------------- turba (dos bloques separados por el canal)
for x0, x1 in ((0, CH0), (CH1, 985)):
    pts = [(x, top(x)) for x in range(x0, x1 + 1, 4)] + [(x, wt(x)) for x in range(x1, x0 - 1, -4)]
    cid = f"peat{x0}"
    svg.append(f'<clipPath id="{cid}"><polygon points="{poly(pts)}"/></clipPath>')
    svg.append(f'<polygon points="{poly(pts)}" fill="#8f5d3e"/>')
    fib = []
    for _ in range(int((x1 - x0) * 1.3)):  # textura fibrosa
        x = rnd.uniform(x0, x1)
        t, b = top(x), wt(x)
        if b - t < 4:
            continue
        yy = rnd.uniform(t + 2, b - 1)
        L, a = rnd.uniform(8, 26), math.radians(rnd.uniform(-9, 9))
        col = rnd.choice(["#6c4027", "#7a4a2e", "#a8744e", "#b4825b"])
        fib.append(f'<line x1="{x:.1f}" y1="{yy:.1f}" x2="{x + L * math.cos(a):.1f}" y2="{yy + L * math.sin(a):.1f}" '
                   f'stroke="{col}" stroke-width="{rnd.uniform(1, 2.2):.1f}" stroke-linecap="round" opacity=".55"/>')
    svg.append(f'<g clip-path="url(#{cid})">{"".join(fib)}</g>')
# agua en el canal de P2
svg.append(f'<polygon points="{poly([(CH0, top(CH0)), (CH0 + 6, wt(CH0) - 6), (CH1 - 6, wt(CH1) - 6), (CH1, top(CH1)), (CH1, wt(CH1)), (CH0, wt(CH0))])}" fill="#cfe0f2"/>')

# ---------------------------------------------------------------- nivel freático
svg.append(f'<path d="{path_along(wt, 0, W, 6)}" fill="none" stroke="#2f8ad8" stroke-width="3.2" stroke-linecap="round"/>')

# ---------------------------------------------------------------- superficie y vegetación
svg.append(f'<path d="{path_along(top, 0, 985, 3, .8)}" fill="none" stroke="#333" stroke-width="1.1"/>')
svg.append(f'<path d="M985 {WET} L{W} {WET - 2}" fill="none" stroke="#333" stroke-width="1.1"/>')
grass = []
for x in range(0, 990, 3):  # césped del bofedal (plantas en cojín)
    if CH0 + 4 < x < CH1 - 4:
        continue
    t = top(x)
    for _ in range(2):
        h, lean = rnd.uniform(3, 11), rnd.uniform(-3, 3)
        col = rnd.choice(["#2f9e44", "#37b24d", "#40a84a", "#2b8a3e"])
        grass.append(f'<path d="M{x:.1f} {t:.1f} q{lean / 2:.1f} {-h / 2:.1f} {lean:.1f} {-h:.1f}" stroke="{col}" '
                     f'stroke-width="1.7" fill="none" stroke-linecap="round"/>')
svg.append(f'<path d="{path_along(lambda x: top(x) - 2, 0, CH0, 3, 1.6)}" fill="none" stroke="#3aaa4a" stroke-width="3"/>')
svg.append(f'<path d="{path_along(lambda x: top(x) - 2, CH1, 985, 3, 1.6)}" fill="none" stroke="#3aaa4a" stroke-width="3"/>')
for x in range(992, 1270, 3):  # vega húmeda a la derecha
    if 1000 <= x <= 1105:
        col, hmin, hmax = rnd.choice(["#a9d34f", "#94c43c", "#c1e06b"]), 6, 17
    elif 1125 <= x <= 1178:
        col, hmin, hmax = rnd.choice(["#2f8f46", "#3aa555", "#237a3b"]), 12, 30
    else:
        col, hmin, hmax = rnd.choice(["#2e6b3a", "#3f7f45"]), 3, 13
    if rnd.random() < 0.75:
        h, lean = rnd.uniform(hmin, hmax), rnd.uniform(-2, 2)
        grass.append(f'<path d="M{x:.1f} {WET:.1f} l{lean:.1f} {-h:.1f}" stroke="{col}" stroke-width="2" stroke-linecap="round"/>')
svg.append("".join(grass))
# tallos secos y una espiga verde
for x0, x1, y1 in ((165, 190, 262), (380, 386, 238), (486, 486, 250), (540, 545, 286), (430, 428, 292), (262, 270, 280)):
    svg.append(f'<path d="M{x0} {top(x0):.1f} Q{(x0 + x1) / 2 + 3:.1f} {(top(x0) + y1) / 2:.1f} {x1} {y1}" stroke="#a5653d" '
               f'stroke-width="3" fill="none" stroke-linecap="round"/>')
svg.append(f'<path d="M78 {top(78):.1f} Q70 250 78 225 T90 200" stroke="#37a84a" stroke-width="3.2" fill="none" stroke-linecap="round"/>')
svg.append("</svg>")
(OUT / "perfil.svg").write_text("".join(svg), encoding="utf-8")


# ---------------------------------------------------------------- pozos de monitoreo (piezómetros)
def piezometer(name, top_y, ground, water, bottom, w=40):
    h = bottom - top_y
    g, wl = ground - top_y, water - top_y
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-3 -3 {w + 6} {h + 6}">',
           f'<rect x="0" y="0" width="{w}" height="{wl}" fill="#ffffff"/>',                       # interior seco
           f'<rect x="0" y="{wl}" width="{w}" height="{h - wl}" fill="#ffffff" opacity=".35"/>',   # interior bajo el agua
           f'<path d="M0 {wl} V0 H{w} V{wl}" fill="none" stroke="#111" stroke-width="3.2" stroke-linejoin="round"/>',
           f'<path d="M0 {wl} V{h} H{w} V{wl}" fill="none" stroke="#111" stroke-width="2.6" stroke-dasharray="7 5"/>']
    yy = g + 14
    while yy < h - 8:  # ranuras del filtro
        out.append(f'<path d="M{w * .3:.1f} {yy + 6:.1f} L{w * .62:.1f} {yy - 3:.1f}" stroke="#111" stroke-width="2.4" stroke-linecap="round"/>')
        yy += 21
    out.append("</svg>")
    (OUT / f"{name}.svg").write_text("".join(out), encoding="utf-8")
    return w, h


TUBES = {  # nombre: (x izquierda, y superior, superficie, nivel freático, fondo)
    "P1": (97, 230, top(116), wt(116), 548),
    "P2": (552, 220, 326, wt(572), 540),
    "P3": (1016, 218, WET, wt(1036), 537),
}
for k, (x, ty, gr, wa, bo) in TUBES.items():
    piezometer("piezometro_" + k.lower(), ty, gr, wa, bo)

# ---------------------------------------------------------------- proyecto de BioFig
def nid():
    return "n" + uuid.uuid4().hex[:8]


def svg_size(p):
    import re
    vb = re.search(r'viewBox="([-\d. ]+)"', p.read_text(encoding="utf-8")[:300]).group(1).split()
    return float(vb[2]), float(vb[3])


def icon(src, name, cx, cy, w, h, author="BioFig", lic="Propio (libre)", source="BioFig", **extra):
    return {"kind": "icon", "id": nid(), "x": round(cx * S, 1), "y": round(cy * S, 1), "rotation": 0, "opacity": 1,
            "src": src, "iconId": "own:" + name, "width": round(w * S, 1), "height": round(h * S, 1), "flip": False,
            "tint": None, "alts": [], "meta": {"name": name, "author": author, "license": lic, "source": source}, **extra}


def text(t, x, y, size, fill="#222", style="normal", align="center", width=None, halo=False):
    it = {"kind": "text", "id": nid(), "x": round(x * S, 1), "y": round(y * S, 1), "rotation": 0, "opacity": 1, "text": t,
          "fontSize": round(size * S, 1), "fontFamily": "Arial", "fontStyle": style, "fill": fill, "align": align,
          "halo": halo}
    if width:
        it["width"] = round(width * S, 1)
        if align == "center":
            it["x"] = round(it["x"] - it["width"] / 2, 1)
    return it


items = [icon("/static/demo/bofedal/perfil.svg", "Perfil del bofedal", W / 2, H / 2, W, H, locked=True)]
items[0]["draggable"] = False
for k, (x, ty, gr, wa, bo) in TUBES.items():
    pw, ph = svg_size(OUT / f"piezometro_{k.lower()}.svg")
    items.append(icon(f"/static/demo/bofedal/piezometro_{k.lower()}.svg", f"Pozo de monitoreo {k}",
                      x + 20, ty - 3 + ph / 2, pw, ph))
    items.append(text(k, x + 20, ty + 5, 15, width=40))

# vicuña de PhyloPic (CC0, Kai Caspar), pastoreando: teñida de marrón
VIC = "f6280a5d-e66b-4d57-ae02-0d7388935c30"
ALP = "5629fe18-166f-4e7f-ac6a-ce29c95bec56"
vic = icon(f"/phylopic/{VIC}.svg", "Lama vicugna", 812, 217, 370, 370 / 1.3714,
           author="Kai Caspar", lic="CC0", source="PhyloPic")
vic["iconId"] = "pp:" + VIC
vic["tint"] = "#6b4428"
vic["alts"] = [{"id": "pp:" + ALP, "name": "Lama pacos (alpaca)", "src": f"/phylopic/{ALP}.svg", "author": "Ben Murrell",
                "license": "CC0", "source": "PhyloPic", "aspect": 0.9674}]
items.append(vic)

# rótulos (opcionales: se pueden borrar)
items.append(text("Turba", 250, 322, 15, fill="#f6eadc", style="bold", width=120))
items.append(text("Nivel freático", 1185, 399, 12, fill="#1f6fb8", style="italic", width=160, halo=True))
items.append(text("Sedimentos saturados", 300, 452, 13, fill="#2c3e5c", style="italic", width=260, halo=True))

pid = f"bofedal-perfil-{uuid.uuid4().hex[:6]}"
doc = {"w": round(W * S), "h": round(H * S), "bg": "#ffffff", "items": items}
(ROOT / "data" / "projects" / f"{pid}.json").write_text(json.dumps(
    {"id": pid, "name": "Bofedal - perfil con pozos de monitoreo", "updated": time.time(), "doc": doc, "thumb": None},
    ensure_ascii=False), encoding="utf-8")
print("SVG en", OUT, "| proyecto:", pid, "|", len(items), "elementos")
print("perfil.svg:", round((OUT / "perfil.svg").stat().st_size / 1024), "KB")
