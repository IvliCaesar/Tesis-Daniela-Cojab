"""Módulo 4 (reconstruido): participación del SIC por suma de centros.

Uso: python pipeline/m4_participacion.py <carpeta con m1_*.parquet y calendario.parquet> <carpeta de salida>

Escribe m4_psic_diaria/mensual/anual(_real).parquet con las mismas columnas que los
archivos de la autora. Reglas (apartado 3.3.1 de la tesis):
  V_s,t = V^BMV + V^BIVA, con BIVA nulo antes del 25 de julio de 2018;
  PSIC = 100 * V_SIC / (V_SIC + V_LOCAL); solo sesiones del calendario;
  el consolidado (sufijo MM) se conserva como referencia.
El INPC anual (promedio, base 2018 = 100) se lee de la serie MXCPI de la terminal
si se pasa el libro de índices como tercer argumento.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

IN, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
BIVA0 = pd.Timestamp('2018-07-25')
cal = pd.read_parquet(IN / 'calendario.parquet')
ses = set(cal.loc[cal.sesion, 'fecha'])


def importe(seg, centro):
    x = pd.read_parquet(IN / f'm1_{seg}_{centro}.parquet', columns=['fecha', 'turnover'])
    x = x[x.fecha.isin(ses) & (x.turnover > 0)]
    if centro == 'biva':
        x = x[x.fecha >= BIVA0]
    return x.groupby('fecha').turnover.sum()


idx = pd.DatetimeIndex(sorted(ses))
d = pd.DataFrame(index=idx)
d['sic'] = importe('sic', 'bmv').reindex(idx, fill_value=0) + importe('sic', 'biva').reindex(idx, fill_value=0)
d['sic_mm'] = importe('sic', 'glob').reindex(idx, fill_value=0)
d['loc'] = importe('loc', 'bmv').reindex(idx, fill_value=0) + importe('loc', 'biva').reindex(idx, fill_value=0)
d['loc_mm'] = importe('loc', 'glob').reindex(idx, fill_value=0)
d.index.name = 'fecha'


def shares(z):
    z = z.copy()
    z['psic'] = 100 * z.sic / (z.sic + z['loc'])
    z['psic_consolidado'] = 100 * z.sic_mm / (z.sic_mm + z.loc_mm)
    return z


dia = shares(d)
dia.reset_index().to_parquet(OUT / 'm4_psic_diaria.parquet', index=False)
for nom, f in [('mensual', 'MS'), ('anual', 'YS')]:
    z = shares(d.resample(f).sum())
    z['diferencia_pp'] = z.psic - z.psic_consolidado
    z.index.name = 'periodo'
    z.reset_index().to_parquet(OUT / f'm4_psic_{nom}.parquet', index=False)
print('ok', len(dia), 'sesiones')
