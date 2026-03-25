"""
Script: 07_export_postgresql.py
Capa: EXPORT (Gold → PostgreSQL)

Propósito:
  Exportar las vistas Gold a PostgreSQL siguiendo un Star Schema
  basado en la metodología HEFESTO.

Star Schema diseñado:
  - dim_tiempo: dimensión temporal (fecha, mes, trimestre, etc.)
  - dim_ciudad: dimensión geográfica (ciudad, provincia, zona, altitud)
  - dim_estacion: dimensión de estación de monitoreo
  - dim_contaminante: dimensión de tipos de contaminantes
  - fact_medicion_diaria: tabla de hechos con mediciones
  - fact_calidad_ciudad: tabla de hechos agregada por ciudad

Prompt utilizado (IA):
  "Diseña un Star Schema siguiendo la metodología HEFESTO para un Data Warehouse
   de calidad del aire. La tabla de hechos debe ser la medición diaria con
   dimensiones de tiempo, ciudad, estación y contaminante. Genera el DDL SQL
   y el script de carga desde los Parquets de la capa Gold."
"""
import os
import sys
import pandas as pd
import json
from utils import get_logger, safe_read_parquet, get_project_root

logger = get_logger("export_postgresql")
root = get_project_root()

GLD_DIR = os.path.join(root, "data", "gold")
INT_DIR = os.path.join(root, "data", "silver", "integrated")
SQL_DIR = os.path.join(root, "docker")
os.makedirs(SQL_DIR, exist_ok=True)

logger.info(">>> EXPORT: Generando DDL y datos para PostgreSQL <<<")

# =============================================================================
# GENERAR DDL SQL (Star Schema - Metodología HEFESTO)
# =============================================================================

ddl_sql = """
-- ============================================================================
-- STAR SCHEMA: Data Warehouse de Calidad del Aire - Ecuador 2023
-- Metodología: HEFESTO
-- Motor: PostgreSQL 15+
-- ============================================================================

-- Limpieza previa
DROP TABLE IF EXISTS fact_medicion_diaria CASCADE;
DROP TABLE IF EXISTS fact_calidad_ciudad CASCADE;
DROP TABLE IF EXISTS dim_tiempo CASCADE;
DROP TABLE IF EXISTS dim_ciudad CASCADE;
DROP TABLE IF EXISTS dim_estacion CASCADE;

-- ============================================================================
-- DIMENSIONES
-- ============================================================================

-- Dimensión Tiempo
CREATE TABLE dim_tiempo (
    id_tiempo       SERIAL PRIMARY KEY,
    fecha           DATE NOT NULL UNIQUE,
    anio            INTEGER NOT NULL,
    mes             INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    mes_nombre      VARCHAR(20) NOT NULL,
    dia             INTEGER NOT NULL,
    dia_semana      VARCHAR(15) NOT NULL,
    trimestre       INTEGER NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    es_fin_semana   BOOLEAN DEFAULT FALSE,
    temporada       VARCHAR(20) NOT NULL -- 'Lluviosa' o 'Seca'
);

-- Dimensión Ciudad
CREATE TABLE dim_ciudad (
    id_ciudad       SERIAL PRIMARY KEY,
    ciudad          VARCHAR(100) NOT NULL,
    provincia       VARCHAR(100) NOT NULL,
    poblacion_2023  INTEGER,
    area_km2        FLOAT,
    densidad_hab_km2 FLOAT,
    zona_climatica  VARCHAR(20) -- 'sierra' o 'costa'
);

-- Dimensión Estación
CREATE TABLE dim_estacion (
    id_estacion     SERIAL PRIMARY KEY,
    codigo          VARCHAR(20) NOT NULL UNIQUE,
    nombre          VARCHAR(100) NOT NULL,
    ciudad          VARCHAR(100) NOT NULL,
    tipo            VARCHAR(20) NOT NULL, -- 'urbana', 'industrial', 'periurbana'
    latitud         FLOAT,
    longitud        FLOAT,
    altitud         INTEGER
);

-- ============================================================================
-- TABLAS DE HECHOS
-- ============================================================================

-- Hecho: Medición diaria por estación
-- Grano: Una medición de una estación en un día específico
CREATE TABLE fact_medicion_diaria (
    id_fact         SERIAL PRIMARY KEY,
    id_tiempo       INTEGER NOT NULL REFERENCES dim_tiempo(id_tiempo),
    id_estacion     INTEGER NOT NULL REFERENCES dim_estacion(id_estacion),
    pm25_ug_m3      FLOAT,
    pm10_ug_m3      FLOAT,
    no2_ug_m3       FLOAT,
    so2_ug_m3       FLOAT,
    o3_ug_m3        FLOAT,
    co_mg_m3        FLOAT,
    temperatura_c   FLOAT,
    humedad_pct     FLOAT,
    precipitacion_mm FLOAT,
    viento_km_h     FLOAT,
    categoria_calidad VARCHAR(40),
    UNIQUE(id_tiempo, id_estacion)
);

-- Hecho: Calidad del aire anual por ciudad (agregado)
CREATE TABLE fact_calidad_ciudad (
    id_fact         SERIAL PRIMARY KEY,
    id_ciudad       INTEGER NOT NULL REFERENCES dim_ciudad(id_ciudad),
    anio            INTEGER NOT NULL DEFAULT 2023,
    pm25_anual      FLOAT,
    pm10_anual      FLOAT,
    no2_anual       FLOAT,
    so2_anual       FLOAT,
    o3_anual        FLOAT,
    co_anual        FLOAT,
    icac            FLOAT, -- Índice Compuesto de Calidad del Aire
    ranking_calidad INTEGER,
    clasificacion   VARCHAR(20),
    dias_excede_pm25 INTEGER,
    pct_excede_pm25  FLOAT,
    UNIQUE(id_ciudad, anio)
);

-- ============================================================================
-- ÍNDICES PARA RENDIMIENTO
-- ============================================================================
CREATE INDEX idx_fact_med_tiempo ON fact_medicion_diaria(id_tiempo);
CREATE INDEX idx_fact_med_estacion ON fact_medicion_diaria(id_estacion);
CREATE INDEX idx_fact_ciudad ON fact_calidad_ciudad(id_ciudad);

-- ============================================================================
-- VISTAS ANALÍTICAS
-- ============================================================================

-- Vista: Resumen por ciudad con todas las métricas
CREATE VIEW v_resumen_calidad_ciudad AS
SELECT
    c.ciudad,
    c.provincia,
    c.poblacion_2023,
    c.zona_climatica,
    f.pm25_anual,
    f.pm10_anual,
    f.no2_anual,
    f.icac,
    f.ranking_calidad,
    f.clasificacion,
    f.dias_excede_pm25,
    f.pct_excede_pm25
FROM fact_calidad_ciudad f
JOIN dim_ciudad c ON f.id_ciudad = c.id_ciudad
ORDER BY f.ranking_calidad;

-- Vista: Promedio mensual por ciudad
CREATE VIEW v_promedio_mensual AS
SELECT
    e.ciudad,
    t.mes,
    t.mes_nombre,
    t.temporada,
    AVG(m.pm25_ug_m3) as pm25_promedio,
    AVG(m.pm10_ug_m3) as pm10_promedio,
    AVG(m.temperatura_c) as temp_promedio,
    SUM(m.precipitacion_mm) as precipitacion_total
FROM fact_medicion_diaria m
JOIN dim_tiempo t ON m.id_tiempo = t.id_tiempo
JOIN dim_estacion e ON m.id_estacion = e.id_estacion
GROUP BY e.ciudad, t.mes, t.mes_nombre, t.temporada
ORDER BY e.ciudad, t.mes;
"""

