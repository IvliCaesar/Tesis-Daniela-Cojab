"""Tabla de archivos de entrada con huella SHA-256 y el módulo que alimenta cada uno.

Uso: python pipeline/huellas.py <carpeta con los archivos de la autora> <salida.csv>

El papel de cada archivo se estableció reproduciendo sus salidas (pipeline/README.md).
"""
import csv, datetime, hashlib, os, sys
from pathlib import Path

D, OUT = Path(sys.argv[1]), Path(sys.argv[2])
PAPEL = {
    'Universo Liquidez emisoras DD.xlsx': 'Módulo 1: universo de liquidez (349 series, hojas Diario Global/BIVA/BMV). Reproducido al 100%.',
    'Universo local completo dividido DD.xlsx': 'Módulo 1: universo local (hojas TOTAL/BIVA/BMV), completado con 19 series del universo de liquidez.',
    'Universo SIC emisoras.xlsx': 'Módulo 1: universo SIC (hojas Diarios Global/BIVA/BMV). Reproducido al 100%, salvo la serie TXG1N.',
    'Universo SIC completo DD.xlsx': 'Otra extracción del SIC (hojas GLOBAL/BIVA/BMV); no es la que usa la tesis.',
    'm2_mapa_empresas.parquet': 'Módulo 2: serie -> empresa (ID_BB_COMPANY de la terminal; no resuelto en los libros descargados).',
    'indices, macroeconomicos y AMIB DD.xlsx': 'Módulos 4 y 7: INPC (MXCPI), IPC, VIX, TIIE 28, tipo de cambio; hoja AMIB como contraste externo.',
    'PIBA_2.csv': 'H1: PIB real anual (INEGI, precios de 2018), hasta 2024.',
    'Mercado local vs global BMVBIVA AMIB V2.xlsx': 'Contraste externo (apartado 4.1.4): boletines de la AMIB.',
    'DATOS SIC INFORME BMV.xlsx': 'Contexto (cronología del SIC, informes anuales de la BMV); no entra en cálculos.',
    'Tesis daniela cojab 261106.docx': 'Texto de la tesis, versión del 6 de noviembre de 2026.',
    'IDBB COMPANY Y GICS SECTOR NAME DD.xlsx': 'Identificadores y sector (incompleto: 84 series sin ID); no se usa en los resultados.',
    'sector emisoras.xlsx': 'Sector y estado por universo (fórmulas sin resolver); no se usa en los resultados.',
    'INPC.xlsx': 'INPC de Banxico; no se usa (el cálculo usa MXCPI de la terminal).',
    'Tesis_procedimiento_de_calculo.ipynb': 'Versión anterior del procedimiento; no reproduce la tesis.',
}
NO_USADO = 'Versión anterior, duplicado o libro solo con fórmulas; no se usa en los resultados.'
filas = []
for f in sorted(os.listdir(D)):
    p = D / f
    if not p.is_file() or not f.lower().endswith(('.xlsx', '.csv', '.parquet', '.ipynb', '.docx')):
        continue
    if not (f in PAPEL or f.startswith(('m1_', 'm2_', 'm3_', 'm4_', 'm7_', 'calendario')) or 'niverso' in f.lower()
            or 'VOMS' in f or 'CETE28' in f):
        continue
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    if f in PAPEL:
        papel = PAPEL[f]
    elif f.startswith(('m1_', 'm2_', 'm3_', 'm4_', 'm7_', 'calendario')):
        papel = 'Salida de la autora (referencia para validar la reconstrucción).'
    else:
        papel = NO_USADO
    filas.append([f, p.stat().st_size, datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                  h.hexdigest(), papel])
dup = {}
for r in filas:
    dup.setdefault(r[3], []).append(r[0])
for r in filas:
    otros = [x for x in dup[r[3]] if x != r[0]]
    if otros:
        r[4] += f' Idéntico a: {", ".join(otros)}.'
with open(OUT, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh); w.writerow(['archivo', 'bytes', 'modificado', 'sha256', 'papel'])
    w.writerows(filas)
print(len(filas), 'archivos')
