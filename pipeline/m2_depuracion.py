"""Módulo 2 (reconstruido): calendario, panel diario, serie principal, vigencia, capitalización y terciles.

Uso: python pipeline/m2_depuracion.py <carpeta con m1_*.parquet> <mapa_empresas.parquet> <carpeta de salida>

El mapa serie -> empresa (columnas instrumento, empresa) viene del campo ID_BB_COMPANY de la
terminal; en los libros descargados ese campo no está resuelto ("#N/A Requesting Data"), así que
es una entrada y no se reconstruye. Reglas (apartados 3.2.3, 3.2.4 y 3.3.3 de la tesis):
  * calendario: días hábiles del 1/1/2004 al 30/9/2026; sesión = algún instrumento del
    universo local completo con importe positivo en BMV o BIVA;
  * panel diario: campos del consolidado (MM) con el importe sustituido por BMV + BIVA,
    BIVA nulo antes del 25/7/2018; solo sesiones del calendario;
  * serie principal: la de mayor importe acumulado de cada empresa;
  * vigencia: sesiones entre la primera y la última operación de la serie, y con alguna
    operación en los doce meses previos;
  * capitalización de la empresa: máximo entre clases en cada sesión, en pesos;
  * terciles fijos por el promedio del logaritmo de la capitalización diaria de la empresa.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

IN, MAPA, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
INI, FIN, BIVA0 = pd.Timestamp('2004-01-01'), pd.Timestamp('2026-09-30'), pd.Timestamp('2018-07-25')

# ---- calendar
op = []
for c in ('bmv', 'biva'):
    x = pd.read_parquet(IN / f'm1_loc_{c}.parquet', columns=['fecha', 'turnover'])
    if c == 'biva':
        x = x[x.fecha >= BIVA0]
    op.append(x.loc[x.turnover > 0, 'fecha'])
con_op = set(pd.concat(op))
dias = pd.bdate_range(INI, FIN)
cal = pd.DataFrame({'fecha': dias, 'sesion': [d in con_op for d in dias]})
cal.to_parquet(OUT / 'calendario.parquet', index=False)
ses = pd.DatetimeIndex(cal.loc[cal.sesion, 'fecha'])

# ---- daily panel of the liquidity universe
g = pd.read_parquet(IN / 'm1_liq_glob.parquet')
imp = []
for c in ('bmv', 'biva'):
    x = pd.read_parquet(IN / f'm1_liq_{c}.parquet', columns=['fecha', 'instrumento', 'turnover'])
    if c == 'biva':
        x = x[x.fecha >= BIVA0]
    imp.append(x)
imp = pd.concat(imp).groupby(['fecha', 'instrumento']).turnover.sum(min_count=1).rename('turnover_c').reset_index()
p = g.merge(imp, on=['fecha', 'instrumento'], how='left')
p['turnover'] = p.turnover_c; p = p.drop(columns='turnover_c')
p = p[p.fecha.isin(ses)]
mapa = pd.read_parquet(MAPA)[['instrumento', 'empresa']]
p = p[p.instrumento.isin(mapa.instrumento)]
p.to_parquet(OUT / 'm2_panel_diario.parquet', index=False)

# ---- principal series
s = mapa.copy()
s['importe_acumulado'] = s.instrumento.map(p[p.turnover > 0].groupby('instrumento').turnover.sum()).fillna(0)
s = s.sort_values(['empresa', 'importe_acumulado', 'instrumento'], ascending=[True, False, True])
s['es_principal'] = ~s.duplicated('empresa')
s.to_parquet(OUT / 'm2_series.parquet', index=False)

# ---- vigencia
pos = pd.Series(np.arange(len(ses)), index=ses)
filas = []
for ins, x in p[p.turnover > 0].groupby('instrumento'):
    d0, d1 = x.fecha.min(), x.fecha.max()
    rng = ses[(ses >= d0) & (ses <= d1)]
    opero = rng.isin(x.fecha)
    ult = pd.Series(pd.DatetimeIndex(np.where(opero, rng, pd.NaT)), index=rng).ffill()
    vig = (pd.DatetimeIndex(ult.shift().values) + pd.DateOffset(months=12)) >= rng
    vig = np.where(opero, True, vig)
    filas.append(pd.DataFrame({'instrumento': ins, 'fecha': rng, 'opero': opero, 'vigente': vig}))
pd.concat(filas, ignore_index=True).to_parquet(OUT / 'm2_vigencia.parquet', index=False)

# ---- company market cap: maximum across classes, pesos
c = p[['fecha', 'instrumento', 'cur_mkt_cap']].dropna().merge(mapa, on='instrumento')
cap = c.groupby(['empresa', 'fecha']).cur_mkt_cap.max().mul(1e6).rename('capitalizacion').reset_index()
cap.to_parquet(OUT / 'm2_capitalizacion.parquet', index=False)

# ---- fixed terciles
t = np.log(cap.capitalizacion[cap.capitalizacion > 0]).groupby(cap.empresa).mean().rename('ln_mc_promedio').reset_index()
t['tercil'] = pd.qcut(t.ln_mc_promedio, 3, labels=['menor', 'intermedia', 'mayor'])
t.to_parquet(OUT / 'm2_terciles.parquet', index=False)
print('ok', len(ses), 'sesiones;', p.instrumento.nunique(), 'series;', s.empresa.nunique(), 'empresas')
