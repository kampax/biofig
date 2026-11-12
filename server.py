"""BioFig - editor local de figuras cientificas (ecologia y biologia molecular).

Ejecutar:  python server.py   ->  http://127.0.0.1:8765
"""
import asyncio
import json
import os
import re
import time
import unicodedata
import uuid
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import bgremove
import phylopic

ROOT = Path(__file__).parent
ENV_FILE = Path(os.environ.get("BIOFIG_ENV", ROOT / ".env"))
PROJECTS = ROOT / "data" / "projects"
PROJECTS.mkdir(parents=True, exist_ok=True)
ICON_DIR = ROOT / "vendor_src" / "bioicons" / "static" / "icons"

HOST, PORT = "127.0.0.1", int(os.environ.get("BIOFIG_PORT", "8765"))


# ---------------------------------------------------------------- config (.env)
def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def cfg(key: str, default: str = "") -> str:
    return os.environ.get(key) or load_env().get(key) or default


def save_env(updates: dict):
    env = load_env()
    env.update({k: v for k, v in updates.items() if v is not None})
    ENV_FILE.write_text("".join(f"{k}={v}\n" for k, v in env.items()), encoding="utf-8")


# ---------------------------------------------------------------- iconos
_INDEX = ROOT / "data" / "icons.json"
if _INDEX.exists():
    ICONS = json.loads(_INDEX.read_text(encoding="utf-8"))
else:  # todavía no se ejecutó el instalador
    print("AVISO: falta data/icons.json. Ejecutá «python instalar.py» (o abrí iniciar.bat) para instalar la biblioteca de iconos.")
    ICONS = []
ICON_BY_ID = {i["id"]: i for i in ICONS}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def tokens(s: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", norm(s)) if len(t) > 1]


for _i in ICONS:
    _i["_name"] = set(tokens(_i["name"]))
    _i["_tags"] = set(tokens(_i.get("tags", "")))
    _i["_cat"] = set(tokens(_i["category"]))


def search_icons(query: str, group: str | None = None, limit: int = 8, with_score: bool = False) -> list:
    q = tokens(query)
    if not q:
        return []
    scored = []
    for ic in ICONS:
        s = 0.0
        for t in q:
            if t in ic["_name"] or t in ic["_tags"]:
                s += 3
            elif any(n.startswith(t) or t.startswith(n) for n in ic["_name"] if len(n) > 3 and len(t) > 3):
                s += 1.5
            if t in ic["_cat"]:
                s += 1
        if s <= 0:
            continue
        if group and group in ic["groups"]:
            s += 0.5
        if ic["source"] == "BioFig":
            s += 0.3
        s -= 0.05 * max(0, len(ic["_name"]) - len(q))  # nombres cortos y precisos primero
        scored.append((s, ic))
    scored.sort(key=lambda x: -x[0])
    if with_score:
        return [(sc, public_icon(ic)) for sc, ic in scored[:limit]]
    return [public_icon(ic) for _, ic in scored[:limit]]


def public_icon(ic: dict) -> dict:
    return {k: v for k, v in ic.items() if not k.startswith("_")}


# ---------------------------------------------------------------- app
app = FastAPI(title="BioFig")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
if ICON_DIR.exists():
    app.mount("/icons", StaticFiles(directory=ICON_DIR), name="icons")
CUSTOM_DIR = ROOT / "data" / "custom_icons"
CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/custom", StaticFiles(directory=CUSTOM_DIR), name="custom")
for _route, _dir in (("/fluent", ROOT / "vendor_src" / "fluent" / "assets"),
                     ("/healthicons", ROOT / "vendor_src" / "healthicons" / "public" / "icons" / "svg" / "filled")):
    if _dir.exists():  # bibliotecas libres opcionales (Fluent Emoji: MIT; Health Icons: CC0)
        app.mount(_route, StaticFiles(directory=_dir), name=_route.strip("/"))


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/icons")
def api_icons():
    return [public_icon(i) for i in ICONS]


@app.get("/api/icons/search")
def api_icon_search(q: str, group: str | None = None, limit: int = 8):
    return search_icons(q, group, limit)


# ---------------------------------------------------------------- PhyloPic (siluetas de organismos)
async def ai_common_to_taxon(name: str) -> str | None:
    """Usa la IA configurada (si hay) para traducir un nombre comun a nombre cientifico."""
    if not ai_settings()["api_key"]:
        return None
    try:
        out = await llm_chat("Reply ONLY with the scientific name (genus, species or higher clade) that best "
                             "matches the organism the user names. No extra words.", name, max_tokens=2048, temperature=0)
        return out.strip().strip(".").splitlines()[0].lower()[:80] if out.strip() else None
    except HTTPException:
        return None


async def phylopic_lookup(query: str, limit: int = 12) -> list[dict]:
    hits = await phylopic.search(query, limit)
    if not hits:
        taxon = await ai_common_to_taxon(query)
        if taxon:
            hits = await phylopic.search(taxon, limit)
    return hits


@app.get("/api/phylopic/search")
async def api_phylopic_search(q: str, limit: int = 12):
    try:
        return await phylopic_lookup(q, limit)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"PhyloPic no respondio: {e}")


