"""
Script: 06_gold_layer.py
Capa: GOLD (Silver Integrated → Gold)

Propósito:
  Generar las vistas analíticas finales que responden las preguntas de negocio:
  1. Ranking de ciudades por calidad del aire
  2. Evolución mensual de contaminantes
  3. Análisis por tipo de estación
  4. Relación clima-contaminación
  5. Índice compuesto de calidad del aire

Prompt utilizado (IA):
  "A partir de los datos integrados, genera la capa Gold con:
   - Un fact table de riesgo ambiental por ciudad con ranking
   - Vistas resumen mensuales
   - Indicadores compuestos de calidad del aire
   - Todo en Parquet y CSV para consumo analítico."
"""
import os
import sys
import pandas as pd
import numpy as np
from utils import get_logger, safe_read_parquet, get_project_root

logger = get_logger("gold_layer")
root = get_project_root()

INT_DIR = os.path.join(root, "data", "silver", "integrated")
GLD_DIR = os.path.join(root, "data", "gold")
os.makedirs(GLD_DIR, exist_ok=True)

logger.info(">>> CAPA GOLD: Vistas Analíticas Finales <<<")

# Leer fuentes integradas
df_annual = safe_read_parquet(os.path.join(INT_DIR, "int_anual_ciudad_2023.parquet"), logger)
df_monthly = safe_read_parquet(os.path.join(INT_DIR, "int_mensual_ciudad_2023.parquet"), logger)
df_daily = safe_read_parquet(os.path.join(INT_DIR, "int_diario_aire_meteo_2023.parquet"), logger)

if df_annual is None:
    logger.error("Datos anuales obligatorios. Abortando.")
    sys.exit(1)

# =============================================================================
# 1. FACT: RANKING DE CALIDAD DEL AIRE POR CIUDAD
# Responde: ¿Cuáles ciudades tienen peor calidad del aire?
# =============================================================================
logger.info("\n1. Generando ranking de calidad del aire por ciudad...")

df_rank = df_annual.copy()

# Calcular Índice de Calidad del Aire Compuesto (ICAC)
# Normalización sobre guías OMS 2021:
#   PM2.5 anual: 5 µg/m³ | PM10 anual: 15 µg/m³ | NO2 anual: 10 µg/m³
#   SO2 diario: 40 µg/m³ | O3 (8h): 100 µg/m³
oms = {'pm25': 5, 'pm10': 15, 'no2': 10, 'so2': 40, 'o3': 100}

df_rank['ratio_pm25_oms'] = (df_rank['pm25_anual'] / oms['pm25']).round(2)
df_rank['ratio_pm10_oms'] = (df_rank['pm10_anual'] / oms['pm10']).round(2)
df_rank['ratio_no2_oms'] = (df_rank['no2_anual'] / oms['no2']).round(2)

# ICAC: promedio ponderado de ratios vs OMS
# PM2.5 tiene mayor peso por su impacto en salud (40%)
df_rank['icac'] = (
    df_rank['ratio_pm25_oms'] * 0.40 +
    df_rank['ratio_pm10_oms'] * 0.25 +
    df_rank['ratio_no2_oms'] * 0.20 +
    (df_rank['so2_anual'] / oms['so2']) * 0.08 +
    (df_rank['o3_anual'] / oms['o3']) * 0.07
).round(3)

# Ranking (1 = peor calidad)
df_rank['ranking_calidad'] = df_rank['icac'].rank(ascending=False, method='min').astype(int)

# Clasificación
def clasificar_icac(icac):
    if icac <= 1.5: return "Aceptable"
    elif icac <= 2.5: return "Moderada"
    elif icac <= 3.5: return "Mala"
    else: return "Muy mala"

df_rank['clasificacion'] = df_rank['icac'].apply(clasificar_icac)

df_rank = df_rank.sort_values('ranking_calidad')

out_rank = os.path.join(GLD_DIR, "gold_ranking_calidad_aire_ciudad.parquet")
out_rank_csv = os.path.join(GLD_DIR, "gold_ranking_calidad_aire_ciudad.csv")
df_rank.to_parquet(out_rank, index=False)
df_rank.to_csv(out_rank_csv, index=False)
logger.info(f"Guardado: {out_rank}")
logger.info(f"Top 5 peor calidad:\n{df_rank[['ciudad', 'icac', 'ranking_calidad', 'clasificacion']].head()}")

# =============================================================================
# 2. EVOLUCIÓN MENSUAL DE CONTAMINANTES
# Responde: ¿Cómo varía la calidad del aire a lo largo del año?
# =============================================================================
logger.info("\n2. Generando evolución mensual de contaminantes...")

