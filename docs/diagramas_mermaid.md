# Diagramas del Proyecto - Mermaid

## 1. Modelo Conceptual

Este diagrama representa las entidades principales del dominio y sus relaciones
a nivel de negocio, sin detalles técnicos de implementación.

```mermaid
erDiagram
    ESTACION_MONITOREO ||--o{ MEDICION_AIRE : "registra"
    ESTACION_MONITOREO ||--o{ DATO_METEOROLOGICO : "captura"
    CIUDAD ||--o{ ESTACION_MONITOREO : "contiene"
    PROVINCIA ||--o{ CIUDAD : "agrupa"
    MEDICION_AIRE }o--|| CONTAMINANTE : "mide"
    CIUDAD ||--|| POBLACION : "tiene"
    MEDICION_AIRE }o--|| FECHA : "ocurre_en"
    DATO_METEOROLOGICO }o--|| FECHA : "registrado_en"

    ESTACION_MONITOREO {
        string nombre
        string tipo
        string zona_climatica
    }

    CIUDAD {
        string nombre
        int poblacion
    }

    MEDICION_AIRE {
        float valor
        string categoria_calidad
    }

    CONTAMINANTE {
        string nombre
        string unidad
        float limite_oms
    }

    DATO_METEOROLOGICO {
        float temperatura
        float precipitacion
        float humedad
    }
```

## 2. Modelo Lógico

Este diagrama representa la estructura de datos con claves primarias,
claves foráneas, tipos de datos y relaciones con cardinalidad.

```mermaid
erDiagram
    dim_tiempo {
        int id_tiempo PK
        date fecha
        int anio
        int mes
        string mes_nombre
        int dia
        string dia_semana
        int trimestre
        boolean es_fin_semana
        string temporada
    }

    dim_ciudad {
        int id_ciudad PK
        string ciudad
        string provincia
        int poblacion_2023
        float area_km2
        float densidad_hab_km2
        string zona_climatica
    }

    dim_estacion {
        int id_estacion PK
        string codigo
        string nombre
        string ciudad
        string tipo
        float latitud
        float longitud
        int altitud
    }

    fact_medicion_diaria {
        int id_fact PK
        int id_tiempo FK
        int id_estacion FK
        float pm25_ug_m3
        float pm10_ug_m3
        float no2_ug_m3
        float so2_ug_m3
        float o3_ug_m3
        float co_mg_m3
        float temperatura_c
        float humedad_pct
        float precipitacion_mm
        float viento_km_h
        string categoria_calidad
    }

    fact_calidad_ciudad {
        int id_fact PK
        int id_ciudad FK
        int anio
        float pm25_anual
        float pm10_anual
        float no2_anual
        float so2_anual
        float o3_anual
        float co_anual
        float icac
        int ranking_calidad
        string clasificacion
        int dias_excede_pm25
        float pct_excede_pm25
    }

    dim_tiempo ||--o{ fact_medicion_diaria : "id_tiempo"
    dim_estacion ||--o{ fact_medicion_diaria : "id_estacion"
    dim_ciudad ||--o{ fact_calidad_ciudad : "id_ciudad"
    dim_ciudad ||--o{ dim_estacion : "ciudad"
```

## 3. Arquitectura del Pipeline ETL

```mermaid
flowchart LR
    subgraph RAW["Capa RAW"]
        R1[CSV: Mediciones Aire]
        R2[JSON: Meteorología]
        R3[CSV: Población INEC]
    end

    subgraph BRONZE["Capa BRONZE"]
        B1[brz_mediciones_aire.parquet]
        B2[brz_meteorologia.parquet]
        B3[brz_poblacion_ciudades.parquet]
    end

    subgraph SILVER_STD["Silver Standardized"]
        S1[std_mediciones_aire.parquet]
        S2[std_meteorologia.parquet]
        S3[std_poblacion_ciudades.parquet]
    end

    subgraph SILVER_INT["Silver Integrated"]
        I1[int_diario_aire_meteo.parquet]
        I2[int_mensual_ciudad.parquet]
        I3[int_anual_ciudad.parquet]
    end

    subgraph GOLD["Capa GOLD"]
        G1[gold_ranking_calidad_aire.csv]
        G2[gold_evolucion_mensual.csv]
        G3[gold_contaminacion_tipo_zona.csv]
        G4[gold_clima_contaminacion.csv]
        G5[gold_excedencias_oms.csv]
    end

    subgraph CONSUME["Consumo"]
        DB[(PostgreSQL Star Schema)]
        DASH[Dashboard HTML Chart.js]
    end

    R1 --> B1
    R2 --> B2
    R3 --> B3
    B1 --> S1
    B2 --> S2
    B3 --> S3
    S1 --> I1
    S2 --> I1
    S3 --> I2
    I1 --> I2
    I1 --> I3
    I2 --> G1
    I2 --> G2
    I3 --> G1
    I1 --> G3
    I1 --> G4
    I1 --> G5
    G1 --> DB
    G2 --> DB
    G1 --> DASH
    G2 --> DASH
```

## 4. Star Schema HEFESTO

```mermaid
erDiagram
    dim_tiempo ||--o{ fact_medicion_diaria : ""
    dim_estacion ||--o{ fact_medicion_diaria : ""
    dim_ciudad ||--o{ fact_calidad_ciudad : ""

    fact_medicion_diaria {
        float pm25_ug_m3
        float pm10_ug_m3
        float no2_ug_m3
        float so2_ug_m3
        float o3_ug_m3
        float co_mg_m3
        float temperatura_c
        string categoria_calidad
    }

    fact_calidad_ciudad {
        float icac
        int ranking_calidad
        string clasificacion
        int dias_excede_pm25
    }

    dim_tiempo {
        date fecha
        string mes_nombre
        string temporada
    }

    dim_estacion {
        string nombre
        string tipo
        int altitud
    }

    dim_ciudad {
        string ciudad
        string provincia
        int poblacion_2023
    }
```