@app.get("/phylopic/{name}")
async def phylopic_svg(name: str):
    p = await phylopic.svg_path(name.removesuffix(".svg"))
    if not p:
        raise HTTPException(404, "imagen no disponible")
    return FileResponse(p, media_type="image/svg+xml")


# ---------------------------------------------------------------- proyectos
class Project(BaseModel):
    name: str
    doc: dict
    thumb: str | None = None


def project_path(pid: str) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", pid):
        raise HTTPException(400, "id invalido")
    return PROJECTS / f"{pid}.json"


@app.get("/api/projects")
def list_projects():
    out = []
    for p in PROJECTS.glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            out.append({"id": p.stem, "name": d.get("name"), "updated": d.get("updated"), "thumb": d.get("thumb")})
        except Exception:
            pass
    return sorted(out, key=lambda x: x.get("updated") or 0, reverse=True)


@app.get("/api/projects/{pid}")
def get_project(pid: str):
    p = project_path(pid)
    if not p.exists():
        raise HTTPException(404, "no existe")
    return json.loads(p.read_text(encoding="utf-8"))


@app.post("/api/projects")
def create_project(body: Project):
    slug = re.sub(r"[^a-z0-9]+", "-", norm(body.name)).strip("-")[:40] or "figura"
    pid = f"{slug}-{uuid.uuid4().hex[:6]}"
    return save_project(pid, body)


@app.put("/api/projects/{pid}")
def save_project(pid: str, body: Project):
    data = {"id": pid, "name": body.name, "updated": time.time(), "doc": body.doc, "thumb": body.thumb}
    project_path(pid).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return {"id": pid, "updated": data["updated"]}


@app.delete("/api/projects/{pid}")
def delete_project(pid: str):
    p = project_path(pid)
    if p.exists():
        p.unlink()
    return {"ok": True}


# ---------------------------------------------------------------- iconos personalizados y quitar fondo (rembg)
import base64 as _b64

CUSTOM_INDEX = CUSTOM_DIR / "index.json"


def _decode_data_url(data: str) -> tuple[str, bytes]:
    m = re.match(r"data:image/(png|jpeg|jpg|webp|gif|svg\+xml)(;base64)?,(.*)", data, re.S)
    if not m:
        raise HTTPException(400, "Formato no soportado (PNG, JPG, WebP, GIF o SVG)")
    kind = {"jpg": "jpeg", "svg+xml": "svg"}.get(m.group(1), m.group(1))
    if m.group(2):
        raw = _b64.b64decode(m.group(3))
    else:
        from urllib.parse import unquote
        raw = unquote(m.group(3)).encode("utf-8")
    return kind, raw


def _custom_list() -> list[dict]:
    return json.loads(CUSTOM_INDEX.read_text(encoding="utf-8")) if CUSTOM_INDEX.exists() else []


def _custom_public(it: dict) -> dict:
    return {"id": "my:" + it["id"], "name": it["name"], "src": f"/custom/{it['file']}", "category": "Mis iconos",
            "groups": ["mis"], "author": "Propio", "license": "Propia", "source": "Mis iconos",
            "aspect": it.get("aspect", 1.0), "tags": it.get("tags", "")}


class BgRequest(BaseModel):
    data: str
    quality: str = "alta"
    soft: bool = True


@app.get("/api/remove-bg/status")
def remove_bg_status():
    return bgremove.status()


