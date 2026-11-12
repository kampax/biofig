"""Recrea las figuras "Direct and functional Tubulin-PMCA interaction" como proyectos editables de BioFig.

Uso:  python ejemplos/figuras_tubulina_pmca.py          (recuadros para pegar los blots reales)
      python ejemplos/figuras_tubulina_pmca.py --demo   (con blots SIMULADOS de static/demo, solo para ver)
Crea dos proyectos en data/projects/. Las posiciones se tomaron de fotos de la figura original:
X = (px - ox) * S,  Y = (py - oy) * S. Los paneles de blot son marcadores para pegar las imagenes reales.
"""
import json
import re
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = {i["name"]: i for i in json.loads((ROOT / "data" / "icons.json").read_text(encoding="utf-8"))}
OUT = ROOT / "data" / "projects"
SERIF = "Times New Roman"
INK = "#1f1f1f"
DEMO = "--demo" in sys.argv


class Fig:
    def __init__(self, ox, oy, s=1.6):
        self.ox, self.oy, self.s, self.items = ox, oy, s, []

    def X(self, px): return round((px - self.ox) * self.s, 1)
    def Y(self, py): return round((py - self.oy) * self.s, 1)
    def L(self, v): return round(v * self.s, 1)

    def _id(self): return "n" + uuid.uuid4().hex[:8]

    def icon(self, name, cx, cy, w=None, h=None, rot=0, flip=False):
        ic = ICONS[name]
        a = ic["aspect"]
        if w is not None:
            w = self.L(w); h = round(w / a, 1)
        else:
            h = self.L(h); w = round(h * a, 1)
        it = {"kind": "icon", "id": self._id(), "x": self.X(cx), "y": self.Y(cy), "rotation": rot, "opacity": 1,
              "src": ic["src"], "iconId": ic["id"], "width": w, "height": h, "flip": flip, "tint": None, "alts": [],
              "meta": {"name": ic["name"], "author": ic["author"], "license": ic["license"], "source": ic["source"]}}
        self.items.append(it)
        return it

    PDB = {  # estructuras reales renderizadas con 3Dmol.js (static/tools/render_pdb.html)
        "tub": ("1jff_tubulina.png", "pdb:1JFF", "Tubulina αβ (PDB 1JFF)", "Löwe, Li, Downing & Nogales 2001",
                "Dimero de tubulina (cintas)", 1.12),
        "pmca": ("6a69_pmca1.png", "pdb:6A69", "PMCA1 (PDB 6A69)", "Gong et al. 2018", "Proteina en cintas (PMCA)", 0.94),
        "bsa": ("4f5s_bsa.png", "pdb:4F5S", "Albúmina sérica bovina (PDB 4F5S)", "Bujacz 2012",
                "Proteina en cintas (BSA)", 1.2),
    }

    def pdb_icon(self, key, cx, cy, w, rot=0):
        """Estructura PDB real; si falta el PNG, usa el dibujo equivalente."""
        fname, iid, label, author, fallback, k = self.PDB[key]
        png = ROOT / "static" / "pdb" / fname
        if not png.exists():
            return self.icon(fallback, cx, cy, w=w, rot=rot)
        import struct
        pw, ph = struct.unpack(">II", png.read_bytes()[16:24])  # cabecera IHDR
        wc = self.L(w * k)
        it = {"kind": "icon", "id": self._id(), "x": self.X(cx), "y": self.Y(cy), "rotation": rot, "opacity": 1,
              "src": f"/static/pdb/{fname}", "iconId": iid, "width": wc, "height": round(wc * ph / pw, 1),
              "flip": False, "tint": None, "alts": [], "realW": {"pdb:1JFF": 98.8, "pdb:6A69": 131.9, "pdb:4F5S": 83.6}[iid],
              "meta": {"name": label, "author": author, "license": "Dominio público (PDB)", "source": "RCSB PDB"}}
        self.items.append(it)
        return it

    def text(self, t, px, py, size, font=SERIF, style="normal", fill=INK, align="left", width=None, halo=False):
        it = {"kind": "text", "id": self._id(), "x": self.X(px), "y": self.Y(py), "rotation": 0, "opacity": 1,
              "text": t, "fontSize": self.L(size), "fontFamily": font, "fontStyle": style, "fill": fill,
              "align": align, "halo": halo}
        if width:
            it["width"] = self.L(width)
            if align == "center":
                it["x"] = round(it["x"] - it["width"] / 2, 1)
        self.items.append(it)
        return it

    def rect(self, x0, y0, x1, y1, fill, stroke=None, sw=0, radius=0, dashed=False):
        it = {"kind": "rect", "id": self._id(), "x": self.X(x0), "y": self.Y(y0), "width": self.L(x1 - x0),
              "height": self.L(y1 - y0), "rotation": 0, "opacity": 1, "fill": fill, "stroke": stroke,
              "strokeWidth": sw, "cornerRadius": radius, "dashed": dashed}
        self.items.append(it)
        return it

    def line(self, x0, y0, x1, y1, color=INK, sw=2, head="none", tail="none", dashed=False):
        a, b = (self.X(x0), self.Y(y0)), (self.X(x1), self.Y(y1))
        it = {"kind": "connector", "id": self._id(), "x": 0, "y": 0, "rotation": 0, "opacity": 1,
              "pts": [a[0], a[1], (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, b[0], b[1]], "stroke": color,
              "strokeWidth": sw, "head": head, "tail": tail, "dashed": dashed, "curved": False}
        self.items.append(it)
        return it

    def image(self, src, x0, y0, x1, y1, name):
        w, h = self.L(x1 - x0), self.L(y1 - y0)
        self.items.append({"kind": "icon", "id": self._id(), "x": round(self.X(x0) + w / 2, 1),
                           "y": round(self.Y(y0) + h / 2, 1), "rotation": 0, "opacity": 1, "src": src,
                           "iconId": "img:" + self._id(), "width": w, "height": h, "flip": False, "tint": None,
                           "alts": [], "meta": {"name": name, "author": "—", "license": "Propia",
                                                "source": "Imagen propia"}})

    def blot_slot(self, x0, y0, x1, y1, dark=True, note="Pegá aquí la imagen del blot", demo=None):
        """Marcador para la imagen experimental real; con --demo, una imagen SIMULADA."""
        if DEMO and demo:
            self.image(f"/static/demo/{demo}", x0, y0, x1, y1, f"{demo} (simulado)")
            return
        self.rect(x0, y0, x1, y1, "#101412" if dark else "#dcdbe8", "#7a8a80" if dark else "#9a98b0", 1, dashed=True)
        self.text(note, (x0 + x1) / 2, (y0 + y1) / 2 - 7, 9.5, font="Arial", style="italic",
                  fill="#8fa397" if dark else "#6b6985", align="center", width=x1 - x0 - 6)

    def ruler(self, x0, x1, y, label="10 mm"):
        self.line(x0, y, x1, y, "#9aa3a0", 1.2)
        n = 10
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            self.line(x, y, x, y - (4 if i % 5 == 0 else 2.5), "#9aa3a0", 1)
        self.text(label, (x0 + x1) / 2, y + 3, 8.5, font="Arial", fill="#8a9390", align="center", width=60)

    def save(self, name, w, h):
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:40]
        pid = f"{slug}-{uuid.uuid4().hex[:6]}"
        doc = {"w": w, "h": h, "bg": "#ffffff", "items": self.items}
        (OUT / f"{pid}.json").write_text(json.dumps({"id": pid, "name": name, "updated": time.time(), "doc": doc,
                                                     "thumb": None}, ensure_ascii=False), encoding="utf-8")
        print("proyecto:", pid, "-", len(self.items), "elementos")
        return pid


