"""Quitar el fondo de imágenes con rembg (https://github.com/danielgatis/rembg, licencia MIT).

Todo corre en esta máquina. Cada modelo se descarga una sola vez (a ~/.u2net) la primera vez que se usa.
"""
import io
import os
import threading
from pathlib import Path

MODELS = {  # clave -> (modelo de rembg, tamaño aproximado de la descarga en MB, descripción)
    "alta": ("isnet-general-use", 179, "Alta calidad (IS-Net)"),
    "estandar": ("u2net", 176, "Estándar (U²-Net)"),
    "rapida": ("u2netp", 5, "Rápida (U²-Netp, liviano)"),
}
_sessions: dict = {}
_lock = threading.Lock()
MAX_SIDE = 2000  # las imágenes más grandes se reducen antes de procesar


def installed() -> bool:
    try:
        import rembg  # noqa: F401
        return True
    except Exception:
        return False


def _model_dir() -> Path:
    return Path(os.environ.get("U2NET_HOME", Path.home() / ".u2net"))


def status() -> dict:
    return {
        "installed": installed(),
        "models": {k: {"label": d, "sizeMB": mb, "ready": (_model_dir() / f"{name}.onnx").exists()}
                   for k, (name, mb, d) in MODELS.items()},
    }


def _session(quality: str):
    name = MODELS.get(quality, MODELS["alta"])[0]
    with _lock:  # una sesión por modelo; la primera vez descarga el modelo
        if name not in _sessions:
            from rembg import new_session
            _sessions[name] = new_session(name)
        return _sessions[name]


def trim_png(png: bytes, pad: int = 6) -> tuple[bytes, int, int]:
    """Recorta el borde transparente."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bbox = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        im = im.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad)))
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return out.getvalue(), im.width, im.height


def remove_background(data: bytes, quality: str = "alta", soft_edges: bool = True) -> tuple[bytes, int, int]:
    """Devuelve PNG con fondo transparente, recortado al objeto."""
    from PIL import Image
    from rembg import remove
    im = Image.open(io.BytesIO(data))
    im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
    if max(im.size) > MAX_SIDE:
        k = MAX_SIDE / max(im.size)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    result = remove(im, session=_session(quality), post_process_mask=soft_edges)
    buf = io.BytesIO()
    result.save(buf, "PNG")
    return trim_png(buf.getvalue())
