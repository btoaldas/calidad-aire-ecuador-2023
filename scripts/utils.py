"""
Módulo de utilidades compartidas por todos los scripts del pipeline.
Proporciona logging consistente y funciones de lectura segura.
"""
import logging
import pandas as pd
import os


def get_logger(name: str) -> logging.Logger:
    """Crea un logger formateado para el pipeline."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        ))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def safe_read_csv(filepath: str, logger: logging.Logger, **kwargs) -> pd.DataFrame:
    """Lee un CSV con manejo de errores."""
    try:
        df = pd.read_csv(filepath, **kwargs)
        logger.info(f"Leído {filepath}: {len(df):,} filas x {len(df.columns)} columnas")
        return df
    except Exception as e:
        logger.error(f"Error leyendo {filepath}: {e}")
        return None


def safe_read_json(filepath: str, logger: logging.Logger) -> dict:
    """Lee un JSON con manejo de errores."""
    import json
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Leído {filepath}")
        return data
    except Exception as e:
        logger.error(f"Error leyendo {filepath}: {e}")
        return None


def safe_read_parquet(filepath: str, logger: logging.Logger) -> pd.DataFrame:
    """Lee un Parquet con manejo de errores."""
    try:
        df = pd.read_parquet(filepath)
        logger.info(f"Leído {filepath}: {len(df):,} filas x {len(df.columns)} columnas")
        return df
    except Exception as e:
        logger.error(f"Error leyendo {filepath}: {e}")
        return None


def get_project_root() -> str:
    """Retorna la raíz del proyecto."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
