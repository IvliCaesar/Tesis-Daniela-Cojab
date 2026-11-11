# Tesis — Daniela Cojab Mizrahi

**La transformación del mercado accionario mexicano del mercado local al SIC entre 2004 y 2026.**
Tesis de licenciatura en Finanzas Cuantitativas, Universidad Panamericana.
Dirección: Laura Jiménez Casillas. Codirección: Julio César Galindo López.

## Contenido

| Carpeta | Qué es |
|---|---|
| [`tesis-sic/`](tesis-sic) | La tesis en LaTeX y PDF (plantilla de la UP), **versión de cierre** del 9 de noviembre de 2026: el texto de la autora del 6 de noviembre con las correcciones editoriales, las dos correcciones numéricas verificadas y las hipótesis reformuladas por decisión de la dirección. |
| [`propuesta/`](propuesta) | Las hipótesis reformuladas: prueba, resultado, texto adoptado y decisiones tomadas. |
| [`notas-de-clase/`](notas-de-clase) | Notas de clase sobre el tema: medición del importe operado, crecimiento, tendencias con raíz unitaria, medidas de liquidez, una variable agregada en un panel, identificación. Cronología con fuentes primarias (LMV, DOF, Reglas Operativas de la BMV, CONSAR). |
| [`pipeline/`](pipeline) | El procedimiento de cálculo completo (módulos 1 a 7), de los libros de Bloomberg al panel de la tercera hipótesis, reconstruido y validado contra las salidas de la autora; tabla de archivos de entrada con huella SHA-256 (`archivos_entrada.csv`). |
| [`scripts/`](scripts) | Conversión del `.docx`, versión de cierre, verificaciones y análisis de las notas. |

## Qué cambió en la versión de cierre

* **Hipótesis (1.5).** La hipótesis general pasa a hecho descriptivo. H1 se divide en H1a (participación) y
  H1b (importe local sobre PIB); H2 en H2a (deterioro después de 2014–2018) y H2b (tamaño, en la ventana del
  deterioro); H3 se contrasta con la descomposición de Shapley–Owen en primeras diferencias y una regla de rechazo.
* **Resultados.** Se reescriben 4.3.4, 4.4.4, 4.5.4, la síntesis 4.6 (Tabla 4.19) y las conclusiones 5.1;
  se añaden las Tablas 4.20 (tamaño en la ventana del deterioro) y 4.21 (H3 en diferencias).
* **Correcciones numéricas** verificadas con el panel de la autora: 473 → 480 y 0.349 → 0.387.
* Las demás correcciones editoriales (C1 a C22) están listadas, una por una, en `scripts/build_body_sic.py`.

## Reproducir

Los datos de Bloomberg tienen licencia y **no** están en este repositorio. Con la carpeta donde están los
libros de la autora y sus salidas:

```
bash pipeline/correr_todo.sh <datos> <salida>     # módulos 1 a 7 y validación
python pipeline/huellas.py <datos> pipeline/archivos_entrada.csv
python scripts/verifica_tesis.py <datos>
python scripts/verifica_h3.py <salida>
python scripts/notas_analisis.py <datos> notas-de-clase
```

`pipeline/README.md` resume qué se reproduce (liquidez, calendario, panel, vigencia, capitalización y terciles
al 100%; participación del SIC a 0.0005 puntos porcentuales al año) y las reglas efectivas que el texto de la
tesis no dice. Para compilar los documentos, `pdflatex` dos o tres veces en cada carpeta. La tesis se regenera
desde el `.docx` con `pandoc` + `scripts/build_body_sic.py` + `scripts/cierre_tesis.py`.

## Pendiente

* El código original de la autora, deseable para documentar la tesis (el procedimiento ya está reconstruido).
* Dos cifras marcadas en rojo en la tesis que solo el código original puede resolver: la fecha del quiebre del
  diferencial (agosto u octubre de 2014) y la proporción de observaciones sin estimación de los estimadores de
  rango (5.25% o 5.33%).
* Dedicatoria y agradecimientos.
