"""
Script: 05_silver_integrated.py
Capa: SILVER - Integrated (Standardized → Integrated)

Propósito:
  Integrar las fuentes estandarizadas en una vista unificada:
  - Cruzar mediciones de aire con datos meteorológicos (por estación y fecha)
  - Enriquecer con datos de población por ciudad
  - Generar agregaciones clave por ciudad y mes

Prompt utilizado (IA):
  "Integra las tres fuentes estandarizadas: mediciones de aire, meteorología
   y población. El cruce principal es por estacion_id y fecha. Genera un
   dataset integrado a nivel diario y otro agregado a nivel mensual por ciudad."
"""
import os
import sys
import pandas as pd
import numpy as np
from utils import get_logger, safe_read_parquet, get_project_root

logger = get_logger("silver_integrated")
root = get_project_root()

STD_DIR = os.path.join(root, "data", "silver", "standardized")
INT_DIR = os.path.join(root, "data", "silver", "integrated")
os.makedirs(INT_DIR, exist_ok=True)

logger.info(">>> CAPA SILVER INTEGRATED: Integración de Fuentes <<<")

# =============================================================================
# 1. LECTURA DE FUENTES ESTANDARIZADAS
# =============================================================================
df_med = safe_read_parquet(os.path.join(STD_DIR, "std_mediciones_aire_2023.parquet"), logger)
df_meteo = safe_read_parquet(os.path.join(STD_DIR, "std_meteorologia_2023.parquet"), logger)
df_pob = safe_read_parquet(os.path.join(STD_DIR, "std_poblacion_ciudades.parquet"), logger)

if df_med is None:
    logger.error("Tabla de mediciones es obligatoria. Abortando.")
    sys.exit(1)

# =============================================================================
# 2. INTEGRACIÓN DIARIA: Mediciones + Meteorología
# =============================================================================
logger.info("\n--- Integrando mediciones con meteorología ---")

# Join por estacion_id y fecha
cols_meteo = ['fecha', 'estacion_id', 'temperatura_c', 'humedad_relativa_pct',
              'velocidad_viento_km_h', 'precipitacion_mm', 'presion_hpa',
              'radiacion_solar_w_m2', 'condicion_climatica']

if df_meteo is not None:
    df_daily = df_med.merge(
        df_meteo[cols_meteo],
        on=['fecha', 'estacion_id'],
        how='left'
    )
    logger.info(f"Join diario: {len(df_daily):,} filas (antes: {len(df_med):,})")
    sin_meteo = df_daily['temperatura_c'].isnull().sum()
    logger.info(f"Registros sin datos meteorológicos: {sin_meteo}")
else:
    df_daily = df_med.copy()
    logger.warning("Sin datos meteorológicos, continuando solo con mediciones.")

# Guardar integración diaria
out_daily = os.path.join(INT_DIR, "int_diario_aire_meteo_2023.parquet")
df_daily.to_parquet(out_daily, index=False)
logger.info(f"Guardado: {out_daily}")

# =============================================================================
# 3. AGREGACIÓN MENSUAL POR CIUDAD
# =============================================================================
logger.info("\n--- Generando agregación mensual por ciudad ---")

agg_dict = {
    'pm25_ug_m3': ['mean', 'max', 'min', 'std'],
    'pm10_ug_m3': ['mean', 'max'],
    'no2_ug_m3':  ['mean', 'max'],
    'so2_ug_m3':  ['mean', 'max'],
    'o3_ug_m3':   ['mean', 'max'],
    'co_mg_m3':   ['mean', 'max'],
    'estacion_id': 'nunique',
}

if 'temperatura_c' in df_daily.columns:
    agg_dict['temperatura_c'] = 'mean'
    agg_dict['precipitacion_mm'] = 'sum'
    agg_dict['humedad_relativa_pct'] = 'mean'

df_monthly = df_daily.groupby(['ciudad', 'provincia', 'mes']).agg(agg_dict).reset_index()

# Aplanar columnas multi-nivel
df_monthly.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col
                       for col in df_monthly.columns]

# Renombrar para claridad
rename_map = {
    'pm25_ug_m3_mean': 'pm25_promedio',
    'pm25_ug_m3_max': 'pm25_maximo',
    'pm25_ug_m3_min': 'pm25_minimo',
    'pm25_ug_m3_std': 'pm25_desv_std',
    'pm10_ug_m3_mean': 'pm10_promedio',
    'pm10_ug_m3_max': 'pm10_maximo',
    'no2_ug_m3_mean': 'no2_promedio',
    'no2_ug_m3_max': 'no2_maximo',
    'so2_ug_m3_mean': 'so2_promedio',
    'so2_ug_m3_max': 'so2_maximo',
    'o3_ug_m3_mean': 'o3_promedio',
    'o3_ug_m3_max': 'o3_maximo',
    'co_mg_m3_mean': 'co_promedio',
    'co_mg_m3_max': 'co_maximo',
    'estacion_id_nunique': 'num_estaciones',
}
if 'temperatura_c_mean' in df_monthly.columns:
    rename_map['temperatura_c_mean'] = 'temperatura_promedio'
    rename_map['precipitacion_mm_sum'] = 'precipitacion_total_mm'
    rename_map['humedad_relativa_pct_mean'] = 'humedad_promedio'

df_monthly.rename(columns=rename_map, inplace=True)

# Redondear
for col in df_monthly.select_dtypes(include=[np.number]).columns:
    df_monthly[col] = df_monthly[col].round(2)

# Enriquecer con población
if df_pob is not None:
    df_monthly = df_monthly.merge(
        df_pob[['ciudad', 'poblacion_2023', 'area_km2', 'densidad_hab_km2']],
        on='ciudad',
        how='left'
    )
    logger.info(f"Enriquecido con datos de población")

out_monthly = os.path.join(INT_DIR, "int_mensual_ciudad_2023.parquet")
df_monthly.to_parquet(out_monthly, index=False)
logger.info(f"Guardado: {out_monthly} ({len(df_monthly):,} filas)")

# =============================================================================
# 4. AGREGACIÓN ANUAL POR CIUDAD (para ranking)
# =============================================================================
logger.info("\n--- Generando agregación anual por ciudad ---")

df_annual = df_daily.groupby(['ciudad', 'provincia']).agg({
    'pm25_ug_m3': 'mean',
    'pm10_ug_m3': 'mean',
    'no2_ug_m3': 'mean',
    'so2_ug_m3': 'mean',
    'o3_ug_m3': 'mean',
    'co_mg_m3': 'mean',
    'estacion_id': 'nunique',
}).reset_index()

df_annual.columns = ['ciudad', 'provincia', 'pm25_anual', 'pm10_anual', 'no2_anual',
                      'so2_anual', 'o3_anual', 'co_anual', 'num_estaciones']

for col in df_annual.select_dtypes(include=[np.number]).columns:
    df_annual[col] = df_annual[col].round(2)

if df_pob is not None:
    df_annual = df_annual.merge(
        df_pob[['ciudad', 'poblacion_2023', 'area_km2', 'densidad_hab_km2']],
        on='ciudad',
        how='left'
    )

out_annual = os.path.join(INT_DIR, "int_anual_ciudad_2023.parquet")
df_annual.to_parquet(out_annual, index=False)
logger.info(f"Guardado: {out_annual} ({len(df_annual):,} filas)")

logger.info("\n>>> SILVER INTEGRATED COMPLETADO <<<")
