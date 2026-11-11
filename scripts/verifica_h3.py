"""Re-estimate the H3 tables of the thesis (4.11, 4.13, 4.15-4.17) from m7_panel_mensual.parquet.

Usage: python scripts/verifica_h3.py <folder with m7_panel_mensual.parquet>

Within (firm fixed effects) estimator with a linear trend, Driscoll-Kraay standard
errors (Bartlett kernel, bandwidth floor(4 (T/100)^(2/9))), written from scratch so
no extra package is needed.
"""
import sys
import numpy as np, pandas as pd
from scipy import stats

D = sys.argv[1].rstrip('/') + '/'
d = pd.read_parquet(D + 'm7_panel_mensual.parquet')
CTRL = ['rend_mercado', 'vol_sistematica', 'tasa', 'tipo_cambio', 'vix', 'vol_idiosincratica']
DEP = {'spread': 'Diferencial', 'ln_illiq': 'ln ILLIQ', 'zret': 'Rend. cero', 'rotacion': 'Rotación'}


def within(df, cols):
    return df[cols] - df.groupby('empresa')[cols].transform('mean')


def fit(df, y, X, dk=True):
    df = df.dropna(subset=[y] + X).copy()
    W = within(df, [y] + X)
    Y = W[y].values; M = W[X].values
    b, *_ = np.linalg.lstsq(M, Y, rcond=None)
    e = Y - M @ b
    n, k = M.shape; G = df.empresa.nunique()
    XtXi = np.linalg.inv(M.T @ M)
    s2 = (e @ e) / (n - k - G)
    se_conv = np.sqrt(np.diag(XtXi) * s2)
    # Driscoll-Kraay
    per = df.periodo.values
    h = pd.DataFrame(M * e[:, None]).groupby(per).sum().sort_index().values
    T = h.shape[0]; L = int(np.floor(4 * (T / 100) ** (2 / 9)))
    S = h.T @ h
    for l in range(1, L + 1):
        w = 1 - l / (L + 1); G_ = h[l:].T @ h[:-l]; S += w * (G_ + G_.T)
    V = XtXi @ S @ XtXi
    se_dk = np.sqrt(np.diag(V))
    r2w = 1 - (e @ e) / (Y @ Y)
    return dict(b=b, se_conv=se_conv, se_dk=se_dk, n=n, firms=G, T=T, r2w=r2w, X=X)


def row(r, var='psic10'):
    j = r['X'].index(var); t = r['b'][j] / r['se_dk'][j]
    return r['b'][j], r['se_conv'][j], r['se_dk'][j], 2 * (1 - stats.norm.cdf(abs(t)))


print('== Tabla 4.11 (contemporánea): coef, EE conv, EE DK, p, n, empresas')
base = ['psic10'] + CTRL + ['t']
for y, nom in DEP.items():
    r = fit(d, y, base); b, sc, sd, p = row(r)
    print(f'  {nom:12s} {b:+.4f}  {sc:.4f}  {sd:.4f}  p={p:.3f}  n={r["n"]:,}  empresas={r["firms"]}  T={r["T"]}')

print('\n== Tabla 4.13: incremento del R2 intragrupo (misma muestra)')
for y, nom in DEP.items():
    s = d.dropna(subset=[y, 'psic10', 't'] + CTRL)
    r0 = fit(s, y, ['t'])['r2w']; rc = fit(s, y, ['t'] + CTRL)['r2w']
    rp = fit(s, y, ['t', 'psic10'])['r2w']; rall = fit(s, y, ['t'] + CTRL + ['psic10'])['r2w']
    ctrl1, psic2 = rc - r0, rall - rc          # controls first, then psic
    psic1, ctrl2 = rp - r0, rall - rp          # psic first, then controls
    print(f'  {nom:12s} controles {100*ctrl1:.2f}%  psic {100*psic2:.3f}%  razón {ctrl1/psic2:,.0f}  '
          f'| orden inverso: psic {100*psic1:.3f}%  controles {100*ctrl2:.2f}%  dif.orden(psic) {100*(psic1-psic2):+.3f}%')

print('\n== Tabla 4.15: submuestras (coef, p DK)')
pre = d[d.periodo < '2018-07-01']; nopan = d[~d.anio.isin([2020, 2021])]
for y, nom in DEP.items():
    out = []
    for s in (d, pre, nopan):
        r = fit(s, y, base); b, _, _, p = row(r); out.append(f'{b:+.4f} p={p:.3f} (T={r["T"]})')
    print(f'  {nom:12s} ' + ' | '.join(out))

print('\n== Tabla 4.16: primeras diferencias (solo mes inmediato anterior)')
f = d.sort_values(['empresa', 'periodo']).copy()
gap = f.groupby('empresa').periodo.diff().dt.days.between(27, 32)
for c in list(DEP) + ['psic10'] + CTRL:
    f['d_' + c] = f.groupby('empresa')[c].diff().where(gap)
for y, nom in DEP.items():
    s = f.dropna(subset=['d_' + y, 'd_psic10'] + ['d_' + c for c in CTRL]).copy()
    # pooled OLS in differences with constant, DK errors (no fixed effects after differencing)
    X = np.column_stack([np.ones(len(s))] + [s['d_' + c].values for c in ['psic10'] + CTRL])
    Y = s['d_' + y].values; b, *_ = np.linalg.lstsq(X, Y, rcond=None); e = Y - X @ b
    XtXi = np.linalg.inv(X.T @ X)
    h = pd.DataFrame(X * e[:, None]).groupby(s.periodo.values).sum().sort_index().values
    T = h.shape[0]; L = int(np.floor(4 * (T / 100) ** (2 / 9))); S = h.T @ h
    for l in range(1, L + 1):
        w = 1 - l / (L + 1); G_ = h[l:].T @ h[:-l]; S += w * (G_ + G_.T)
    se = np.sqrt(np.diag(XtXi @ S @ XtXi)); p = 2 * (1 - stats.norm.cdf(abs(b[1] / se[1])))
    print(f'  {nom:12s} {b[1]:+.4f}  p={p:.3f}  T={T}')

print('\n== Tabla 4.17: controles rezagados un mes')
lag = ['psic10'] + [c + '_r1' for c in CTRL] + ['t']
for y, nom in DEP.items():
    r = fit(d, y, lag); b, _, _, p = row(r)
    print(f'  {nom:12s} {b:+.4f}  p={p:.3f}')

print('\n== Participación rezagada (prometida en 3.4.3, no reportada)')
for v in ['psic10_r1', 'psic10_r3']:
    X = [v] + CTRL + ['t']
    print('  ' + v + ': ' + ' | '.join(f'{nom} {row(fit(d, y, X), v)[0]:+.4f} p={row(fit(d, y, X), v)[3]:.3f}'
                                    for y, nom in DEP.items()))

print('\n== Por tercil (prometido en 3.4.3, no reportado)')
for g in ['menor', 'intermedia', 'mayor']:
    s = d[d.tercil.astype(str) == g]
    print(f'  {g:10s} ' + ' | '.join(f'{nom} {row(fit(s, y, base))[0]:+.4f} p={row(fit(s, y, base))[3]:.3f}'
                                     for y, nom in DEP.items()))
