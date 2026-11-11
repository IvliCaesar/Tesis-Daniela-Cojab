"""Versión de cierre: aplica a tesis-sic/cuerpo.tex las decisiones de la propuesta.

Uso (después de build_body_sic.py):  python scripts/cierre_tesis.py tesis-sic

Decisiones adoptadas (propuesta/Propuesta_hipotesis.tex, 9 de noviembre de 2026):
  * la hipótesis general pasa a hecho descriptivo;
  * H1 = H1a (aumento de la participación, deriva en diferencias) + H1b (importe local / PIB);
  * H2 = H2a (deterioro después de 2014-2018) + H2b (tamaño en la ventana del deterioro);
  * H3 = contribución de Shapley-Owen en primeras diferencias con regla de rechazo;
  * se reescriben 1.5, el criterio de 3.4.3, 4.3.4, 4.4.4, 4.5.4, 4.6, 5.1 y los
    resultados del resumen y del abstract.
Las cifras vienen de scripts/notas_analisis.py y scripts/verifica_h3.py sobre los datos de
la autora; las tablas nuevas se leen de notas-de-clase/tabla_tamano.tex y tabla_h3.tex.
"""
import shutil, sys
from pathlib import Path

T = Path(sys.argv[1])
NOTAS = T.parent / 'notas-de-clase'
for f in ('tabla_tamano.tex', 'tabla_h3.tex'):
    shutil.copyfile(NOTAS / f, T / f)
p = T / 'cuerpo.tex'
t = p.read_text(encoding='utf8')


def between(start, end, new):
    global t
    i = t.index(start); j = t.index(end, i + len(start))
    t = t[:i] + start + '\n\n' + new.strip() + '\n\n' + t[j:]


def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80])
    t = t.replace(a, b)


between(r'\seccion{1.5 Hipótesis}', r'\seccion{1.6', r"""
El punto de partida es un hecho y no una hipótesis: la participación del Sistema Internacional de Cotizaciones en el importe operado del mercado accionario mexicano pasó de 3.13\% en 2004 a 45.83\% en 2026, con un máximo de 55.91\% en 2020. Las hipótesis se refieren a lo que ese hecho implica.

\textbf{H1a.} La participación del Sistema Internacional de Cotizaciones aumentó entre 2004 y 2026 con una deriva positiva.

\textbf{H1b.} El importe operado real del segmento local, como proporción del producto interno bruto real, disminuyó desde su máximo del periodo.

\textbf{H2a.} La liquidez de las emisoras mexicanas se deterioró después del tramo 2014--2018.

\textbf{H2b.} Ese deterioro fue mayor en las emisoras de menor capitalización que en las de mayor capitalización.

\textbf{H3.} En los cambios mensuales, la contribución de la participación del Sistema Internacional de Cotizaciones a la variación de la liquidez de las emisoras mexicanas es menor que la del factor financiero común más importante.
""")

rep(r'\subseccion{3.4.3 Tercera hipótesis. Relación entre el SIC y la liquidez}',
    r"""\subseccion{3.4.3 Tercera hipótesis. Relación entre el SIC y la liquidez}

\textbf{Criterio de contraste adoptado.} Como la participación toma un solo valor por mes y las pruebas de raíz unitaria no permiten descartarla, la contribución de la participación se mide sobre las series mensuales en primeras diferencias: la mediana transversal de cada indicador (meses con al menos 30 emisoras) se descompone entre la participación y cinco factores comunes (rendimiento y volatilidad del IPC, VIX, Cetes a 28 días y logaritmo del tipo de cambio) con el valor de Shapley--Owen, que no depende del orden de entrada de los regresores (Huettner y Sunder, 2012). H3 se sostiene si el intervalo al 95\% por remuestreo de bloques de doce meses de la diferencia entre la contribución de la participación y la del factor común más importante queda por debajo de cero. El panel por empresa que se describe a continuación se conserva como análisis complementario.""")

