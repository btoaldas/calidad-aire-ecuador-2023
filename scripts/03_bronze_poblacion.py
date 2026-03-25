"""
Script: 03_bronze_poblacion.py
Capa: BRONZE (Raw → Bronze)
Fuente: ciudades_poblacion.csv

Propósito:
  Leer el archivo CSV de población por ciudades del Ecuador (basado en
  proyecciones INEC Censo 2022, revisión 2024) y convertirlo a formato
  Parquet en la capa Bronze.

Prompt utilizado (IA):
  "Lee el CSV de población por ciudades y conviértelo a Parquet en Bronze,
   asegurando que las columnas numéricas tengan el tipo correcto."
"""
import os
import sys
import pandas as pd
from utils import get_logger, safe_read_csv, get_project_root

logger = get_logger("bronze_poblacion")
root = get_project_root()

RAW_DIR = os.path.join(root, "data", "raw")
BRZ_DIR = os.path.join(root, "data", "bronze")
os.makedirs(BRZ_DIR, exist_ok=True)

logger.info(">>> CAPA BRONZE: Población por Ciudades <<<")

input_file = os.path.join(RAW_DIR, "ciudades_poblacion.csv")
df = safe_read_csv(input_file, logger)

if df is None or df.empty:
    logger.error("No se pudieron leer los datos de población.")
    sys.exit(1)

logger.info(f"Columnas: {list(df.columns)}")
logger.info(f"Ciudades: {len(df)}")

# Guardar en Bronze
csv_out = os.path.join(BRZ_DIR, "brz_poblacion_ciudades.csv")
parquet_out = os.path.join(BRZ_DIR, "brz_poblacion_ciudades.parquet")

df.to_csv(csv_out, index=False)
df.to_parquet(parquet_out, index=False)

logger.info(f"Bronze CSV: {csv_out}")
logger.info(f"Bronze Parquet: {parquet_out}")
logger.info(">>> BRONZE POBLACIÓN COMPLETADO <<<")
