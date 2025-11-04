#!/usr/bin/env bash
# Script de inicialización de repositorio nuevo en GitHub

set -euo pipefail

REPO_NAME="SARAi_AGI"
REPO_OWNER="iagenerativa"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 Preparando repositorio SARAi_AGI para GitHub"
echo "================================================"
echo ""

# 1. Verificar que estamos en el directorio correcto
if [[ ! -f "$CURRENT_DIR/VERSION" ]]; then
    echo "❌ Error: No se encuentra VERSION. ¿Estás en el directorio raíz de SARAi_AGI?"
    exit 1
fi

VERSION=$(cat "$CURRENT_DIR/VERSION")
echo "✓ Versión detectada: $VERSION"

# 2. Inicializar git si no existe
if [[ ! -d "$CURRENT_DIR/.git" ]]; then
    echo "📦 Inicializando repositorio Git..."
    cd "$CURRENT_DIR"
    git init
    git branch -M main
    echo "✓ Repositorio Git inicializado (branch: main)"
else
    echo "✓ Repositorio Git ya existe"
fi

# 3. Configurar .gitignore si no existe
if [[ ! -f "$CURRENT_DIR/.gitignore" ]]; then
    echo "⚠️  Advertencia: .gitignore no existe. Crear antes de continuar."
    exit 1
fi

# 4. Stage inicial
echo ""
echo "📝 Staging archivos iniciales..."
cd "$CURRENT_DIR"
git add .gitignore
git add VERSION
git add CHANGELOG.md
git add README.md
git add LICENSE
git add requirements.txt
git add docs/
git add config/
git add src/
git add tests/
git add scripts/
git add logs/.gitkeep
git add state/.gitkeep
git add data/.gitkeep
git add models/.gitkeep

# 5. Commit inicial
if ! git rev-parse HEAD > /dev/null 2>&1; then
    echo "💾 Creando commit inicial..."
    git commit -m "feat: Initial commit - SARAi_AGI v${VERSION}

- Pipeline paralela con orquestación async
- Cuantización dinámica (IQ3_XXS/Q4_K_M/Q5_K_M)
- Sistema de configuración YAML con aliases
- Test suite completo (11 pruebas)
- Documentación en español
- Estructura preparada para GitHub

Migrado desde SARAi_v2 con arquitectura limpia y SemVer.
"
    echo "✓ Commit inicial creado"
else
    echo "✓ Ya existen commits en el repositorio"
fi

# 6. Crear tag de versión
if ! git tag | grep -q "^v${VERSION}\$"; then
    echo "🏷️  Creando tag v${VERSION}..."
    git tag -a "v${VERSION}" -m "Release v${VERSION} - Base limpia para SARAi_AGI

Pipeline paralela + Cuantización dinámica + Documentación completa
"
    echo "✓ Tag v${VERSION} creado"
else
    echo "✓ Tag v${VERSION} ya existe"
fi

# 7. Instrucciones para crear el repositorio remoto
echo ""
echo "================================================"
echo "✅ Repositorio local preparado"
echo ""
echo "📋 PASOS SIGUIENTES:"
echo ""
echo "1. Crear repositorio en GitHub:"
echo "   https://github.com/new"
echo "   Nombre: SARAi_AGI"
echo "   Owner: ${REPO_OWNER}"
echo "   ⚠️  NO inicializar con README/LICENSE/.gitignore"
echo ""
echo "2. Conectar repositorio local con remoto:"
echo "   git remote add origin https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
echo ""
echo "3. Push inicial (con tags):"
echo "   git push -u origin main"
echo "   git push origin --tags"
echo ""
echo "4. Configurar branch protection en GitHub:"
echo "   - Settings > Branches > Add rule"
echo "   - Branch name pattern: main"
echo "   - ✓ Require pull request reviews"
echo "   - ✓ Require status checks to pass"
echo ""
echo "5. Configurar GitHub Actions (CI/CD):"
echo "   - Crear .github/workflows/ci.yml"
echo "   - pytest + linting + coverage"
echo ""
echo "================================================"
echo ""
echo "🎯 Estado actual:"
git log --oneline -n 1
git tag -l
echo ""