if df_monthly is not None:
    out_monthly = os.path.join(GLD_DIR, "gold_evolucion_mensual.parquet")
    out_monthly_csv = os.path.join(GLD_DIR, "gold_evolucion_mensual.csv")
    df_monthly.to_parquet(out_monthly, index=False)
    df_monthly.to_csv(out_monthly_csv, index=False)
    logger.info(f"Guardado: {out_monthly} ({len(df_monthly):,} filas)")

# =============================================================================
# 3. ANÁLISIS POR TIPO DE ESTACIÓN
# Responde: ¿Qué tipo de zona (industrial/urbana) contamina más?
# =============================================================================
logger.info("\n3. Generando análisis por tipo de zona...")

if df_daily is not None:
    # Necesitamos el tipo de estación del catálogo
    import json
    cat_path = os.path.join(root, "data", "raw", "catalogo_estaciones.json")
    with open(cat_path, 'r') as f:
        cat = json.load(f)

    df_est = pd.DataFrame(cat['estaciones'])
    df_tipo = df_daily.merge(df_est[['id', 'tipo', 'zona', 'altitud']],
                              left_on='estacion_id', right_on='id', how='left')

    df_tipo_agg = df_tipo.groupby(['tipo', 'zona']).agg({
        'pm25_ug_m3': 'mean',
        'pm10_ug_m3': 'mean',
        'no2_ug_m3': 'mean',
        'so2_ug_m3': 'mean',
        'co_mg_m3': 'mean',
    }).round(2).reset_index()

    out_tipo = os.path.join(GLD_DIR, "gold_contaminacion_por_tipo_zona.parquet")
    out_tipo_csv = os.path.join(GLD_DIR, "gold_contaminacion_por_tipo_zona.csv")
    df_tipo_agg.to_parquet(out_tipo, index=False)
    df_tipo_agg.to_csv(out_tipo_csv, index=False)
    logger.info(f"Guardado: {out_tipo}")

# =============================================================================
# 4. RELACIÓN CLIMA - CONTAMINACIÓN (mensual)
# Responde: ¿El clima afecta la calidad del aire?
# =============================================================================
logger.info("\n4. Generando análisis clima-contaminación...")

if df_daily is not None and 'temperatura_c' in df_daily.columns:
    df_clima = df_daily.groupby(['ciudad', 'mes']).agg({
        'pm25_ug_m3': 'mean',
        'temperatura_c': 'mean',
        'precipitacion_mm': 'sum',
        'humedad_relativa_pct': 'mean',
        'velocidad_viento_km_h': 'mean',
    }).round(2).reset_index()

    df_clima.columns = ['ciudad', 'mes', 'pm25_promedio', 'temp_promedio',
                         'precipitacion_total', 'humedad_promedio', 'viento_promedio']

    out_clima = os.path.join(GLD_DIR, "gold_clima_contaminacion.parquet")
    out_clima_csv = os.path.join(GLD_DIR, "gold_clima_contaminacion.csv")
    df_clima.to_parquet(out_clima, index=False)
    df_clima.to_csv(out_clima_csv, index=False)
    logger.info(f"Guardado: {out_clima}")

# =============================================================================
# 5. DÍAS CON EXCEDENCIA DE NORMAS OMS
# Responde: ¿Cuántos días se superan los límites?
# =============================================================================
logger.info("\n5. Generando análisis de excedencias OMS...")

if df_daily is not None:
    # PM2.5 diario OMS: 15 µg/m³ | PM10 diario: 45 µg/m³
    df_exc = df_daily.copy()
    df_exc['excede_pm25_oms'] = df_exc['pm25_ug_m3'] > 15
    df_exc['excede_pm10_oms'] = df_exc['pm10_ug_m3'] > 45

    df_exc_city = df_exc.groupby('ciudad').agg({
        'excede_pm25_oms': ['sum', 'mean'],
        'excede_pm10_oms': ['sum', 'mean'],
        'fecha': 'count'
    }).reset_index()

    df_exc_city.columns = ['ciudad', 'dias_excede_pm25', 'pct_excede_pm25',
                            'dias_excede_pm10', 'pct_excede_pm10', 'total_dias']
    df_exc_city['pct_excede_pm25'] = (df_exc_city['pct_excede_pm25'] * 100).round(1)
    df_exc_city['pct_excede_pm10'] = (df_exc_city['pct_excede_pm10'] * 100).round(1)

    out_exc = os.path.join(GLD_DIR, "gold_excedencias_oms.parquet")
    out_exc_csv = os.path.join(GLD_DIR, "gold_excedencias_oms.csv")
    df_exc_city.to_parquet(out_exc, index=False)
    df_exc_city.to_csv(out_exc_csv, index=False)
    logger.info(f"Guardado: {out_exc}")
    logger.info(f"\nExcedencias PM2.5 OMS:\n{df_exc_city[['ciudad','dias_excede_pm25','pct_excede_pm25']].to_string()}")

logger.info("\n>>> CAPA GOLD COMPLETADA <<<")
logger.info(f"Archivos generados en: {GLD_DIR}")