# =====================================================================================================
# Figura 1: ensayo de superposicion en membrana (dot-blot overlay), paneles A-D
# =====================================================================================================
f = Fig(ox=40, oy=110)
f.text("Direct and functional Tubulin-PMCA interaction", 62, 146, 17, font="Arial")

# ---------------- (A) sonda: PMCA, detectada con anti-PMCA
f.text("(A)", 257, 258, 19, font="Arial")
f.icon("Membrana de blot", 512, 543, w=508)
f.pdb_icon("pmca", 312, 514, w=100)
f.pdb_icon("bsa", 486, 500, w=62)
f.pdb_icon("tub",  660, 497, w=118)
f.pdb_icon("pmca", 662, 412, w=88, rot=78)          # PMCA unida a la tubulina
f.icon("Anticuerpo primario", 300, 438, h=42)
f.icon("Anticuerpo secundario fluorescente", 297, 370, w=66)
f.icon("Anticuerpo primario", 654, 317, h=42)
f.icon("Anticuerpo secundario fluorescente", 652, 252, w=66)
f.text("ANTI-PMCA", 364, 298, 13, font="Arial", style="bold")
f.line(380, 330, 334, 362, INK, 2, head="arrow")
f.line(482, 317, 630, 314, INK, 2, head="arrow")
f.text("PMCA", 285, 588, 15)
f.text("BSA", 461, 583, 15)
f.text("TUBULIN", 607, 576, 15)
rows_a = ["PMCA", "BSA", "TUBULIN", "DM1A(anti tub)", "5F10 (anti PMCA)"]
signs_a = ["+", "-", "-", "-", "+"]
for i, (r, sg) in enumerate(zip(rows_a, signs_a)):
    y = 618 + i * 33
    f.text(r, 624, y, 15)
    f.text(sg, 872, y, 12, font="Arial", fill="#666")
