"""Corrected analyses for the lecture notes (notas-de-clase/).

Usage: python scripts/notas_analisis.py <folder with the author's outputs> <output folder>

Reads the module outputs (m3_*, m4_* parquets), PIBA_2.csv and the market-series
workbook "indices, macroeconomicos y AMIB DD.xlsx". Writes the figures and
resultados.tex (LaTeX macros with every number quoted in the notes), so the text
never carries a number typed by hand.
"""
import itertools, math, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
warnings.filterwarnings('ignore')

D = Path(sys.argv[1]); OUT = Path(sys.argv[2]); (OUT / 'figuras').mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261109)
MAC = {}
def mac(name, value, fmt='{:.2f}'):
    MAC[name] = fmt.format(value) if not isinstance(value, str) else value

BLUE, ORANGE, GRAY, INK = '#2a78d6', '#eb6834', '#8a8a8a', '#1b1b1b'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#e3e3e3',
                     'grid.linewidth': .6, 'axes.edgecolor': '#bbbbbb', 'savefig.dpi': 200})

def year(s):
    return s if np.issubdtype(s.dtype, np.integer) else pd.to_datetime(s).dt.year

# ------------------------------------------------------------------ data
pa = pd.read_parquet(D / 'm4_psic_anual_real.parquet'); pa['periodo'] = year(pa.periodo); pa = pa.set_index('periodo')
pm = pd.read_parquet(D / 'm4_psic_mensual.parquet'); pm['periodo'] = pd.to_datetime(pm.periodo).dt.to_period('M'); pm = pm.set_index('periodo')
pib = pd.read_csv(D / 'PIBA_2.csv', encoding='utf-8-sig', index_col=0).iloc[0]
pib.index = [int(str(c)[:4]) for c in pib.index]; pib = pib.astype(float)
inpc_a = pa.inpc / pa.inpc[2018]

x = pd.read_excel(D / 'indices, macroeconomicos y AMIB DD.xlsx', sheet_name='Indices', header=None)
ser = {}
for j in range(0, x.shape[1] - 1, 3):
    name = str(x.iloc[0, j + 1]).strip()
    d = pd.to_datetime(x.iloc[6:, j], errors='coerce'); v = pd.to_numeric(x.iloc[6:, j + 1], errors='coerce')
    s = pd.Series(v.values, index=d.values).dropna(); s = s[s.index.notna()].sort_index()
    ser[name] = s[~s.index.duplicated()]
mx = ser['MEXBOL Index']; r = mx.pct_change().dropna()
k = r.index.to_period('M')
F = pd.DataFrame({'rmkt': r.groupby(k).sum(), 'volmkt': r.groupby(k).std(),
                  'vix': ser['VIX Index'].groupby(ser['VIX Index'].index.to_period('M')).mean(),
                  'cete': ser['GCETAA28 Index'].groupby(ser['GCETAA28 Index'].index.to_period('M')).mean(),
                  'lnfx': np.log(ser['MXN BGN Curncy']).groupby(ser['MXN BGN Curncy'].index.to_period('M')).mean()})
inpc_m = ser['MXCPI Index'].groupby(ser['MXCPI Index'].index.to_period('M')).last()

lm = pd.read_parquet(D / 'm3_liquidez_mensual.parquet'); lm['periodo'] = pd.to_datetime(lm.periodo).dt.to_period('M')
lm['turn'] = lm.importe / lm.cap_promedio
lm['ln_illiq_real'] = lm.ln_illiq + np.log(lm.periodo.map(inpc_m / inpc_m[pd.Period('2018-07', 'M')]).astype(float))
la = pd.read_parquet(D / 'm3_liquidez_anual.parquet'); la['periodo'] = year(la.periodo)
la['turn'] = la.importe / la.cap_promedio
la['ln_illiq_real'] = la.ln_illiq + np.log(la.periodo.map(inpc_a))

