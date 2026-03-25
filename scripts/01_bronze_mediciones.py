"""
Script: 01_bronze_mediciones.py
Capa: BRONZE (Raw → Bronze)
Fuente: mediciones_calidad_aire_2023.csv

Propósito:
  Leer el archivo CSV crudo de mediciones de calidad del aire y convertirlo
  a formato Parquet estandarizado en la capa Bronze. No se aplican
  transformaciones de negocio, solo conversión de formato.

Prompt utilizado (IA):
  "Lee el CSV de mediciones de calidad del aire y conviértelo a Parquet
   sin transformaciones, solo garantizando tipos de datos correctos y
   preservando la estructura original."
"""
import os
import sys
import pandas as pd
from utils import get_logger, safe_read_csv, get_project_root

logger = get_logger("bronze_mediciones")
root = get_project_root()

RAW_DIR = os.path.join(root, "data", "raw")
BRZ_DIR = os.path.join(root, "data", "bronze")
os.makedirs(BRZ_DIR, exist_ok=True)

logger.info(">>> CAPA BRONZE: Mediciones de Calidad del Aire <<<")

# Leer fuente CSV cruda
input_file = os.path.join(RAW_DIR, "mediciones_calidad_aire_2023.csv")
df = safe_read_csv(input_file, logger)

if df is None or df.empty:
    logger.error("No se pudieron leer los datos de mediciones.")
    sys.exit(1)

# Asegurar tipo fecha
df['fecha'] = pd.to_datetime(df['fecha'])

# Información del dataset
logger.info(f"Columnas: {list(df.columns)}")
logger.info(f"Tipos:\n{df.dtypes}")
logger.info(f"Nulos por columna:\n{df.isnull().sum()}")

# Guardar en Bronze (CSV + Parquet)
csv_out = os.path.join(BRZ_DIR, "brz_mediciones_aire_2023.csv")
parquet_out = os.path.join(BRZ_DIR, "brz_mediciones_aire_2023.parquet")

df.to_csv(csv_out, index=False)
df.to_parquet(parquet_out, index=False)

logger.info(f"Bronze CSV: {csv_out}")
logger.info(f"Bronze Parquet: {parquet_out}")
logger.info(f"Total registros: {len(df):,}")
logger.info(">>> BRONZE MEDICIONES COMPLETADO <<<")
