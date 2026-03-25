# Laboratorio: Pipeline ETL Modular en Apache Airflow

Este laboratorio enseña cómo construir un pipeline ETL modular en Apache Airflow, usando una arquitectura profesional donde:

- **El DAG principal solo orquesta**: No contiene lógica de procesamiento.
- **Las tareas están en scripts separados**: Facilita la reutilización y el mantenimiento.
- **Cada script tiene una responsabilidad clara**: Sigue el principio de responsabilidad única.

Los estudiantes usarán **Cursor** o **Antigravity** para generar parte del código automáticamente.

## Objetivos de aprendizaje

Al terminar este ejercicio el estudiante podrá:
- Crear un DAG de Airflow.
- Separar lógica ETL en módulos.
- Entender la arquitectura de pipelines.
- Orquestar tareas con dependencias.
- Ejecutar DAGs desde la UI de Airflow.
- Usar IA (Cursor, Antigravity) para acelerar el desarrollo.

## Arquitectura del ejercicio

El ejercicio tendrá la siguiente estructura:

```text
etls_fad
│
├─ dags
│  └─ ejercicio_api_etl
│     ├─ dag_api_etl.py
│     └─ tasks
│        ├─ A_extract.py
│        ├─ B_transform.py
│        └─ C_load.py
│
├─ data
│  ├─ raw
│  └─ processed
```

### Concepto clave

El **DAG NO contiene lógica de negocio**. Solo define el flujo:
`extract >> transform >> load`

La lógica vive en los módulos de tareas:
- `tasks/A_extract.py`
- `tasks/B_transform.py`
- `tasks/C_load.py`

## Caso de estudio

Usaremos la API pública: [JSONPlaceholder - Posts](https://jsonplaceholder.typicode.com/posts)

**Datos de ejemplo:**
- `userId`
- `id`
- `title`
- `body`

**Pipeline final:**
`API` → `Extract` → `Transform` → `Load CSV`

---

## Paso 1 — Crear estructura del ejercicio

Primero crear la estructura base.

### Prompt para Cursor, Antigravity
> Quiero crear la estructura base de un ejercicio de Apache Airflow.
> 
> Dentro de la carpeta `dags` crea una carpeta llamada: `ejercicio_api_etl`.
> 
> Dentro crea `dag_api_etl.py` y una carpeta llamada `tasks`.
> 
> Dentro de `tasks` crea tres archivos:
> - `A_extract.py`
> - `B_transform.py`
> - `C_load.py`
> 
> No agregues código todavía. Solo crea la estructura.

---

## Paso 2 — Crear la función de Extract

Ahora vamos a implementar **Extract**.
**Responsabilidad**: Descargar datos de la API.

### Prompt para Cursor
> Abre el archivo: `dags/ejercicio_api_etl/tasks/A_extract.py`
> 
> Este archivo debe
> 
> 1. Llamar a la API: `https://jsonplaceholder.typicode.com/posts`
> 2. Descargar los primeros 20 registros.
> 3. Incluye comentarios detallados de que hace cada parte del código explicando cada paso. 

---



## Paso 3 — Crear el DAG principal (Probar Extract)

Ahora crearemos el DAG padre inicial para orquestar y probar únicamente la tarea de extracción. El DAG no contiene lógica de negocio, solo llama a la función.

### Prompt para Cursor
> Abre el archivo: `dags/ejercicio_api_etl/dag_api_etl.py`
> 
> Crea un DAG de Apache Airflow.
> - `dag_id`: `api_posts_etl`
> - `schedule`: `*/3 * * * *`
> - `catchup`: `False`
> - `start_date`: `2026-01-01`
> 
> Importa la tarea programada anteriormente (`A_extract.py`). Importa correctamente.
> 
> Crea la tarea `extract_task`.
> 
> **Flujo del DAG**: por ahora solo será la extracción.
> Incluye comentarios explicando el flujo.

---

## Paso 4 — Crear Transform

**Transform** limpia y prepara los datos.
**Responsabilidad**: Transformar datos.

**Transformaciones:**
- Seleccionar columnas específicas.
- Limpiar texto.
- Crear columna nueva.

### Prompt para Cursor
> Utiliza los resultados de la extracción en el paso 3.
> Abre el archivo: `dags/ejercicio_api_etl/tasks/B_transform.py`
> 
> 1. Seleccionar las columnas: `userId`, `id`, `title`.
> 2. Limpiar `title` convirtiendo todo a minisculas y eliminando espacios.
> 3. Crear una columna nueva llamada `title_length` que sea la longitud del título.
> Agrega comentarios explicando cada paso.

---

## Paso 5 — Actualizar el DAG (Probar Transform)

Actualizaremos el DAG para incluir la nueva tarea de transformación y probarla.

### Prompt para Cursor
> Abre el archivo: `dags/ejercicio_api_etl/dag_api_etl.py`
> 
> Actualiza el DAG para:
> 1. Importar la tarea de transformación (`B_transform.py`).
> 2. Crear la tarea `transform_task`.
> 3. Agregar la tarea al flujo: `extract >> transform`.
> 4. Asegurar que `transform_task` reciba los datos de `extract_task`.

---

## Paso 6 — Crear Load

**Load** guarda el resultado final.
**Responsabilidad**: Persistir datos.

### Prompt para Cursor
> Abre el archivo: `dags/ejercicio_api_etl/tasks/C_load.py`
> 
> 
> 1. Guardar un CSV en: mi carpeta daga.
> 2. Crear la carpeta si no existe.
> 3. No incluir el índice.
> 4. Devolver la ruta del archivo.
> Agrega comentarios explicando cada paso.

---

## Paso 7 — Actualizar el DAG (Completar Pipeline)

Finalmente, actualizaremos el DAG para incluir la tarea de carga y completar el pipeline ETL.

### Prompt para Cursor
> Abre el archivo: `dags/ejercicio_api_etl/dag_api_etl.py`
> 
> Actualiza el DAG para:
> 1. Importar la tarea de carga (`C_load.py`).
> 2. Crear la tarea `load_task`.
> 3. Completar el flujo del DAG: `extract >> transform >> load`.
> 4. Asegurar que `load_task` reciba los datos de `transform_task`.
> 5. Incluye comentarios finales explicando el flujo completo.

---

## Paso 8 — Ejecutar el DAG

1. Levantar Airflow o verifica que ya este levantado, el docker compose esta en la raiz del proyecto. 
2. Abrir la UI: [http://localhost:8080](http://localhost:8080)
3. Buscar: `api_posts_etl`.
4. Activar el DAG.
5. Presionar: **Trigger DAG**.

---

## Paso 9 — Verificar resultados

Revisar la carpeta: `data/processed`.
Debe aparecer: `posts_processed.csv`.

**Columnas esperadas:**
- `userId`
- `id`
- `title`
- `title_length`

---

## Buenas prácticas aprendidas

- **Separación de responsabilidades**:
  - `Extract` → Obtener datos.
  - `Transform` → Limpiar datos.
  - `Load` → Guardar datos.

- **Arquitectura modular**:
  ```text
  DAG
  └── tasks
  ```
  Esto permite:
  - Facilitar el **testing**.
  - Fomentar la **reutilización**.
  - Simplificar el **mantenimiento**.