# ------------------------------------------------------------------ 1. trend of the share
p = pm.psic / 100; t = np.arange(len(p))
r1 = sm.OLS(100 * p.values, sm.add_constant(t)).fit(cov_type='HAC', cov_kwds={'maxlags': 5})
mac('tHAC', r1.tvalues[1]); mac('pendHAC', 12 * r1.params[1])
lg = np.log(p / (1 - p))
mac('adfLogit', adfuller(lg.values, autolag='AIC')[1], '{:.3f}')
mac('kpssLogit', kpss(lg.values, regression='ct', nlags='auto')[1], '{:.3f}')
dl = lg.diff().dropna()
L = int(np.floor(4 * (len(dl) / 100) ** (2 / 9)))
rd = sm.OLS(dl.values, np.ones(len(dl))).fit(cov_type='HAC', cov_kwds={'maxlags': L})
mac('derivaAnual', 12 * rd.params[0], '{:.3f}'); mac('tDeriva', rd.tvalues[0]); mac('pDeriva', rd.pvalues[0], '{:.3f}')
mac('lagNW', L, '{:d}')
# drift by sub-period
for nm, a, b in [('A', '2004-01', '2013-12'), ('B', '2014-01', '2018-12'), ('C', '2019-01', '2026-09')]:
    z = dl.loc[a:b]; rz = sm.OLS(z.values, np.ones(len(z))).fit(cov_type='HAC', cov_kwds={'maxlags': L})
    mac('deriva' + nm, 12 * rz.params[0], '{:.3f}'); mac('pDeriva' + nm, rz.pvalues[0], '{:.3f}')
# spurious-trend demonstration: random walks of the same length
tt = []
for _ in range(2000):
    w = np.cumsum(rng.standard_normal(len(p)))
    tt.append(abs(sm.OLS(w, sm.add_constant(t)).fit(cov_type='HAC', cov_kwds={'maxlags': 5}).tvalues[1]))
tt = np.array(tt)
mac('rwRechazo', 100 * (tt > 1.96).mean(), '{:.0f}'); mac('rwMediana', np.median(tt), '{:.1f}')

fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.1))
ax[0].plot(p.index.to_timestamp(), 100 * p, color=BLUE, lw=1.4)
ax[0].set_title('Participación del SIC, %', loc='left', fontsize=9)
for (d_, lab), y_ in zip([('2014-01-10', 'apertura 2014'), ('2018-07-25', 'BIVA'),
                          ('2020-06-15', 'reglas SIC 2020')], [50, 2, 12]):
    ax[0].axvline(pd.Timestamp(d_), color=ORANGE, lw=.9, ls='--')
    ax[0].text(pd.Timestamp(d_), y_, ' ' + lab, fontsize=7, color=ORANGE, va='bottom',
               ha='right' if lab.startswith('apertura') else 'left')
ax[1].hist(tt, bins=40, color=GRAY); ax[1].axvline(1.96, color=ORANGE, lw=1.4)
ax[1].set_title('|t| de la tendencia en caminatas aleatorias (HAC, 5 rezagos)', loc='left', fontsize=9)
fig.tight_layout(); fig.savefig(OUT / 'figuras' / 'f1_tendencia.png'); plt.close(fig)

# ------------------------------------------------------------------ 2. growth
cagr = lambda s, a, b: 100 * ((s[b] / s[a]) ** (1 / (b - a)) - 1)
def slope(s, a, b):
    y = np.log(s.loc[a:b].astype(float)); return 100 * (np.exp(np.polyfit(np.arange(len(y)), y.values, 1)[0]) - 1)
rows = []
for a, b in [(2004, 2025), (2006, 2025), (2013, 2025), (2004, 2013), (2014, 2018), (2019, 2025)]:
    bp = min(b, 2024)
    rows.append((f'{a}--{b}', cagr(pa.sic_real, a, b), slope(pa.sic_real, a, b), cagr(pa.loc_real, a, b),
                 slope(pa.loc_real, a, b), cagr(pib, a, bp), slope(pib, a, bp)))
with open(OUT / 'tabla_crecimiento.tex', 'w', encoding='utf8') as f:
    for rw in rows:
        f.write(rw[0] + ' & ' + ' & '.join(f'{v:.2f}' for v in rw[1:]) + r' \\' + '\n')
ratio = (pa.loc_real / pib.reindex(pa.index)); ratio = 100 * ratio / ratio[2004]
mac('ratioDosMilTrece', ratio[2013], '{:.0f}'); mac('ratioDosMilVeinticuatro', ratio[2024], '{:.0f}')
fig, ax = plt.subplots(figsize=(9.2, 2.9))
ax.plot(ratio.index, ratio.values, color=BLUE, lw=1.8, marker='o', ms=3)
ax.set_title('Importe operado real del segmento local entre PIB real (2004 = 100)', loc='left', fontsize=9)
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
fig.tight_layout(); fig.savefig(OUT / 'figuras' / 'f2_local_pib.png'); plt.close(fig)

