"""Módulo 7 (reconstruido): panel mensual de H3.

Uso: python pipeline/m7_panel.py <carpeta de la autora> <carpeta con m3/m4 reconstruidos> <libro de índices>

Une las medidas mensuales (m3), la participación (m4), los terciles (m2) y los factores
comunes. Reglas deducidas de m7_panel_mensual.parquet de la autora:
  * factores mensuales: promedio sobre todos los días hábiles del calendario, con el
    último valor arrastrado en días sin dato (tasa = TIIE 28, tipo de cambio, VIX);
  * rendimiento del mercado: rendimiento compuesto del IPC en el mes;
    volatilidad sistemática: desviación estándar de sus rendimientos diarios;
  * volatilidad idiosincrática: desviación estándar (ddof = 2) de los residuos del modelo de
    mercado con los rendimientos diarios de la serie principal en todas las sesiones vigentes
    con rendimiento medible, mínimo 10 por mes. Desde 2019 eso incluye sesiones sin
    operación con índice arrastrado (rendimiento cero): efecto del cambio del proveedor;
  * rotación = importe / capitalización promedio (y variantes al cierre y de la serie principal);
  * psic10 = participación / 10, rezagos de 1 y 3 meses; t = 1..273; controles rezagados _r1.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

A, B, LIB = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
cal = pd.read_parquet(A / 'calendario.parquet')
allc = pd.DatetimeIndex(cal.fecha); ses = pd.DatetimeIndex(cal.loc[cal.sesion, 'fecha'])
x = pd.read_excel(LIB, sheet_name='Indices', header=None)
ser = {}
for j in range(0, x.shape[1] - 1, 3):
    n = str(x.iloc[0, j + 1]).strip()
    s = pd.Series(pd.to_numeric(x.iloc[6:, j + 1], errors='coerce').values,
                  index=pd.to_datetime(x.iloc[6:, j], errors='coerce')).dropna()
    s = s[s.index.notna()].sort_index(); ser[n] = s[~s.index.duplicated()]
M = lambda i: i.to_period('M').to_timestamp()


def media_cal(s):
    a = s.reindex(allc.union(s.index)).ffill().reindex(allc)
    return a.groupby(M(a.index)).mean()


mx = ser['MEXBOL Index'].reindex(ses.union(ser['MEXBOL Index'].index)).ffill().reindex(ses)
rm = mx.pct_change()
F = pd.DataFrame({'rend_mercado': (1 + rm).groupby(M(rm.index)).prod() - 1,
                  'vol_sistematica': rm.groupby(M(rm.index)).std(),
                  'tasa': media_cal(ser['MXIBTIIE Index']),
                  'tipo_cambio': media_cal(ser['MXN BGN Curncy']),
                  'vix': media_cal(ser['VIX Index'])})

m3 = pd.read_parquet(B / 'm3_liquidez_mensual.parquet')
m4 = pd.read_parquet(B / 'm4_psic_mensual.parquet')[['periodo', 'psic']]
te = pd.read_parquet(A / 'm2_terciles.parquet')

# idiosyncratic volatility: market-model residuals of the principal series, all sessions
# vigentes with a measurable return (module 3), at least 10 per month, ddof = 2
p = pd.read_parquet(B / 'm3_rendimientos.parquet')
p = p[p.vigente & p.R.notna()].copy()
p['rm'] = p.fecha.map(rm)
p = p.dropna(subset=['rm'])
p['periodo'] = M(pd.DatetimeIndex(p.fecha))


def idio(g):
    if len(g) < 10:
        return np.nan
    X = np.column_stack([np.ones(len(g)), g.rm.values]); b, *_ = np.linalg.lstsq(X, g.R.values, rcond=None)
    return np.std(g.R.values - X @ b, ddof=2)


vi = p.groupby(['empresa', 'periodo']).apply(idio, include_groups=False).rename('vol_idiosincratica').reset_index()

d = (m3.merge(te, on='empresa', how='left').merge(m4, on='periodo', how='left')
       .merge(F, left_on='periodo', right_index=True, how='left').merge(vi, on=['empresa', 'periodo'], how='left'))
d['rotacion'] = d.importe / d.cap_promedio
d['anio'] = d.periodo.dt.year
d['psic10'] = d.psic / 10
per = sorted(m4.periodo); tmap = {q: i + 1 for i, q in enumerate(per)}
d['t'] = d.periodo.map(tmap)
ps = m4.set_index('periodo').psic / 10
d['psic10_r1'] = d.periodo.map(ps.shift(1)); d['psic10_r3'] = d.periodo.map(ps.shift(3))
for c in ['rend_mercado', 'vol_sistematica', 'tasa', 'tipo_cambio', 'vix']:
    d[c + '_r1'] = d.periodo.map(F[c].shift(1))
d = d.sort_values(['empresa', 'periodo'])
prev = d.groupby('empresa').periodo.shift()
d['vol_idiosincratica_r1'] = d.groupby('empresa').vol_idiosincratica.shift().where(
    (d.periodo - prev).dt.days.between(27, 32))
d.to_parquet(B / 'm7_panel_mensual.parquet', index=False)
print('ok', d.shape)
