#!/usr/bin/env bash
# Corre el procedimiento completo, de los libros de Bloomberg al panel de H3, y lo valida.
# Uso: bash pipeline/correr_todo.sh <carpeta con libros y salidas de la autora> <carpeta de salida>
set -euo pipefail
DATOS="$1"; SAL="$2"; AQUI="$(cd "$(dirname "$0")" && pwd)"
PY="python -E -P"
mkdir -p "$SAL"
$PY "$AQUI/m1_lectura.py"       "$DATOS" "$SAL" liq loc sic
$PY "$AQUI/m2_depuracion.py"    "$SAL" "$DATOS/m2_mapa_empresas.parquet" "$SAL"
$PY "$AQUI/m4_participacion.py" "$SAL" "$SAL"
$PY "$AQUI/m3_medidas.py"       "$SAL" "$SAL"
$PY "$AQUI/m7_panel.py"         "$DATOS" "$SAL" "$DATOS/indices, macroeconomicos y AMIB DD.xlsx"
$PY "$AQUI/validar.py" "$DATOS" "$SAL" \
    m1_liq_glob.parquet m1_liq_bmv.parquet m1_liq_biva.parquet \
    m1_loc_glob.parquet m1_loc_bmv.parquet m1_loc_biva.parquet \
    m1_sic_glob.parquet m1_sic_bmv.parquet m1_sic_biva.parquet \
    calendario.parquet m2_panel_diario.parquet m2_series.parquet m2_vigencia.parquet \
    m2_capitalizacion.parquet m2_terciles.parquet \
    m4_psic_diaria.parquet m4_psic_mensual.parquet m4_psic_anual.parquet \
    m3_liquidez_mensual.parquet m3_liquidez_anual.parquet m7_panel_mensual.parquet