@app.post("/api/remove-bg")
def remove_bg(body: BgRequest):
    if not bgremove.installed():
        raise HTTPException(503, "rembg no está instalado. Ejecutá: .venv\\Scripts\\python -m pip install \"rembg[cpu]\"")
    kind, raw = _decode_data_url(body.data)
    if kind == "svg":
        raise HTTPException(400, "Los SVG son vectoriales: no hace falta quitarles el fondo")
    try:
        png, w, h = bgremove.remove_background(raw, body.quality, body.soft)
    except Exception as e:  # p. ej. sin conexión para descargar el modelo la primera vez
        raise HTTPException(500, f"No se pudo quitar el fondo: {e}")
    return {"data": "data:image/png;base64," + _b64.b64encode(png).decode(), "w": w, "h": h}


class CustomIconRequest(BaseModel):
    name: str
    data: str
    tags: str = ""


@app.get("/api/custom-icons")
def list_custom_icons():
    return [_custom_public(it) for it in _custom_list()]


@app.post("/api/custom-icons")
def add_custom_icon(body: CustomIconRequest):
    kind, raw = _decode_data_url(body.data)
    iid = uuid.uuid4().hex[:10]
    if kind == "svg":
        txt = raw.decode("utf-8", errors="ignore")
        if "<svg" not in txt[:5000]:
            raise HTTPException(400, "El archivo no parece un SVG válido")
        file, aspect_ = f"{iid}.svg", 1.0
        m = re.search(r'viewBox\s*=\s*["\']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', txt[:5000])
        if m and float(m.group(2)) > 0:
            aspect_ = float(m.group(1)) / float(m.group(2))
        (CUSTOM_DIR / file).write_bytes(raw)
    else:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(raw))
        im = im.convert("RGBA")
        if max(im.size) > 2400:  # limitar el tamaño guardado
            k = 2400 / max(im.size)
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        file, aspect_ = f"{iid}.png", im.width / im.height
        im.save(CUSTOM_DIR / file, "PNG", optimize=True)
    items = _custom_list()
    it = {"id": iid, "name": (body.name or "Mi icono").strip()[:80], "file": file, "aspect": round(aspect_, 4),
          "tags": body.tags, "created": time.time()}
    items.insert(0, it)
    CUSTOM_INDEX.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    return _custom_public(it)


@app.delete("/api/custom-icons/{iid}")
def delete_custom_icon(iid: str):
    iid = iid.removeprefix("my:")
    items = _custom_list()
    keep = [it for it in items if it["id"] != iid]
    for it in items:
        if it["id"] == iid:
            (CUSTOM_DIR / it["file"]).unlink(missing_ok=True)
    CUSTOM_INDEX.write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "removed": len(items) - len(keep)}


# ---------------------------------------------------------------- estructuras 3D (RCSB PDB)
PDB_CACHE = ROOT / "data" / "pdb_cache"
PDB_RENDERS = ROOT / "static" / "pdb" / "renders"


@app.get("/api/pdb/{pid}")
async def get_pdb(pid: str):
    """Coordenadas de una entrada del PDB (con cache local). Formato PDB, o mmCIF si la entrada es muy grande."""
    pid = pid.upper()
    if not re.fullmatch(r"[0-9][A-Z0-9]{3}", pid):
        raise HTTPException(400, "Código PDB inválido (4 caracteres, ej. 1JFF)")
    PDB_CACHE.mkdir(parents=True, exist_ok=True)
    for ext in ("pdb", "cif"):
        p = PDB_CACHE / f"{pid}.{ext}"
        if p.exists():
            return Response(p.read_bytes(), media_type="text/plain", headers={"X-Format": ext})
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            for ext in ("pdb", "cif"):
                r = await client.get(f"https://files.rcsb.org/download/{pid}.{ext}")
                if r.status_code == 200:
                    (PDB_CACHE / f"{pid}.{ext}").write_bytes(r.content)
                    return Response(r.content, media_type="text/plain", headers={"X-Format": ext})
    except httpx.HTTPError as e:
        raise HTTPException(502, f"No se pudo contactar al RCSB PDB: {e}")
    raise HTTPException(404, f"No existe la entrada {pid} en el PDB")


class RenderRequest(BaseModel):
    id: str
    data: str  # data URL PNG con fondo transparente


@app.post("/api/pdb/render")
def save_pdb_render(body: RenderRequest):
    m = re.match(r"data:image/png;base64,(.+)", body.data, re.S)
    if not m or not re.fullmatch(r"[0-9][A-Za-z0-9]{3}", body.id):
        raise HTTPException(400, "datos inválidos")
    import base64
    import hashlib
    raw = base64.b64decode(m.group(1))
    PDB_RENDERS.mkdir(parents=True, exist_ok=True)
    name = f"{body.id.upper()}-{hashlib.sha1(raw).hexdigest()[:10]}.png"
    (PDB_RENDERS / name).write_bytes(raw)
    return {"src": f"/static/pdb/renders/{name}"}


