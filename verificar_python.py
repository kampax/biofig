"""Usado por iniciar.bat / iniciar.sh: imprime la ruta de este Python si es 3.11 o más nuevo.

Sale con código 0 si sirve y 1 si es demasiado viejo. Compatible con cualquier Python 3.
"""
import sys

if sys.version_info >= (3, 11):
    print(sys.executable)
    sys.exit(0)
sys.exit(1)
