"""Orienta una estructura PDB para dibujarla: eje principal en X, vista por la cara mas ancha.

Uso:
  python ejemplos/orientar_pdb.py entrada.pdb salida.pdb A B        # dimero: cadena A a la izquierda, B a la derecha
  python ejemplos/orientar_pdb.py entrada.pdb salida.pdb --chain A  # solo la cadena A
"""
import sys

import numpy as np

args = sys.argv[1:]
keep = None
if "--chain" in args:
    i = args.index("--chain")
    keep = args[i + 1]
    del args[i:i + 2]
src, dst = args[0], args[1]
left, right = (args[2], args[3]) if len(args) > 3 else (None, None)

lines = open(src, encoding="utf-8").read().splitlines()
if keep:  # descartar las demas cadenas (y el agua)
    lines = [l for l in lines if not l.startswith(("ATOM", "HETATM", "ANISOU", "TER"))
             or (l[21] == keep and l[17:20] != "HOH")]
atoms = [i for i, l in enumerate(lines) if l.startswith(("ATOM", "HETATM"))]
xyz = np.array([[float(lines[i][30:38]), float(lines[i][38:46]), float(lines[i][46:54])] for i in atoms])
ca = np.array([lines[i][12:16].strip() == "CA" and lines[i].startswith("ATOM") for i in atoms])
chain = np.array([lines[i][21] for i in atoms])

c = xyz[ca].mean(0)
_, _, vt = np.linalg.svd(xyz[ca] - c, full_matrices=False)  # ejes principales
R = vt.copy()
if np.linalg.det(R) < 0:
    R[2] *= -1
new = (xyz - c) @ R.T
if left and right:
    flip = new[ca & (chain == left), 0].mean() > new[ca & (chain == right), 0].mean()
else:  # una cadena: extremo N a la izquierda
    nca = np.where(ca)[0]
    flip = new[nca[: len(nca) // 10], 0].mean() > new[nca[-len(nca) // 10:], 0].mean()
if flip:
    new[:, 0] *= -1
    new[:, 2] *= -1  # rotacion de 180 grados en Y (conserva la quiralidad)
for k, i in enumerate(atoms):
    l = lines[i].ljust(80)
    lines[i] = f"{l[:30]}{new[k, 0]:8.3f}{new[k, 1]:8.3f}{new[k, 2]:8.3f}{l[54:]}".rstrip()
open(dst, "w", encoding="utf-8").write("\n".join(l for l in lines if not l.startswith("ANISOU")) + "\n")
ext = new[ca].max(0) - new[ca].min(0)
print(f"orientado -> {dst}; {ca.sum()} residuos; extension (A): x={ext[0]:.0f} y={ext[1]:.0f} z={ext[2]:.0f}")
