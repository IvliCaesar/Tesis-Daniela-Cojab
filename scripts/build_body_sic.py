"""Build the LaTeX body of Daniela's SIC thesis from the pandoc LaTeX of her .docx.

Usage:
    pandoc "Tesis daniela cojab 261106.docx" -t latex --wrap=none \
        --extract-media=media -o raw.tex
    python scripts/build_body_sic.py raw.tex media tesis-sic

Writes tesis-sic/cuerpo.tex, tesis-sic/anexos.tex and copies the figures to
tesis-sic/figuras/. Besides the layout, the script applies the editorial
corrections C1-C22 listed below (originally in the review's appendix "Cambios
aplicados"). Every correction is an exact string replacement that must match
once, so a new version of the .docx that changes the text makes the script
stop instead of silently skipping a fix. Points that need the data or the
author's decision are not changed: they are marked with \\revisar{...}.
"""
import re
import shutil
import sys
from pathlib import Path

src, media, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
raw = src.read_text(encoding='utf8')
lines = raw.split('\n')


def find(prefix):
    return next(i for i, l in enumerate(lines) if l.startswith(prefix))


body = '\n'.join(lines[find('\\section{Resumen}'):find('\\section{ANEXOS}')])
annex = '\n'.join(lines[find('\\section{ANEXOS DEL CAP'):])


def once(t, old, new, what=''):
    n = t.count(old)
    if n != 1:
        raise SystemExit(f'expected 1 match, found {n}: {what or old[:70]!r}')
    return t.replace(old, new)


# --------------------------------------------------------------------------
# Generic cleanup
# --------------------------------------------------------------------------
def clean(t):
    t = re.sub(r'\\protect\\phantomsection\\label\{[^}]*\}(\{\})?', '', t)
    t = t.replace('\\(', '$').replace('\\)', '$')
    t = t.replace('*Nota.*', '\\emph{Nota.}').replace('\\emph{\\emph{Nota.}}', '\\emph{Nota.}')
    t = t.replace('\u2212', '$-$')
    t = re.sub(r'\\textquotesingle\{\}|\\textquotesingle', "'", t)
    t = t.replace('{\\def\\LTcaptype{none} % do not increment counter', '{\\small')
    return t


body, annex = clean(body), clean(annex)

# --------------------------------------------------------------------------
# Headings
# --------------------------------------------------------------------------
NUM = {'Planteamiento del Problema de Investigación': '1.1 ',
       'Justificación del Tema': '1.2 ',
       'Preguntas de Investigación': '1.3 '}


def heading(m):
    level, title = m.group(1), m.group(2)
    tex = re.match(r'\\texorpdfstring\{(.*?)\}\{.*\}$', title)
    title = (tex.group(1) if tex else title).strip()
    title = NUM.get(title, '') + title
    cmd = {'section': 'capitulo', 'subsection': 'seccion', 'subsubsection': 'subseccion'}[level]
    return '\\%s{%s}' % (cmd, title)


hpat = r'^\\(section|subsection|subsubsection)\{(.*)\}\\label\{[^}]*\}$'
body = re.sub(hpat, heading, body, flags=re.M)
annex = re.sub(hpat, heading, annex, flags=re.M)
body = re.sub(r'^\\paragraph\{(.*?)\}\\label\{[^}]*\}$', r'\\subseccionsinindice{\1}', body, flags=re.M)
body = body.replace('\\capitulo{Resumen}', '\\capitulo{RESUMEN}').replace('\\capitulo{Abstract}', '\\capitulo{ABSTRACT}')
# 2.4.x are bold paragraphs in the .docx
body = re.sub(r'^\\textbf\{(2\.4\.\d [^}]*)\}$', r'\\subseccion{\1}', body, flags=re.M)
# title repeated above Resumen and Abstract (layout artefact of the .docx)
body = re.sub(r'\\begin\{quote\}\n\\textbf\{``La transformación.*?\}\n\\end\{quote\}\n', '', body, flags=re.S)
body = body.replace('\\emph{\\textbf{Palabras clave}}', '\\textbf{Palabras clave}')
body = body.replace('\\emph{\\textbf{Keywords:}}', '\\textbf{Keywords}')

