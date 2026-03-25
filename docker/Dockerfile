FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
RUN pip install --no-cache-dir pandas numpy pyarrow psycopg2-binary

# Copiar proyecto
COPY scripts/ /app/scripts/
COPY data/raw/ /app/data/raw/

# Ejecutar pipeline al iniciar
CMD ["python3", "scripts/run_all_pipeline.py"]