# AMIB counting convention (values from the BMV annual reports and the AMIB bulletins)
mac('amibDosMilCuatro', 100 * 12665 / (1103391 + 12665)); mac('amibCorregido', 100 * 2 * 12665 / (1103391 + 2 * 12665))
mac('bbgDosMilCuatro', pa.psic[2004])

# ------------------------------------------------------------------ 3. measures
med = la.groupby('periodo')[['ln_illiq', 'ln_illiq_real', 'zret', 'spread', 'turn']].median()
mean_z = la.groupby('periodo').zret.mean()
mac('illNomA', med.ln_illiq[2014] - med.ln_illiq[2004]); mac('illRealA', med.ln_illiq_real[2014] - med.ln_illiq_real[2004])
mac('illNomB', med.ln_illiq[2025] - med.ln_illiq[2014]); mac('illRealB', med.ln_illiq_real[2025] - med.ln_illiq_real[2014])
mac('zMedA', 100 * med.zret[2004], '{:.1f}'); mac('zMedB', 100 * med.zret[2018], '{:.1f}'); mac('zMedC', 100 * med.zret[2026], '{:.1f}')
mac('zMeanA', 100 * mean_z[2004], '{:.1f}'); mac('zMeanB', 100 * mean_z[2018], '{:.1f}'); mac('zMeanC', 100 * mean_z[2026], '{:.1f}')
fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.1))
ax[0].plot(med.index, med.ln_illiq, color=GRAY, lw=1.6, label='nominal')
ax[0].plot(med.index, med.ln_illiq_real, color=BLUE, lw=1.8, label='pesos de 2018')
ax[0].set_title('Mediana de ln ILLIQ', loc='left', fontsize=9); ax[0].legend(frameon=False)
ax[1].plot(med.index, 100 * med.zret, color=GRAY, lw=1.6, label='mediana')
ax[1].plot(mean_z.index, 100 * mean_z, color=BLUE, lw=1.8, label='media')
ax[1].set_title('Rendimientos cero, % de sesiones vigentes', loc='left', fontsize=9); ax[1].legend(frameon=False)
for a_ in ax: a_.xaxis.set_major_locator(MaxNLocator(integer=True))
fig.tight_layout(); fig.savefig(OUT / 'figuras' / 'f3_medidas.png'); plt.close(fig)
# distribution of ZRET: bimodality
fig, ax = plt.subplots(figsize=(9.2, 2.6))
for y, c in [(2006, GRAY), (2018, BLUE), (2024, ORANGE)]:
    ax.hist(100 * la[la.periodo == y].zret, bins=20, range=(0, 100), histtype='step', lw=1.6, color=c, label=str(y))
ax.set_title('Distribución de ZRET entre emisoras', loc='left', fontsize=9); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / 'figuras' / 'f4_zret_bimodal.png'); plt.close(fig)

# ------------------------------------------------------------------ 4. H3 redone: time-series decomposition
need = 30
agg = lm.groupby('periodo').agg(n=('spread', 'count'))
cs = pd.DataFrame({c: lm.groupby('periodo')[c].median() for c in ['spread', 'ln_illiq_real', 'zret', 'turn']})
cs = cs[agg.n >= need]
Z = pd.concat([cs, (pm.psic / 10).rename('psic'), F], axis=1).dropna()
dZ = Z.diff().dropna()
REG = ['psic', 'rmkt', 'volmkt', 'vix', 'cete', 'lnfx']
NOM = {'psic': 'Participación SIC', 'rmkt': 'Rendimiento IPC', 'volmkt': 'Volatilidad IPC',
       'vix': 'VIX', 'cete': 'Cetes 28', 'lnfx': 'ln tipo de cambio'}
DEP = {'spread': 'Diferencial', 'ln_illiq_real': 'ln ILLIQ real', 'zret': 'Rend. cero', 'turn': 'Rotación'}

def shapley(df, dep):
    """Shapley-Owen decomposition of R2: all 2^m subsets fitted once."""
    y = df[dep].values; y = y - y.mean(); sst = (y ** 2).sum(); m = len(REG)
    X = df[REG].values; X = X - X.mean(axis=0)
    R2 = {}
    for kk in range(m + 1):
        for S in itertools.combinations(range(m), kk):
            if not S: R2[S] = 0.0; continue
            b, *_ = np.linalg.lstsq(X[:, S], y, rcond=None)
            e = y - X[:, S] @ b; R2[S] = 1 - (e ** 2).sum() / sst
    out = {}
    for v in range(m):
        s = 0.0; others = [u for u in range(m) if u != v]
        for kk in range(m):
            w = math.factorial(kk) * math.factorial(m - kk - 1) / math.factorial(m)
            for S in itertools.combinations(others, kk):
                s += w * (R2[tuple(sorted(S + (v,)))] - R2[S])
        out[REG[v]] = s
    return pd.Series(out)

