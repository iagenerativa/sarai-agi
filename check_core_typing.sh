#!/bin/bash
echo "🔍 SARAi AGI - Verificación de Typing (Core Modules)"
echo "================================================="
python3 -m mypy $(cat .mypy_files | xargs echo) --show-error-codes --ignore-missing-imports
echo "================================================="
if [ $? -eq 0 ]; then
    echo "✅ CORE MODULES: Typing verificado exitosamente"
else
    echo "❌ CORE MODULES: Errores de typing detectados"
fi