# ---------------------------------------------------------------- exportaciones a disco
EXPORTS = ROOT / "exports"


class ExportRequest(BaseModel):
    name: str
    data: str  # data URL (image/png o image/jpeg)


@app.post("/api/export")
def save_export(body: ExportRequest):
    m = re.match(r"data:image/(png|jpeg);base64,(.+)", body.data, re.S)
    if not m:
        raise HTTPException(400, "formato no soportado")
    import base64
    EXPORTS.mkdir(exist_ok=True)
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", norm(body.name)).strip("-")[:80] or "figura"
    path = EXPORTS / f"{stem}.{'png' if m.group(1) == 'png' else 'jpg'}"
    path.write_bytes(base64.b64decode(m.group(2)))
    return {"path": str(path), "bytes": path.stat().st_size}


# ---------------------------------------------------------------- IA (DeepSeek)
CANVAS_W, CANVAS_H = 1400, 900

SYSTEM_PROMPT = f"""You design clean scientific figures (ecology and molecular biology), like those in
textbooks and papers. Given a description, return ONLY a JSON object describing the figure layout on a
{CANVAS_W}x{CANVAS_H} px canvas (origin top-left). Schema:
{{
  "title": "short title (in the user's language)",
  "elements": [
    {{"id": "e1", "kind": "icon", "query": "1-3 ENGLISH keywords to find a pictogram, e.g. 'fox', 'oak tree', 'ribosome', 'DNA helix'",
      "taxon": "ONLY for organisms: binomial of a well-known REPRESENTATIVE species, never a broad group (grasshopper -> 'Locusta migratoria', grass -> 'Poa pratensis', mushroom/fungi -> 'Agaricus bisporus', oak -> 'Quercus robur'); omit otherwise",
      "clade": "for organisms: a broader family or order as fallback, e.g. 'Canidae', 'Fagaceae', 'Phasianidae'",
      "label": "caption in the user's language", "x": 300, "y": 400, "w": 140}},
    {{"id": "r1", "kind": "region", "shape": "rect" | "ellipse", "x": 100, "y": 100, "w": 500, "h": 300,
      "fill": "#hex light color", "label": "e.g. Citoplasma / Suelo / Atmosfera"}},
    {{"id": "t1", "kind": "text", "text": "free text", "x": 700, "y": 40, "size": 28}}
  ],
  "connectors": [
    {{"from": "e1", "to": "e2", "kind": "arrow" | "inhibit" | "dashed" | "double", "label": "optional short label"}}
  ]
}}
Rules:
- icon x,y are the CENTER of the icon; region/text x,y are the TOP-LEFT corner.
- Icons 80-200 px wide. Leave at least 60 px between icons and room for captions below them.
- Use regions for compartments (cell, nucleus, membrane areas, soil, water, atmosphere, trophic levels).
  List regions FIRST so they are drawn behind icons.
- "inhibit" = blunt-ended (T-bar) inhibition arrow; "dashed" = indirect/flux; "double" = reversible.
- For food webs: arrows go from prey to predator (direction of energy flow).
- For biogeochemical cycles (carbon, nitrogen, water) arrange processes in a loop with labelled arrows.
- For signaling pathways: ligand -> receptor at membrane -> cascade -> nucleus -> gene expression.
- Keep it readable: 4-18 icons. Put a title text at the top.
- Self-made pictograms available (use these exact queries when relevant): sun, cloud, rain, tree, conifer,
  grass, soil, water, mountain, co2, lipid bilayer, dna helix, mrna, protein, receptor, ion channel,
  enzyme, food web node.
"""


MICROBE_WORDS = ("bacteri", "archae", "virus", "viral", "phage", "fago", "protist", "protozo", "amoeba",
                 "ameba", "plasmodium", "yeast", "levadura", "microb")


class AIRequest(BaseModel):
    prompt: str
    group: str | None = None  # "ecologia" | "molecular" | None


class KeyRequest(BaseModel):
    provider: str = "deepseek"  # "deepseek" | "gemini"
    api_key: str
    model: str | None = None
    base_url: str | None = None


