"""Usage: python scripts/verifica_tesis.py <carpeta con los .parquet de la autora>

Check the thesis figures and the review's claims against the thesis parquets.

Reads only the parquet/CSV outputs in Downloads (data); runs no downloaded code.
"""
import numpy as np, pandas as pd, warnings
from scipy import stats
warnings.filterwarnings('ignore')
import sys
# Folder with the author's parquet/CSV outputs (licensed Bloomberg data is not in the repo).
D = sys.argv[1].rstrip('/') + '/'
pd.set_option('display.width', 200)

def holm(ps):
    ps = np.asarray(ps, float); o = np.argsort(ps); n = len(ps); adj = np.empty(n); run = 0
    for r, i in enumerate(o):
        run = max(run, (n - r) * ps[i]); adj[i] = min(run, 1.0)
    return adj

# ---------------------------------------------------------------- H1
pa = pd.read_parquet(D + 'm4_psic_anual_real.parquet')
pa['periodo'] = pd.to_datetime(pa.periodo).dt.year; pa = pa.set_index('periodo'); pa['psic'] = pa.psic/100
print('== A. Participación anual (Tabla 4.5) y razón suma/consolidado')
print(pa[['psic', 'psic_consolidado', 'diferencia_pp']].round(4).T.to_string())

# AMIB, BMV only (values hard-coded in the author's earlier notebook, cell 1.1)
AMIB = {2004:(1103391,12665),2005:(1225186,49670),2006:(1838053,289976),2007:(2893299,315433),
        2008:(2871445,642180),2009:(2977594,465784),2010:(4705718,779254),2011:(4194664,1065309),
        2012:(5320576,1026719),2013:(5815515,1434515),2014:(4906508,1299037),2015:(4678735,1855242),
        2016:(5176770,2171542),2017:(4643043,2620843),2018:(4578353,3293586),2019:(3832526,2821293),
        2020:(3733960,4176234),2021:(4119042,4481672),2022:(4490558,4481162),2023:(4548846,2998454),
        2024:(4919151,2913486),2025:(4942958,3708130)}
INF = {2003:2537,2004:12665,2005:24835,2006:144985,2007:157717,2008:321090,2009:232892,
       2010:389627,2011:532655,2012:513359,2013:717245}   # BMV annual reports, SIC, MXN mn
am = pd.DataFrame(AMIB, index=['loc', 'sic']).T
print('\n== B. AMIB global / informe anual BMV (SIC):',
      ' '.join(f'{y}:{am.sic[y]/INF[y]:.2f}' for y in INF if y in am.index))
print('   psic AMIB (BMV) 2004: %.2f%%  con el SIC de 2004 duplicado: %.2f%%  Bloomberg: %.2f%%'
      % (100*am.sic[2004]/am.sum(axis=1)[2004], 100*2*am.sic[2004]/(am.loc[2004,'loc']+2*am.sic[2004]),
         100*pa.psic[2004]))
print('   razón Bloomberg/AMIB por segmento (sic, loc), pesos corrientes:')
print('   ' + ' '.join(f"{y}:{pa.sic[y]/1e6/am.sic[y]:.2f}/{pa.loc[y,'loc']/1e6/am.loc[y,'loc']:.2f}"
                     for y in range(2004, 2026)))

pib = pd.read_csv(D + 'PIBA_2.csv', encoding='utf-8-sig', index_col=0).iloc[0]
pib.index = [int(str(c)[:4]) for c in pib.index]; pib = pib.astype(float)
cagr = lambda s, a, b: 100 * ((s[b] / s[a]) ** (1 / (b - a)) - 1)
def slope(s, a, b):
    y = np.log(s.loc[a:b].astype(float)); t = np.arange(len(y))
    return 100 * (np.exp(np.polyfit(t, y.values, 1)[0]) - 1)