between(r'\subseccion{4.3.4 Lectura de la hipótesis}', r'\seccion{4.4 ', r"""
\textbf{H1a.} La participación aumentó de 3.13\% a 45.83\%, pero la serie no permite distinguir una tendencia determinista de una caminata aleatoria con deriva. La regresión contra el tiempo del apartado 4.3.2 no es válida si la serie tiene raíz unitaria: con caminatas aleatorias del mismo largo, esa prueba encuentra una tendencia significativa en 82\% de los casos. La prueba válida es la media de las diferencias mensuales del logit de la participación, con errores de Newey--West. La deriva es positiva, de 0.151 por año, y no significativa ($p=0.303$); la más clara corresponde a 2014--2018 (0.318 por año, $p=0.078$), después de la apertura del SIC a cualquier inversionista en enero de 2014. H1a se sostiene como hecho descriptivo y no como tendencia estadística.

\textbf{H1b.} El importe operado real del segmento local sobre el producto interno bruto real, con 2004 igual a 100, llega a 353 en 2013 y baja a 175 en 2024. La tasa entre extremos de la Tabla 4.6 (4.17\% contra 1.59\% del producto) depende del año inicial: con la pendiente logarítmica de todo el periodo el segmento local crece 1.50\%, prácticamente lo mismo que la economía, y desde 2013 se contrae 4.58\% real anual. H1b se sostiene: el segmento local se expandió hasta 2013 y se contrajo frente a la economía desde entonces.
""")

between(r'\subseccion{4.4.4 Lectura de la hipótesis}', r'\seccion{4.5 ', r"""
\textbf{H2a.} Entre 2014--2018 y 2019--2025 la iliquidez de Amihud aumentó 0.322 unidades logarítmicas ($p$ ajustada 0.001) y la rotación disminuyó 0.48 puntos porcentuales ($p$ ajustada 0.025), mientras que el diferencial aumentó 0.22 puntos con $p$ ajustada de 0.079 (Tabla 4.9). Dentro del tramo 2019--2025 las pruebas de tendencia detectan deterioro en los cuatro indicadores (Tabla 4.8). H2a se sostiene.

\textbf{H2b.} La comparación por tamaño debe hacerse en la ventana del deterioro. La Tabla 4.10 compara 2004--2013 con 2019--2025, un periodo de mejora neta del diferencial; la Tabla 4.20 repite el contraste entre 2014--2018 y 2019--2025.

\tabla{4.20}{Cambio entre 2014--2018 y 2019--2025 por tercil de capitalización}
\begin{center}\small
\begin{tabular}{@{}llcrrr@{}}\toprule
Indicador & Grupo & $n$ (grupo / mayor) & Cambio grupo & Cambio mayor & $p$ Holm\\\midrule
\tablainput{tabla_tamano}
\bottomrule\end{tabular}
\end{center}
\emph{Nota.} Elaboración propia. Mediana del cambio por emisora; puntos porcentuales, salvo $\ln ILLIQ$ en pesos de 2018. Prueba de Mann y Whitney bilateral contra el tercil mayor, corrección de Holm sobre ocho pruebas.

El cambio fue de mayor magnitud en las emisoras de menor capitalización en la iliquidez de Amihud, los rendimientos cero y la rotación, pero con entre 25 y 43 empresas por grupo ninguna diferencia es significativa. H2b no puede confirmarse ni descartarse con estos datos. En el panel mensual, la asociación entre la participación del SIC y los rendimientos cero se concentra en el tercil menor (coeficiente 0.039, $p<0.001$, frente a 0.005 sin significancia en el tercil mayor), el único indicio de heterogeneidad por tamaño de la investigación.
""")

