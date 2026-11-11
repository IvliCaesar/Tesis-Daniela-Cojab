"""Módulo 1 (reconstruido): de los libros de Bloomberg a tablas largas por centro.

Uso: python pipeline/m1_lectura.py <carpeta con los libros> <carpeta de salida> [universo ...]
     universo: liq, loc, sic (por omisión, los tres)

Cada hoja trae, desde la columna B, bloques de campos por serie: fila 4 = clave de
Bloomberg (p. ej. "GMEXICOB MF Equity"), fila 6 = nemónico del campo, datos desde la fila 7
con las fechas en la columna A. Se conservan las filas con algún campo numérico
("#N/A ..." y celdas vacías cuentan como faltantes). Salida: m1_<universo>_<centro>.parquet
con columnas fecha, ticker, instrumento y los campos en minúsculas. Solo se conservan las fechas
en que alguna serie del consolidado del mismo libro tuvo importe positivo: los feriados traen
capitalizaciones arrastradas y se descartan. El universo local se completa con las series
del universo de liquidez que no trae su libro (por eso liq se lee antes que loc).
"""
import datetime, sys
from pathlib import Path
import numpy as np, openpyxl, pandas as pd

IN, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
LIBROS = {
    'liq': ('Universo Liquidez emisoras DD.xlsx', {'glob': 'Diario Global', 'biva': 'Diarios BIVA', 'bmv': 'Diarios BMV'}),
    'loc': ('Universo local completo dividido DD.xlsx', {'glob': 'TOTAL', 'biva': 'BIVA', 'bmv': 'BMV'}),
    # the author's SIC source (values match 100%; the series TXG1N, empty here, came from another extraction)
    'sic': ('Universo SIC emisoras.xlsx', {'glob': 'Diarios Global', 'biva': 'Diarios BIVA', 'bmv': 'Diarios BMV'}),
}
CAMPOS = {'TOT_RETURN_INDEX': 'tot_return_index_gross_dvds', 'TOT_RETURN_INDEX_GROSS_DVDS': 'tot_return_index_gross_dvds'}


def lee_hoja(ws):
    it = ws.iter_rows(values_only=True)
    head = [next(it) for _ in range(6)]
    claves, campos = head[3], head[5]
    cols, actual = [], None
    for j in range(1, len(campos)):
        if claves[j] not in (None, ''):
            actual = str(claves[j]).strip()
        if campos[j] in (None, '') or actual is None:
            continue
        c = str(campos[j]).strip().upper()
        cols.append((j, actual, CAMPOS.get(c, c.lower())))
    fechas, datos = [], []
    for r in it:
        f = r[0]
        if not isinstance(f, datetime.datetime):
            continue
        fechas.append(f)
        datos.append([r[j] if j < len(r) and isinstance(r[j], (int, float)) and not isinstance(r[j], bool) else np.nan
                      for j, _, _ in cols])
    arr = np.array(datos, dtype='float64')
    meta = pd.DataFrame(cols, columns=['j', 'ticker', 'campo'])
    partes = []
    for tk, g in meta.groupby('ticker', sort=False):
        idx = [meta.index.get_loc(i) for i in g.index]
        df = pd.DataFrame(arr[:, idx], columns=g.campo.values)
        df.insert(0, 'ticker', tk); df.insert(0, 'fecha', pd.to_datetime(fechas))
        partes.append(df.dropna(how='all', subset=list(g.campo.values)))
    out = pd.concat(partes, ignore_index=True)
    out.insert(2, 'instrumento', out.ticker.str.replace(r'\s+(MM|MF|MU)\s+Equity$', '', regex=True, case=False).str.strip())
    return out


for u in (sys.argv[3:] or list(LIBROS)):
    libro, hojas = LIBROS[u]
    wb = openpyxl.load_workbook(IN / libro, read_only=True, data_only=True)
    sesiones = None
    for centro, hoja in hojas.items():          # glob is read first
        df = lee_hoja(wb[hoja])
        if sesiones is None:
            sesiones = set(df.loc[df.turnover > 0, 'fecha'])
        df = df[df.fecha.isin(sesiones)]
        if u == 'loc':
            # the local universe is completed with the liquidity-universe series it lacks
            # (19 CPO and UB series); requires m1_liq_<centro>.parquet in OUT
            liq = pd.read_parquet(OUT / f'm1_liq_{centro}.parquet', columns=list(df.columns))
            extra = liq[~liq.instrumento.isin(df.instrumento)].dropna(how='all', subset=['turnover', 'px_volume', 'px_last'])
            df = pd.concat([df, extra], ignore_index=True)
        df.to_parquet(OUT / f'm1_{u}_{centro}.parquet', index=False)
        print(u, centro, df.shape, flush=True)
    wb.close()
