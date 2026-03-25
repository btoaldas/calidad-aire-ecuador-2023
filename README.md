# Calidad del Aire en Ecuador 2023 - Proyecto Integrador

**Curso:** Fundamentos de Arquitectura de Datos para IA (CEDIA)
**Alumno:** Alberto Alexander Aldas Villacres
**Fecha:** Marzo 2026

---

## 1. Descripcion del Proyecto

### Caso de Negocio

Ecuador carece de una plataforma unificada de monitoreo de calidad del aire. Las mediciones
existen en estaciones dispersas operadas por gobiernos locales (como la red REMMAQ de Quito),
pero no existe una vista integrada que permita comparar ciudades entre si, identificar patrones
estacionales, ni relacionar la contaminacion con variables demograficas o climaticas.

### Objetivo del Analisis

Construir una arquitectura de datos que integre mediciones de calidad del aire, datos
meteorologicos y demograficos de 10 ciudades del Ecuador, para generar indicadores
comparables que permitan priorizar ciudades segun su riesgo ambiental.

### Preguntas del Negocio

1. **¿Cuales ciudades tienen la peor calidad del aire?** → Ranking por Indice Compuesto (ICAC)
2. **¿Como varia la calidad del aire a lo largo del ano?** → Evolucion mensual por ciudad
3. **¿Que tipo de zona (industrial/urbana) contamina mas?** → Analisis por tipo de estacion
4. **¿Existe relacion entre clima y contaminacion?** → Correlacion temperatura-PM2.5
5. **¿Cuantos dias se superan los limites OMS?** → Excedencias por ciudad

---

## 2. Fuentes de Datos

### Fuente 1: Mediciones de Calidad del Aire (CSV)

- **Archivo:** `data/raw/mediciones_calidad_aire_2023.csv`
- **Formato:** CSV
- **Registros:** 6,570 (18 estaciones x 365 dias)
- **Contaminantes:** PM2.5, PM10, NO2, SO2, O3, CO
- **Origen:** Datos sinteticos basados en patrones reales de la red REMMAQ (Quito)
  y reportes de la OMS. Se intentó obtener datos de OpenAQ pero Ecuador no tiene
  estaciones registradas en dicha plataforma.

### Fuente 2: Datos Meteorologicos (JSON)

- **Archivo:** `data/raw/datos_meteorologicos_2023.json`
- **Formato:** JSON
- **Registros:** 6,570
- **Variables:** Temperatura, humedad, viento, precipitacion, presion, radiacion
- **Origen:** Datos sinteticos basados en patrones climaticos del INAMHI

### Fuente 3: Poblacion por Ciudades (CSV)

- **Archivo:** `data/raw/ciudades_poblacion.csv`
- **Formato:** CSV
- **Registros:** 20 ciudades
- **Origen:** Proyecciones INEC, Censo 2022, revision 2024

---

## 3. Modelo Conceptual

El modelo conceptual representa las entidades del dominio y sus relaciones a nivel de negocio.
Fue diseñado con Mermaid.

**Ver diagrama completo en:** `docs/diagramas_mermaid.md` - Seccion 1

Las entidades principales son:
- **ESTACION_MONITOREO**: Puntos de medicion distribuidos en las ciudades
- **MEDICION_AIRE**: Registros diarios de contaminantes
- **DATO_METEOROLOGICO**: Condiciones climaticas asociadas
- **CIUDAD / PROVINCIA**: Dimension geografica
- **CONTAMINANTE**: Tipos de contaminantes medidos (PM2.5, PM10, etc.)
- **POBLACION**: Datos demograficos para calculos per capita

---

## 4. Modelo Logico

El modelo logico detalla la estructura con PKs, FKs, tipos de datos y cardinalidad.
Sigue un Star Schema basado en la **metodologia HEFESTO**.

**Ver diagrama completo en:** `docs/diagramas_mermaid.md` - Seccion 2 y 4

### Tablas de Hechos:
- `fact_medicion_diaria`: Grano = 1 medicion por estacion por dia
- `fact_calidad_ciudad`: Grano = 1 registro por ciudad por ano (agregado)

### Dimensiones:
- `dim_tiempo`: Fecha, mes, trimestre, temporada (lluviosa/seca)
- `dim_ciudad`: Geografia + poblacion + densidad
- `dim_estacion`: Puntos de monitoreo con tipo y ubicacion