print('\n== C. Tasas reales (Tabla 4.6): extremos vs pendiente log-lineal')
print('   (PIBA_2.csv llega a 2024: la columna PIB usa 2024 como año final)')
for a, b in [(2004, 2025), (2004, 2024), (2004, 2013), (2014, 2018), (2019, 2025), (2014, 2024), (2006, 2025), (2013, 2025)]:
    print('   %d-%d  SIC %7.2f%% (pend %7.2f%%)  local %6.2f%% (pend %6.2f%%)  PIB %5.2f%%'
          % (a, b, cagr(pa.sic_real, a, b), slope(pa.sic_real, a, b), cagr(pa.loc_real, a, b),
             slope(pa.loc_real, a, b), (cagr(pib, a, min(b, 2024)) if a < 2024 else float('nan'))))
r = (pa.loc_real / pa.inpc.iloc[0] * 0 + pa.loc_real) / pib.reindex(pa.index)
print('   importe local real / PIB (índice 2004=100): ' +
      ' '.join(f'{y}:{100*r[y]/r[2004]:.0f}' for y in [2004, 2008, 2013, 2014, 2018, 2019, 2022, 2024]))

# ---------------------------------------------------------------- H2
la = pd.read_parquet(D + 'm3_liquidez_anual.parquet')
if not np.issubdtype(la.periodo.dtype, np.integer): la['periodo'] = pd.to_datetime(la.periodo).dt.year
la['turn'] = la.importe / la.cap_promedio
inpc = pa.inpc / pa.inpc[2018]
la['defl'] = la.periodo.map(inpc)
la['ln_illiq_real'] = la.ln_illiq + np.log(la.defl)     # |R|/(V/defl) = defl*|R|/V
print('\n== D. Panel anual: %d obs, %d empresas; válidas spread %d, illiq %d, zret %d, turn %d'
      % (len(la), la.empresa.nunique(), la.spread.notna().sum(), la.ln_illiq.notna().sum(),
         la.zret.notna().sum(), la.turn.notna().sum()))
med = la.groupby('periodo')[['spread', 'ln_illiq', 'ln_illiq_real', 'zret', 'turn']].median()
print('   medianas (Tabla 4.7):')
print(med.loc[[2004, 2013, 2014, 2018, 2025, 2026]].round(4).to_string())
print('   ln INPC 2014/2004 = %.3f ; caída ln_illiq nominal 2004->2014 = %.3f, real = %.3f'
      % (np.log(inpc[2014] / inpc[2004]), med.ln_illiq[2014] - med.ln_illiq[2004],
         med.ln_illiq_real[2014] - med.ln_illiq_real[2004]))
mm = la.groupby('periodo').zret.mean()
print('   ZRET media: 2004 %.3f  2018 %.3f  2026 %.3f' % (mm[2004], mm[2018], mm[2026]))

# composition: ZRET 2004 vs 2018 for firms present in both years
both = set(la[la.periodo == 2004].empresa) & set(la[la.periodo == 2018].empresa)
z = la[la.empresa.isin(both)].pivot_table(index='empresa', columns='periodo', values='zret')
print('   ZRET mediana entre las %d empresas presentes en 2004 y 2018: 2004 %.3f -> 2018 %.3f'
      % (len(both), z[2004].median(), z[2018].median()))
for y in (2004, 2018):
    s = la[la.periodo == y]
    print('   %d: empresas %d, ZRET mediana %.3f; proporción con ZRET>0.5: %.2f'
          % (y, len(s), s.zret.median(), (s.zret > .5).mean()))

# ---------------------------------------------------------------- terciles
te = pd.read_parquet(D + 'm2_terciles.parquet')
cap = pd.read_parquet(D + 'm2_capitalizacion.parquet')
cap['anio'] = cap.fecha.dt.year
yr = cap.groupby('empresa').anio.mean().rename('anio_medio')
te = te.join(yr, on='empresa')
rho = stats.spearmanr(te.ln_mc_promedio, te.anio_medio, nan_policy='omit')
print('\n== E. Terciles: %d empresas. Spearman(ln MC promedio, año medio de cotización) = %+.3f (p=%.4f)'
      % (len(te), rho.statistic, rho.pvalue))
