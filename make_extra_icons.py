"""Iconos propios adicionales de BioFig (diseño original, libre): membranas, gráficos y símbolos,
satélites y teledetección, equipo de campo, paisajes y agricultura.

Uso:  python make_extra_icons.py   ->  static/extra/*.svg + static/extra/extra.json
"""
import json
import math
import random
from pathlib import Path

OUT = Path(__file__).parent / "static" / "extra"
OUT.mkdir(parents=True, exist_ok=True)
rnd = random.Random(3)
ICONS = []  # (archivo, nombre, categoría, grupos, etiquetas)
INK = "#2b2f33"


def save(fname, name, cat, groups, tags, w, h, body):
    (OUT / fname).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">{body}</svg>', encoding="utf-8")
    ICONS.append((fname, name, cat, groups, tags))


# =============================================================================== MEMBRANAS
HEAD, HEAD_ST, TAIL = "#f2c94c", "#c99a1e", "#e0a43c"
MEM = ["membranas", "molecular", "celular"]
THICK = 94  # distancia entre las cabezas de las dos capas


def lipid(x, y, nx, ny, L=35, r=6.5, head=HEAD, stroke=HEAD_ST):
    """Fosfolípido: cabeza en (x,y); las colas apuntan en la dirección (nx,ny)."""
    px, py = -ny, nx
    t = []
    for s in (-2.6, 2.6):
        x0, y0 = x + px * s + nx * r * .7, y + py * s + ny * r * .7
        x1, y1 = x0 + nx * L, y0 + ny * L
        mx, my = (x0 + x1) / 2 + px * s * .5, (y0 + y1) / 2 + py * s * .5
        t.append(f'<path d="M{x0:.1f} {y0:.1f}Q{mx:.1f} {my:.1f} {x1:.1f} {y1:.1f}" fill="none" stroke="{TAIL}" stroke-width="2.4" stroke-linecap="round"/>')
    return "".join(t) + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{head}" stroke="{stroke}" stroke-width="1.6"/>'


def resample(pts, spacing):
    """Puntos a distancia fija sobre una polilínea, con su tangente."""
    out, carry = [], spacing / 2
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg == 0:
            continue
        tx, ty = (x1 - x0) / seg, (y1 - y0) / seg
        d = carry
        while d <= seg:
            out.append((x0 + tx * d, y0 + ty * d, tx, ty))
            d += spacing
        carry = d - seg
    return out


def leaflet(pts, tails, spacing=14, L=35, r=6.5, colorf=None):
    """Monocapa. tails: 'down' | 'up' | ('in', cx, cy) | ('out', cx, cy): hacia dónde apuntan las colas."""
    out = []
    for x, y, tx, ty in resample(pts, spacing):
        nx, ny = -ty, tx
        if tails == "down":
            s = 1 if ny > 0 else -1
        elif tails == "up":
            s = 1 if ny < 0 else -1
        else:
            kind, cx, cy = tails
            toward = (cx - x) * nx + (cy - y) * ny
            s = (1 if toward > 0 else -1) * (1 if kind == "in" else -1)
        hc, sc = colorf(x, y) if colorf else (HEAD, HEAD_ST)
        out.append(lipid(x, y, nx * s, ny * s, L, r, hc, sc))
    return "".join(out)