def block_boot(df, B=300, blk=12):
    n = len(df); idx = np.arange(n); res = []
    for _ in range(B):
        starts = rng.integers(0, n - blk, size=n // blk + 1)
        ii = np.concatenate([idx[s:s + blk] for s in starts])[:n]
        res.append(ii)
    return res

rows, shp_all, coef = [], {}, {}
boots = block_boot(dZ)
for dep in DEP:
    sh = shapley(dZ, dep); shp_all[dep] = sh
    tot = sh.sum()
    fit = sm.OLS(dZ[dep].values, sm.add_constant(dZ[REG].values)).fit(cov_type='HAC', cov_kwds={'maxlags': L})
    coef[dep] = (fit.params[1], fit.pvalues[1])
    # bootstrap: share of psic, and psic minus the largest control
    bs, bd = [], []
    for ii in boots:
        s2 = shapley(dZ.iloc[ii].reset_index(drop=True), dep)
        bs.append(s2['psic']); bd.append(s2['psic'] - s2.drop('psic').max())
    lo, hi = np.percentile(bs, [2.5, 97.5]); dlo, dhi = np.percentile(bd, [2.5, 97.5])
    rank = int((sh.sort_values(ascending=False).index == 'psic').argmax()) + 1
    rows.append((DEP[dep], 100 * tot, 100 * sh['psic'], 100 * lo, 100 * hi, rank, 100 * dlo, 100 * dhi,
                 fit.params[1], fit.pvalues[1]))
    # levels, same regressors: the misleading version
    lv = sm.OLS(Z[dep].values, sm.add_constant(Z[REG].values)).fit()
    MAC['lvR' + 'ABCD'[len(rows) - 1]] = f'{100 * lv.rsquared:.1f}'
with open(OUT / 'tabla_h3.tex', 'w', encoding='utf8') as f:
    for rw in rows:
        f.write(f'{rw[0]} & {rw[1]:.1f} & {rw[2]:.2f} & [{rw[3]:.2f}, {rw[4]:.2f}] & {rw[5]} de 6 & '
                f'[{rw[6]:.2f}, {rw[7]:.2f}] & {rw[8]:+.4f} & {rw[9]:.3f} \\\\\n')
mac('nMeses', len(dZ), '{:d}'); mac('nMin', need, '{:d}')
mac('mesIni', str(dZ.index.min())); mac('mesFin', str(dZ.index.max()))
fig, axs = plt.subplots(1, 4, figsize=(10, 2.9), sharey=True)
for ax, dep in zip(axs, DEP):
    sh = 100 * shp_all[dep].reindex(REG)
    ax.barh([NOM[v] for v in REG][::-1], sh.values[::-1],
            color=[ORANGE if v == 'psic' else BLUE for v in REG][::-1])
    ax.set_title(DEP[dep], loc='left', fontsize=9); ax.set_xlabel('% de R²')
fig.tight_layout(); fig.savefig(OUT / 'figuras' / 'f5_shapley.png'); plt.close(fig)

# ------------------------------------------------------------------ 5. size test, right window
te = pd.read_parquet(D / 'm2_terciles.parquet').set_index('empresa').tercil.astype(str)
la['tramo'] = pd.cut(la.periodo, [2003, 2013, 2018, 2025], labels=['T1', 'T2', 'T3'])
def holm(ps):
    ps = np.asarray(ps, float); o = np.argsort(ps); n = len(ps); adj = np.empty(n); run = 0
    for rr, i in enumerate(o):
        run = max(run, (n - rr) * ps[i]); adj[i] = min(run, 1.0)
    return adj
out = []
for A, B in [('T1', 'T3'), ('T2', 'T3')]:
    res = []
    for c in ['spread', 'ln_illiq_real', 'zret', 'turn']:
        E = la.pivot_table(index='empresa', columns='tramo', values=c, aggfunc='median', observed=True)
        d = E[[A, B]].dropna().copy(); d['g'] = te.reindex(d.index).values; d['ch'] = d[B] - d[A]
        for g in ['menor', 'intermedia']:
            u = stats.mannwhitneyu(d[d.g == g].ch, d[d.g == 'mayor'].ch, alternative='two-sided')
            res.append([A + B, DEP[c], g, (d.g == g).sum(), (d.g == 'mayor').sum(),
                        d[d.g == g].ch.median(), d[d.g == 'mayor'].ch.median(), u.pvalue])
    ph = holm([r_[-1] for r_ in res])
    for r_, q in zip(res, ph): out.append(r_ + [q])
with open(OUT / 'tabla_tamano.tex', 'w', encoding='utf8') as f:
    for r_ in out:
        if r_[0] != 'T2T3': continue
        sc = 1 if 'ILLIQ' in r_[1] else 100
        f.write(f'{r_[1]} & {r_[2]} & {r_[3]} / {r_[4]} & {sc*r_[5]:+.2f} & {sc*r_[6]:+.2f} & {r_[8]:.3f} \\\\\n')
t13 = [r_ for r_ in out if r_[0] == 'T1T3' and r_[1] == 'Rotación' and r_[2] == 'menor'][0]
mac('rotTunoTres', t13[8], '{:.3f}')

# ------------------------------------------------------------------ 6. numbers quoted in the text
# sum of venues vs consolidated
mac('difDosMilDieciocho', pa.diferencia_pp[2018]); mac('difDosMilDiecinueve', pa.diferencia_pp[2019])
# AMIB (SIC, BMV only) over the BMV annual report (single count)
AMIB_SIC = {2004: 12665, 2005: 49670, 2006: 289976, 2007: 315433, 2008: 642180, 2009: 465784,
            2010: 779254, 2011: 1065309, 2012: 1026719, 2013: 1434515}
INF_SIC = {2004: 12665, 2005: 24835, 2006: 144985, 2007: 157717, 2008: 321090, 2009: 232892,
           2010: 389627, 2011: 532655, 2012: 513359, 2013: 717245}
rat = pd.Series({y: AMIB_SIC[y] / INF_SIC[y] for y in AMIB_SIC})
mac('razonAmibCuatro', rat[2004]); mac('razonAmibMin', rat.drop(2004).min()); mac('razonAmibMax', rat.drop(2004).max())
# local growth, first row of the table
mac('locExt', cagr(pa.loc_real, 2004, 2025)); mac('locPend', slope(pa.loc_real, 2004, 2025))
mac('pibExt', cagr(pib, 2004, 2024)); mac('razonMultiplo', ratio[2013] / 100, '{:.1f}')
# within-firm ZRET 2004 -> 2018
both = set(la[la.periodo == 2004].empresa) & set(la[la.periodo == 2018].empresa)
zz = la[la.empresa.isin(both)].pivot_table(index='empresa', columns='periodo', values='zret')
mac('nPermanecen', len(both), '{:d}'); mac('zPermA', zz[2004].median()); mac('zPermB', zz[2018].median())
mac('zMedTrece', 100 * med.zret[2013], '{:.1f}')
# sessions without measurable return, and zero returns on traded sessions
sm_ = la.groupby('periodo')[['sesiones_sin_medir', 'sesiones_operadas']].sum()
pct = 100 * sm_.sesiones_sin_medir / sm_.sesiones_operadas
mac('sinMedirMin', pct.loc[2014:2018].min(), '{:.0f}'); mac('sinMedirMax', pct.loc[2014:2018].max(), '{:.0f}')
mac('sinMedirPost', pct.loc[2020:2025].max(), '{:.2f}')
sp = pd.read_parquet(D / 'm2_series.parquet'); prin = sp[sp.es_principal][['instrumento', 'empresa']]
pdia = pd.read_parquet(D / 'm2_panel_diario.parquet', columns=['fecha', 'instrumento', 'turnover', 'tot_return_index_gross_dvds'])
vig = pd.read_parquet(D / 'm2_vigencia.parquet')
pdia = pdia.merge(prin, on='instrumento').merge(vig, on=['instrumento', 'fecha'], how='inner')
pdia = pdia[pdia.vigente].sort_values(['instrumento', 'fecha'])
pdia['op'] = pdia.turnover > 0
tri_op = pdia.tot_return_index_gross_dvds.where(pdia.op)
pdia['prev'] = tri_op.groupby(pdia.instrumento).shift().groupby(pdia.instrumento).ffill()
pdia['R'] = np.where(pdia.op, pdia.tot_return_index_gross_dvds / pdia.prev - 1, np.nan)
pdia['y'] = pdia.fecha.dt.year
opz = pdia[pdia.op & pdia.R.notna()].groupby('y').R.apply(lambda s: 100 * (s == 0).mean())
mac('ceroOpA', opz[2018], '{:.1f}'); mac('ceroOpB', opz[2019], '{:.0f}')
mac('ceroOpC', opz.loc[2022:2025].mean(), '{:.0f}')
g_ = pdia.groupby(['empresa', 'y'])
alt = pd.DataFrame({'vig': g_.op.size(), 'noop': g_.op.apply(lambda x: (~x).sum()),
                    'cero': g_.R.apply(lambda x: (x == 0).sum()),
                    'nm': pdia[pdia.op].groupby(['empresa', 'y']).R.apply(lambda x: x.isna().sum())}).fillna(0)
alt['zalt'] = (alt.noop + alt.cero) / (alt.vig - alt.nm)
mm_ = la.merge(alt.reset_index()[['empresa', 'y', 'zalt']], left_on=['empresa', 'periodo'], right_on=['empresa', 'y'])
mac('corrZalt', mm_[['zret', 'zalt']].corr().iloc[0, 1], '{:.3f}')
# ------------------------------------------------------------------ 7. the thesis panel (m7), re-estimated
def fit_fe(df, y, X):
    """Within estimator with Driscoll-Kraay errors (Bartlett, floor(4 (T/100)^(2/9)))."""
    df = df.dropna(subset=[y] + X)
    W = df[[y] + X] - df.groupby('empresa')[[y] + X].transform('mean')
    Y = W[y].values; M = W[X].values
    b, *_ = np.linalg.lstsq(M, Y, rcond=None); e = Y - M @ b
    XtXi = np.linalg.inv(M.T @ M)
    h = pd.DataFrame(M * e[:, None]).groupby(df.periodo.values).sum().sort_index().values
    T = h.shape[0]; Lb = int(np.floor(4 * (T / 100) ** (2 / 9))); S = h.T @ h
    for l in range(1, Lb + 1):
        G_ = h[l:].T @ h[:-l]; S += (1 - l / (Lb + 1)) * (G_ + G_.T)
    se = np.sqrt(np.diag(XtXi @ S @ XtXi))
    return b, se, 1 - (e @ e) / (Y @ Y), len(df)

m7p = D / 'm7_panel_mensual.parquet'
if m7p.exists():
    p7 = pd.read_parquet(m7p)
    CT = ['rend_mercado', 'vol_sistematica', 'tasa', 'tipo_cambio', 'vix', 'vol_idiosincratica']
    DP = {'spread': 'Diferencial', 'ln_illiq': 'ln ILLIQ', 'zret': 'Rend. cero', 'rotacion': 'Rotación'}
    with open(OUT / 'tabla_panel.tex', 'w', encoding='utf8') as f:
        for y, nm in DP.items():
            s = p7.dropna(subset=[y, 'psic10', 't'] + CT)
            b, se, _, n = fit_fe(s, y, ['psic10'] + CT + ['t'])
            pv = 2 * (1 - stats.norm.cdf(abs(b[0] / se[0])))
            r0 = fit_fe(s, y, ['t'])[2]; rc = fit_fe(s, y, ['t'] + CT)[2]
            rp = fit_fe(s, y, ['t', 'psic10'])[2]; ra = fit_fe(s, y, ['t'] + CT + ['psic10'])[2]
            f.write(f'{nm} & {b[0]:+.4f} & {pv:.3f} & {100*(rc-r0):.2f} & {100*(ra-rc):.3f} & {(rc-r0)/(ra-rc):,.0f} '
                    f'& {100*(rp-r0):.3f} & {(ra-rp)/(rp-r0):,.1f} \\\\\n')
    with open(OUT / 'tabla_tercil.tex', 'w', encoding='utf8') as f:
        for g in ['menor', 'intermedia', 'mayor']:
            s = p7[p7.tercil.astype(str) == g]; cells = []
            for y in DP:
                b, se, _, _ = fit_fe(s, y, ['psic10'] + CT + ['t'])
                cells.append(f'{b[0]:+.4f} ({2 * (1 - stats.norm.cdf(abs(b[0] / se[0]))):.3f})')
            f.write(g.capitalize() + ' & ' + ' & '.join(cells) + ' \\\\\n')
    mac('panelDisponible', 'sí')

with open(OUT / 'resultados.tex', 'w', encoding='utf8') as f:
    f.write('% Generado por scripts/notas_analisis.py. No editar a mano.\n')
    for kname, v in MAC.items():
        f.write('\\newcommand{\\R%s}{%s}\n' % (kname, v))
print('ok', len(MAC), 'macros;', len(dZ), 'meses')
