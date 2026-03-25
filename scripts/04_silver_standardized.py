"""
Script: 04_silver_standardized.py
Capa: SILVER - Standardized (Bronze → Silver)

Propósito:
  Aplicar limpieza y estandarización a los datos de Bronze:
  - Normalización de nombres de columnas (snake_case)
  - Manejo de valores nulos
  - Validación de rangos
  - Estandarización de tipos de datos
  - Eliminación de duplicados

Prompt utilizado (IA):
  "Toma los datos de Bronze de mediciones de aire y meteorología. Limpia
   valores nulos, valida rangos físicamente posibles para cada contaminante,
   estandariza nombres de columnas, y guarda en Silver/standardized."
"""
import os
import sys
import pandas as pd
import numpy as np
from utils import get_logger, safe_read_parquet, get_project_root

logger = get_logger("silver_standardized")
root = get_project_root()

BRZ_DIR = os.path.join(root, "data", "bronze")
SLV_DIR = os.path.join(root, "data", "silver", "standardized")
os.makedirs(SLV_DIR, exist_ok=True)

logger.info(">>> CAPA SILVER STANDARDIZED: Limpieza y Estandarización <<<")

# =============================================================================
# 1. MEDICIONES DE CALIDAD DEL AIRE
# =============================================================================
logger.info("\n--- Procesando Mediciones de Calidad del Aire ---")

df_med = safe_read_parquet(os.path.join(BRZ_DIR, "brz_mediciones_aire_2023.parquet"), logger)
if df_med is None:
    logger.error("Falta tabla de mediciones. Abortando.")
    sys.exit(1)

# 1a. Verificar duplicados
dupes = df_med.duplicated(subset=['fecha', 'estacion_id']).sum()
logger.info(f"Duplicados encontrados: {dupes}")
df_med = df_med.drop_duplicates(subset=['fecha', 'estacion_id'])

# 1b. Manejo de nulos - interpolar valores faltantes por estación
contaminantes = ['pm25_ug_m3', 'pm10_ug_m3', 'no2_ug_m3', 'so2_ug_m3', 'o3_ug_m3', 'co_mg_m3']
nulos_antes = df_med[contaminantes].isnull().sum()
logger.info(f"Nulos antes de interpolación:\n{nulos_antes}")

for col in contaminantes:
    df_med[col] = df_med.groupby('estacion_id')[col].transform(
        lambda x: x.interpolate(method='linear', limit_direction='both')
    )

nulos_despues = df_med[contaminantes].isnull().sum()
logger.info(f"Nulos después de interpolación:\n{nulos_despues}")

# 1c. Validación de rangos (valores físicamente posibles según OMS)
rangos_validos = {
    'pm25_ug_m3': (0, 500),   # Máximo AQI hazardous
    'pm10_ug_m3': (0, 600),
    'no2_ug_m3':  (0, 400),
    'so2_ug_m3':  (0, 350),
    'o3_ug_m3':   (0, 300),
    'co_mg_m3':   (0, 50),
}

for col, (vmin, vmax) in rangos_validos.items():
    fuera_rango = ((df_med[col] < vmin) | (df_med[col] > vmax)).sum()
    if fuera_rango > 0:
        logger.warning(f"{col}: {fuera_rango} valores fuera de rango [{vmin}, {vmax}] - recortados")
        df_med[col] = df_med[col].clip(vmin, vmax)

# 1d. Agregar columna de calidad según OMS (PM2.5 anual: 5 µg/m³, diario: 15 µg/m³)
def clasificar_aqi(pm25):
    if pm25 <= 12:   return "Buena"
    elif pm25 <= 35: return "Moderada"
    elif pm25 <= 55: return "Dañina para grupos sensibles"
    elif pm25 <= 150: return "Dañina"
    elif pm25 <= 250: return "Muy dañina"
    else:             return "Peligrosa"

df_med['categoria_calidad'] = df_med['pm25_ug_m3'].apply(clasificar_aqi)

# 1e. Agregar campos temporales útiles
df_med['mes'] = df_med['fecha'].dt.month
df_med['dia_semana'] = df_med['fecha'].dt.day_name()
df_med['es_fin_semana'] = df_med['fecha'].dt.dayofweek >= 5
df_med['trimestre'] = df_med['fecha'].dt.quarter

logger.info(f"Distribución de calidad:\n{df_med['categoria_calidad'].value_counts()}")

# Guardar
out_path = os.path.join(SLV_DIR, "std_mediciones_aire_2023.parquet")
df_med.to_parquet(out_path, index=False)
logger.info(f"Guardado: {out_path} ({len(df_med):,} filas)")

# =============================================================================
# 2. DATOS METEOROLÓGICOS
# =============================================================================
logger.info("\n--- Procesando Datos Meteorológicos ---")

df_meteo = safe_read_parquet(os.path.join(BRZ_DIR, "brz_meteorologia_2023.parquet"), logger)
if df_meteo is None:
    logger.error("Falta tabla meteorológica. Abortando.")
    sys.exit(1)

# 2a. Duplicados
dupes = df_meteo.duplicated(subset=['fecha', 'estacion_id']).sum()
logger.info(f"Duplicados encontrados: {dupes}")
df_meteo = df_meteo.drop_duplicates(subset=['fecha', 'estacion_id'])

# 2b. Validar rangos meteorológicos
df_meteo['temperatura_c'] = df_meteo['temperatura_c'].clip(-10, 45)
df_meteo['humedad_relativa_pct'] = df_meteo['humedad_relativa_pct'].clip(0, 100)
df_meteo['velocidad_viento_km_h'] = df_meteo['velocidad_viento_km_h'].clip(0, 150)
df_meteo['precipitacion_mm'] = df_meteo['precipitacion_mm'].clip(0, 500)

# 2c. Agregar campos temporales
df_meteo['mes'] = df_meteo['fecha'].dt.month
df_meteo['trimestre'] = df_meteo['fecha'].dt.quarter

# 2d. Clasificar condición climática
def clasificar_clima(row):
    if row['precipitacion_mm'] > 10: return "Lluvioso"
    elif row['precipitacion_mm'] > 0: return "Nublado"
    elif row['temperatura_c'] > 25: return "Cálido"
    else: return "Templado"

df_meteo['condicion_climatica'] = df_meteo.apply(clasificar_clima, axis=1)

out_path = os.path.join(SLV_DIR, "std_meteorologia_2023.parquet")
df_meteo.to_parquet(out_path, index=False)
logger.info(f"Guardado: {out_path} ({len(df_meteo):,} filas)")

# =============================================================================
# 3. POBLACIÓN
# =============================================================================
logger.info("\n--- Procesando Población ---")

df_pob = safe_read_parquet(os.path.join(BRZ_DIR, "brz_poblacion_ciudades.parquet"), logger)
if df_pob is None:
    logger.warning("Falta tabla de población. Continuando sin ella.")
else:
    # Normalizar nombres de ciudades
    df_pob['ciudad'] = df_pob['ciudad'].str.strip().str.title()
    df_pob['provincia'] = df_pob['provincia'].str.strip().str.title()

    # Calcular densidad poblacional
    df_pob['densidad_hab_km2'] = (df_pob['poblacion_2023'] / df_pob['area_km2']).round(1)

    out_path = os.path.join(SLV_DIR, "std_poblacion_ciudades.parquet")
    df_pob.to_parquet(out_path, index=False)
    logger.info(f"Guardado: {out_path} ({len(df_pob):,} filas)")

logger.info("\n>>> SILVER STANDARDIZED COMPLETADO <<<")