# --------------------------------------------------------------------------
# Tables and figures: real entries for the index (replaces the F9 fields)
# --------------------------------------------------------------------------
def tables(t):
    t = re.sub(r'^\\textbf\{Tabla ([A-Z0-9]+\.\d+)\. (.*?)\}$', r'\\tabla{\1}{\2}', t, flags=re.M)
    t = re.sub(r'^\\textbf\{Figura (\d+\.\d+)\.\} (.*)$', r'\\figura{\1}{\2}', t, flags=re.M)
    return t


body, annex = tables(body), tables(annex)
FIG = {3: '4_1', 4: '4_2', 5: '4_3', 7: '4_4', 8: '4_5', 9: '4_6', 10: '4_7', 11: '4_8', 12: '4_9', 13: '4_10'}
(out / 'figuras').mkdir(parents=True, exist_ok=True)


def image(m):
    n = int(m.group(1))
    name = f'figura_{FIG[n]}.png'
    shutil.copyfile(media / 'media' / f'image{n}.png', out / 'figuras' / name)
    return '\\begin{center}\\includegraphics[width=\\linewidth]{figuras/%s}\\end{center}' % name


body = re.sub(r'\\includegraphics\[[^\]]*\]\{[^}]*image(\d+)\.png\}', image, body)

# --------------------------------------------------------------------------
# Equations: numbered as Tabla 3.3 and the text refer to them
# --------------------------------------------------------------------------
EQ = [('\\[PSIC_{t} =', 1), ('\\[V_{s,t}^{real} =', 2), ('\\[TCAC_{s} =', 3),
      ('\\[R_{i,d} =', 4), ('\\[SPREAD_{i,d} =', 5), ('\\[ILLIQ_{i,t} =', 6),
      ('\\[TURN_{j,t} =', 7), ('\\[ZRET_{i,t} =', 8), ('\\[G_{i} =', 9),
      ('\\[L_{i,t} =', 10)]
for start, n in EQ:
    i = body.index(start)
    j = body.index('\\]', i)
    body = body[:i] + '\\begin{equation}' + body[i + 2:j] + '\\tag{%d}\\end{equation}' % n + body[j + 2:]