PROVIDERS = {
    "deepseek": {"label": "DeepSeek", "key": "DEEPSEEK_API_KEY", "model": "DEEPSEEK_MODEL", "base": "DEEPSEEK_BASE_URL",
                 "default_model": "deepseek-chat", "default_base": "https://api.deepseek.com"},
    "gemini": {"label": "Gemini", "key": "GEMINI_API_KEY", "model": "GEMINI_MODEL", "base": "GEMINI_BASE_URL",
               "default_model": "gemini-2.5-flash", "default_base": "https://generativelanguage.googleapis.com"},
}


def provider_settings(name: str) -> dict:
    p = PROVIDERS[name]
    return {"provider": name, "label": p["label"], "api_key": cfg(p["key"]),
            "model": cfg(p["model"], p["default_model"]),
            "base_url": cfg(p["base"], p["default_base"]).rstrip("/")}


def ai_settings() -> dict:
    """Proveedor activo: AI_PROVIDER si esta definido, si no el primero que tenga clave."""
    chosen = cfg("AI_PROVIDER").lower()
    if chosen in PROVIDERS:
        return provider_settings(chosen)
    for name in PROVIDERS:
        s = provider_settings(name)
        if s["api_key"]:
            return s
    return provider_settings("deepseek")


@app.get("/api/ai/status")
def ai_status():
    s = ai_settings()
    return {"configured": bool(s["api_key"]), "provider": s["provider"], "label": s["label"], "model": s["model"],
            "base_url": s["base_url"],
            "providers": {n: {"label": p["label"], "configured": bool(provider_settings(n)["api_key"]),
                              "model": provider_settings(n)["model"]} for n, p in PROVIDERS.items()}}


class ProviderRequest(BaseModel):
    provider: str


@app.post("/api/ai/provider")
def ai_set_provider(body: ProviderRequest):
    if body.provider not in PROVIDERS:
        raise HTTPException(400, "proveedor desconocido")
    if not provider_settings(body.provider)["api_key"]:
        raise HTTPException(400, f"Primero carga la clave de {PROVIDERS[body.provider]['label']}")
    save_env({"AI_PROVIDER": body.provider})
    return ai_status()


def pick_gemini_model(models: list[dict]) -> str | None:
    """Elige el modelo Flash estable mas nuevo que soporte generateContent."""
    best = None
    for m in models:
        name = m.get("name", "").removeprefix("models/")
        if "generateContent" not in m.get("supportedGenerationMethods", []):
            continue
        mm = re.fullmatch(r"gemini-(\d+(?:\.\d+)?)-flash", name)  # sin lite/preview/image/tts/latest
        if not mm:
            continue
        ver = float(mm.group(1))
        if best is None or ver > best[0]:
            best = (ver, name)
    return best[1] if best else None


@app.post("/api/ai/key")
async def ai_set_key(body: KeyRequest):
    if body.provider not in PROVIDERS:
        raise HTTPException(400, "proveedor desconocido")
    p = PROVIDERS[body.provider]
    key = body.api_key.strip()
    if not key:
        raise HTTPException(400, "clave vacia")
    base = ((body.base_url or "").strip() or cfg(p["base"], p["default_base"])).rstrip("/")
    model = (body.model or "").strip() or None
    note = ""
    # Validar la clave antes de guardarla
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            if body.provider == "gemini":
                r = await client.get(f"{base}/v1beta/models", params={"pageSize": 200}, headers={"x-goog-api-key": key})
                if r.status_code == 200 and not model:
                    model = pick_gemini_model(r.json().get("models", []))
            else:
                r = await client.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"})
        if r.status_code in (400, 401, 403):
            raise HTTPException(400, f"{p['label']} rechazo la clave ({r.status_code}). Revisala.")
        if r.status_code != 200:
            note = f"No se pudo verificar la clave ({r.status_code}); se guardo igual."
    except httpx.HTTPError:
        note = "Sin conexion para verificar la clave; se guardo igual."
    save_env({p["key"]: key, p["model"]: model, p["base"]: (body.base_url or "").strip() or None,
              "AI_PROVIDER": body.provider})
    return {**ai_status(), "note": note}