---

## 5. Arquitectura por Capas

### RAW (datos crudos)
Archivos originales sin transformacion.
```
data/raw/
├── mediciones_calidad_aire_2023.csv    (Fuente 1)
├── datos_meteorologicos_2023.json      (Fuente 2)
├── ciudades_poblacion.csv              (Fuente 3)
└── catalogo_estaciones.json            (Referencia)
```

### BRONZE (conversion de formato)
Datos convertidos a Parquet manteniendo estructura original.
```
data/bronze/
├── brz_mediciones_aire_2023.parquet
├── brz_meteorologia_2023.parquet
└── brz_poblacion_ciudades.parquet
```

### SILVER - Standardized (limpieza)
Datos limpios con interpolacion de nulos, validacion de rangos,
campos derivados (categoria calidad, dia de semana, trimestre).
```
data/silver/standardized/
├── std_mediciones_aire_2023.parquet
├── std_meteorologia_2023.parquet
└── std_poblacion_ciudades.parquet
```

### SILVER - Integrated (integracion)
Fuentes cruzadas: mediciones + meteorologia por estacion/fecha,
enriquecidas con datos de poblacion. Agregaciones mensual y anual.
```
data/silver/integrated/
├── int_diario_aire_meteo_2023.parquet
├── int_mensual_ciudad_2023.parquet
└── int_anual_ciudad_2023.parquet
```

### GOLD (vistas analiticas)
Respuestas directas a las preguntas del negocio:
```
data/gold/
├── gold_ranking_calidad_aire_ciudad.csv    (Pregunta 1)
├── gold_evolucion_mensual.csv              (Pregunta 2)
├── gold_contaminacion_por_tipo_zona.csv    (Pregunta 3)
├── gold_clima_contaminacion.csv            (Pregunta 4)
└── gold_excedencias_oms.csv                (Pregunta 5)
```

---

## 6. Uso de Prompting (IA)

Todo el proyecto fue desarrollado con apoyo de **Claude (Anthropic)** como asistente de IA.
A continuacion se documentan los principales prompts utilizados:

### Prompt 1: Generacion de datos realistas
> "Genera datos sinteticos realistas de calidad del aire para 10 ciudades del Ecuador
>  con 18 estaciones de monitoreo. Los datos deben reflejar patrones estacionales
>  conocidos (temporada lluviosa vs seca), diferencias entre zonas industriales y
>  urbanas, y rangos consistentes con informes de la red REMMAQ de Quito."

### Prompt 2: Diseno del pipeline ETL
> "Diseña un pipeline ETL con capas Bronze, Silver (standardized + integrated) y Gold,
>  siguiendo el patron del repositorio riesgo_vial_territorial del profesor Mendieta."

### Prompt 3: Limpieza Silver
> "Aplica limpieza a los datos Bronze: interpola nulos por estacion, valida rangos
>  fisicamente posibles segun OMS, clasifica calidad del aire por PM2.5."

### Prompt 4: Integracion de fuentes
> "Integra mediciones de aire con meteorologia (join por estacion_id y fecha),
>  enriquece con poblacion por ciudad, genera agregaciones mensuales y anuales."

### Prompt 5: Capa Gold e indicadores
> "Calcula el Indice Compuesto de Calidad del Aire (ICAC) normalizando cada
>  contaminante contra las guias OMS 2021, con PM2.5 al 40% de peso."

### Prompt 6: Star Schema HEFESTO
> "Diseña un Star Schema para PostgreSQL con fact_medicion_diaria y fact_calidad_ciudad,
>  dimensiones de tiempo, ciudad y estacion, siguiendo metodologia HEFESTO."

### Prompt 7: Dashboard interactivo
> "Crea un dashboard HTML con Chart.js: ranking horizontal, evolucion mensual,
>  scatter de clima vs contaminacion, radar de ratios OMS, y tabla de detalle."

---

## 7. Resultados Principales