between(r'\subseccion{4.5.4 Lectura de la hipótesis}', r'\subseccion{4.5.5', r"""
Con el criterio del apartado 3.4.3, la Tabla 4.21 descompone la variación mensual de cada indicador en primeras diferencias.

\tabla{4.21}{Contribución de la participación del SIC en primeras diferencias}
\begin{center}\small
\begin{tabular}{@{}lrrcccrr@{}}\toprule
Indicador & $R^2$ & $\phi_{PSIC}$ & IC 95\% & Lugar & Diferencia & $\hat\beta_{PSIC}$ & $p$\\\midrule
\tablainput{tabla_h3}
\bottomrule\end{tabular}
\end{center}
\emph{Nota.} Elaboración propia, 272 meses. $R^2$ y $\phi$ en porcentaje de la varianza; ``Diferencia'': $\phi_{PSIC}$ menos el mayor $\phi$ de los factores comunes, intervalo al 95\% por remuestreo de bloques de doce meses. Coeficiente con errores de Newey--West.

La participación explica menos de un tercio de punto porcentual de la varianza mensual de los cuatro indicadores y ocupa el último o el penúltimo lugar entre seis factores; su coeficiente no es significativo en ninguno. Para el diferencial cotizado y la proporción de rendimientos cero, el intervalo de la diferencia queda por debajo de cero: H3 se sostiene. Para la iliquidez de Amihud y la rotación el intervalo incluye el cero y los factores comunes también explican poco, de modo que los datos no permiten ordenarlos.

La comparación de la Tabla 4.13 en niveles se conserva como descriptiva y no como prueba. Además de usar series integradas, su razón depende del orden de entrada: si la participación entra antes que los controles, la razón del diferencial pasa de 480 a 20 y la de Amihud de 15 a 3.7.
""")

between(r'\seccion{4.6 Síntesis de los resultados}', r'\capitulo{CAPÍTULO V', r"""
\tabla{4.19}{Resultado de las hipótesis}
\begin{center}\small
\begin{tabular}{@{}p{0.09\linewidth}p{0.55\linewidth}p{0.28\linewidth}@{}}\toprule
Hipótesis & Evidencia & Lectura\\\midrule
H1a & Participación de 3.13\% a 45.83\%; deriva del logit positiva, $p=0.303$ & Hecho descriptivo; tendencia no demostrada\\
H1b & Importe local real / PIB: 100 (2004), 353 (2013), 175 (2024) & Se sostiene desde 2013\\
H2a & Amihud y rotación empeoran entre 2014--2018 y 2019--2025; tendencias de deterioro en los cuatro indicadores después de 2018 & Se sostiene\\
H2b & Cambios mayores en el tercil menor, ninguno significativo (Tabla 4.20) & Indeterminada por falta de potencia\\
H3 & Participación en el lugar 5 o 6 de 6 factores; diferencia significativa en diferencial y rendimientos cero (Tabla 4.21) & Se sostiene en dos indicadores; indeterminada en dos\\\bottomrule
\end{tabular}
\end{center}
\emph{Nota.} Elaboración propia.

El segmento internacional ganó peso de manera sustancial y el segmento local, después de crecer más que la economía hasta 2013, se contrajo frente a ella. La liquidez de las emisoras mexicanas mejoró hasta mediados de la década de 2010 y se deterioró después. La participación del SIC acompaña esos movimientos en los niveles, pero en los cambios mensuales su contribución es pequeña frente a la de los factores financieros comunes. Los resultados describen co-movimiento y no efectos causales.
""")

