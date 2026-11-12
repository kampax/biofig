"""Construye data/icons.json a partir de los SVG de Bioicons y de los iconos propios.

Uso:  python build_index.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
BIOICONS = ROOT / "vendor_src" / "bioicons" / "static" / "icons"
BUILTIN = ROOT / "static" / "builtin"
OUT = ROOT / "data" / "icons.json"
MAX_BYTES = 500_000  # SVG mas grandes suelen traer bitmaps incrustados enormes

GROUPS = {
    "ecologia": {"Animals", "Plants_Algae", "Parasites", "Microbiology", "Viruses",
                 "Scientific_graphs", "People-Other", "General_items"},
    "molecular": {"Amino-Acids", "Nucleic_acids", "Genetics", "Genomics", "Epigenetics",
                  "Peptides", "Receptors_channels", "Molecular_modelling", "Molecular_Biology",
                  "Chemistry", "Chemo-_and_Bioinformatics", "Nanotechnology", "Cell_membrane"},
    "celular": {"Cell_membrane", "Cell_types", "Cell_lines", "Cell_culture",
                "Intracellular_components", "Extracellular_matrix", "Blood_Immunology",
                "Tissues", "Oncology", "Neuroscience", "Human_physiology", "Microbiology", "Viruses"},
    "laboratorio": {"Lab_apparatus", "Imaging", "Procedures", "Safety_symbols",
                    "Computer_hardware", "Machine_Learning", "General_items"},
    "membranas": {"Cell_membrane", "Receptors_channels"},
    "graficos": {"Scientific_graphs", "Safety_symbols"},
    "agricultura": {"Plants_Algae"},
}

LICENSES = {
    "cc-0": "CC0", "cc-by-3.0": "CC BY 3.0", "cc-by-4.0": "CC BY 4.0",
    "cc-by-sa-3.0": "CC BY-SA 3.0", "cc-by-sa-4.0": "CC BY-SA 4.0",
    "mit": "MIT", "bsd": "BSD",
}

NUM = r"([0-9.]+)"


def aspect(svg_head: str) -> float:
    m = re.search(r'viewBox\s*=\s*["\']\s*[-0-9.]+[\s,]+[-0-9.]+[\s,]+' + NUM + r'[\s,]+' + NUM, svg_head)
    if not m:
        w = re.search(r'\swidth\s*=\s*["\']' + NUM, svg_head)
        h = re.search(r'\sheight\s*=\s*["\']' + NUM, svg_head)
        if not (w and h):
            return 1.0
        m = (None, w.group(1), h.group(1))
        w_, h_ = float(m[1]), float(m[2])
    else:
        w_, h_ = float(m.group(1)), float(m.group(2))
    return round(w_ / h_, 4) if w_ > 0 and h_ > 0 else 1.0


def pretty(stem: str) -> str:
    s = re.sub(r"[_\-]+", " ", stem)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    icons = []
    skipped = 0
    for svg in sorted(BIOICONS.rglob("*.svg")):
        rel = svg.relative_to(BIOICONS).parts  # license/category/author/name.svg
        if len(rel) < 4:
            continue
        if svg.stat().st_size == 0 or svg.stat().st_size > MAX_BYTES:  # vacíos (error de origen) o enormes
            skipped += 1
            continue
        lic, cat, author = rel[0], rel[1], rel[2]
        head = svg.read_text(encoding="utf-8", errors="ignore")[:4000]
        icons.append({
            "id": f"bi:{'/'.join(rel)}",
            "name": pretty(svg.stem),
            "src": "/icons/" + "/".join(rel),
            "category": cat.replace("_", " "),
            "groups": [g for g, cats in GROUPS.items() if cat in cats] or ["otros"],
            "author": author.replace("_", " "),
            "license": LICENSES.get(lic, lic),
            "source": "Bioicons",
            "aspect": aspect(head),
        })

    meta_path = BUILTIN / "builtin.json"
    for item in json.loads(meta_path.read_text(encoding="utf-8")):
        svg = BUILTIN / item["file"]
        icons.append({
            "id": f"own:{item['file']}",
            "name": item["name"],
            "src": f"/static/builtin/{item['file']}",
            "category": item["category"],
            "groups": item["groups"],
            "author": "BioFig",
            "license": "Propio (libre)",
            "source": "BioFig",
            "aspect": aspect(svg.read_text(encoding="utf-8")[:4000]),
            "tags": item.get("tags", ""),
        })

    # ------------------------------------------------ iconos propios adicionales (membranas, gráficos, satélites, campo, agro)
    extra = ROOT / "static" / "extra" / "extra.json"
    if extra.exists():
        for item in json.loads(extra.read_text(encoding="utf-8")):
            svg = ROOT / "static" / "extra" / item["file"]
            icons.append({
                "id": f"own:extra/{item['file']}", "name": item["name"], "src": f"/static/extra/{item['file']}",
                "category": item["category"], "groups": item["groups"], "author": "BioFig", "license": "Propio (libre)",
                "source": "BioFig", "aspect": aspect(svg.read_text(encoding="utf-8")[:4000]), "tags": item.get("tags", ""),
            })

    # ------------------------------------------------ Fluent Emoji (MIT) y Health Icons (CC0): selección curada
    from urllib.parse import quote
    from fuentes_extra import HEALTH, fluent_items
    fl_dir = ROOT / "vendor_src" / "fluent" / "assets"
    if fl_dir.exists():
        dirs = {d.name.lower(): d for d in fl_dir.iterdir() if d.is_dir()}
        seen, missing = set(), []
        for en, es, cat, groups in fluent_items():
            d = dirs.get(en.lower())
            files = sorted(d.glob("Flat/*.svg")) or sorted(d.glob("Default/Flat/*.svg")) if d else []
            if not files:
                missing.append(en)
                continue
            rel = files[0].relative_to(fl_dir).as_posix()
            key = (rel, cat)
            if key in seen:
                continue
            seen.add(key)
            icons.append({
                "id": f"fl:{cat}:{rel}", "name": es, "src": "/fluent/" + quote(rel), "category": cat, "groups": groups,
                "author": "Microsoft (Fluent Emoji)", "license": "MIT", "source": "Fluent Emoji",
                "aspect": aspect(files[0].read_text(encoding="utf-8")[:4000]), "tags": en,
            })
        if missing:
            print("Fluent: no encontrados ->", ", ".join(missing))
    hi_dir = ROOT / "vendor_src" / "healthicons" / "public" / "icons" / "svg" / "filled"
    if hi_dir.exists():
        for folder, (cat, groups, only) in HEALTH.items():
            for svg in sorted((hi_dir / folder).glob("*.svg")):
                if only and svg.stem not in only:
                    continue
                rel = svg.relative_to(hi_dir).as_posix()
                icons.append({
                    "id": f"hi:{rel}", "name": pretty(svg.stem), "src": "/healthicons/" + quote(rel), "category": cat,
                    "groups": list(groups), "author": "Resolve to Save Lives (Health Icons)", "license": "CC0",
                    "source": "Health Icons", "aspect": aspect(svg.read_text(encoding="utf-8")[:4000]), "silhouette": True,
                })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(icons, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print("por fuente:", dict(Counter(i["source"] for i in icons)))
    print(f"{len(icons)} iconos indexados ({skipped} omitidos por tamano) -> {OUT}")


if __name__ == "__main__":
    main()
