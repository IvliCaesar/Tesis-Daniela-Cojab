"""Módulo 3 (reconstruido): medidas de liquidez por empresa y periodo.

Uso: python pipeline/m3_medidas.py <carpeta con m2_*.parquet y calendario.parquet> <carpeta de salida>

Reglas (apartados 3.2.3, 3.2.4 y 3.3.2 de la tesis, contrastadas con las salidas de la autora):
  * serie principal de cada empresa (m2_series.es_principal) para las medidas de precio;
  * sesión operada: importe (BMV + BIVA) positivo; vigencia según m2_vigencia;
  * rendimiento con el índice de rendimiento total contra la sesión previa del calendario;
    un |R| > 50% invalida los dos valores del índice que lo producen y se recalcula;
  * diferencial: sesiones operadas con posturas positivas y no cruzadas;
  * Amihud: |R| / importe en millones, recorte de los percentiles 1 y 99 de la
    distribución diaria conjunta; logaritmo indefinido si vale cero;
  * mínimo de 10 sesiones operadas al mes y 50 al año para diferencial y Amihud;
  * rendimientos cero = (vigentes sin operar + operadas con R = 0) / (vigentes - sin medir),
    ecuación 8; la columna sesiones_vigentes de la autora ya viene neta de las sesiones sin medir;
  * importe de todas las series de la empresa; capitalización promedio diaria de la empresa.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

IN, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
cal = pd.read_parquet(IN / 'calendario.parquet')
ses = pd.DatetimeIndex(sorted(cal.loc[cal.sesion, 'fecha']))
pos = pd.Series(np.arange(len(ses)), index=ses)

series = pd.read_parquet(IN / 'm2_series.parquet')
emp = series.set_index('instrumento').empresa
prin = series[series.es_principal].set_index('instrumento').empresa
p = pd.read_parquet(IN / 'm2_panel_diario.parquet')
p = p[p.fecha.isin(ses)]
vig = pd.read_parquet(IN / 'm2_vigencia.parquet')
p = p.merge(vig[['instrumento', 'fecha', 'vigente']], on=['instrumento', 'fecha'], how='left')
p['vigente'] = p.vigente.astype('boolean').fillna(False).astype(bool)
p['empresa'] = p.instrumento.map(emp)
p['op'] = p.turnover > 0

# --- returns on the principal series
q = p[p.instrumento.isin(prin.index)].sort_values(['instrumento', 'fecha']).copy()
q['s'] = q.fecha.map(pos)


def returns(df, tri):
    prev_tri = df.groupby('instrumento')[tri].shift()
    prev_s = df.groupby('instrumento').s.shift()
    return np.where((df.s - prev_s == 1) & (prev_tri > 0), df[tri] / prev_tri - 1, np.nan)


q['tri'] = q.tot_return_index_gross_dvds
q['R'] = returns(q, 'tri')
bad = np.abs(q.R) > 0.5
prev_bad = bad.groupby(q.instrumento).shift(-1, fill_value=False)
q.loc[bad | prev_bad, 'tri'] = np.nan
q['R'] = returns(q, 'tri')

q['spread_d'] = np.where(q.op & (q.px_bid > 0) & (q.px_ask > q.px_bid),
                         (q.px_ask - q.px_bid) / ((q.px_ask + q.px_bid) / 2), np.nan)
q['illiq_d'] = np.where(q.op & q.R.notna(), q.R.abs() / (q.turnover / 1e6), np.nan)
lo, hi = np.nanpercentile(q.illiq_d, [1, 99])
q['illiq_t'] = q.illiq_d.where((q.illiq_d >= lo) & (q.illiq_d <= hi))
q['cero'] = q.vigente & ((~q.op) | (q.op & (q.R == 0)))
q['sin_medir'] = q.vigente & q.op & q.R.isna()

q[['empresa', 'instrumento', 'fecha', 'R', 'vigente', 'op']].to_parquet(OUT / 'm3_rendimientos.parquet', index=False)
cap = pd.read_parquet(IN / 'm2_capitalizacion.parquet')


def agrega(freq, dmin, name):
    per = q.fecha.dt.to_period(freq).dt.start_time
    v = q[q.vigente].assign(periodo=per[q.vigente])
    g = v.groupby(['empresa', 'periodo'])
    a = pd.DataFrame({
        'sesiones_operadas': g.op.sum(), 'spread': g.spread_d.mean(), 'n_spread': g.spread_d.count(),
        'illiq': g.illiq_t.mean(), 'n_illiq': g.illiq_t.count(), 'illiq_sin_recorte': g.illiq_d.mean(),
        'sesiones_vigentes': g.size() - g.sin_medir.sum(), 'ceros': g.cero.sum(),
        'sesiones_sin_medir': g.sin_medir.sum()})
    a.loc[a.sesiones_operadas == 0, ['sesiones_operadas', 'n_spread', 'n_illiq']] = np.nan
    a['cumple_minimo'] = a.sesiones_operadas >= dmin
    for c in ['spread', 'illiq', 'illiq_sin_recorte']:
        a.loc[~a.cumple_minimo, c] = np.nan
    a['illiq_cero'] = a.illiq == 0
    a['ln_illiq'] = np.log(a.illiq.where(a.illiq > 0))
    a['ln_illiq_sin_recorte'] = np.log(a.illiq_sin_recorte.where(a.illiq_sin_recorte > 0))
    a['zret'] = a.ceros / a.sesiones_vigentes
    allp = p[p.vigente & p.op].assign(periodo=p.fecha.dt.to_period(freq).dt.start_time)
    a['importe'] = allp.groupby(['empresa', 'periodo']).turnover.sum()
    c2 = cap.assign(periodo=cap.fecha.dt.to_period(freq).dt.start_time)
    a['cap_promedio'] = c2.groupby(['empresa', 'periodo']).capitalizacion.mean()
    a = a.reset_index()
    a.to_parquet(OUT / f'm3_liquidez_{name}.parquet', index=False)
    return a


agrega('M', 10, 'mensual'); agrega('Y', 50, 'anual')
print('ok')
