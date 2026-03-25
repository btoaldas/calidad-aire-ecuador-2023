"""
Script: run_all_pipeline.py
Orquestador principal del pipeline ETL completo.

Ejecuta secuencialmente todos los scripts del pipeline:
  Bronze → Silver (Standardized) → Silver (Integrated) → Gold → Export PostgreSQL
"""
import os
import subprocess
import time
from utils import get_logger

logger = get_logger("run_all_pipeline")

PIPELINE_SCRIPTS = [
    # Capa Bronze (Raw → Bronze)
    "01_bronze_mediciones.py",
    "02_bronze_meteorologia.py",
    "03_bronze_poblacion.py",

    # Capa Silver Standardized (Bronze → Silver limpio)
    "04_silver_standardized.py",

    # Capa Silver Integrated (Silver → Silver integrado)
    "05_silver_integrated.py",

    # Capa Gold (Silver → Gold analítico)
    "06_gold_layer.py",

    # Export a PostgreSQL (Gold → SQL)
    "07_export_postgresql.py",
]


def run_pipeline():
    logger.info("=" * 60)
    logger.info("PIPELINE ETL - CALIDAD DEL AIRE ECUADOR 2023")
    logger.info("=" * 60)

    start_global = time.time()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    failed = []

    for script in PIPELINE_SCRIPTS:
        path = os.path.join(script_dir, script)
        logger.info(f"\n[{time.strftime('%H:%M:%S')}] Ejecutando: {script}...")

        if not os.path.exists(path):
            logger.error(f"Script no encontrado: {script}")
            failed.append(script)
            continue

        try:
            start = time.time()
            subprocess.run(['python3', script], cwd=script_dir, check=True)
            elapsed = time.time() - start
            logger.info(f"OK: {script} completado en {elapsed:.2f}s")
        except subprocess.CalledProcessError as e:
            logger.error(f"FALLO: {script} (exit code: {e.returncode})")
            failed.append(script)

    total = time.time() - start_global
    logger.info("\n" + "=" * 60)
    logger.info(f"PIPELINE COMPLETADO EN {total:.2f} SEGUNDOS")
    ok = len(PIPELINE_SCRIPTS) - len(failed)
    logger.info(f"Resultado: {ok} exitosos, {len(failed)} fallidos")
    if failed:
        logger.warning(f"Fallidos: {', '.join(failed)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
