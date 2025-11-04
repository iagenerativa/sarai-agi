#!/usr/bin/env bash
set -euo pipefail

# Script de arranque para preparar el entorno de desarrollo de SARAi_AGI
echo "[SARAi_AGI] Preparando entorno..."

python_exe="python3"
if ! command -v "$python_exe" >/dev/null 2>&1; then
  echo "Error: Python 3 no está instalado en el PATH." >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual .venv"
  "$python_exe" -m venv .venv
else
  echo "Entorno virtual .venv ya existe"
fi

source .venv/bin/activate
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
  echo "Instalando dependencias declaradas"
  pip install -r requirements.txt
else
  echo "No se encontró requirements.txt; omitiendo instalación de dependencias"
fi

echo "[SARAi_AGI] Entorno listo. Recuerda ejecutar: source .venv/bin/activate"
