"""
Script: 02_bronze_meteorologia.py
Capa: BRONZE (Raw → Bronze)
Fuente: datos_meteorologicos_2023.json

Propósito:
  Leer el archivo JSON crudo de datos meteorológicos (INAMHI) y convertirlo
  a formato tabular (Parquet + CSV) en la capa Bronze.

Prompt utilizado (IA):
  "Lee el JSON de datos meteorológicos, extrae los registros del array
   'registros', conviértelos a DataFrame y guárdalos en formato Parquet
   y CSV en la capa Bronze."
"""
import os
import sys
import pandas as pd
from utils import get_logger, safe_read_json, get_project_root

logger = get_logger("bronze_meteorologia")
root = get_project_root()

RAW_DIR = os.path.join(root, "data", "raw")
BRZ_DIR = os.path.join(root, "data", "bronze")
os.makedirs(BRZ_DIR, exist_ok=True)

logger.info(">>> CAPA BRONZE: Datos Meteorológicos <<<")

# Leer fuente JSON cruda
input_file = os.path.join(RAW_DIR, "datos_meteorologicos_2023.json")
data = safe_read_json(input_file, logger)

if data is None:
    logger.error("No se pudieron leer los datos meteorológicos.")
    sys.exit(1)

# Extraer registros del JSON
registros = data.get("registros", [])
logger.info(f"Registros extraídos del JSON: {len(registros):,}")

df = pd.DataFrame(registros)
df['fecha'] = pd.to_datetime(df['fecha'])

logger.info(f"Columnas: {list(df.columns)}")
logger.info(f"Tipos:\n{df.dtypes}")

# Guardar en Bronze
csv_out = os.path.join(BRZ_DIR, "brz_meteorologia_2023.csv")
parquet_out = os.path.join(BRZ_DIR, "brz_meteorologia_2023.parquet")

df.to_csv(csv_out, index=False)
df.to_parquet(parquet_out, index=False)

logger.info(f"Bronze CSV: {csv_out}")
logger.info(f"Bronze Parquet: {parquet_out}")
logger.info(f"Total registros: {len(df):,}")
logger.info(">>> BRONZE METEOROLOGÍA COMPLETADO <<<")