f.text("PMCA", 843, 443, 15)
f.blot_slot(818, 488, 935, 550, demo="dotblot_A.png")
f.ruler(820, 900, 574)

# ---------------- (B) sonda: tubulina, detectada con anti-tubulina
f.text("(B)", 278, 696, 19, font="Arial")
f.icon("Membrana de blot", 520, 993, w=480)
f.pdb_icon("pmca", 360, 964, w=95)
f.pdb_icon("tub",  364, 882, w=88, rot=90)          # tubulina unida a la PMCA
f.icon("Anticuerpo primario", 357, 817, h=40)
f.icon("Anticuerpo secundario fluorescente", 355, 758, w=62)
f.pdb_icon("bsa", 500, 946, w=60)
f.pdb_icon("tub",  633, 961, w=82)
f.icon("Anticuerpo primario", 628, 906, h=40)
f.icon("Anticuerpo secundario fluorescente", 627, 848, w=62)
f.text("ANTI-TUBULIN", 532, 786, 13, font="Arial", style="bold")
f.line(522, 798, 455, 798, INK, 2, head="arrow")
f.text("PMCA", 305, 1017, 15)
f.text("BSA", 471, 1014, 15)
f.text("TUBULIN", 611, 1012, 15)
for i, r in enumerate(rows_a):
    f.text(r, 629, 1039 + i * 30, 14)
f.text("+", 864, 1039, 12, font="Arial", fill="#666")   # unico signo legible en la foto: completar el resto
f.text("PMCA", 845, 883, 15)
f.blot_slot(811, 921, 935, 980, demo="dotblot_B.png")
f.ruler(812, 895, 1000)

# ---------------- (C) y (D): encabezados visibles en la foto
f.text("(C)", 300, 1220, 17, font="Arial")
for lab, x in (("PMCA", 337), ("BSA", 470), ("TUB.", 571)):
    f.text(lab, x, 1254, 12, fill="#555")
f.line(322, 1300, 628, 1300, "#1f2a44", 5)
f.text("(D)", 764, 1214, 17, font="Arial")
f.text("PMCA", 834, 1245, 12, fill="#555")
f.line(802, 1293, 930, 1293, "#1f2a44", 5)
f.save("Tubulin-PMCA - Fig A (overlay)" + (" DEMO" if DEMO else ""), 1500, 1920)

# =====================================================================================================
# Figura 2: pull-down con resina + western blot, paneles A-C
# =====================================================================================================
g = Fig(ox=8, oy=470)
g.text("Direct and functional Tubulin-PMCA interaction", 15, 487, 17, font="Arial")

# ---------------- (A) esquema del pull-down
g.text("(A)", 82, 593, 19, font="Arial")
g.icon("Bola de resina", 362, 664, w=40)
g.pdb_icon("pmca", 404, 651, w=46, rot=-35)
lav = "#b9c8e4"
g.line(147, 688, 627, 688, "#a9cbe8", 4)
g.line(147, 690, 147, 722, lav, 4, head="arrow")
g.line(627, 690, 627, 720, lav, 4, head="arrow")

