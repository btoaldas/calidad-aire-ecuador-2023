
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