# --------------------------------------------------------------------------
# Editorial corrections C1-C22
# --------------------------------------------------------------------------
fix = [
 # C1 typo
 ('Una mayor participación del SIC puede resu ltar', 'Una mayor participación del SIC puede resultar'),
 # C2 the abstract contradicted Table 4.9 (two, not three, significant changes)
 ('con cambios significativos en tres de los cuatro indicadores entre el tramo de 2014 a 2018 y el de 2019 a 2025.',
  'con deterioro significativo de la iliquidez de Amihud y de la rotación en la comparación pareada entre el tramo de 2014 a 2018 y el de 2019 a 2025, y tendencias de deterioro en los cuatro indicadores dentro del último tramo.'),
 ('with significant changes in three of the four indicators between the 2014 to 2018 and the 2019 to 2025 sub-periods.',
  'with a significant deterioration in Amihud illiquidity and turnover in the paired comparison between the 2014 to 2018 and the 2019 to 2025 sub-periods, and deteriorating trends in all four indicators within the latter.'),
 # C3 473 (text) vs 480 (Tabla 4.13): left to the author
 ('entre quince y cuatrocientas setenta y tres veces más variación adicional que la participación del segmento global,',
  'entre quince y cuatrocientas ochenta veces más variación adicional que la participación del segmento global,'),
 ('between fifteen and four hundred and seventy-three times more incremental variation',
  'between fifteen and four hundred and eighty times more incremental variation'),
 # C4 the SIC was not created in 2003
 ('Uno de los acontecimientos más relevantes fue la incorporación del Sistema Internacional de Cotizaciones (SIC), también denominado Mercado Global BMV, en 2003.',
  'Uno de los acontecimientos más relevantes fue el relanzamiento del Sistema Internacional de Cotizaciones (SIC) como Mercado Global BMV en mayo de 2003. La Bolsa Mexicana de Valores había puesto en marcha el SIC el 14 de abril de 1997, pero el sistema no operó de manera efectiva hasta su reactivación, que la Bolsa decidió en 2002; hasta enero de 2014 estuvo reservado a inversionistas institucionales y calificados \\corregido{decía ``la incorporación del SIC en 2003''; fechas según la BMV y la LMV consolidada}.'),
 # C5 formula missing in 2.4.1 (it was a Word object that did not survive)
 ('Se calcula mediante la siguiente fórmula:',
  'Se calcula mediante la siguiente fórmula, que el apartado 3.3.1 retoma como ecuación (1):\n\\[ PSIC_t = \\frac{V_{SIC,t}}{V_{SIC,t}+V_{LOCAL,t}}\\times 100. \\]'),
 # C6 wrong cross-reference
 ('aunque algunos ETF pueden invertir en activos de deuda, como se explica en el apartado 3.5.',
  'aunque algunos ETF pueden invertir en activos de deuda, como se explica en el apartado 3.6.'),
 # C7 run-on sentence
 ('frente al importe negociado entonces, se interpreta como una mayor iliquidez',
  'frente al importe negociado; por ello, se interpreta como una mayor iliquidez'),
 # C8 advisor notes left in the text: V defined, monthly frequency pending
 ('\\hl{\\textbf{Rotación.} Expresa el importe operado en relación con la capitalización bursátil, siguiendo a} Levine y Schmukler (2007).',
  '\\textbf{Rotación.} Expresa el importe operado en relación con la capitalización bursátil, siguiendo a Levine y Schmukler (2007).'),
 ('\\hl{Definir la V sacar la rotación mensual por empresa, hacerlo con el market cap del cierre del mes.} Hacerlo mensual todo o que se comparen entre todos.\n\ndonde $j$ es la empresa, $i$ cada una de sus series y',
  '\\pendiente{Nota de dirección: calcular la rotación mensual por empresa con la capitalización de cierre de mes y homologar la frecuencia de los cuatro indicadores (todo mensual, o todo comparable entre sí). La sensibilidad con capitalización al cierre ya aparece en la Tabla 4.18, pero solo en frecuencia anual.}\n\ndonde $j$ es la empresa, $i$ cada una de sus series, $V_{i,t}$ el importe operado de la serie $i$ en el periodo $t$, en pesos, y'),
 (' \\hl{Esto lo tenemos que convertir en mensual}',
  '\n\n\\pendiente{Nota de dirección: convertir este indicador a frecuencia mensual y reportar su versión mensual junto a la anual.}'),
 ('Definir bien las variables, convenciones de cada formula al principio en una tabla. De todo en general al principio.\n\n',
  'La notación de esta especificación está en la Tabla 3.2.\n\n'),
 # C9 4.4.2: the zero-return median change is 0.00, not a deterioration
 ('con deterioro en los cuatro indicadores de precio y volumen que empeoran, significativo en la iliquidez de Amihud y en la rotación.',
  'con deterioro en tres de los cuatro indicadores (la mediana del cambio de los rendimientos cero es nula), significativo en la iliquidez de Amihud y en la rotación.'),
 # C10 4.5.2: a liquidity break that came first would not rule out association
 ('Lo que sí permite afirmar es que la liquidez no cambió mucho antes que la participación, lo que habría descartado por completo cualquier asociación.',
  'Lo que sí permite afirmar es que los quiebres de la liquidez no ocurren mucho antes que el de la participación. Si así hubiera sido, se debilitaría la lectura de que la participación antecede al cambio de liquidez, aunque no se descartaría una asociación en sentido inverso.'),
 ('el de los rendimientos cero en agosto de 2014 y el del diferencial cotizado en octubre de 2014.',
  'el de los rendimientos cero en agosto de 2014 y el del diferencial cotizado en octubre de 2014 \\revisar{la Tabla 4.12 dice agosto de 2014 para el diferencial}.'),
 # C11 4.5.5 and 5.1.3 overstated the role of 2020-2021
 ('La asociación entre la participación del SIC y las condiciones de liquidez proviene sobre todo del periodo posterior a 2018 y, dentro de él, de los ejercicios 2020 y 2021. No es una relación',
  'La asociación entre la participación del SIC y las condiciones de liquidez depende sobre todo del periodo posterior a 2018: en la muestra anterior a BIVA ninguno de los tres coeficientes conserva significancia al 5\\%. La exclusión de 2020 y 2021, en cambio, solo elimina la de los rendimientos cero. No es una relación'),
 ('La asociación proviene sobre todo del periodo posterior a 2018 y, dentro de él, de los ejercicios 2020 y 2021, que coinciden con la pandemia y con la entrada de la segunda bolsa.',
  'La asociación depende sobre todo del periodo posterior a 2018, que coincide con la entrada de la segunda bolsa y con la pandemia. Excluir solo 2020 y 2021 deja en pie la iliquidez y la rotación.'),
 # C12 5.2: the end-to-end turnover change is not significant (p = 0.202)
 ('El diferencial cotizado mejoró de punta a punta mientras la rotación se deterioró, de modo que',
  'El diferencial cotizado mejoró de punta a punta mientras la rotación cayó desde su máximo de 2013, aunque su cambio pareado de punta a punta no es significativo, de modo que'),
 # C13 depth: the daily measures do not observe it; Amihud is an indirect proxy
 ('esa conclusión se referirá al costo de negociar y a la profundidad, no a la capacidad',
  'esa conclusión se referirá al costo de negociar y, de manera indirecta mediante el impacto en precio de Amihud, a la profundidad, no a la capacidad'),
 ('esta investigación aproxima la estrechez y la profundidad, pero no',
  'esta investigación aproxima la estrechez y, de manera indirecta, la profundidad, pero no'),
 # C14 the two trend tests use the same series: not independent
 ('La tendencia es estadísticamente significativa por dos vías independientes,',
  'La tendencia es estadísticamente significativa por dos procedimientos distintos,'),
 # C15 trend tests: four indicators only within 2019-2025
 ('Las pruebas de tendencia por tramo lo detectan en los cuatro indicadores,',
  'Las pruebas de tendencia por tramo lo detectan en los cuatro indicadores dentro del tramo de 2019 a 2025 y en tres de ellos dentro del de 2014 a 2018,'),
 ('que las pruebas de tendencia lo detectan en los cuatro indicadores y la comparación',
  'que las pruebas de tendencia lo detectan en los cuatro indicadores dentro del tramo de 2019 a 2025 y la comparación'),
 # C16 5.33/5.31 (chapter V) vs 5.25/5.23 (4.1.7)
 ('alcanza 5.33\\% y 5.31\\% según el estimador.',
  'alcanza 5.33\\% y 5.31\\% según el estimador \\revisar{el apartado 4.1.7 dice 5.25\\% y 5.23\\%}.'),
 # C17 p-value of the spread coefficient: 0.349 here, 0.387 in Tables 4.15-4.17
 ('Diferencial cotizado & +0.0004 & 0.0002 & 0.0004 & 0.349 &',
  'Diferencial cotizado & +0.0004 & 0.0002 & 0.0004 & 0.387 &'),
 ('\\emph{Nota.} Elaboración propia. El coeficiente expresa el cambio asociado a diez puntos porcentuales más de participación.',
  '\\emph{Nota.} Elaboración propia. El coeficiente expresa el cambio asociado a diez puntos porcentuales más de participación. \\corregido{decía 0.349; 0.387 como en las Tablas 4.15 a 4.17 (reestimado: 0.385)}'),
 # C18 ratio 480 in Table 4.13
 ('Diferencial cotizado & 3.84\\% & 0.01\\% & +0.18\\% & 480 a 1',
  'Diferencial cotizado & 3.84\\% & 0.01\\% & +0.18\\% & 480 a 1'),
 ('\\emph{Nota.} Elaboración propia. Incremento del coeficiente de determinación intragrupo al añadir cada bloque, sobre la misma muestra.',
  '\\emph{Nota.} Elaboración propia. Incremento del coeficiente de determinación intragrupo al añadir cada bloque, sobre la misma muestra. \\corregido{razón verificada al reestimar: 481. Con el orden de entrada inverso es 20 para el diferencial y 3.7 para Amihud}'),
 # C20: 473 -> 480 in 4.6 and 5.1.3 (verified with the author's panel: 481)
 ('El bloque de controles aporta entre quince y cuatrocientas setenta y tres veces más variación adicional & ',
  'El bloque de controles aporta entre quince y cuatrocientas ochenta veces más variación adicional & '),
 ('El bloque de controles aporta entre quince y cuatrocientas setenta y tres veces más variación adicional que el',
  'El bloque de controles aporta entre quince y cuatrocientas ochenta veces más variación adicional que el'),
 # C19 bold paragraph in 3.6
 ('\\textbf{Sobre las decisiones de construcción. Las reglas', '\\textbf{Sobre las decisiones de construcción.} Las reglas'),
]
for old, new in fix:
    body = once(body, old, new)
