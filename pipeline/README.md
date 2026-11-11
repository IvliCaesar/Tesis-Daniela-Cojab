# Procedimiento de cálculo reconstruido

Código que reproduce, desde los libros de Bloomberg hasta el panel de la tercera hipótesis, las
salidas de la autora (`m1_*` a `m7_*.parquet`). Se escribió entre el 9 y el 10 de noviembre de 2026
a partir del texto de la tesis y se ajustó contra los archivos de la autora hasta reproducirlos.
Documenta las reglas efectivas, que en varios puntos el texto de la tesis no dice.

Los datos de Bloomberg tienen licencia y **no** están en el repositorio. Todo se corre sobre la
carpeta donde la autora guarda sus libros y sus `.parquet`:

```
bash pipeline/correr_todo.sh <datos> <salida>      # módulos 1, 2, 4, 3 y 7, y la validación
python pipeline/huellas.py <datos> pipeline/archivos_entrada.csv   # tabla de huellas SHA-256
python scripts/verifica_h3.py <salida>
```

| Módulo | Archivo | Entrada |
|---|---|---|
| 1. Lectura | `m1_lectura.py` | Los tres libros de Bloomberg (`archivos_entrada.csv`) |
| 2. Depuración | `m2_depuracion.py` | Salidas del módulo 1 y el mapa serie–empresa |
| 4. Participación | `m4_participacion.py` | Salidas de los módulos 1 y 2 |
| 3. Medidas | `m3_medidas.py` | Salidas del módulo 2 |
| 7. Panel de H3 | `m7_panel.py` | Salidas de los módulos 2, 3 y 4, y el libro de índices |
| Validación | `validar.py` | Las salidas de la autora |

El mapa serie–empresa (`m2_mapa_empresas.parquet`) es la única entrada que no sale de los libros
descargados: viene del campo ID_BB_COMPANY de la terminal, que en los libros aparece como
"#N/A Requesting Data".

## Qué se reproduce desde los libros (validación del 10 de noviembre de 2026)

| Salida | Coincidencia |
|---|---|
| Universo de liquidez, tres centros | 100% de filas y campos |
| Universo local, tres centros | 100% de importe y volumen; 56 filas de más y 1.5% de precios de cierre distintos en certificados estructurados (CAPI, CAPGLP, GLOB), campo que no entra en ningún resultado |
| Universo SIC, tres centros | 100% de los campos con `Universo SIC emisoras.xlsx`; falta solo la serie TXG1N (1,393 filas, 34 sesiones con importe), vacía en ese libro y tomada por la autora de otra extracción |
| Calendario, panel diario, series principales, vigencia, capitalización, terciles | 100% |
| Participación del SIC | Diaria 99.3%; diferencias de a lo sumo 0.0005 puntos porcentuales al año, todas por la serie TXG1N |
| Medidas mensuales | 99.1% a 100% por columna; 210 filas de la autora no se generan |
| Medidas anuales | 100%, salvo Amihud (94.7%): el recorte anual no se reproduce con tres variantes |
| Panel de H3 | Medidas 99%+, volatilidad idiosincrática 99.92%; factores comunes exactos en los meses sin feriado |
| Tablas 4.11 y 4.13 | Amihud 0.2224 contra 0.2235; incrementos de R² 3.84/9.73/8.00/4.45 contra 3.84/9.75/8.02/4.46 |

## Reglas efectivas que el texto de la tesis no dice

* **Feriados.** El módulo 1 solo conserva las fechas en que alguna serie del consolidado del mismo
  libro tuvo importe positivo. Los feriados traen capitalizaciones arrastradas; esas 414 filas del
  universo de liquidez explican que la Tabla 4.1 de la tesis cuente 1,100,258 registros en BMV y el
  archivo final 1,099,844.
* **Universo local.** Se completa con 19 series del universo de liquidez que su libro no trae (CPO y
  series UB, entre ellas CEMEXCPO, FEMSAUB y TLEVICPO).
* **Vigencia.** La ventana es de doce meses de calendario, no de 365 días.
* **Terciles.** Promedio del logaritmo de la capitalización **diaria** de la empresa.
* **Rendimientos cero.** La columna `sesiones_vigentes` ya viene neta de las sesiones sin rendimiento
  medible; con eso la razón coincide con la ecuación 8.
* **Factores mensuales.** Tasa = TIIE a 28 días; tasa, tipo de cambio y VIX son promedios sobre
  todos los días hábiles del calendario con el último valor arrastrado; el rendimiento del mercado
  es el compuesto del IPC en el mes. El INPC es la serie MXCPI de la terminal, no el archivo de
  Banxico (la nota de la Tabla B.3 decía lo contrario).
* **Volatilidad idiosincrática.** Residuos del modelo de mercado con todas las sesiones vigentes con
  rendimiento medible, mínimo diez por mes, dos grados de libertad descontados. Desde 2019 eso incluye
  sesiones sin operación con índice arrastrado (rendimiento cero) y la deja entre 10% y 13% por debajo
  de la versión con solo sesiones operadas; antes de 2019 ambas son idénticas. Con la versión
  consistente los coeficientes de H3 casi no cambian (rendimientos cero: 0.0113 a 0.0087, p de 0.005
  a 0.028).
* **Fechas de quiebre.** Las de la Tabla 4.12 no se reproducen con el algoritmo del cuaderno de la
  autora (cambio de nivel, mínimo de doce meses, BIC).

## Tabla de archivos de entrada

`archivos_entrada.csv`: nombre, tamaño, fecha, SHA-256 y papel de cada archivo descargado el 9 de
noviembre de 2026. Solo cuatro libros entran en los cálculos (liquidez, local, SIC e índices), más
`PIBA_2.csv` para el PIB. Hay siete duplicados exactos y varias versiones anteriores del universo.
