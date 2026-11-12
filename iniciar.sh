#!/usr/bin/env bash
# BioFig: ./iniciar.sh para abrir. La primera vez instala todo lo necesario
# y, si faltan Python 3.11+ o Git, ofrece instalarlos (Homebrew en Mac; apt/dnf/pacman/zypper en Linux).
set -u
cd "$(dirname "$0")"

buscar_python() {  # deja en PY la ruta de un Python 3.11+ (o vacío)
  PY=""
  [ -n "${BIOFIG_SIMULAR_SIN_PYTHON:-}" ] && return
  for c in python3.13 python3.12 python3.11 python3 python /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if command -v "$c" >/dev/null 2>&1; then
      p="$("$c" verificar_python.py 2>/dev/null)" && [ -n "$p" ] && { PY="$p"; return; }
    fi
  done
}

hay_git() { [ -z "${BIOFIG_SIMULAR_SIN_GIT:-}" ] && command -v git >/dev/null 2>&1; }

preguntar() {  # devuelve 0 si la respuesta es sí
  printf "%s [s/N] " "$1"
  read -r r || r=""
  case "$r" in s|S|si|SI|sí|Sí|y|Y) return 0 ;; *) return 1 ;; esac
}

instalar_requisitos() {  # $1 = qué falta
  echo
  echo "Falta: $1"
  if [ "$(uname)" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
      preguntar "¿Instalo Python 3.12 y Git con Homebrew?" && brew install python@3.12 git
    else
      echo "Opción 1: instalá Homebrew (https://brew.sh) y ejecutá:  brew install python@3.12 git"
      echo "Opción 2: descargá Python desde https://www.python.org/downloads/ e instalá Git con:  xcode-select --install"
    fi
    return
  fi
  if command -v apt-get >/dev/null 2>&1; then CMD="sudo apt-get update && sudo apt-get install -y git python3 python3-venv"
  elif command -v dnf >/dev/null 2>&1; then CMD="sudo dnf install -y git python3"
  elif command -v pacman >/dev/null 2>&1; then CMD="sudo pacman -S --needed --noconfirm git python"
  elif command -v zypper >/dev/null 2>&1; then CMD="sudo zypper install -y git python3"
  else
    echo "Instalá Python 3.11+ y Git con el gestor de paquetes de tu sistema."
    return
  fi
  echo "Comando para instalarlo: $CMD"
  preguntar "¿Lo ejecuto ahora? (te va a pedir tu contraseña de administrador)" && bash -c "$CMD"
}

if [ ! -f .instalado ]; then
  echo "================================================================"
  echo "  BioFig - primera vez: preparando la instalación"
  echo "================================================================"
  buscar_python
  FALTA=""
  [ -z "$PY" ] && FALTA="Python 3.11+"
  hay_git || FALTA="${FALTA:+$FALTA y }Git"
  if [ -n "$FALTA" ]; then
    instalar_requisitos "$FALTA"
    buscar_python
  fi
  # Ubuntu 22.04 y similares traen python3 3.10: ofrecer python3.11 en paralelo
  if [ -z "$PY" ] && [ -z "${BIOFIG_SIMULAR_SIN_PYTHON:-}" ] && command -v apt-get >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
    echo "Tu python3 es anterior a 3.11."
    preguntar "¿Instalo python3.11 en paralelo (sudo apt-get install -y python3.11 python3.11-venv)?" \
      && sudo apt-get install -y python3.11 python3.11-venv && buscar_python
  fi
  if [ -z "$PY" ]; then echo; echo "No se encontró Python 3.11 o más nuevo. Instalalo y volvé a ejecutar ./iniciar.sh"; exit 1; fi
  if ! hay_git; then echo; echo "No se encontró Git. Instalalo y volvé a ejecutar ./iniciar.sh"; exit 1; fi
  echo "  OK  Python: $PY"
  echo "  OK  Git"
  "$PY" instalar.py "$@" || { echo; echo "La instalación no terminó. Revisá el mensaje de arriba y volvé a ejecutar ./iniciar.sh"; exit 1; }
fi

if [ ! -x .venv/bin/python ]; then rm -f .instalado; echo "Falta el entorno de BioFig: volvé a ejecutar ./iniciar.sh"; exit 1; fi
echo "Abriendo BioFig en http://127.0.0.1:8765 ... (Ctrl+C para apagarlo)"
( sleep 3; (xdg-open http://127.0.0.1:8765 || open http://127.0.0.1:8765) >/dev/null 2>&1 || true ) &
exec .venv/bin/python server.py