# Lupa de detalle: el vertice del cono va al borde derecho del tubo y la lupa se dibuja DETRAS del tubo.
# Icono de 200x130 (vertice en 4,126; circulo en 146,62; r=50) escalado a w=118 -> k=0.59.
def callout(tube_x, tube_y, w=118):
    k = w / 200
    ax, ay = tube_x + 13, tube_y - 10                      # vertice: borde derecho del tubo
    cx, cy = ax - (4 - 100) * k, ay - (126 - 65) * k        # centro del icono
    g.icon("Lupa de detalle (zoom)", cx, cy, w=w)
    return cx + (146 - 100) * k, cy + (62 - 65) * k         # centro del circulo


TUBE_H = 88
lx, ly = 147, 778
c1 = callout(lx, ly)
g.icon("microtube open blue", lx, ly, h=TUBE_H)
g.pdb_icon("tub", c1[0], c1[1] - 9, w=30)
g.pdb_icon("pmca", c1[0] + 2, c1[1] + 12, w=26, rot=-20)
g.text("Tubulin\n+ PMCA", 82, 770, 15, style="bold", align="center", width=80)

rx, ry = 627, 776
c2 = callout(rx, ry)
g.icon("microtube open blue", rx, ry, h=TUBE_H)
g.pdb_icon("tub", c2[0], c2[1], w=32)
g.text("Tubulin\nalone", 770, 776, 15, style="bold", align="center", width=80)

g.icon("centrifuge", 390, 786, h=78)
g.text("washed resin, centrifuged (900 xg\n2 min.) collect supernatant for WB", 383, 838, 14.5, style="bold",
       align="center", width=330)
# flechas de cada paso: arrancan debajo del tubo, alineadas con el
y_bottom = ly + TUBE_H / 2 + 8
g.line(lx, y_bottom, lx, y_bottom + 42, lav, 5, head="arrow")
g.text("C1 (wash)", lx, 890, 14, style="bold", align="center", width=110)
g.line(lx, 940, lx, 990, lav, 5, head="arrow")
g.text("C1 (elution)", lx, 1012, 14, style="bold", align="center", width=110)
g.line(rx, y_bottom, rx, y_bottom + 42, lav, 5, head="arrow")
g.text("C2 (wash)", rx, 890, 14, style="bold", align="center", width=110)
g.line(rx, 940, rx, 990, lav, 5, head="arrow")
g.text("C2 (elution)", rx, 1012, 14, style="bold", align="center", width=110)

g.icon("centrifuge", 392, 940, h=78)
g.text("The sample was eluted whith elution\nbuffer centrifuged at 900 xg 2 min\ncollect supernatant for WB", 398, 1003,
       14.5, style="bold", align="center", width=330)
g.icon("western blotting", 345, 1128, w=62, rot=-22)
g.icon("electrophoresis chamber", 410, 1098, w=58)

# ---------------- (B) western blot con marcadores de peso molecular
g.text("(B)", 806, 593, 19, font="Arial")
for kda, y in ((150, 724), (102, 828), (76, 889), (52, 973), (38, 1040)):
    g.text(str(kda), 808, y, 18)
g.blot_slot(868, 640, 1015, 1085, dark=False, note="Pegá aquí la imagen del western blot", demo="western.png")

# ---------------- (C) dot blot de tubulina: lavados (+Ca2+) y eluciones
g.text("(C)", 262, 1250, 15, font="Arial")
g.text("Tubulin", 615, 1210, 22)
g.text("Washed (+ Ca²⁺)", 347, 1253, 22)
g.line(275, 1294, 740, 1294, INK, 2)
for lab, x in (("I", 337), ("II", 412), ("III", 489), ("IV", 586), ("V", 678)):
    g.text(lab, x - 10, 1306, 15, align="center", width=30)
g.blot_slot(302, 1338, 725, 1452, demo="dotblot_lavados.png")
g.ruler(305, 385, 1470)
g.line(282, 1520, 735, 1520, INK, 2)
g.text("Elution", 810, 1250, 22)
g.line(783, 1296, 1000, 1296, INK, 2)
g.text("I", 822, 1306, 15, align="center", width=30)
g.blot_slot(793, 1342, 876, 1462, demo="dotblot_elucion.png")
g.line(775, 1522, 1000, 1522, INK, 2)
g.text("Tubulin + DMPC", 610, 1535, 22)
g.save("Tubulin-PMCA - Fig B (pull-down)" + (" DEMO" if DEMO else ""), 1650, 1800)
