"""Instalador de BioFig: deja todo listo la primera vez que se descarga o clona el proyecto.

Uso:
    python instalar.py              # instalación completa
    python instalar.py --sin-rembg  # sin "quitar fondo" (ahorra ~400 MB de dependencias)
    python instalar.py --sin-ejemplos

Se puede volver a ejecutar cuando quieras: lo que ya está instalado se saltea.
Solo usa la biblioteca estándar de Python (no necesita nada instalado de antemano salvo Python y Git).
"""
import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8: no fallar por los símbolos ✓ ✗
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
VENDOR = ROOT / "vendor_src"

# Bibliotecas de iconos libres, fijadas a una versión exacta para que todos tengan los mismos iconos.
# (nombre, repositorio, commit, carpetas a descargar)
LIBRARIES = [
    ("bioicons", "https://github.com/duerrsimon/bioicons.git",
     "d29e766ea7580b8063c4f47b29e872db40a4d979", ["/static/icons/"]),
    ("fluent", "https://github.com/microsoft/fluentui-emoji.git",
     "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc", ["/assets/*/Flat/*.svg", "/assets/*/Default/Flat/*.svg"]),
    ("healthicons", "https://github.com/resolvetosavelives/healthicons.git",
     "2080c1b40e4829f2f4217e03bc22908b4e402f6b", ["/public/icons/svg/filled/*", "/public/icons/meta-data.json"]),
]


def paso(n, total, texto):
    print(f"\n[{n}/{total}] {texto}", flush=True)


def run(cmd, **kw):
    print("   $", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def ok(texto):
    print(f"   ✓ {texto}", flush=True)


def fail(texto):
    print(f"\n✗ {texto}", flush=True)
    sys.exit(1)


def check_requisitos():
    if sys.version_info < (3, 11):
        fail(f"Hace falta Python 3.11 o más nuevo (tenés {sys.version.split()[0]}). Descargalo de https://www.python.org/downloads/")
    ok(f"Python {sys.version.split()[0]}")
    if not shutil.which("git"):
        fail("Hace falta Git para descargar las bibliotecas de iconos. Instalalo desde https://git-scm.com/downloads")
    ok("Git disponible")


def crear_venv():
    if PY.exists():
        ok("El entorno virtual .venv ya existe")
        return
    venv.EnvBuilder(with_pip=True).create(VENV)
    ok("Entorno virtual creado en .venv")


def instalar_dependencias(con_rembg):
    run([PY, "-m", "pip", "install", "--disable-pip-version-check", "-q", "--upgrade", "pip"])
    run([PY, "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", ROOT / "requirements.txt"])
    ok("Servidor web y dependencias principales")
    if con_rembg:
        print("   (rembg + ONNX Runtime para quitar fondos: puede tardar unos minutos)", flush=True)
        run([PY, "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", ROOT / "requirements-rembg.txt"])
        ok("rembg (quitar fondo de imágenes, corre local)")
    else:
        print("   - rembg omitido (--sin-rembg). Se puede instalar después con:")
        print(f"     {PY} -m pip install -r requirements-rembg.txt")


def git_head(path):
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def descargar_bibliotecas():
    VENDOR.mkdir(exist_ok=True)
    for name, url, commit, patterns in LIBRARIES:
        dest = VENDOR / name
        if git_head(dest) == commit:
            ok(f"{name} ya está descargado")
            continue
        if dest.exists():
            shutil.rmtree(dest, onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))
        dest.mkdir(parents=True)
        g = ["git", "-C", dest]
        run(g + ["init", "-q"])
        run(g + ["remote", "add", "origin", url])
        run(g + ["config", "core.sparseCheckout", "true"])
        run(g + ["config", "core.longpaths", "true"])  # Windows: algunos nombres superan los 260 caracteres
        (dest / ".git" / "info").mkdir(parents=True, exist_ok=True)
        (dest / ".git" / "info" / "sparse-checkout").write_text("\n".join(patterns) + "\n", encoding="utf-8")
        run(g + ["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", commit])
        run(g + ["checkout", "-q", "FETCH_HEAD"])
        ok(f"{name} descargado")


def generar_iconos():
    # Los iconos propios ya vienen en el repositorio; se regeneran solo si faltan.
    if not (ROOT / "static" / "builtin" / "builtin.json").exists():
        run([PY, ROOT / "make_builtin.py"], cwd=ROOT)
    if not (ROOT / "static" / "extra" / "extra.json").exists():
        run([PY, ROOT / "make_extra_icons.py"], cwd=ROOT)
    run([PY, ROOT / "build_index.py"], cwd=ROOT)
    ok("Índice de la biblioteca de iconos (data/icons.json)")


def crear_ejemplos():
    marca = ROOT / "data" / ".ejemplos_creados"
    if marca.exists():
        ok("Las figuras de ejemplo ya estaban creadas")
        return
    (ROOT / "data" / "projects").mkdir(parents=True, exist_ok=True)
    for args in (["ejemplos/figuras_tubulina_pmca.py"], ["ejemplos/figuras_tubulina_pmca.py", "--demo"], ["ejemplos/bofedal.py"]):
        run([PY, ROOT / args[0], *args[1:]], cwd=ROOT)
    marca.write_text("ok", encoding="utf-8")
    ok("Figuras de ejemplo (abrilas desde «Abrir» en la app)")


def main():
    ap = argparse.ArgumentParser(description="Instalador de BioFig")
    ap.add_argument("--sin-rembg", action="store_true", help="no instalar la función de quitar fondo")
    ap.add_argument("--sin-ejemplos", action="store_true", help="no crear las figuras de ejemplo")
    a = ap.parse_args()
    print("=" * 64 + "\n  BioFig — instalación\n" + "=" * 64)
    total = 6
    paso(1, total, "Requisitos");                 check_requisitos()
    paso(2, total, "Entorno virtual de Python");  crear_venv()
    paso(3, total, "Dependencias");               instalar_dependencias(not a.sin_rembg)
    paso(4, total, "Bibliotecas de iconos libres (~620 MB, solo la primera vez)"); descargar_bibliotecas()
    paso(5, total, "Biblioteca de iconos");       generar_iconos()
    paso(6, total, "Figuras de ejemplo")
    if a.sin_ejemplos:
        print("   - omitidas (--sin-ejemplos)")
    else:
        crear_ejemplos()
    (ROOT / ".instalado").write_text("ok", encoding="utf-8")
    inicio = "iniciar.bat (doble clic)" if os.name == "nt" else "./iniciar.sh"
    print("\n" + "=" * 64 + f"\n  ✓ Listo. Para abrir BioFig: {inicio}\n    → http://127.0.0.1:8765\n"
          "  Opcional: cargá una clave de Gemini o DeepSeek en la pestaña «IA» para generar figuras con IA.\n" + "=" * 64)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        fail(f"Falló un paso: {' '.join(str(c) for c in e.cmd)}\n  Revisá tu conexión a internet y volvé a ejecutar «python instalar.py».")
    except KeyboardInterrupt:
        fail("Instalación cancelada. Podés retomarla ejecutando de nuevo «python instalar.py».")
