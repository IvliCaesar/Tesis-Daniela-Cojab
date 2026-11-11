"""Compara las salidas reconstruidas con las de la autora, columna por columna.

Uso: python pipeline/validar.py <carpeta de la autora> <carpeta reconstruida> archivo1 [archivo2 ...]
Reporta, por columna numérica común, la proporción de filas que coinciden con
tolerancia relativa de 1e-6 y la diferencia máxima.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

A, B = Path(sys.argv[1]), Path(sys.argv[2])
KEYS = ['empresa', 'fecha', 'periodo', 'instrumento']
for f in sys.argv[3:]:
    a = pd.read_parquet(A / f); b = pd.read_parquet(B / f)
    k = [c for c in KEYS if c in a.columns and c in b.columns]
    m = a.merge(b, on=k, how='outer', suffixes=('_a', '_b'), indicator=True)
    print(f'\n== {f}: autora {len(a):,} filas, reconstruido {len(b):,}; '
          f'solo autora {(m._merge == "left_only").sum():,}, solo reconstruido {(m._merge == "right_only").sum():,}')
    both = m[m._merge == 'both']
    for c in a.columns:
        if c in k or c + '_b' not in both or not pd.api.types.is_numeric_dtype(a[c]):
            continue
        x, y = both[c + '_a'].astype(float), both[c + '_b'].astype(float)
        ok = np.isclose(x, y, rtol=1e-6, atol=1e-12, equal_nan=True)
        dmax = np.nanmax(np.abs(x - y)) if (~ok).any() else 0.0
        print(f'   {c:24s} coinciden {100 * ok.mean():6.2f}%   dif. máx {dmax:.4g}')