# the bold paragraph in 3.6 ends with a stray closing brace of \textbf
body = once(body, 'la magnitud de ese efecto no se determina con la información disponible.}',
            'la magnitud de ese efecto no se determina con la información disponible.')

# 2.4.2: definitions written as "Término - texto"
i0, i1 = body.index('\\subseccion{2.4.2'), body.index('\\subseccion{2.4.3')
sec = re.sub(r'^([A-ZÁÉÍÓÚ][^\n$]{2,60}?) - ', r'\\textbf{\1.} ', body[i0:i1], flags=re.M)
sec = re.sub(r'^\\textbf\{([^}]*?) -\} ', r'\\textbf{\1.} ', sec, flags=re.M)
body = body[:i0] + sec + body[i1:]
body = re.sub(r'\\textbf\{([^}]*?) -\} ', r'\\textbf{\1.} ', body)

# Notation table asked for by the advisor ("definir variables y convenciones al principio")
NOTACION = r"""
\tabla{3.2}{Notación y convenciones}
\begin{longtable}{@{}p{0.24\linewidth}p{0.71\linewidth}@{}}
\toprule
\textbf{Símbolo} & \textbf{Significado y convención}\\
\midrule
\endhead
\bottomrule
\endlastfoot
$i$, $j$ & Serie accionaria ($i$) y empresa ($j$); $i\in j$ indica que la serie $i$ pertenece a la empresa $j$.\\
$s\in\{SIC, LOCAL\}$ & Segmento: valores de emisores domiciliados fuera de México ($SIC$) o en México ($LOCAL$).\\
$d$, $t$ & Sesión bursátil del calendario del apartado 3.2.3 ($d$) y periodo de agregación ($t$): mes o ejercicio, según se indique.\\
$V_{s,t}$, $V_{i,d}$ & Importe operado del segmento $s$ en $t$ (suma de BMV y BIVA, ecuación sin número del apartado 3.3.1) y de la serie $i$ en $d$. En pesos corrientes salvo el superíndice $real$; en la ecuación (6) en millones de pesos.\\
$PSIC_t$ & Participación del SIC, ecuación (1). En el panel entra en múltiplos de diez puntos porcentuales.\\
$INPC_t$ & Índice nacional de precios al consumidor, reexpresado con promedio de 2018 igual a 100.\\
$I_{i,d}$, $R_{i,d}$ & Índice de rendimiento total con dividendos brutos y rendimiento diario, ecuación (4).\\
$ASK_{i,d}$, $BID_{i,d}$ & Posturas de venta y de compra al cierre de la sesión.\\
$\mathcal{D}_{i,t}$, $D_{i,t}$ & Conjunto y número de sesiones operadas (importe positivo) de la serie $i$ en $t$.\\
$N^{vigentes}_{i,t}$, $NOOP_{i,d}$ & Sesiones de vigencia de la serie (apartado 3.2.4) e indicador de sesión vigente sin importe operado.\\
$MC_{j,t}$, $\overline{MC}_{j,t}$ & Capitalización de la empresa y su promedio diario en $t$, en pesos corrientes.\\
$G_j$ & Tercil fijo de tamaño, ecuación (9).\\
$L_{i,t}$ & Indicador de liquidez: $SPREAD$, $\ln ILLIQ$, $ZRET$ o $TURN$, ecuaciones (5) a (8).\\
$X_{i,t}$, $Z_t$ & Controles propios de la emisora (volatilidad idiosincrática: desviación estándar de los residuos del modelo de mercado en el mes, mínimo diez sesiones) y comunes (rendimiento compuesto y volatilidad diaria del IPC en el mes; TIIE a 28 días, tipo de cambio y VIX, promedios mensuales); apartado 3.3.4.\\
$\alpha_i$, $\delta t$ & Efecto fijo por emisora y tendencia lineal.\\
Porcentajes y logaritmos & Los indicadores se reportan en porcentaje; $\ln$ es el logaritmo natural; pp significa puntos porcentuales.\\
\end{longtable}
\emph{Nota.} Elaboración propia. Definiciones verificadas reproduciendo el procedimiento de cálculo (\texttt{pipeline/}). El importe de la ecuación (6) y la capitalización están en pesos corrientes; la versión en pesos de 2018 se usa en el apartado 4.4.4.
"""
body = once(body, '\\subseccion{3.3.1 Operatividad del mercado y participación del SIC}',
            NOTACION + '\n\\subseccion{3.3.1 Operatividad del mercado y participación del SIC}')