async def llm_chat(system: str, user: str, json_mode: bool = False, max_tokens: int = 4000,
                   temperature: float = 0.4) -> str:
    """Envia un mensaje al proveedor activo y devuelve el texto de la respuesta."""
    s = ai_settings()
    if not s["api_key"]:
        raise HTTPException(503, "Falta la clave de la IA. Cargala en el panel IA o en el archivo .env")
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            if s["provider"] == "gemini":
                gen = {"temperature": temperature, "maxOutputTokens": max(max_tokens, 8192)}
                if json_mode:
                    gen["responseMimeType"] = "application/json"
                r = await client.post(
                    f"{s['base_url']}/v1beta/models/{s['model']}:generateContent",
                    headers={"x-goog-api-key": s["api_key"]},
                    json={"systemInstruction": {"parts": [{"text": system}]},
                          "contents": [{"role": "user", "parts": [{"text": user}]}],
                          "generationConfig": gen})
            else:
                payload = {"model": s["model"], "temperature": temperature, "max_tokens": max_tokens,
                           "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}
                r = await client.post(f"{s['base_url']}/chat/completions", json=payload,
                                      headers={"Authorization": f"Bearer {s['api_key']}"})
    except httpx.HTTPError as e:
        raise HTTPException(502, f"No se pudo contactar a {s['label']}: {e}")
    if r.status_code != 200:
        raise HTTPException(502, f"{s['label']} respondio {r.status_code}: {r.text[:400]}")
    data = r.json()
    if s["provider"] == "gemini":
        cands = data.get("candidates") or []
        parts = (cands[0].get("content") or {}).get("parts", []) if cands else []
        text = "".join(pt.get("text", "") for pt in parts if not pt.get("thought"))
        if not text:
            reason = cands[0].get("finishReason") if cands else (data.get("promptFeedback") or {}).get("blockReason")
            raise HTTPException(502, f"Gemini no devolvio texto (motivo: {reason or 'desconocido'})")
        return text
    return data["choices"][0]["message"]["content"]


@app.post("/api/ai/figure")
async def ai_figure(body: AIRequest):
    content = await llm_chat(SYSTEM_PROMPT, body.prompt, json_mode=True, max_tokens=8000)
    try:
        spec = json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            raise HTTPException(502, "La respuesta de la IA no es JSON valido")
        spec = json.loads(m.group(0))

    # Resolver cada elemento a un icono real (en paralelo). Organismos: siluetas de PhyloPic primero, para
    # que la figura tenga un estilo uniforme; los iconos de Bioicons quedan como alternativas.
    # Microorganismos: Bioicons primero (sus dibujos son mejores que las siluetas).
    async def resolve(el):
        q = el.get("query") or el.get("label") or ""
        local = search_icons(q, body.group, limit=6, with_score=True)
        strong = [ic for sc, ic in local if sc >= 3 * len(q.split())]  # todas las palabras coinciden
        hits = strong + [ic for _, ic in local if ic not in strong]
        taxon = (el.get("taxon") or "").strip()
        microbe = any(w in norm(f"{taxon} {el.get('clade', '')} {q}") for w in MICROBE_WORDS)
        broad = taxon and " " not in taxon  # genero o grupo amplio: sus siluetas suelen ser poco tipicas
        if taxon and not ((microbe or broad) and strong):
            try:
                pp = (await phylopic.search(taxon, 6)
                      or (el.get("clade") and await phylopic.search(el["clade"], 6))
                      or await phylopic.search(q, 6))
            except httpx.HTTPError:
                pp = []
            hits = pp[:4] + hits + pp[4:]
        if not hits and el.get("label"):
            hits = search_icons(el["label"], body.group, limit=6)
        el["icon"] = hits[0] if hits else None
        el["alternatives"] = hits[1:7]

    await asyncio.gather(*(resolve(el) for el in spec.get("elements", []) if el.get("kind") == "icon"))
    spec["canvas"] = {"w": CANVAS_W, "h": CANVAS_H}
    return spec


@app.get("/api/version")
def api_version():
    """Permite a la página detectar si el servidor quedó desactualizado."""
    return {"pdb": True, "export": True}


if __name__ == "__main__":
    print(f"BioFig en http://{HOST}:{PORT}")
    # reload: si cambia el código de Python, el servidor se reinicia solo (no hace falta cerrar iniciar.bat)
    uvicorn.run("server:app", host=HOST, port=PORT, app_dir=str(ROOT), reload=True,
                reload_dirs=[str(ROOT)], reload_includes=["*.py"],
                reload_excludes=["vendor_src/*", "data/*", "exports/*", ".venv/*", "static/*"])
