#!/usr/bin/env bash
# BioFig: ./iniciar.sh para abrir. La primera vez instala todo lo necesario.
set -e
cd "$(dirname "$0")"
if [ ! -f .instalado ]; then
  echo "Primera vez: instalando BioFig (puede tardar unos minutos)..."
  PY="$(command -v python3 || command -v python || true)"
  if [ -z "$PY" ]; then echo "No se encontró Python 3.11+. Instalalo desde https://www.python.org/downloads/"; exit 1; fi
  "$PY" instalar.py "$@"
fi
echo "Abriendo BioFig en http://127.0.0.1:8765 ... (Ctrl+C para apagarlo)"
( sleep 3; (xdg-open http://127.0.0.1:8765 || open http://127.0.0.1:8765) >/dev/null 2>&1 || true ) &
exec .venv/bin/python server.py