# the old Tabla 3.2 becomes 3.3
body = once(body, '\\tabla{3.2}{Síntesis de las principales variables}', '\\tabla{3.3}{Síntesis de las principales variables}')

# --------------------------------------------------------------------------
# References: hanging indent; flag citations without an entry
# --------------------------------------------------------------------------
r0 = body.index('\\capitulo{REFERENCIAS}')
head, refs = body[:r0], body[r0:]
refs = refs.replace('\\textbf{Referencias académicas}', '\\subseccionsinindice{Referencias académicas}\n\\begin{referencias}')
refs = refs.replace('\\textbf{Referencias institucionales y documentales}',
                    '\\end{referencias}\n\\subseccionsinindice{Referencias institucionales y documentales}\n\\begin{referencias}')
refs = refs.rstrip() + '\n\\end{referencias}\n'
refs += r"""
\pendiente{Citas sin entrada en esta lista: Doar (2023); Comisión Nacional Bancaria y de Valores (s.\,f.); Bolsa Mexicana de Valores (2004); Centro de Estudios de las Finanzas Públicas (2024); Junta de Gobernadores del Sistema de la Reserva Federal (s.\,f.), que en la lista aparece como Bernanke (2013); The White House (2025), que en la lista aparece como 2025a y 2025b. La Ley del Mercado de Valores se cita como Cámara de Diputados (2025) y en la lista aparece con 2005. Entradas de la lista que no se citan en el texto: OMS (2009b), Secretaría de Salud (2020a, 2020b), Secretaría de Hacienda y Crédito Público (2020), Rich (s.\,f.), Federal Reserve Bank of New York (s.\,f.), INEGI (2025), Grupo BMV (2025), Banco de México (2021) y (s.\,f., anuncios de política monetaria), BIVA (s.\,f.), BMV (s.\,f., dos entradas), Instituto Federal Electoral (2012), INE (2025), TEPJF (2024). Citar o eliminar.}
"""
body = head + refs

