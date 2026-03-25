#!/bin/bash
echo "=========================================="
echo "  Calidad del Aire Ecuador 2023"
echo "  Proyecto Integrador - Arquitectura de Datos"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Verificar Docker
if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker no esta instalado."
    exit 1
fi

# Ejecutar pipeline ETL primero (genera datos y SQL)
echo "[1/3] Ejecutando pipeline ETL..."
python3 scripts/run_all_pipeline.py

echo ""
echo "[2/3] Levantando servicios Docker..."
docker compose up -d --build

echo ""
echo "[3/3] Esperando PostgreSQL..."
sleep 5

echo ""
echo "=========================================="
echo "  SERVICIOS ACTIVOS:"
echo "  Dashboard:  http://localhost:8085"
echo "  PostgreSQL: localhost:5433"
echo "    DB: calidad_aire_dw"
echo "    User: admin / Pass: cedia2023"
echo "=========================================="