| Ciudad | PM2.5 Anual | ICAC | Clasificacion | Excedencia OMS |
|--------|-------------|------|---------------|----------------|
| Esmeraldas | 22.03 ug/m3 | 3.270 | Mala | 82.7% dias |
| Cuenca | 21.42 ug/m3 | 3.189 | Mala | 78.4% dias |
| Quito | 17.87 ug/m3 | 2.710 | Mala | 66.5% dias |
| Manta | 15.30 ug/m3 | 2.226 | Moderada | 52.6% dias |
| Santo Domingo | 14.71 ug/m3 | 2.236 | Moderada | 53.7% dias |

**Hallazgos clave:**
- Todas las ciudades exceden la guia anual OMS de PM2.5 (5 ug/m3)
- Las zonas industriales registran hasta 40% mas PM2.5 que las urbanas
- La temporada seca (jun-nov) presenta 20-25% mas contaminacion
- Las ciudades costeras con industria (Esmeraldas) tienen peor calidad
- No se observa correlacion directa entre temperatura y PM2.5

---

## 8. Como Ejecutar

### Requisitos
- Docker y Docker Compose
- Python 3.8+ (para pipeline ETL local)

### Inicio rapido
```bash
chmod +x start.sh stop.sh
./start.sh
```

### Acceso
- **Dashboard:** http://localhost:8085
- **PostgreSQL:** localhost:5433
  - DB: `calidad_aire_dw`
  - Usuario: `admin`
  - Password: `cedia2023`

### Pipeline ETL manual
```bash
python3 scripts/run_all_pipeline.py
```

---

## 9. Estructura del Proyecto

```
calidad-aire-ecuador-2023/
├── README.md                          <- Este archivo
├── start.sh / stop.sh                 <- Scripts de inicio y parada
├── docker-compose.yml                 <- Orquestacion Docker
│
├── docs/
│   ├── diagramas_mermaid.md           <- Codigo Mermaid de todos los diagramas
│   ├── modelo_conceptual.png          <- Imagen modelo conceptual
│   ├── modelo_logico.png              <- Imagen modelo logico
│   ├── star_schema_hefesto.png        <- Imagen Star Schema HEFESTO
│   ├── GUIA_DOCKER_DASHBOARD.md       <- Guia de uso Docker y Dashboard
│   ├── CHECKLIST_CUMPLIMIENTO.md      <- Checklist de requisitos del proyecto
│   └── recursos_curso/               <- Materiales de referencia del curso
│
├── data/
│   ├── raw/                           <- Datos crudos originales
│   ├── bronze/                        <- Conversion a Parquet
│   ├── silver/
│   │   ├── standardized/              <- Datos limpios
│   │   └── integrated/                <- Datos integrados
│   └── gold/                          <- Vistas analiticas finales (CSV + Parquet)
│
├── scripts/
│   ├── utils.py                       <- Utilidades compartidas
│   ├── 00_generate_raw_data.py        <- Generacion de datos sinteticos
│   ├── 01_bronze_mediciones.py        <- Bronze: mediciones aire
│   ├── 02_bronze_meteorologia.py      <- Bronze: meteorologia
│   ├── 03_bronze_poblacion.py         <- Bronze: poblacion
│   ├── 04_silver_standardized.py      <- Silver: limpieza y validacion
│   ├── 05_silver_integrated.py        <- Silver: integracion de fuentes
│   ├── 06_gold_layer.py               <- Gold: vistas analiticas finales
│   ├── 07_export_postgresql.py        <- Export: DDL + datos SQL
│   └── run_all_pipeline.py            <- Orquestador del pipeline
│
├── docker/
│   ├── Dockerfile                     <- Imagen del pipeline
│   ├── init.sql                       <- DDL Star Schema HEFESTO
│   └── load_data.sql                  <- 6,973 sentencias INSERT
│
└── dashboards/
    └── index.html                     <- Dashboard interactivo
```

---

## 10. Tecnologias Utilizadas

| Componente | Tecnologia |
|------------|-----------|
| Lenguaje | Python 3.11 |
| Pipeline ETL | pandas, numpy, pyarrow |
| Base de datos | PostgreSQL 15 (Star Schema HEFESTO) |
| Dashboard | HTML5, CSS3, Chart.js 4.4 |
| Contenedores | Docker, Docker Compose |
| Diagramas | Mermaid |
| IA / Prompting | Claude (Anthropic) |
| Servidor web | Nginx Alpine |
