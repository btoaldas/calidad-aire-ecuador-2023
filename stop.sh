#!/bin/bash
cd "$(dirname "$0")"
echo "Deteniendo servicios..."
docker compose down
echo "Servicios detenidos."
