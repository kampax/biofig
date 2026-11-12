"""Genera los iconos SVG propios de BioFig en static/builtin (diseno original, libre)."""
import json
import math
import random
from pathlib import Path

OUT = Path(__file__).parent / "static" / "builtin"
OUT.mkdir(parents=True, exist_ok=True)

S = {}
S["sun.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><g stroke="#f5a623" stroke-width="10" stroke-linecap="round">'
                + "".join(f'<line x1="100" y1="12" x2="100" y2="40" transform="rotate({a} 100 100)"/>' for a in range(0, 360, 45))
                + '</g><circle cx="100" cy="100" r="46" fill="#ffd34d" stroke="#f5a623" stroke-width="6"/></svg>')
S["cloud.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 140"><path d="M60 125h125a45 45 0 0 0 4-90 60 60 0 0 0-112 12 40 40 0 0 0-17 78z" fill="#eef3f8" stroke="#9fb3c8" stroke-width="6" stroke-linejoin="round"/></svg>'
S["rain.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 200"><path d="M60 105h125a45 45 0 0 0 4-90 60 60 0 0 0-112 12 40 40 0 0 0-17 78z" fill="#c9d6e3" stroke="#7d93ab" stroke-width="6"/>'
                 + "".join(f'<path d="M{x} {y}q-7 12 0 18q7-6 0-18z" fill="#3b8fd9"/>' for x, y in [(70, 130), (110, 150), (150, 128), (190, 148), (90, 170), (170, 172)])
                 + '</svg>')
S["tree.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 260"><path d="M88 170h24l6 85H82z" fill="#8b5a2b"/><circle cx="100" cy="95" r="70" fill="#3f9b4a"/><circle cx="60" cy="125" r="45" fill="#4caf50"/><circle cx="140" cy="125" r="45" fill="#4caf50"/><circle cx="100" cy="60" r="45" fill="#5cbf60"/></svg>'
S["conifer.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 260"><rect x="70" y="210" width="20" height="45" fill="#7a4e24"/><path d="M80 10l50 80h-25l40 60h-28l35 65H3l35-65H10l40-60H25z" fill="#2e7d4f"/></svg>'
S["grass.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 90"><g fill="none" stroke="#5fae3e" stroke-width="7" stroke-linecap="round">'
                  + "".join(f'<path d="M{x} 88q{d} -40 {d * 2} -{h}"/>' for x, d, h in [(15, 4, 60), (35, -5, 75), (55, 6, 55), (80, -4, 80), (105, 5, 62), (130, -6, 72), (155, 4, 58), (180, -5, 78), (205, 6, 60), (225, -3, 50)])
                  + '</g></svg>')
S["soil.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 160"><rect width="400" height="35" fill="#4a3424"/><rect y="35" width="400" height="55" fill="#7a5638"/><rect y="90" width="400" height="70" fill="#a98463"/>'
                 + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#5e4430" opacity=".6"/>' for x, y, r in [(40, 60, 6), (120, 70, 4), (210, 55, 7), (300, 75, 5), (360, 58, 4), (80, 120, 8), (180, 135, 5), (260, 115, 9), (340, 140, 6)])
                 + '</svg>')
S["water.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 140"><rect y="20" width="400" height="120" fill="#4aa3df"/><path d="M0 20q25-18 50 0t50 0 50 0 50 0 50 0 50 0 50 0 50 0v20H0z" fill="#7cc4f0"/><g fill="none" stroke="#bfe3fa" stroke-width="4" stroke-linecap="round"><path d="M40 75q15-8 30 0"/><path d="M180 95q15-8 30 0"/><path d="M300 70q15-8 30 0"/></g></svg>'
S["mountain.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 220"><path d="M0 220L130 40l60 80 50-60 160 160z" fill="#8a9bb0"/><path d="M130 40l30 42-18-6-14 14-14-12-18 8z" fill="#fff"/><path d="M240 60l30 40-16-4-14 10-10-10-14 4z" fill="#fff"/></svg>'
S["co2.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 90"><g stroke="#555" stroke-width="5"><line x1="62" y1="38" x2="92" y2="38"/><line x1="62" y1="52" x2="92" y2="52"/><line x1="128" y1="38" x2="158" y2="38"/><line x1="128" y1="52" x2="158" y2="52"/></g><circle cx="40" cy="45" r="28" fill="#e04b4b"/><circle cx="110" cy="45" r="26" fill="#444"/><circle cx="180" cy="45" r="28" fill="#e04b4b"/></svg>'
S["lipid_bilayer.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 130"><g stroke="#e0a43c" stroke-width="3" fill="none">'
                          + "".join(f'<path d="M{x - 3} 26v34M{x + 3} 26v34M{x - 3} 70v34M{x + 3} 70v34"/>' for x in range(12, 400, 25))
                          + '</g><g fill="#f2c94c" stroke="#c99a1e" stroke-width="2">'
                          + "".join(f'<circle cx="{x}" cy="18" r="11"/><circle cx="{x}" cy="112" r="11"/>' for x in range(12, 400, 25))
                          + '</g></svg>')

pts1, pts2, rungs = [], [], ""
for i in range(0, 361, 6):
    y = 10 + i * 0.7
    s = math.sin(math.radians(i * 2))
    x1, x2 = 60 + 40 * s, 60 - 40 * s
    pts1.append(f"{x1:.1f},{y:.1f}")
    pts2.append(f"{x2:.1f},{y:.1f}")
    if i % 24 == 0 and i not in (0, 360):
        c = ["#e57373", "#64b5f6", "#81c784", "#ffb74d"][(i // 24) % 4]
        rungs += f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{c}" stroke-width="5"/>'
S["dna_helix.svg"] = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 272">{rungs}'
                      f'<polyline points="{" ".join(pts1)}" fill="none" stroke="#3b5ba5" stroke-width="7" stroke-linecap="round"/>'
                      f'<polyline points="{" ".join(pts2)}" fill="none" stroke="#c0392b" stroke-width="7" stroke-linecap="round"/></svg>')
S["mrna.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 60"><path d="M10 40q20-25 40 0t40 0 40 0 40 0 40 0 40 0 40 0 40 0 40 0" fill="none" stroke="#8e44ad" stroke-width="7" stroke-linecap="round"/><circle cx="12" cy="40" r="9" fill="#8e44ad"/><text x="355" y="22" font-family="Arial" font-size="18" fill="#8e44ad">AAA</text></svg>'
S["protein_blob.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 170"><path d="M40 60c-10-40 50-60 75-35 30-25 85 5 65 45 25 25 0 80-40 70-25 30-85 20-90-15C10 120 10 80 40 60z" fill="#7fb3d5" stroke="#2e6a99" stroke-width="5"/><path d="M70 80q20-20 40 0t40 0" fill="none" stroke="#2e6a99" stroke-width="4" opacity=".6"/></svg>'
S["receptor.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 240"><path d="M30 10q-5 50 25 70v120h30V80q30-20 25-70H92q2 40-22 52Q46 50 48 10z" fill="#9b59b6" stroke="#5e2e78" stroke-width="4"/><rect x="50" y="200" width="40" height="30" rx="8" fill="#9b59b6" stroke="#5e2e78" stroke-width="4"/></svg>'
S["ion_channel.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 200"><rect x="10" y="20" width="55" height="160" rx="25" fill="#48c9b0" stroke="#148f77" stroke-width="5"/><rect x="95" y="20" width="55" height="160" rx="25" fill="#48c9b0" stroke="#148f77" stroke-width="5"/><circle cx="80" cy="70" r="9" fill="#f39c12"/><circle cx="80" cy="120" r="9" fill="#f39c12"/></svg>'
S["enzyme.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 160"><path d="M20 80a80 70 0 0 1 160-10l-40 10 40 10A80 70 0 0 1 20 80z" fill="#f0b27a" stroke="#ca6f1e" stroke-width="5"/><circle cx="170" cy="80" r="16" fill="#58d68d" stroke="#239b56" stroke-width="4"/></svg>'
S["food_web_node.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160"><circle cx="80" cy="80" r="70" fill="#eaf6ec" stroke="#3f9b4a" stroke-width="6"/></svg>'

META = [
    ("sun.svg", "Sol", "Clima", ["ecologia"], "sol sun luz light energia energy"),
    ("cloud.svg", "Nube", "Clima", ["ecologia"], "nube cloud"),
    ("rain.svg", "Lluvia", "Clima", ["ecologia"], "lluvia rain precipitacion precipitation"),
    ("tree.svg", "Arbol frondoso", "Vegetacion", ["ecologia"], "arbol tree bosque forest"),
    ("conifer.svg", "Conifera", "Vegetacion", ["ecologia"], "pino pine conifer arbol tree"),
    ("grass.svg", "Pasto", "Vegetacion", ["ecologia"], "pasto grass pradera herb"),
    ("soil.svg", "Suelo (horizontes)", "Paisaje", ["ecologia"], "suelo soil horizonte"),
    ("water.svg", "Agua", "Paisaje", ["ecologia"], "agua water lago lake rio river oceano"),
    ("mountain.svg", "Montana", "Paisaje", ["ecologia"], "montana mountain"),
    ("co2.svg", "CO2", "Molecula", ["ecologia", "molecular"], "co2 carbono carbon dioxido"),
    ("lipid_bilayer.svg", "Bicapa lipidica", "Membrana", ["molecular", "celular"], "membrana membrane bicapa bilayer lipid"),
    ("dna_helix.svg", "Doble helice ADN", "Acidos nucleicos", ["molecular"], "adn dna helice helix"),
    ("mrna.svg", "ARNm", "Acidos nucleicos", ["molecular"], "arn rna mrna transcripto"),
    ("protein_blob.svg", "Proteina", "Proteinas", ["molecular"], "proteina protein"),
    ("receptor.svg", "Receptor transmembrana", "Proteinas", ["molecular", "celular"], "receptor"),
    ("ion_channel.svg", "Canal ionico", "Proteinas", ["molecular", "celular"], "canal channel ion"),
    ("enzyme.svg", "Enzima + sustrato", "Proteinas", ["molecular"], "enzima enzyme sustrato substrate"),
    ("food_web_node.svg", "Nodo de red trofica", "Diagramas", ["ecologia"], "nodo red trofica food web"),
]


# ------------------------------------------------------------------ proteinas en cintas (estilo PDB cartoon)
def _mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def _color_at(palette, f):
    f = min(max(f, 0), 0.9999) * (len(palette) - 1)
    i = int(f)
    return _mix(palette[i], palette[i + 1], f - i)


def _ribbon_parts(rnd, palette, cx, cy, rx, ry, n, x0, x1, len_range=(26, 54), amp=5.0, strands=2):
    """Helices (cintas en espiral), lazos y laminas beta dentro de una elipse."""
    out, prev = [], None
    for _ in range(n):
        r, th = math.sqrt(rnd.random()), rnd.uniform(0, 2 * math.pi)
        c = (cx + rx * r * math.cos(th), cy + ry * r * math.sin(th))
        ang = rnd.uniform(0, math.pi)
        L = rnd.uniform(*len_range)
        d, pp = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))
        st = (c[0] - d[0] * L / 2, c[1] - d[1] * L / 2)
        col = _color_at(palette, (c[0] - x0) / (x1 - x0))
        if prev:
            mx, my = (prev[0] + st[0]) / 2 + rnd.uniform(-18, 18), (prev[1] + st[1]) / 2 + rnd.uniform(-18, 18)
            out.append(f'<path d="M{prev[0]:.1f} {prev[1]:.1f}Q{mx:.1f} {my:.1f} {st[0]:.1f} {st[1]:.1f}" '
                       f'fill="none" stroke="{_mix(col, "#888888", .25)}" stroke-width="1.8" stroke-linecap="round"/>')
        pts = []
        t = 0.0
        while t <= L:
            s = amp * math.sin(t * 2 * math.pi / 7.5)
            pts.append(f"{st[0] + d[0] * t + pp[0] * s:.1f},{st[1] + d[1] * t + pp[1] * s:.1f}")
            t += 1.2
        poly = " ".join(pts)
        out.append(f'<polyline points="{poly}" fill="none" stroke="{_mix(col, "#000000", .45)}" stroke-width="6.2" stroke-linejoin="round" stroke-linecap="round"/>')
        out.append(f'<polyline points="{poly}" fill="none" stroke="{col}" stroke-width="4.2" stroke-linejoin="round" stroke-linecap="round"/>')
        out.append(f'<polyline points="{poly}" fill="none" stroke="{_mix(col, "#ffffff", .55)}" stroke-width="1.1" stroke-opacity=".8"/>')
        prev = (st[0] + d[0] * L, st[1] + d[1] * L)
    for _ in range(strands):  # laminas beta: flechas planas
        r, th = math.sqrt(rnd.random()), rnd.uniform(0, 2 * math.pi)
        c = (cx + rx * r * math.cos(th) * .8, cy + ry * r * math.sin(th) * .8)
        ang = rnd.uniform(0, math.pi)
        L, wdt = rnd.uniform(22, 34), 3.2
        d, pp = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))
        a = (c[0] - d[0] * L / 2, c[1] - d[1] * L / 2)
        b = (c[0] + d[0] * (L / 2 - 7), c[1] + d[1] * (L / 2 - 7))
        tip = (c[0] + d[0] * L / 2, c[1] + d[1] * L / 2)
        poly = [(a[0] + pp[0] * wdt, a[1] + pp[1] * wdt), (b[0] + pp[0] * wdt, b[1] + pp[1] * wdt),
                (b[0] + pp[0] * wdt * 2.2, b[1] + pp[1] * wdt * 2.2), tip,
                (b[0] - pp[0] * wdt * 2.2, b[1] - pp[1] * wdt * 2.2), (b[0] - pp[0] * wdt, b[1] - pp[1] * wdt),
                (a[0] - pp[0] * wdt, a[1] - pp[1] * wdt)]
        col = _color_at(palette, (c[0] - x0) / (x1 - x0))
        out.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in poly)}" fill="{col}" '
                   f'stroke="{_mix(col, "#000000", .45)}" stroke-width="1.2" stroke-linejoin="round"/>')
    return out


def ribbon_svg(w, h, lobes, seed):
    rnd = random.Random(seed)
    parts = []
    for (palette, cx, cy, rx, ry, n) in lobes:
        parts += _ribbon_parts(rnd, palette, cx, cy, rx, ry, n, cx - rx, cx + rx)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">{"".join(parts)}</svg>'


TEAL = ["#e4572e", "#2a9d8f", "#23867a", "#3fb7c6", "#2a9d8f", "#1d7480"]
RAINBOW = ["#d62828", "#f77f00", "#fcbf49", "#8ac926", "#2a9d8f", "#1982c4", "#6a4c93"]
REDS = ["#c1121f", "#e4572e", "#f4a261", "#e76f51", "#d62828"]
TEALS = ["#2a9d8f", "#48cae4", "#21867a", "#43aa8b", "#1d7480"]
S["pmca_ribbon.svg"] = ribbon_svg(260, 110, [(TEAL, 130, 55, 112, 36, 17)], seed=11)
S["bsa_ribbon.svg"] = ribbon_svg(140, 170, [(RAINBOW, 70, 88, 52, 68, 15)], seed=7)
S["tubulin_ribbon.svg"] = ribbon_svg(270, 140, [(REDS, 85, 74, 68, 52, 13), (TEALS, 188, 70, 70, 52, 13)], seed=5)

S["antibody_primary.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 80"><path d="M30 4V40M30 40L8 76M30 40L52 76" '
                             'fill="none" stroke="#1e63c4" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
S["antibody_secondary_fluor.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="47" fill="#111"/>'
                                     '<path d="M50 80V52M50 52L31 30M50 52L69 30" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>'
                                     '<circle cx="50" cy="22" r="8" fill="#3ddc5a"/></svg>')
S["resin_bead.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><radialGradient id="g" cx="35%" cy="32%" r="70%">'
                       '<stop offset="0" stop-color="#666"/><stop offset=".35" stop-color="#1a1a1a"/><stop offset="1" stop-color="#000"/></radialGradient></defs>'
                       '<circle cx="50" cy="50" r="46" fill="url(#g)"/></svg>')
S["zoom_callout.svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 130"><polygon points="4,126 122,22 128,108" fill="#bfe4f6" opacity=".85"/>'
                         '<circle cx="146" cy="62" r="50" fill="#fff" stroke="#9fb9c8" stroke-width="3"/></svg>')
S["blot_membrane.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 14"><rect x="1" y="1" width="398" height="12" fill="#f7e1e1" stroke="#e3b4b4" stroke-width="1.5"/></svg>'

META += [
    ("pmca_ribbon.svg", "Proteina en cintas (PMCA)", "Proteinas", ["molecular"], "pmca proteina protein ribbon cinta bomba calcio atpasa"),
    ("bsa_ribbon.svg", "Proteina en cintas (BSA)", "Proteinas", ["molecular"], "bsa albumina albumin proteina protein ribbon cinta"),
    ("tubulin_ribbon.svg", "Dimero de tubulina (cintas)", "Proteinas", ["molecular", "celular"], "tubulina tubulin dimero dimer proteina ribbon cinta"),
    ("antibody_primary.svg", "Anticuerpo primario", "Anticuerpos", ["molecular", "laboratorio"], "anticuerpo antibody primario primary igg"),
    ("antibody_secondary_fluor.svg", "Anticuerpo secundario fluorescente", "Anticuerpos", ["molecular", "laboratorio"], "anticuerpo antibody secundario secondary fluorescente fluor conjugado"),
    ("resin_bead.svg", "Bola de resina", "Laboratorio", ["laboratorio", "molecular"], "resina resin bola bead agarosa pull down"),
    ("zoom_callout.svg", "Lupa de detalle (zoom)", "Diagramas", ["laboratorio", "molecular", "ecologia"], "zoom detalle ampliacion lupa callout"),
    ("blot_membrane.svg", "Membrana de blot", "Laboratorio", ["laboratorio", "molecular"], "membrana nitrocelulosa blot dot"),
]

for name, svg in S.items():
    (OUT / name).write_text(svg, encoding="utf-8")
(OUT / "builtin.json").write_text(json.dumps(
    [dict(file=f, name=n, category=c, groups=g, tags=t) for f, n, c, g, t in META],
    ensure_ascii=False, indent=1), encoding="utf-8")
print(len(S), "iconos propios generados")