# Guardar DDL
ddl_path = os.path.join(SQL_DIR, "init.sql")
with open(ddl_path, 'w', encoding='utf-8') as f:
    f.write(ddl_sql)
logger.info(f"DDL generado: {ddl_path}")

# =============================================================================
# GENERAR SCRIPT DE CARGA DE DATOS
# =============================================================================
logger.info("\nGenerando datos de carga...")

# Leer datos para generar INSERTs
df_daily = safe_read_parquet(os.path.join(INT_DIR, "int_diario_aire_meteo_2023.parquet"), logger)
df_rank = safe_read_parquet(os.path.join(GLD_DIR, "gold_ranking_calidad_aire_ciudad.parquet"), logger)
df_exc = safe_read_parquet(os.path.join(GLD_DIR, "gold_excedencias_oms.parquet"), logger)

# Catálogo de estaciones
cat_path = os.path.join(root, "data", "raw", "catalogo_estaciones.json")
with open(cat_path, 'r') as f:
    cat = json.load(f)

# Generar SQL de datos
data_sql_lines = []
data_sql_lines.append("-- DATOS DE CARGA\n")

# 1. dim_tiempo
data_sql_lines.append("-- Dimensión Tiempo")
meses_es = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
             7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
fechas = pd.date_range('2023-01-01', '2023-12-31')
for f in fechas:
    mes_n = meses_es[f.month]
    dia_sem = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][f.dayofweek]
    trim = (f.month - 1) // 3 + 1
    fds = 'TRUE' if f.dayofweek >= 5 else 'FALSE'
    temp = 'Lluviosa' if f.month in [1,2,3,4,5,12] else 'Seca'
    data_sql_lines.append(
        f"INSERT INTO dim_tiempo (fecha, anio, mes, mes_nombre, dia, dia_semana, trimestre, es_fin_semana, temporada) "
        f"VALUES ('{f.strftime('%Y-%m-%d')}', {f.year}, {f.month}, '{mes_n}', {f.day}, '{dia_sem}', {trim}, {fds}, '{temp}');"
    )