i = t.index(r'\subseccion{5.1.1'); j = t.index(r'\seccion{5.2')
t = t[:i] + r"""\subseccion{5.1.1 La expansión del segmento internacional}

La participación del Sistema Internacional de Cotizaciones pasó de 3.13\% en 2004 a 45.83\% en 2026, con un máximo de 55.91\% en 2020. El avance no fue uniforme: la deriva más clara corresponde a 2014--2018, después de que la reforma financiera de enero de 2014 derogó el párrafo del artículo 264 de la Ley del Mercado de Valores que reservaba el SIC a inversionistas institucionales y calificados. El máximo de 2020--2021 coincide con la ampliación de los márgenes de operación de los valores del SIC en la Bolsa Mexicana de Valores (filtro de precio, cruces por excepción y rangos de fluctuación, entre junio y diciembre de 2020) y con la triplicación de las cuentas de personas físicas en casas de bolsa. Con una sola trayectoria de 22 años, la serie no permite distinguir una tendencia determinista de una deriva aleatoria.

El segmento local creció más que la economía hasta 2013 y desde entonces se contrajo frente a ella: su importe real sobre el producto interno bruto real perdió la mitad del nivel alcanzado. La lectura de que el segmento local creció por encima de la economía durante todo el periodo depende de tomar 2004 como año inicial.

\subseccion{5.1.2 La liquidez de las emisoras mexicanas}

Los indicadores de precio describen una forma de U: mejoran hasta mediados de la década de 2010 y se deterioran después. Entre 2014--2018 y 2019--2025 la iliquidez de Amihud aumentó y la rotación disminuyó de manera significativa, y dentro de 2019--2025 los cuatro indicadores muestran tendencias de deterioro. Los niveles de 2026 siguen siendo mejores que los de 2004 en el diferencial cotizado.

El deterioro fue de mayor magnitud en las emisoras de menor capitalización, pero con el número de empresas disponible ninguna diferencia por tamaño es estadísticamente significativa. La evidencia no permite afirmar ni descartar que las emisoras pequeñas hayan resultado más afectadas.

\subseccion{5.1.3 La magnitud de la relación}

En los cambios mensuales, la participación del SIC explica menos de un tercio de punto porcentual de la varianza de cada indicador y ocupa el último o el penúltimo lugar entre seis factores comunes. Para el diferencial cotizado y los rendimientos cero, su contribución es significativamente menor que la del factor común más importante; para la iliquidez de Amihud y la rotación, los factores comunes también explican poco y no pueden ordenarse. En el panel por empresa, la asociación con los rendimientos cero se concentra en las emisoras de menor capitalización.

\subseccion{5.1.4 Lectura conjunta}

La transformación del mercado accionario mexicano entre 2004 y 2026 tiene tres componentes: la expansión del segmento internacional, con su mayor avance después de la apertura de 2014 y un máximo en 2020--2021; la contracción relativa del segmento local desde 2013; y el deterioro de la liquidez de las emisoras mexicanas después de 2014--2018. La década de mayor crecimiento del segmento internacional coincidió con una mejora de la liquidez local, y en los cambios mensuales la participación del SIC aporta poco frente a las condiciones financieras comunes. Con un único regresor agregado, la investigación documenta co-movimiento y no efectos. Separar el papel del SIC del de la apertura de 2014, del impuesto de 10\% a las ganancias de capital en bolsa que entró en vigor el mismo año y del auge de inversionistas minoristas requiere variación entre emisoras en su exposición al segmento internacional, que se propone como continuación de este trabajo.

""" + t[j:]

i = t.index('Los resultados muestran que la participación del segmento global'); j = t.index('\n', i)
t = t[:i] + (r"Los resultados muestran que la participación del segmento global pasó de 3.13\% en 2004 a 45.83\% en 2026, con un máximo de 55.91\% en 2020, y que el segmento local creció más que la economía hasta 2013 y se contrajo frente a ella después: su importe real sobre el producto perdió la mitad del nivel alcanzado. La serie de participación no permite distinguir una tendencia determinista de una deriva aleatoria. La liquidez de las emisoras mexicanas mejoró hasta mediados de la década pasada y se deterioró después, con aumentos significativos de la iliquidez de Amihud y caídas de la rotación entre 2014--2018 y 2019--2025; el deterioro fue mayor en las emisoras pequeñas, pero sin significancia estadística. En los cambios mensuales, la participación del segmento global ocupa el último o el penúltimo lugar entre seis factores en la explicación de la liquidez, y su contribución es significativamente menor que la del factor financiero común más importante en el diferencial cotizado y en la proporción de rendimientos cero. La investigación documenta co-movimiento y no efectos causales.") + t[j:]
i = t.index("The results show that the global segment"); j = t.index('\n', i)
t = t[:i] + (r"The results show that the global segment's share rose from 3.13\% in 2004 to 45.83\% in 2026, peaking at 55.91\% in 2020, and that the local segment grew faster than the economy until 2013 and contracted relative to it thereafter, losing half of its peak ratio of real traded value to GDP. The share series cannot distinguish a deterministic trend from a random walk with drift. The liquidity of Mexican issuers improved until the middle of the past decade and deteriorated thereafter, with significant increases in Amihud illiquidity and declines in turnover between 2014--2018 and 2019--2025; the deterioration was larger for small issuers, but not statistically significant. In monthly changes, the global segment's share ranks last or next to last among six factors in explaining liquidity, and its contribution is significantly smaller than that of the most important common financial factor for the quoted spread and the proportion of zero returns. The study documents co-movement, not causal effects.") + t[j:]

p.write_text(t, encoding='utf8')
print('ok')