# --------------------------------------------------------------------------
# Annexes
# --------------------------------------------------------------------------
# C22: the CPI used in the computations is the terminal series MXCPI, not Banxico's file
annex = once(annex, 'El índice nacional de precios al consumidor procede del Banco de México y el producto',
             'El índice nacional de precios al consumidor es la serie MXCPI de la terminal \\corregido{decía ``procede del Banco de México''; '
             'el cálculo reproducido usa MXCPI, que coincide con el apartado 3.2.1} y el producto')
annex = once(annex, 'la magnitud de ese efecto se reporta en el capítulo IV.',
             'la magnitud de ese efecto es mínima: de 465,306 sesiones operadas de las series principales con rendimiento medible, '
             'en 553 (0.12\\%) el precio no cambia y el índice sí; la proporción de rendimientos cero es 15.60\\% con el índice '
             'y 15.66\\% con el precio \\corregido{decía que la cifra se reporta en el capítulo IV, donde no aparece; '
             'calculada con los datos de la autora}.')
for mod, sec in (('4. Primera hipótesis', '4.3'), ('5. Segunda hipótesis', '4.4'),
                 ('6. Tercera hipótesis', '4.5'), ('7. Validación', '4.1 y 4.5.6')):
    i = annex.index(mod)
    j = annex.index('apartado 4.x', i)
    annex = annex[:j] + 'apartado ' + sec + annex[j + len('apartado 4.x'):]
assert '4.x' not in annex

body = re.sub(r'\n{3,}', '\n\n', body)
annex = re.sub(r'\n{3,}', '\n\n', annex)
for name, t in (('cuerpo.tex', body), ('anexos.tex', annex)):
    assert '\\hl{' not in t and 'Actualizar con F9' not in t, name
    (out / name).write_text(t, encoding='utf8')
print('ok', len(body), len(annex))