# 2. dim_ciudad
data_sql_lines.append("\n-- Dimensión Ciudad")
ciudades_map = {}
if df_rank is not None:
    for i, row in df_rank.iterrows():
        zona = 'costa' if row['ciudad'] in ['Guayaquil','Esmeraldas','Manta','Santo Domingo'] else 'sierra'
        pob = int(row['poblacion_2023']) if pd.notna(row.get('poblacion_2023')) else 'NULL'
        area = round(row['area_km2'], 1) if pd.notna(row.get('area_km2')) else 'NULL'
        dens = round(row['densidad_hab_km2'], 1) if pd.notna(row.get('densidad_hab_km2')) else 'NULL'
        data_sql_lines.append(
            f"INSERT INTO dim_ciudad (ciudad, provincia, poblacion_2023, area_km2, densidad_hab_km2, zona_climatica) "
            f"VALUES ('{row['ciudad']}', '{row['provincia']}', {pob}, {area}, {dens}, '{zona}');"
        )

# 3. dim_estacion
data_sql_lines.append("\n-- Dimensión Estación")
for est in cat['estaciones']:
    data_sql_lines.append(
        f"INSERT INTO dim_estacion (codigo, nombre, ciudad, tipo, latitud, longitud, altitud) "
        f"VALUES ('{est['id']}', '{est['nombre']}', '{est['ciudad']}', '{est['tipo']}', "
        f"{est['lat']}, {est['lon']}, {est['altitud']});"
    )

# 4. fact_medicion_diaria (usar subqueries para IDs)
data_sql_lines.append("\n-- Tabla de Hechos: Mediciones Diarias")
data_sql_lines.append("-- Nota: Se usa INSERT con subquery para resolver IDs de dimensiones")
if df_daily is not None:
    for _, row in df_daily.iterrows():
        fecha = row['fecha'].strftime('%Y-%m-%d') if hasattr(row['fecha'], 'strftime') else str(row['fecha'])[:10]
        vals = []
        for col in ['pm25_ug_m3','pm10_ug_m3','no2_ug_m3','so2_ug_m3','o3_ug_m3','co_mg_m3']:
            vals.append(str(round(row[col], 2)) if pd.notna(row.get(col)) else 'NULL')
        for col in ['temperatura_c','humedad_relativa_pct','precipitacion_mm','velocidad_viento_km_h']:
            vals.append(str(round(row[col], 2)) if pd.notna(row.get(col)) else 'NULL')
        cat_cal = row.get('categoria_calidad', 'NULL')
        cat_val = f"'{cat_cal}'" if cat_cal != 'NULL' else 'NULL'

        data_sql_lines.append(
            f"INSERT INTO fact_medicion_diaria (id_tiempo, id_estacion, pm25_ug_m3, pm10_ug_m3, no2_ug_m3, so2_ug_m3, o3_ug_m3, co_mg_m3, temperatura_c, humedad_pct, precipitacion_mm, viento_km_h, categoria_calidad) "
            f"SELECT t.id_tiempo, e.id_estacion, {','.join(vals)}, {cat_val} "
            f"FROM dim_tiempo t, dim_estacion e "
            f"WHERE t.fecha = '{fecha}' AND e.codigo = '{row['estacion_id']}' "
            f"ON CONFLICT (id_tiempo, id_estacion) DO NOTHING;"
        )

# 5. fact_calidad_ciudad
data_sql_lines.append("\n-- Tabla de Hechos: Calidad por Ciudad (anual)")
if df_rank is not None and df_exc is not None:
    df_merged = df_rank.merge(df_exc[['ciudad','dias_excede_pm25','pct_excede_pm25']], on='ciudad', how='left')
    for _, row in df_merged.iterrows():
        dias_exc = int(row['dias_excede_pm25']) if pd.notna(row.get('dias_excede_pm25')) else 0
        pct_exc = round(row['pct_excede_pm25'], 1) if pd.notna(row.get('pct_excede_pm25')) else 0
        data_sql_lines.append(
            f"INSERT INTO fact_calidad_ciudad (id_ciudad, anio, pm25_anual, pm10_anual, no2_anual, so2_anual, o3_anual, co_anual, icac, ranking_calidad, clasificacion, dias_excede_pm25, pct_excede_pm25) "
            f"SELECT c.id_ciudad, 2023, {round(row['pm25_anual'],2)}, {round(row['pm10_anual'],2)}, "
            f"{round(row['no2_anual'],2)}, {round(row['so2_anual'],2)}, {round(row['o3_anual'],2)}, "
            f"{round(row['co_anual'],2)}, {round(row['icac'],3)}, {int(row['ranking_calidad'])}, "
            f"'{row['clasificacion']}', {dias_exc}, {pct_exc} "
            f"FROM dim_ciudad c WHERE c.ciudad = '{row['ciudad']}' "
            f"ON CONFLICT (id_ciudad, anio) DO NOTHING;"
        )

# Guardar SQL de datos
data_path = os.path.join(SQL_DIR, "load_data.sql")
with open(data_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(data_sql_lines))

logger.info(f"SQL de datos generado: {data_path}")
logger.info(f"Total sentencias INSERT: {len([l for l in data_sql_lines if l.startswith('INSERT')])}")
logger.info("\n>>> EXPORT POSTGRESQL COMPLETADO <<<")