print(te.groupby('tercil').anio_medio.median().round(1).to_string())
cap['real'] = cap.capitalizacion / cap.anio.map(inpc)
c2 = cap[cap.capitalizacion > 0].groupby('empresa').apply(lambda x: np.log(x.real).mean(),
                                                          include_groups=False).rename('lnreal')
te = te.join(c2, on='empresa')
te['tercil_real'] = pd.qcut(te.lnreal, 3, labels=['menor', 'intermedia', 'mayor'])
# rank-based: mean within-year percentile
cap['pct'] = cap[cap.capitalizacion > 0].groupby('fecha').capitalizacion.rank(pct=True)
c3 = cap.groupby('empresa').pct.mean().rename('pct')
te = te.join(c3, on='empresa')
te['tercil_rango'] = pd.qcut(te.pct, 3, labels=['menor', 'intermedia', 'mayor'])
print('   coinciden con el tercil original: deflactado %.1f%%, por rango anual %.1f%%'
      % (100 * (te.tercil.astype(str) == te.tercil_real.astype(str)).mean(),
         100 * (te.tercil.astype(str) == te.tercil_rango.astype(str)).mean()))

# ---------------------------------------------------------------- size tests
la = la.merge(te[['empresa', 'tercil', 'tercil_rango']], on='empresa', how='left')
la['tramo'] = pd.cut(la.periodo, [2003, 2013, 2018, 2025], labels=['T1', 'T2', 'T3'])
GRUPO = te.set_index('empresa')[['tercil', 'tercil_rango']]
print('   columnas:', [c for c in la.columns if 'tercil' in c], 'sin tercil:', GRUPO.tercil.isna().sum())
MED = {'spread': 1, 'ln_illiq': 1, 'ln_illiq_real': 1, 'zret': 1, 'turn': -1}
def size_test(col_t, A, B, cols):
    out = []
    for c in cols:
        E = la.pivot_table(index='empresa', columns='tramo', values=c, aggfunc='median', observed=True)
        d = E[[A, B]].dropna().copy(); d['g'] = GRUPO[col_t].reindex(d.index).astype(str).values
        d['ch'] = (d[B] - d[A])
        for g in ['menor', 'intermedia']:
            x = d[d.g == g].ch; y = d[d.g == 'mayor'].ch
            u = stats.mannwhitneyu(x, y, alternative='two-sided')
            out.append((c, g, len(x), len(y), x.median(), y.median(), u.pvalue))
    o = pd.DataFrame(out, columns=['medida', 'grupo', 'n_g', 'n_mayor', 'cambio_g', 'cambio_mayor', 'p'])
    o['p_holm'] = holm(o.p); return o
cols = ['spread', 'ln_illiq', 'zret', 'turn']
print('\n== F. Tamaño, ventana de la tesis (T1->T3), tercil original:')
print(size_test('tercil', 'T1', 'T3', cols).round(4).to_string(index=False))
print('\n== G. Tamaño, ventana del deterioro (T2->T3), tercil original:')
print(size_test('tercil', 'T2', 'T3', cols).round(4).to_string(index=False))
print('\n== H. Tamaño, T2->T3, tercil por rango anual e illiq real:')
print(size_test('tercil_rango', 'T2', 'T3', ['spread', 'ln_illiq_real', 'zret', 'turn']).round(4).to_string(index=False))

# Wilcoxon T2->T3 replication (Tabla 4.9) with tramo medians per firm
print('\n== I. Wilcoxon por empresa (mediana anual de cada tramo):')
for A, B in [('T1', 'T2'), ('T2', 'T3'), ('T1', 'T3')]:
    row = []
    for c in ['spread', 'ln_illiq', 'zret', 'turn']:
        E = la.pivot_table(index='empresa', columns='tramo', values=c, aggfunc='median', observed=True)
        d = E[[A, B]].dropna(); w = stats.wilcoxon(d[B], d[A])
        row.append((c, len(d), (d[B] - d[A]).median(), w.pvalue))
    adj = holm([r[3] for r in row])
    print('   %s->%s ' % (A, B) + ' | '.join('%s n=%d cambio=%+.4f p_holm=%.3f' % (r[0], r[1], r[2], p)
                                         for r, p in zip(row, adj)))
