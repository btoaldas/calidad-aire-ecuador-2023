# Guia de Uso: Docker y Dashboard

## 1. Arquitectura de Despliegue

El proyecto se despliega con **Docker Compose** usando dos servicios:

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                      │
│                                                      │
│  ┌──────────────────┐    ┌────────────────────────┐  │
│  │   PostgreSQL 15   │    │    Nginx (Dashboard)   │  │
│  │   (Alpine)        │    │    (Alpine)            │  │
│  │                   │    │                        │  │
│  │  DB: calidad_     │    │  Sirve: index.html     │  │
│  │      aire_dw      │    │  + data/gold/*.csv     │  │
│  │                   │    │                        │  │
│  │  Puerto: 5433     │    │  Puerto: 8085          │  │
│  └──────────────────┘    └────────────────────────┘  │
│         ▲                          ▲                  │
│         │                          │                  │
│    init.sql +                 index.html +            │
│    load_data.sql              gold CSVs               │
└─────────────────────────────────────────────────────┘
```

## 2. Como Levantar los Servicios

### Prerequisitos
- Docker Desktop instalado y corriendo
- Docker Compose (incluido en Docker Desktop)
- Python 3.8+ (para ejecutar el pipeline ETL localmente)

### Paso 1: Ejecutar el Pipeline ETL
```bash
cd /opt/cedia-datos-ia
python3 scripts/run_all_pipeline.py
```

Esto genera:
- Datos en todas las capas (Raw → Bronze → Silver → Gold)
- Archivos SQL para PostgreSQL (`docker/init.sql` y `docker/load_data.sql`)

**Salida esperada:**
```
PIPELINE COMPLETADO EN ~12 SEGUNDOS
Resultado: 7 exitosos, 0 fallidos
```

### Paso 2: Levantar Docker Compose
```bash
docker compose up -d
```

**Que sucede internamente:**
1. Se crea un volumen persistente `pgdata` para PostgreSQL
2. Se inicia el contenedor `calidad_aire_db` (PostgreSQL 15 Alpine)
3. PostgreSQL ejecuta automaticamente:
   - `docker/init.sql`: Crea el Star Schema (tablas, indices, vistas)
   - `docker/load_data.sql`: Inserta 6,973 registros (dimensiones + hechos)
4. Cuando PostgreSQL reporta `healthy`, se inicia `calidad_aire_dashboard` (Nginx Alpine)
5. Nginx sirve el dashboard HTML y los archivos CSV de la capa Gold

### Paso 3: Verificar que todo funciona
```bash
# Ver estado de contenedores
docker compose ps

# Verificar PostgreSQL
docker exec calidad_aire_db psql -U admin -d calidad_aire_dw -c "SELECT count(*) FROM fact_medicion_diaria;"

# Abrir dashboard en el navegador
# http://localhost:8085
```

### Para detener los servicios
```bash
docker compose down        # Detiene (conserva datos)
docker compose down -v     # Detiene y elimina volumen de datos
```

---

## 3. PostgreSQL - Star Schema HEFESTO

### Conexion
| Parametro | Valor |
|-----------|-------|
| Host | localhost |
| Puerto | 5433 |
| Base de datos | calidad_aire_dw |
| Usuario | admin |
| Password | cedia2023 |

### Herramientas para conectarse
- **psql** (terminal): `psql -h localhost -p 5433 -U admin -d calidad_aire_dw`
- **DBeaver**: Crear conexion PostgreSQL con los datos de arriba
- **pgAdmin**: Registrar servidor con los datos de arriba

### Esquema de Base de Datos

**Dimensiones (3 tablas):**
| Tabla | Registros | Descripcion |
|-------|-----------|-------------|
| `dim_tiempo` | 365 | Cada dia del 2023 con mes, trimestre, temporada |
| `dim_ciudad` | 10 | Ciudades con poblacion, area, zona climatica |
| `dim_estacion` | 18 | Estaciones de monitoreo con tipo y ubicacion |

**Tablas de Hechos (2 tablas):**
| Tabla | Registros | Grano | Descripcion |
|-------|-----------|-------|-------------|
| `fact_medicion_diaria` | 6,570 | 1 medicion/estacion/dia | PM2.5, PM10, NO2, SO2, O3, CO + meteo |
| `fact_calidad_ciudad` | 10 | 1 registro/ciudad/ano | ICAC, ranking, clasificacion, excedencias |

**Vistas Analiticas (2 vistas):**
| Vista | Descripcion |
|-------|-------------|
| `v_resumen_calidad_ciudad` | Ranking completo con todas las metricas por ciudad |
| `v_promedio_mensual` | Promedios mensuales de contaminantes y clima por ciudad |

### Consultas de ejemplo

```sql
-- Top 3 ciudades con peor calidad del aire
SELECT ciudad, icac, clasificacion, dias_excede_pm25
FROM v_resumen_calidad_ciudad
LIMIT 3;

-- Comparar temporada lluviosa vs seca en Quito
SELECT temporada,
       round(avg(pm25_promedio)::numeric, 1) as pm25_prom,
       round(avg(temp_promedio)::numeric, 1) as temp_prom
FROM v_promedio_mensual
WHERE ciudad = 'Quito'
GROUP BY temporada;

-- Estaciones industriales vs urbanas
SELECT e.tipo,
       round(avg(m.pm25_ug_m3)::numeric, 1) as pm25_prom,
       round(avg(m.no2_ug_m3)::numeric, 1) as no2_prom
FROM fact_medicion_diaria m
JOIN dim_estacion e ON m.id_estacion = e.id_estacion
GROUP BY e.tipo
ORDER BY pm25_prom DESC;
```

---

## 4. Dashboard Interactivo

### Acceso
Abrir en el navegador: **http://localhost:8085**

### Tecnologias
- **HTML5 + CSS3**: Interfaz responsive con tema oscuro
- **Chart.js 4.4**: Libreria de graficos interactivos
- **ChartDataLabels**: Plugin para etiquetas en barras

### Componentes del Dashboard

#### 4.1 Tarjetas KPI (parte superior)
Cinco indicadores clave actualizados con filtros:
- **Estaciones Monitoreadas**: 18 en 10 ciudades
- **PM2.5 Promedio Nacional**: Promedio del contaminante mas danino
- **Dias Excedencia PM2.5**: Porcentaje de dias que superan norma OMS (15 ug/m3 diario)
- **Mejor Calidad**: Ciudad con menor ICAC
- **Peor Calidad**: Ciudad con mayor ICAC

#### 4.2 Filtros Interactivos
Tres selectores en la cabecera:
- **Ciudad**: Filtra por ciudad especifica o muestra todas
- **Contaminante**: Cambia el contaminante en el grafico mensual (PM2.5, PM10, NO2, SO2, O3, CO)
- **Temporada**: Filtra por temporada lluviosa (Ene-May) o seca (Jun-Nov)

#### 4.3 Graficos (7 visualizaciones)

| # | Grafico | Tipo | Pregunta que responde |
|---|---------|------|----------------------|
| 1 | Ranking ICAC | Barras horizontales | ¿Que ciudad tiene peor calidad? |
| 2 | Tabla de detalle | Tabla con badges | Metricas clave por ciudad |
| 3 | Evolucion mensual | Lineas (multi-serie) | ¿Como cambia la calidad en el ano? |
| 4 | Contaminacion por zona | Barras agrupadas | ¿Zona industrial o urbana contamina mas? |
| 5 | Clima vs contaminacion | Scatter (burbujas) | ¿El clima afecta la contaminacion? |
| 6 | Ratio vs OMS | Radar | ¿Cuantas veces excede la norma cada ciudad? |
| 7 | Excedencias PM2.5 | Barras verticales | ¿Cuantos dias se supera el limite? |

#### 4.4 Interactividad
- **Hover**: Tooltips con datos detallados en cada grafico
- **Click en leyenda**: Oculta/muestra series en graficos multi-linea
- **Filtros**: Actualizan KPIs y recrean el grafico mensual en tiempo real
- **Responsive**: Se adapta a pantallas pequenas (mobile/tablet)

### Capturas del Dashboard

Las capturas para evidencia se pueden generar abriendo http://localhost:8085 en el
navegador y usando la funcion de captura de pantalla del sistema operativo.
Se recomienda guardar al menos 2 capturas en la carpeta `dashboards/`.

---

## 5. Flujo Completo de Uso

```
1. git clone <repo>
2. cd calidad-aire-ecuador-2023
3. pip install pandas numpy pyarrow
4. python3 scripts/run_all_pipeline.py    # Pipeline ETL (12 seg)
5. docker compose up -d                    # Levantar servicios
6. Abrir http://localhost:8085             # Ver dashboard
7. psql -h localhost -p 5433 -U admin -d calidad_aire_dw  # Consultar DB
```