def arc_pts(cx, cy, R, a0, a1, n=160):
    return [(cx + R * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + R * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def bilayer_h(x0, x1, ytop, colorf=None):
    """Bicapa horizontal: capa superior en ytop, inferior en ytop+THICK; colas enfrentadas en el centro."""
    return (leaflet([(x0, ytop), (x1, ytop)], "down", colorf=colorf)
            + leaflet([(x0, ytop + THICK), (x1, ytop + THICK)], "up", colorf=colorf))


def bilayer_arc(cx, cy, R, a0, a1):
    """Bicapa curva: capa externa de radio R (colas hacia el centro) e interna de radio R-THICK (colas hacia afuera)."""
    return leaflet(arc_pts(cx, cy, R, a0, a1), ("in", cx, cy)) + leaflet(arc_pts(cx, cy, R - THICK, a0, a1), ("out", cx, cy))


save("mem_bicapa_larga.svg", "Bicapa lipídica larga", "Membranas", MEM, "membrana bicapa bilayer lipid fosfolipido",
     800, 130, bilayer_h(0, 800, 18))
save("mem_bicapa_curva.svg", "Bicapa lipídica curva", "Membranas", MEM, "membrana bicapa curva curved bilayer", 640, 240,
     bilayer_arc(320, 400, 380, 205, 335))
save("mem_bicapa_codo.svg", "Bicapa lipídica en codo (90°)", "Membranas", MEM, "membrana bicapa curva codo curved bilayer", 300, 300,
     bilayer_arc(290, 290, 272, 180, 270))
save("mem_vesicula.svg", "Vesícula / liposoma", "Membranas", MEM, "vesicula liposoma liposome vesicle exosoma", 300, 300,
     '<circle cx="150" cy="150" r="46" fill="#eaf3fb"/>' + bilayer_arc(150, 150, 140, 0, 360))
save("mem_micela.svg", "Micela", "Membranas", MEM, "micela micelle detergente surfactante", 200, 200,
     leaflet(arc_pts(100, 100, 88, 0, 360, 100), ("in", 100, 100), spacing=16, L=46))
save("mem_micela_inversa.svg", "Micela inversa", "Membranas", MEM, "micela inversa reverse micelle", 200, 200,
     '<circle cx="100" cy="100" r="24" fill="#cfe3f5"/>' + leaflet(arc_pts(100, 100, 34, 0, 360, 60), ("out", 100, 100), spacing=14, L=44))
save("mem_fosfolipido.svg", "Fosfolípido", "Membranas", MEM, "fosfolipido phospholipid lipido lipid", 60, 120,
     lipid(30, 16, 0, 1, L=90, r=13))
save("mem_colesterol.svg", "Colesterol", "Membranas", MEM, "colesterol cholesterol esterol sterol", 70, 120,
     '<g fill="#f4a261" stroke="#c46a1f" stroke-width="2"><polygon points="20,40 35,31 50,40 50,57 35,66 20,57"/>'
     '<polygon points="20,57 35,66 35,83 20,92 5,83 5,66"/><polygon points="35,83 50,74 65,83 65,100 50,109 35,100"/></g>'
     '<circle cx="35" cy="16" r="9" fill="#e76f51" stroke="#a63d22" stroke-width="2"/><path d="M35 25V31" stroke="#a63d22" stroke-width="3"/>')

# proteínas en la membrana: bicapa a ambos lados de una proteína de 112 px de alto
BAR = '<rect x="{x}" y="6" width="{w}" height="118" rx="{rx}" fill="{f}" stroke="{s}" stroke-width="3"/>'
sides = bilayer_h(0, 196, 18) + bilayer_h(324, 520, 18)
save("mem_proteina_transmembrana.svg", "Proteína transmembrana en bicapa", "Membranas", MEM,
     "proteina transmembrana transmembrane protein membrana", 520, 130,
     sides + BAR.format(x=200, w=120, rx=40, f="#7fb3d5", s="#2e6a99")
     + '<path d="M222 40h76M222 66h76M222 92h76" stroke="#2e6a99" stroke-width="3" opacity=".5"/>')
save("mem_canal.svg", "Canal iónico en bicapa", "Membranas", MEM, "canal ionico ion channel poro pore membrana", 520, 130,
     sides + BAR.format(x=198, w=52, rx=24, f="#48c9b0", s="#148f77") + BAR.format(x=270, w=52, rx=24, f="#48c9b0", s="#148f77")
     + "".join(f'<circle cx="260" cy="{y}" r="7" fill="#f39c12" stroke="#b9770e" stroke-width="2"/>' for y in (30, 65, 100)))
gpcr = "".join(f'<rect x="{199 + i * 17.5:.1f}" y="{8 + (i % 2) * 6}" width="15" height="{110 - (i % 2) * 8}" rx="7" fill="#b39ddb" stroke="#6a4ca6" stroke-width="2.4"/>' for i in range(7))
save("mem_gpcr.svg", "Receptor acoplado a proteína G (7TM)", "Membranas", MEM, "gpcr receptor proteina g siete transmembrana 7tm",
     520, 170, sides + gpcr + '<ellipse cx="262" cy="148" rx="34" ry="16" fill="#f6bd60" stroke="#c98a1e" stroke-width="2.4"/>'
     '<text x="262" y="153" font-family="Arial" font-size="15" text-anchor="middle" fill="#6b4b10">Gα</text>')
save("mem_transportador.svg", "Transportador en bicapa", "Membranas", MEM, "transportador transporter carrier bomba pump membrana",
     520, 130, sides + '<path d="M196 8h128l-18 57 18 57H196l18-57z" fill="#f28482" stroke="#b5413f" stroke-width="3"/>'
     '<path d="M260 22v86m-9-12 9 13 9-13" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round"/>')

# balsa lipídica: cabezas de esfingolípidos en otro color y colesterol intercalado
raft = lambda x, y: ("#e76f51", "#a63d22") if 300 < x < 500 else (HEAD, HEAD_ST)
chol = "".join(f'<g transform="translate({x} {y})"><polygon points="0,0 7,-4 14,0 14,8 7,12 0,8" fill="#f4a261" stroke="#c46a1f" stroke-width="1.5"/></g>'
               for x in range(318, 490, 28) for y in (36, 82))
save("mem_balsa_lipidica.svg", "Balsa lipídica", "Membranas", MEM, "balsa lipidica lipid raft colesterol esfingolipido", 800, 130,
     bilayer_h(0, 800, 18, colorf=raft) + chol)
save("mem_doble_membrana.svg", "Doble membrana", "Membranas", MEM, "doble membrana double membrane mitocondria envoltura nuclear",
     700, 260, bilayer_h(0, 700, 18) + bilayer_h(0, 700, 148))

# endocitosis: la membrana se hunde formando una fosa (curva suave, capa inferior paralela)
def dip(x, depth=120, sigma=88, y0=20):
    return y0 + depth * math.exp(-((x - 300) / sigma) ** 2)


top = [(x, dip(x)) for x in range(0, 601, 3)]
bot = []
for i in range(1, len(top) - 1):  # curva paralela a THICK px por debajo (hacia el lado convexo de la fosa)
    (xa, ya), (xb, yb) = top[i - 1], top[i + 1]
    tx, ty = xb - xa, yb - ya
    n = math.hypot(tx, ty)
    nx, ny = -ty / n, tx / n
    if ny < 0:
        nx, ny = -nx, -ny
    bot.append((top[i][0] + nx * THICK, top[i][1] + ny * THICK))
save("mem_endocitosis.svg", "Endocitosis (invaginación)", "Membranas", MEM, "endocitosis endocytosis invaginacion fosa clatrina vesicula",
     600, 250, leaflet(top, "down") + leaflet(bot, "up"))

# membrana plasmática con glucocáliz (cadenas de azúcares sobre la capa externa)
glyco = []
for x in range(30, 780, 46):
    chain = [(x, 18)]
    for _ in range(rnd.randint(3, 5)):
        chain.append((chain[-1][0] + rnd.uniform(-10, 10), chain[-1][1] - 14))
    glyco.append(f'<polyline points="{" ".join(f"{a:.0f},{b + 60:.0f}" for a, b in chain)}" fill="none" stroke="#6a994e" stroke-width="2"/>')
    glyco += [f'<polygon points="{a - 5:.0f},{b + 60:.0f} {a:.0f},{b + 55:.0f} {a + 5:.0f},{b + 60:.0f} {a:.0f},{b + 65:.0f}" fill="#a7c957" stroke="#6a994e" stroke-width="1.4"/>' for a, b in chain[1:]]
save("mem_glucocaliz.svg", "Membrana con glucocáliz", "Membranas", MEM, "glucocaliz glycocalyx glicoproteina azucar membrana plasmatica",
     800, 190, "".join(glyco) + bilayer_h(0, 800, 78))

# =============================================================================== GRÁFICOS Y SÍMBOLOS
GR = ["graficos"]
AX = f'<path d="M30 10V170H290" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="square"/>'
C1, C2, C3 = "#2f80ed", "#eb5757", "#27ae60"


def bars(vals, cols, err=True, x0=50, w=34, gap=14):
    out = []
    for i, (v, c) in enumerate(zip(vals, cols)):
        x = x0 + i * (w + gap)
        out.append(f'<rect x="{x}" y="{170 - v}" width="{w}" height="{v}" fill="{c}"/>')
        if err:
            e = v * .12 + 6
            out.append(f'<path d="M{x + w / 2} {170 - v - e}V{170 - v + e}M{x + w / 2 - 7} {170 - v - e}h14M{x + w / 2 - 7} {170 - v + e}h14" stroke="{INK}" stroke-width="2"/>')
    return "".join(out)


save("gr_barras.svg", "Gráfico de barras con error", "Gráficos y símbolos", GR, "grafico barras bar chart error", 300, 180,
     AX + bars([60, 110, 85, 140, 100], [C1] * 5))
save("gr_barras_agrupadas.svg", "Barras agrupadas", "Gráficos y símbolos", GR, "grafico barras agrupadas grouped bar", 300, 180,
     AX + "".join(bars([a, b], [C1, C2], x0=46 + i * 82, w=30, gap=4) for i, (a, b) in enumerate(((70, 100), (90, 130), (60, 115)))))
save("gr_barras_apiladas.svg", "Barras apiladas", "Gráficos y símbolos", GR, "grafico barras apiladas stacked", 300, 180,
     AX + "".join(f'<rect x="{50 + i * 58}" y="{170 - a}" width="40" height="{a}" fill="{C1}"/><rect x="{50 + i * 58}" y="{170 - a - b}" width="40" height="{b}" fill="{C2}"/>'
                  f'<rect x="{50 + i * 58}" y="{170 - a - b - c}" width="40" height="{c}" fill="{C3}"/>' for i, (a, b, c) in enumerate(((40, 30, 20), (60, 35, 30), (30, 50, 25), (70, 40, 35)))))
pts = [(40 + i * 25, 160 - 110 * (1 - math.exp(-i / 3.5)) - rnd.uniform(-6, 6)) for i in range(10)]
save("gr_lineas.svg", "Gráfico de líneas", "Gráficos y símbolos", GR, "grafico lineas line chart serie", 300, 180,
     AX + f'<polyline points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in pts)}" fill="none" stroke="{C1}" stroke-width="3"/>'
     + "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="#fff" stroke="{C1}" stroke-width="2.5"/>' for x, y in pts))
sc = [(rnd.uniform(45, 280), 0) for _ in range(28)]
sc = [(x, 160 - (x - 40) * .45 - rnd.gauss(0, 12)) for x, _ in sc]
save("gr_dispersion.svg", "Dispersión con regresión", "Gráficos y símbolos", GR, "grafico dispersion scatter regresion correlacion", 300, 180,
     AX + "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4.5" fill="{C1}" opacity=".75"/>' for x, y in sc)
     + f'<path d="M40 160L285 50" stroke="{C2}" stroke-width="3"/>')
box = lambda x, q1, md, q3, lo, hi, c: (f'<path d="M{x} {lo}V{q3}M{x} {q1}V{hi}M{x - 10} {lo}h20M{x - 10} {hi}h20" stroke="{INK}" stroke-width="2"/>'
                                        f'<rect x="{x - 22}" y="{q3}" width="44" height="{q1 - q3}" fill="{c}" stroke="{INK}" stroke-width="2"/>'
                                        f'<path d="M{x - 22} {md}h44" stroke="{INK}" stroke-width="3"/>')
save("gr_boxplot.svg", "Diagrama de cajas (boxplot)", "Gráficos y símbolos", GR, "grafico boxplot cajas bigotes", 300, 180,
     AX + box(80, 130, 110, 90, 158, 60, "#cfe1fb") + box(160, 110, 85, 65, 140, 35, "#f9d0d0") + box(240, 145, 125, 105, 165, 80, "#cfeedd"))
violin = lambda x, c: f'<path d="M{x} 30C{x + 34} 70 {x + 30} 120 {x} 160C{x - 30} 120 {x - 34} 70 {x} 30z" fill="{c}" stroke="{INK}" stroke-width="2"/><circle cx="{x}" cy="95" r="5" fill="#fff" stroke="{INK}" stroke-width="2"/>'
save("gr_violin.svg", "Gráfico de violín", "Gráficos y símbolos", GR, "grafico violin violin plot distribucion", 300, 180,
     AX + violin(90, "#cfe1fb") + violin(170, "#f9d0d0") + violin(250, "#cfeedd"))
hist = [math.exp(-((i - 6) / 2.6) ** 2) * 135 + 5 for i in range(13)]
save("gr_histograma.svg", "Histograma", "Gráficos y símbolos", GR, "grafico histograma histogram frecuencia distribucion", 300, 180,
     AX + "".join(f'<rect x="{34 + i * 19.5:.1f}" y="{170 - v:.1f}" width="19" height="{v:.1f}" fill="{C1}" stroke="#fff" stroke-width="1"/>' for i, v in enumerate(hist))
     + f'<path d="{"M" + " L".join(f"{34 + i * 2:.0f} {170 - (math.exp(-(((i * 2 - 117) / 51) ** 2)) * 135 + 5):.0f}" for i in range(128))}" fill="none" stroke="{C2}" stroke-width="3"/>')
cmap = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#fee090", "#fdae61", "#f46d43", "#d73027"]
save("gr_heatmap.svg", "Mapa de calor (heatmap)", "Gráficos y símbolos", GR, "grafico heatmap mapa calor matriz expresion", 300, 200,
     "".join(f'<rect x="{20 + j * 32}" y="{10 + i * 30}" width="31" height="29" fill="{rnd.choice(cmap)}"/>' for i in range(6) for j in range(8))
     + "".join(f'<rect x="{20 + k * 32}" y="190" width="32" height="8" fill="{c}"/>' for k, c in enumerate(cmap)))


def pie(cx, cy, r, fracs, cols, hole=0):
    out, a = [], -90
    for f, c in zip(fracs, cols):
        b = a + f * 360
        x0, y0 = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        x1, y1 = cx + r * math.cos(math.radians(b)), cy + r * math.sin(math.radians(b))
        out.append(f'<path d="M{cx} {cy}L{x0:.1f} {y0:.1f}A{r} {r} 0 {1 if f > .5 else 0} 1 {x1:.1f} {y1:.1f}z" fill="{c}" stroke="#fff" stroke-width="2"/>')
        a = b
    if hole:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{hole}" fill="#fff"/>')
    return "".join(out)


save("gr_torta.svg", "Gráfico de torta", "Gráficos y símbolos", GR, "grafico torta pie chart proporcion", 200, 200,
     pie(100, 100, 90, [.42, .28, .18, .12], [C1, C2, C3, "#f2c94c"]))
save("gr_dona.svg", "Gráfico de dona", "Gráficos y símbolos", GR, "grafico dona donut chart proporcion", 200, 200,
     pie(100, 100, 90, [.5, .3, .2], [C1, C2, C3], hole=50))
save("gr_venn2.svg", "Diagrama de Venn (2)", "Gráficos y símbolos", GR, "venn diagrama conjuntos interseccion", 300, 200,
     f'<circle cx="115" cy="100" r="80" fill="{C1}" opacity=".45" stroke="{C1}" stroke-width="3"/><circle cx="185" cy="100" r="80" fill="{C2}" opacity=".45" stroke="{C2}" stroke-width="3"/>')
save("gr_venn3.svg", "Diagrama de Venn (3)", "Gráficos y símbolos", GR, "venn diagrama tres conjuntos interseccion", 300, 280,
     f'<circle cx="115" cy="100" r="80" fill="{C1}" opacity=".4"/><circle cx="185" cy="100" r="80" fill="{C2}" opacity=".4"/><circle cx="150" cy="165" r="80" fill="{C3}" opacity=".4"/>')
sig = [(40 + i * 2.5, 165 - 140 / (1 + math.exp(-(i - 50) / 9))) for i in range(101)]
save("gr_dosis_respuesta.svg", "Curva dosis-respuesta", "Gráficos y símbolos", GR, "dosis respuesta sigmoide dose response ic50 ec50", 300, 180,
     AX + f'<polyline points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in sig)}" fill="none" stroke="{C1}" stroke-width="3"/>'
     + f'<path d="M165 170V95H30" stroke="{C2}" stroke-width="2" stroke-dasharray="6 5" fill="none"/>')
km = lambda pts, c: f'<path d="M30 25' + "".join(f"H{x}V{y}" for x, y in pts) + f'H285" fill="none" stroke="{c}" stroke-width="3"/>'
save("gr_kaplan_meier.svg", "Curva de supervivencia (Kaplan-Meier)", "Gráficos y símbolos", GR, "kaplan meier supervivencia survival", 300, 180,
     AX + km([(70, 40), (110, 58), (150, 72), (210, 90), (250, 100)], C1) + km([(55, 50), (90, 80), (130, 110), (170, 128), (230, 145)], C2))
vol = []
for _ in range(220):
    fc = rnd.gauss(0, 1.3)
    p = abs(fc) * rnd.uniform(15, 40) + rnd.uniform(0, 12)
    c = C2 if fc > 1.3 and p > 40 else C1 if fc < -1.3 and p > 40 else "#b8bec6"
    vol.append(f'<circle cx="{160 + fc * 38:.0f}" cy="{168 - p:.0f}" r="3.2" fill="{c}"/>')
save("gr_volcano.svg", "Volcano plot", "Gráficos y símbolos", GR, "volcano plot expresion diferencial transcriptomica", 300, 180,
     AX + "".join(vol) + '<path d="M30 128H290M110 10V170M210 10V170" stroke="#999" stroke-dasharray="5 5"/>')
pca = []
for (cx, cy, c) in ((100, 70, C1), (200, 80, C2), (150, 135, C3)):
    pca.append(f'<ellipse cx="{cx}" cy="{cy}" rx="42" ry="28" fill="{c}" opacity=".12" stroke="{c}" stroke-dasharray="5 4"/>')
    pca += [f'<circle cx="{cx + rnd.gauss(0, 15):.0f}" cy="{cy + rnd.gauss(0, 10):.0f}" r="4.5" fill="{c}"/>' for _ in range(14)]
save("gr_pca.svg", "Análisis de componentes principales (PCA)", "Gráficos y símbolos", GR, "pca componentes principales ordenacion nmds clusters", 300, 180,
     AX + "".join(pca))
ts = [(30 + i * 2.6, 95 - 45 * math.sin(i / 100 * 4 * math.pi) - i * .2) for i in range(100)]
save("gr_serie_temporal.svg", "Serie temporal con intervalo de confianza", "Gráficos y símbolos", GR,
     "serie temporal time series intervalo confianza estacional ndvi", 300, 180,
     AX + f'<polygon points="{" ".join(f"{x:.0f},{y - 14:.0f}" for x, y in ts)} {" ".join(f"{x:.0f},{y + 14:.0f}" for x, y in ts[::-1])}" fill="{C3}" opacity=".2"/>'
     + f'<polyline points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in ts)}" fill="none" stroke="{C3}" stroke-width="3"/>')
save("gr_significancia.svg", "Corchete de significancia (***)", "Gráficos y símbolos", GR, "significancia asterisco p valor bracket estadistica", 200, 70,
     f'<path d="M15 64V40H185V64" fill="none" stroke="{INK}" stroke-width="3"/><text x="100" y="32" font-family="Arial" font-size="34" font-weight="bold" text-anchor="middle" fill="{INK}">***</text>')
save("gr_barra_escala.svg", "Barra de escala", "Gráficos y símbolos", GR, "barra escala scale bar um nm mm", 200, 50,
     f'<rect x="10" y="10" width="180" height="10" fill="{INK}"/><text x="100" y="44" font-family="Arial" font-size="20" text-anchor="middle" fill="{INK}">100 µm</text>')
# símbolos
SYM = {
    "sim_ciclo.svg": ("Flechas de ciclo", "ciclo cycle flechas circulares reciclaje", 200, 200,
                      "".join(f'<path d="M{100 + 70 * math.cos(math.radians(a)):.1f} {100 + 70 * math.sin(math.radians(a)):.1f}A70 70 0 0 1 {100 + 70 * math.cos(math.radians(a + 95)):.1f} {100 + 70 * math.sin(math.radians(a + 95)):.1f}" fill="none" stroke="{C1}" stroke-width="12"/>'
                              f'<polygon points="{",".join(f"{100 + r * math.cos(math.radians(a + 112)):.1f},{100 + r * math.sin(math.radians(a + 112)):.1f}" if k == 1 else f"{100 + r * math.cos(math.radians(a + 95)):.1f},{100 + r * math.sin(math.radians(a + 95)):.1f}" for k, r in ((0, 92), (1, 70), (0, 48)))}" fill="{C1}"/>'
                              for a in (-80, 40, 160))),
    "sim_flecha_curva.svg": ("Flecha curva", "flecha curva curved arrow", 220, 120,
                             f'<path d="M15 100Q110 -20 190 80" fill="none" stroke="{INK}" stroke-width="7"/><polygon points="205,98 172,86 195,62" fill="{INK}"/>'),
    "sim_flecha_gruesa.svg": ("Flecha de bloque", "flecha gruesa block arrow proceso paso", 220, 120,
                              f'<polygon points="10,35 140,35 140,8 210,60 140,112 140,85 10,85" fill="#cfe1fb" stroke="{C1}" stroke-width="4" stroke-linejoin="round"/>'),
    "sim_mas.svg": ("Signo más (aumento)", "mas plus aumento positivo", 100, 100, f'<circle cx="50" cy="50" r="46" fill="{C3}"/><path d="M50 25V75M25 50H75" stroke="#fff" stroke-width="12" stroke-linecap="round"/>'),
    "sim_menos.svg": ("Signo menos (disminución)", "menos minus disminucion negativo", 100, 100, f'<circle cx="50" cy="50" r="46" fill="{C2}"/><path d="M25 50H75" stroke="#fff" stroke-width="12" stroke-linecap="round"/>'),
    "sim_flecha_arriba.svg": ("Aumento (flecha arriba)", "aumento incremento upregulation flecha arriba", 80, 120, f'<polygon points="40,5 75,55 52,55 52,115 28,115 28,55 5,55" fill="{C3}"/>'),
    "sim_flecha_abajo.svg": ("Disminución (flecha abajo)", "disminucion downregulation flecha abajo", 80, 120, f'<polygon points="40,115 75,65 52,65 52,5 28,5 28,65 5,65" fill="{C2}"/>'),
    "sim_inhibicion.svg": ("Símbolo de inhibición", "inhibicion inhibition bloqueo t", 160, 100, f'<path d="M10 50H140M140 15V85" stroke="{C2}" stroke-width="10" stroke-linecap="round"/>'),
    "sim_rayo.svg": ("Estímulo (rayo)", "estimulo rayo stimulus luz senal", 80, 130, '<polygon points="50,5 10,75 38,75 26,125 72,50 44,50" fill="#f2c94c" stroke="#c9a227" stroke-width="3" stroke-linejoin="round"/>'),
    "sim_reloj.svg": ("Tiempo (reloj)", "tiempo reloj time clock incubacion", 120, 120, f'<circle cx="60" cy="60" r="52" fill="#fff" stroke="{INK}" stroke-width="7"/><path d="M60 26V60L84 74" stroke="{INK}" stroke-width="7" fill="none" stroke-linecap="round"/>'),
    "sim_temperatura.svg": ("Temperatura", "temperatura termometro temperature calor", 70, 150, f'<rect x="22" y="8" width="26" height="100" rx="13" fill="#fff" stroke="{INK}" stroke-width="5"/><rect x="29" y="50" width="12" height="62" fill="{C2}"/><circle cx="35" cy="122" r="22" fill="{C2}" stroke="{INK}" stroke-width="5"/>'),
    "sim_marca_ok.svg": ("Correcto (tilde)", "correcto check tilde si ok", 100, 100, f'<circle cx="50" cy="50" r="46" fill="{C3}"/><path d="M27 52L44 68L74 34" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
    "sim_marca_no.svg": ("Incorrecto (cruz)", "incorrecto cruz cross no x", 100, 100, f'<circle cx="50" cy="50" r="46" fill="{C2}"/><path d="M32 32L68 68M68 32L32 68" stroke="#fff" stroke-width="10" stroke-linecap="round"/>'),
    "sim_advertencia.svg": ("Advertencia", "advertencia warning precaucion alerta", 120, 110, '<polygon points="60,6 114,102 6,102" fill="#f2c94c" stroke="#2b2f33" stroke-width="6" stroke-linejoin="round"/><path d="M60 38V70" stroke="#2b2f33" stroke-width="9" stroke-linecap="round"/><circle cx="60" cy="86" r="5.5" fill="#2b2f33"/>'),
    "sim_pin_mapa.svg": ("Marcador de mapa", "marcador mapa pin ubicacion sitio muestreo gps", 90, 130, '<path d="M45 125C45 125 8 75 8 45a37 37 0 0 1 74 0c0 30-37 80-37 80z" fill="#eb5757" stroke="#a83232" stroke-width="3"/><circle cx="45" cy="45" r="14" fill="#fff"/>'),
    "sim_norte.svg": ("Flecha norte", "norte north arrow brujula mapa", 80, 130, f'<polygon points="40,20 70,120 40,98 10,120" fill="{INK}"/><polygon points="40,20 40,98 10,120" fill="#fff" stroke="{INK}" stroke-width="3"/><text x="40" y="16" font-family="Arial" font-size="18" font-weight="bold" text-anchor="middle" fill="{INK}">N</text>'),
}
for f, (n, t, w, h, b) in SYM.items():
    save(f, n, "Gráficos y símbolos", GR, t, w, h, b)

# =============================================================================== SATÉLITES Y TELEDETECCIÓN
SAT = ["satelite", "ecologia"]
panel = lambda x, y, w, h: (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1d4e89" stroke="#0d2b4d" stroke-width="2"/>'
                            + "".join(f'<path d="M{x + w * i / 4:.1f} {y}V{y + h}" stroke="#6fa3d8" stroke-width="1.2"/>' for i in range(1, 4))
                            + f'<path d="M{x} {y + h / 2}H{x + w}" stroke="#6fa3d8" stroke-width="1.2"/>')
SATBODY = (panel(10, 45, 90, 40) + panel(200, 45, 90, 40) + '<path d="M100 65H118M182 65H200" stroke="#555" stroke-width="5"/>'
           '<rect x="118" y="35" width="64" height="60" rx="6" fill="#e9ecef" stroke="#6c757d" stroke-width="3"/>'
           '<rect x="126" y="43" width="48" height="10" fill="#ffd166"/><circle cx="150" cy="104" r="10" fill="#495057" stroke="#212529" stroke-width="2"/>'
           '<path d="M150 35V18M142 18h16" stroke="#6c757d" stroke-width="3"/>')
save("sat_satelite.svg", "Satélite de observación", "Satélites y teledetección", SAT, "satelite satellite sentinel landsat orbita", 300, 120, SATBODY)
save("sat_satelite_barrido.svg", "Satélite con franja de barrido", "Satélites y teledetección", SAT,
     "satelite barrido swath sensor teledeteccion imagen remote sensing", 300, 330,
     '<polygon points="150,112 40,300 260,300" fill="#9ad1f5" opacity=".45"/><path d="M150 112L40 300M150 112L260 300" stroke="#4aa3df" stroke-width="2" stroke-dasharray="6 5"/>'
     + SATBODY + '<path d="M10 300Q150 285 290 300V326H10z" fill="#7cb342"/><path d="M40 300H260" stroke="#2e7d32" stroke-width="5"/>')
save("sat_orbita.svg", "Tierra con órbita satelital", "Satélites y teledetección", SAT, "orbita tierra earth orbit satelite polar", 300, 260,
     '<circle cx="150" cy="130" r="80" fill="#4aa3df"/><path d="M95 80c25 10 20 35 45 40s20 30 5 45M180 70c-10 25 25 30 30 55s-25 30-20 50" fill="none" stroke="#7cb342" stroke-width="22" stroke-linecap="round" opacity=".9"/>'
     '<ellipse cx="150" cy="130" rx="140" ry="44" fill="none" stroke="#6c757d" stroke-width="3" stroke-dasharray="8 6" transform="rotate(-18 150 130)"/>'
     f'<g transform="translate(232 62) scale(.25)">{SATBODY}</g>')
save("sat_dron.svg", "Dron (UAV)", "Satélites y teledetección", SAT, "dron drone uav vant multirrotor fotogrametria", 260, 140,
     '<path d="M60 60L200 60M60 60l-20-20M200 60l20-20M60 60l-20 20M200 60l20 20" stroke="#343a40" stroke-width="7" stroke-linecap="round"/>'
     + "".join(f'<ellipse cx="{x}" cy="{y}" rx="34" ry="6" fill="#adb5bd" opacity=".8"/><circle cx="{x}" cy="{y}" r="5" fill="#212529"/>' for x, y in ((40, 38), (220, 38), (40, 82), (220, 82)))
     + '<rect x="100" y="45" width="60" height="32" rx="10" fill="#e9ecef" stroke="#495057" stroke-width="3"/><circle cx="130" cy="92" r="12" fill="#212529"/><circle cx="130" cy="92" r="5" fill="#4aa3df"/>')
save("sat_dron_huella.svg", "Dron con huella de imagen", "Satélites y teledetección", SAT, "dron drone huella footprint ortomosaico vuelo", 260, 300,
     '<polygon points="130,100 50,270 210,270" fill="#9ad1f5" opacity=".4"/><path d="M50 270H210" stroke="#4aa3df" stroke-width="4"/>'
     '<g transform="translate(0 10)"><path d="M60 60L200 60M60 60l-20-20M200 60l20-20M60 60l-20 20M200 60l20 20" stroke="#343a40" stroke-width="7" stroke-linecap="round"/>'
     + "".join(f'<ellipse cx="{x}" cy="{y}" rx="34" ry="6" fill="#adb5bd" opacity=".8"/>' for x, y in ((40, 38), (220, 38), (40, 82), (220, 82)))
     + '<rect x="100" y="45" width="60" height="32" rx="10" fill="#e9ecef" stroke="#495057" stroke-width="3"/><circle cx="130" cy="92" r="11" fill="#212529"/></g>'
     '<path d="M20 270Q130 255 240 270V296H20z" fill="#7cb342"/>')
save("sat_estacion_terrena.svg", "Estación terrena (antena)", "Satélites y teledetección", SAT, "estacion terrena antena parabolica ground station", 200, 220,
     '<path d="M70 200L100 130L130 200" fill="none" stroke="#495057" stroke-width="8"/><path d="M40 205H160" stroke="#495057" stroke-width="8"/>'
     '<path d="M30 60C60 150 160 150 185 100z" fill="#dee2e6" stroke="#495057" stroke-width="5" transform="rotate(-25 100 100)"/>'
     '<path d="M100 120L135 55" stroke="#495057" stroke-width="5"/><circle cx="137" cy="51" r="8" fill="#eb5757"/>'
     '<path d="M150 30q12 -12 24 0M156 18q18 -18 36 0" fill="none" stroke="#4aa3df" stroke-width="4" stroke-linecap="round"/>')
bands = ["#2b6cb0", "#38a169", "#e53e3e", "#805ad5", "#d69e2e"]
save("sat_cubo_multiespectral.svg", "Cubo de imagen multiespectral", "Satélites y teledetección", SAT,
     "multiespectral bandas cubo hiperespectral raster imagen satelital", 240, 220,
     "".join(f'<g transform="translate({60 - i * 12} {20 + i * 14})"><polygon points="0,30 120,30 150,0 30,0" fill="{c}" opacity=".9" stroke="#fff" stroke-width="2"/>'
             f'<rect x="0" y="30" width="120" height="110" fill="{c}" opacity=".85" stroke="#fff" stroke-width="2"/></g>' for i, c in enumerate(bands[::-1])))
ndvi = ["#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850", "#006837"]
grid = []
for i in range(10):
    for j in range(12):
        v = 0.5 + 0.35 * math.sin(i / 2.2) * math.cos(j / 3.0) + rnd.uniform(-.15, .15)
        grid.append(f'<rect x="{10 + j * 20}" y="{10 + i * 20}" width="20" height="20" fill="{ndvi[max(0, min(9, int(v * 10)))]}"/>')
save("sat_mapa_ndvi.svg", "Mapa de píxeles NDVI", "Satélites y teledetección", SAT, "ndvi mapa pixel raster indice vegetacion evi", 260, 240,
     "".join(grid) + '<rect x="10" y="10" width="240" height="200" fill="none" stroke="#343a40" stroke-width="2"/>'
     + "".join(f'<rect x="{10 + k * 24}" y="222" width="24" height="12" fill="{c}"/>' for k, c in enumerate(ndvi)))
wl = [400 + i * 20 for i in range(31)]
veg = [(w, 20 if w < 500 else 35 if w < 560 else 25 if w < 680 else 25 + (min(w, 760) - 680) * 2.4 if w < 760 else 215) for w in wl]
soil = [(w, 40 + (w - 400) * .18) for w in wl]
water = [(w, max(6, 30 - (w - 400) * .05)) for w in wl]
line = lambda pts, c: f'<polyline points="{" ".join(f"{30 + (w - 400) * .43:.0f},{170 - v * .65:.0f}" for w, v in pts)}" fill="none" stroke="{c}" stroke-width="3.5"/>'
save("sat_firma_espectral.svg", "Firmas espectrales (vegetación, suelo, agua)", "Satélites y teledetección", SAT,
     "firma espectral reflectancia spectral signature vegetacion suelo agua", 300, 180,
     AX + '<rect x="146" y="10" width="24" height="160" fill="#e53e3e" opacity=".1"/><rect x="172" y="10" width="40" height="160" fill="#805ad5" opacity=".08"/>'
     + line(veg, "#2f9e44") + line(soil, "#a0522d") + line(water, "#2b6cb0"))
save("sat_torre_flujo.svg", "Torre de flujo (eddy covariance)", "Satélites y teledetección", SAT,
     "torre flujo eddy covariance co2 evapotranspiracion micrometeorologia", 140, 300,
     '<path d="M50 290L70 30L90 290M55 220H85M60 150H80M65 85H75" stroke="#6c757d" stroke-width="5" fill="none"/>'
     '<path d="M70 40H120" stroke="#495057" stroke-width="4"/><rect x="112" y="30" width="20" height="26" rx="3" fill="#e9ecef" stroke="#495057" stroke-width="3"/>'
     '<path d="M118 22V30M126 22V30" stroke="#495057" stroke-width="3"/><rect x="40" y="250" width="22" height="30" fill="#ced4da" stroke="#495057" stroke-width="2"/>'
     '<rect x="30" y="60" width="28" height="18" fill="#1d4e89"/><path d="M0 292H140" stroke="#7cb342" stroke-width="6"/>')
save("sat_estacion_meteo.svg", "Estación meteorológica", "Satélites y teledetección", SAT,
     "estacion meteorologica clima pluviometro anemometro weather station", 160, 300,
     '<path d="M80 290V40" stroke="#6c757d" stroke-width="7"/><path d="M80 50H140M80 50H20" stroke="#6c757d" stroke-width="4"/>'
     + "".join(f'<path d="M140 50l-12-14M140 50l14 -6M140 50l-2 16" stroke="#495057" stroke-width="3"/><circle cx="{x}" cy="{y}" r="6" fill="#495057"/>' for x, y in ((128, 36), (154, 44), (138, 66)))
     + '<polygon points="20,50 0,58 0,42" fill="#eb5757"/><rect x="62" y="120" width="36" height="46" fill="#fff" stroke="#495057" stroke-width="3"/>'
     '<path d="M62 132h36M62 144h36M62 156h36" stroke="#adb5bd" stroke-width="2"/><rect x="100" y="200" width="30" height="20" fill="#1d4e89"/>'
     '<path d="M0 292H160" stroke="#7cb342" stroke-width="6"/>')

# =============================================================================== EQUIPO DE CAMPO (ambiente y ecología)
ENV = ["ecologia", "laboratorio"]
save("campo_cuadrante.svg", "Cuadrante de muestreo", "Ambiente y ecología", ENV, "cuadrante quadrat muestreo vegetacion parcela", 260, 160,
     '<polygon points="40,120 180,120 230,60 90,60" fill="#d8f3dc" stroke="#e85d04" stroke-width="7" stroke-linejoin="round"/>'
     '<path d="M65 120L160 60M110 120L205 60M80 90H205" stroke="#e85d04" stroke-width="2" opacity=".6"/>'
     + "".join(f'<path d="M{x} {y}l-3 -12M{x} {y}l4 -10" stroke="#2f9e44" stroke-width="2.4"/>' for x, y in ((100, 100), (130, 85), (160, 105), (190, 80), (120, 112), (150, 72))))
save("campo_trampa_camara.svg", "Cámara trampa", "Ambiente y ecología", ENV, "camara trampa camera trap fototrampeo mamiferos", 160, 260,
     '<rect x="55" y="0" width="50" height="260" fill="#8b5a2b"/><path d="M60 20v220M95 40v200" stroke="#6f4518" stroke-width="3"/>'
     '<rect x="38" y="100" width="84" height="100" rx="12" fill="#606c38" stroke="#283618" stroke-width="4"/>'
     '<circle cx="80" cy="138" r="20" fill="#212529" stroke="#adb5bd" stroke-width="4"/><circle cx="80" cy="138" r="8" fill="#4aa3df"/>'
     '<rect x="56" y="172" width="48" height="14" rx="3" fill="#212529"/><path d="M38 120H20M122 120H140" stroke="#283618" stroke-width="6"/>')
save("campo_pluviometro.svg", "Pluviómetro", "Ambiente y ecología", ENV, "pluviometro rain gauge precipitacion lluvia", 120, 240,
     '<path d="M20 40H100L80 80H40z" fill="#e9ecef" stroke="#495057" stroke-width="4"/><rect x="40" y="80" width="40" height="140" fill="#fff" stroke="#495057" stroke-width="4"/>'
     '<rect x="44" y="150" width="32" height="66" fill="#9ad1f5"/>' + "".join(f'<path d="M80 {y}h-10" stroke="#495057" stroke-width="2"/>' for y in range(95, 215, 15))
     + '<path d="M0 222H120" stroke="#7cb342" stroke-width="6"/>' + "".join(f'<path d="M{x} {y}l-4 10" stroke="#4aa3df" stroke-width="3" stroke-linecap="round"/>' for x, y in ((40, 5), (65, 15), (90, 2), (55, 25))))
save("campo_barreno.svg", "Barreno / muestreador de suelo", "Ambiente y ecología", ENV, "barreno muestreador suelo soil corer auger nucleo", 140, 280,
     '<path d="M20 30H120" stroke="#495057" stroke-width="12" stroke-linecap="round"/><rect x="62" y="30" width="16" height="170" fill="#adb5bd" stroke="#495057" stroke-width="3"/>'
     '<path d="M0 200H140" stroke="#5e4430" stroke-width="4"/><rect x="0" y="200" width="140" height="80" fill="#8b5a3c" opacity=".35"/>'
     '<rect x="60" y="200" width="20" height="60" fill="#7a5638" stroke="#495057" stroke-width="3"/><polygon points="60,260 80,260 70,274" fill="#495057"/>')
save("campo_transecta.svg", "Transecta con estacas", "Ambiente y ecología", ENV, "transecta transect linea muestreo estaca", 320, 120,
     '<path d="M0 100Q160 88 320 100" stroke="#7cb342" stroke-width="8" fill="none"/>'
     + "".join(f'<rect x="{x - 4}" y="40" width="8" height="62" fill="#8b5a2b"/><rect x="{x - 6}" y="40" width="12" height="10" fill="#e85d04"/>' for x in (20, 160, 300))
     + '<path d="M20 52Q90 60 160 52Q230 60 300 52" fill="none" stroke="#f2c94c" stroke-width="3"/>')
save("campo_gps.svg", "GPS de mano", "Ambiente y ecología", ENV, "gps navegador georreferencia coordenadas", 120, 200,
     '<rect x="20" y="30" width="80" height="160" rx="16" fill="#f2c94c" stroke="#7a5c00" stroke-width="4"/><path d="M80 30V5" stroke="#343a40" stroke-width="8" stroke-linecap="round"/>'
     '<rect x="32" y="48" width="56" height="64" rx="4" fill="#cde7b0" stroke="#343a40" stroke-width="3"/><path d="M40 100l14-20 12 12 14-26" stroke="#2f9e44" stroke-width="3" fill="none"/>'
     '<circle cx="60" cy="140" r="12" fill="#343a40"/><rect x="38" y="164" width="16" height="10" rx="3" fill="#343a40"/><rect x="66" y="164" width="16" height="10" rx="3" fill="#343a40"/>')
save("campo_disco_secchi.svg", "Disco de Secchi", "Ambiente y ecología", ENV, "disco secchi transparencia agua limnologia", 200, 220,
     '<rect x="0" y="60" width="200" height="160" fill="#4aa3df" opacity=".45"/><path d="M100 0V120" stroke="#343a40" stroke-width="3"/>'
     '<ellipse cx="100" cy="130" rx="60" ry="16" fill="#fff" stroke="#343a40" stroke-width="3"/><path d="M40 130A60 16 0 0 0 100 146V130zM160 130A60 16 0 0 0 100 114V130z" fill="#212529"/>')
save("campo_botella_niskin.svg", "Botella muestreadora de agua", "Ambiente y ecología", ENV, "botella niskin van dorn muestreo agua limnologia", 120, 260,
     '<path d="M60 0V40" stroke="#343a40" stroke-width="3"/><rect x="30" y="50" width="60" height="170" rx="10" fill="#9ad1f5" stroke="#1d4e89" stroke-width="4"/>'
     '<rect x="24" y="40" width="72" height="16" rx="4" fill="#495057"/><rect x="24" y="214" width="72" height="16" rx="4" fill="#495057"/><path d="M96 60V210" stroke="#495057" stroke-width="3"/>')
save("campo_red_plancton.svg", "Red de plancton", "Ambiente y ecología", ENV, "red plancton plankton net zooplancton muestreo", 300, 140,
     '<path d="M0 70H60" stroke="#343a40" stroke-width="3"/><ellipse cx="70" cy="70" rx="12" ry="55" fill="none" stroke="#495057" stroke-width="6"/>'
     '<path d="M70 15L240 58V82L70 125" fill="#fff" fill-opacity=".6" stroke="#495057" stroke-width="3"/>'
     + "".join(f'<path d="M{70 + i * 20} {15 + i * 5}V{125 - i * 5}" stroke="#adb5bd" stroke-width="1.5"/>' for i in range(1, 9))
     + '<rect x="240" y="55" width="40" height="30" rx="6" fill="#9ad1f5" stroke="#1d4e89" stroke-width="3"/>')
save("campo_piezometro.svg", "Piezómetro / pozo de monitoreo", "Ambiente y ecología", ENV, "piezometro pozo monitoreo nivel freatico agua subterranea", 70, 300,
     '<rect x="0" y="100" width="70" height="200" fill="#8b5a3c" opacity=".25"/><rect x="0" y="170" width="70" height="130" fill="#8ea6d3" opacity=".35"/>'
     '<path d="M0 170H70" stroke="#2f8ad8" stroke-width="3"/><path d="M15 170V10H55V170" fill="#fff" stroke="#111" stroke-width="4"/>'
     '<path d="M15 170V290H55V170" fill="none" stroke="#111" stroke-width="3.5" stroke-dasharray="8 6"/>'
     + "".join(f'<path d="M26 {y + 6}L44 {y - 4}" stroke="#111" stroke-width="3" stroke-linecap="round"/>' for y in range(120, 285, 22)) + '<path d="M0 100H70" stroke="#2f9e44" stroke-width="5"/>')

# =============================================================================== PAISAJES Y AGRICULTURA
AG = ["agricultura", "ecologia"]
save("agro_campo_cultivo.svg", "Campo cultivado (surcos)", "Agricultura", AG, "campo cultivo surcos parcela agricola cultivo", 400, 200,
     '<polygon points="0,200 400,200 300,40 100,40" fill="#a98463"/>'
     + "".join(f'<path d="M{100 + i * 20} 40L{-40 + i * 48} 200" stroke="#7a5638" stroke-width="3"/>' for i in range(11))
     + "".join(f'<circle cx="{(100 + i * 20) * (1 - t) + (-40 + i * 48) * t:.0f}" cy="{40 + 160 * t:.0f}" r="{2 + 5 * t:.1f}" fill="#4caf50"/>'
               for i in range(11) for t in (0.15, 0.35, 0.55, 0.75, 0.95)))
save("agro_invernadero.svg", "Invernadero", "Agricultura", AG, "invernadero greenhouse cultivo protegido", 260, 180,
     '<path d="M10 170V80Q130 -10 250 80V170z" fill="#d8f3dc" fill-opacity=".7" stroke="#495057" stroke-width="4"/>'
     + "".join(f'<path d="M{x} 170V{80 - (1 - ((x - 130) / 120) ** 2) * 50:.0f}" stroke="#adb5bd" stroke-width="2"/>' for x in range(40, 250, 30))
     + "".join(f'<path d="M{x} 168v-18" stroke="#2f9e44" stroke-width="3"/><circle cx="{x}" cy="146" r="8" fill="#4caf50"/>' for x in range(35, 240, 25)))
save("agro_riego.svg", "Riego por aspersión", "Agricultura", AG, "riego aspersion aspersor irrigacion agua", 240, 180,
     '<path d="M0 170H240" stroke="#7cb342" stroke-width="10"/><path d="M120 165V80" stroke="#6c757d" stroke-width="7"/><rect x="108" y="70" width="24" height="14" rx="3" fill="#495057"/>'
     + "".join(f'<path d="M120 72Q{120 + dx / 2} {20} {120 + dx} {60 + abs(dx) / 3}" fill="none" stroke="#4aa3df" stroke-width="3" stroke-dasharray="4 6"/>' for dx in (-100, -60, 60, 100)))
save("agro_terrazas.svg", "Terrazas de cultivo", "Agricultura", AG, "terrazas andenes cultivo ladera conservacion suelo", 320, 200,
     "".join(f'<path d="M{i * 40} {40 + i * 32}H{320}V{72 + i * 32}H{i * 40 - 10}z" fill="{c}" stroke="#7a5638" stroke-width="2"/>'
             f'<path d="M{i * 40 + 4} {40 + i * 32}H320" stroke="#4caf50" stroke-width="6"/>' for i, c in enumerate(["#b08968", "#a98463", "#9c7a5b", "#8b6b4e", "#7f5f44"])))
save("agro_planta_raices.svg", "Planta con raíces", "Agricultura", AG, "planta raiz raices root anatomia vegetal plantula", 160, 280,
     '<rect x="0" y="130" width="160" height="150" fill="#a98463" opacity=".35"/><path d="M0 130H160" stroke="#7a5638" stroke-width="3"/>'
     '<path d="M80 130V40" stroke="#2f9e44" stroke-width="6"/><path d="M80 90Q40 80 30 50Q65 55 80 90zM80 70Q120 60 130 30Q95 35 80 70zM80 45Q70 20 80 5Q92 22 80 45z" fill="#4caf50" stroke="#2b8a3e" stroke-width="2"/>'
     + "".join(f'<path d="M80 130Q{80 + dx} {170} {80 + dx * 1.6} {250 + dy}" fill="none" stroke="#c8a27a" stroke-width="{w}" stroke-linecap="round"/>' for dx, dy, w in ((0, 20, 5), (-25, 0, 3.5), (25, 5, 3.5), (-45, -30, 2.5), (45, -25, 2.5), (-12, 15, 2), (14, 18, 2))))
save("agro_hoja_enferma.svg", "Hoja con lesiones (fitopatología)", "Agricultura", AG, "fitopatologia hoja enfermedad mancha roya hongo patogeno", 220, 160,
     '<path d="M10 80Q80 0 210 80Q80 160 10 80z" fill="#6ab04c" stroke="#3c7a2a" stroke-width="3"/><path d="M10 80H200M60 80l25 -25M60 80l25 25M110 80l25 -28M110 80l25 28M155 80l20 -18M155 80l20 18" stroke="#3c7a2a" stroke-width="2"/>'
     + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#a0522d" stroke="#f2c94c" stroke-width="2.5"/>' for x, y, r in ((70, 60, 7), (95, 98, 9), (140, 64, 6), (165, 95, 5), (120, 82, 4), (50, 92, 5))))
save("agro_planta_marchita.svg", "Planta marchita (estrés)", "Agricultura", AG, "planta marchita estres hidrico sequia enfermedad", 160, 220,
     '<path d="M30 210H130L120 170H40z" fill="#c1693c" stroke="#8d4a28" stroke-width="3"/><path d="M80 170Q85 110 110 90Q130 80 125 110" fill="none" stroke="#7a8a3a" stroke-width="6"/>'
     '<path d="M95 120Q60 125 55 155Q80 145 95 120zM110 95Q125 125 112 150Q100 125 110 95zM125 108Q150 120 150 148Q130 135 125 108z" fill="#b5a642" stroke="#7a6f2a" stroke-width="2"/>')
save("agro_germinacion.svg", "Etapas de germinación", "Agricultura", AG, "germinacion semilla plantula emergencia etapas fenologia", 360, 160,
     '<path d="M0 110H360" stroke="#7a5638" stroke-width="4"/><rect x="0" y="110" width="360" height="50" fill="#a98463" opacity=".35"/>'
     '<ellipse cx="45" cy="128" rx="14" ry="9" fill="#d4a373" stroke="#8d6748" stroke-width="2"/>'
     '<ellipse cx="135" cy="128" rx="14" ry="9" fill="#d4a373" stroke="#8d6748" stroke-width="2"/><path d="M135 135q-4 12 2 20" stroke="#c8a27a" stroke-width="3" fill="none"/><path d="M138 120q2 -10 -2 -14" stroke="#7cb342" stroke-width="3" fill="none"/>'
     '<path d="M225 140q-3 10 3 16M225 110V80" stroke="#c8a27a" stroke-width="3" fill="none"/><path d="M225 80q-14 -6 -20 4q12 6 20 -4zM225 80q14 -6 20 4q-12 6 -20 -4z" fill="#7cb342"/><path d="M225 110V80" stroke="#2f9e44" stroke-width="4"/>'
     '<path d="M315 150q-8 -6 -10 4M315 150q8 -8 12 2M315 110V40" stroke="#2f9e44" stroke-width="5" fill="none"/><path d="M315 85Q285 75 278 52Q305 58 315 85zM315 65Q345 55 352 32Q325 38 315 65z" fill="#4caf50"/>')
save("agro_rio.svg", "Río con riberas", "Agricultura", AG + ["ecologia"], "rio river cauce ribera arroyo agua", 400, 160,
     '<rect width="400" height="160" fill="#b7d77a"/><path d="M0 70C80 40 140 120 220 80S340 40 400 70V110C340 80 300 130 220 120S80 80 0 110z" fill="#4aa3df"/>'
     '<path d="M0 90C80 60 140 140 220 100S340 60 400 90" fill="none" stroke="#bfe3fa" stroke-width="3" stroke-dasharray="14 10"/>')
save("agro_laguna.svg", "Laguna / lago", "Agricultura", AG + ["ecologia"], "laguna lago lake humedal espejo agua", 320, 180,
     '<ellipse cx="160" cy="95" rx="150" ry="75" fill="#b7d77a"/><path d="M50 95C60 50 150 35 230 55S300 120 240 140S70 150 50 95z" fill="#4aa3df"/>'
     '<path d="M110 80q15 -8 30 0M180 110q15 -8 30 0" stroke="#bfe3fa" stroke-width="4" fill="none" stroke-linecap="round"/>'
     + "".join(f'<path d="M{x} {y}v-18M{x - 5} {y}l-4 -14M{x + 5} {y}l4 -14" stroke="#2f8f46" stroke-width="3"/>' for x, y in ((52, 112), (64, 125), (262, 130), (278, 120))))
save("agro_bosque.svg", "Franja de bosque", "Agricultura", AG + ["ecologia"], "bosque forest arboles franja vegetacion", 400, 160,
     '<path d="M0 150H400" stroke="#7cb342" stroke-width="10"/>'
     + "".join(f'<path d="M{x} 150V{150 - h * .35}" stroke="#6f4518" stroke-width="6"/><circle cx="{x}" cy="{150 - h * .55}" r="{h * .33}" fill="{c}"/>'
               if k % 2 else f'<path d="M{x} 150V140" stroke="#6f4518" stroke-width="6"/><polygon points="{x},{150 - h} {x - h * .3},140 {x + h * .3},140" fill="{c}"/>'
               for k, (x, h, c) in enumerate((x, rnd.uniform(70, 120), rnd.choice(["#2e7d4f", "#3f9b4a", "#4caf50", "#2b8a3e"])) for x in range(20, 400, 32))))
save("agro_granero.svg", "Granero / establo", "Agricultura", AG, "granero establo galpon barn granja", 220, 200,
     '<polygon points="20,90 110,20 200,90" fill="#9b2226" stroke="#5c1416" stroke-width="4"/><rect x="30" y="90" width="160" height="100" fill="#bb3e03" stroke="#5c1416" stroke-width="4"/>'
     '<rect x="85" y="120" width="50" height="70" fill="#fff"/><path d="M85 120L135 190M135 120L85 190" stroke="#bb3e03" stroke-width="5"/><rect x="95" y="50" width="30" height="24" fill="#fff"/>')
save("agro_alambrado.svg", "Alambrado / cerco", "Agricultura", AG, "alambrado cerco cerca fence exclusion clausura ganado", 320, 120,
     '<path d="M0 110H320" stroke="#7cb342" stroke-width="8"/>' + "".join(f'<rect x="{x - 5}" y="20" width="10" height="92" fill="#8b5a2b"/>' for x in (20, 120, 220, 300))
     + "".join(f'<path d="M0 {y}H320" stroke="#6c757d" stroke-width="2.5"/>' for y in (35, 55, 75, 95)))

(OUT / "extra.json").write_text(json.dumps([dict(file=f, name=n, category=c, groups=g, tags=t) for f, n, c, g, t in ICONS],
                                           ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
print(len(ICONS), "iconos:", dict(Counter(c for _, _, c, _, _ in ICONS)))
