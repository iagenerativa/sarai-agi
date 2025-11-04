# Contributing to SARAi_AGI

¡Gracias por tu interés en contribuir a SARAi_AGI! Este documento describe el flujo de trabajo y convenciones del proyecto.

## Flujo de Trabajo

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/TU_USUARIO/SARAi_AGI.git
cd SARAi_AGI
git remote add upstream https://github.com/iagenerativa/SARAi_AGI.git
```

### 2. Crear Branch de Feature

```bash
# Actualizar desde upstream
git fetch upstream
git checkout main
git merge upstream/main

# Crear branch
git checkout -b feat/mi-nueva-caracteristica
```

**Convenciones de nombres de branch:**
- `feat/<descripcion>`: Nuevas características
- `fix/<descripcion>`: Correcciones de bugs
- `docs/<descripcion>`: Documentación
- `refactor/<descripcion>`: Refactorización sin cambios funcionales
- `test/<descripcion>`: Añadir o mejorar tests

### 3. Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt
pip install ruff mypy pytest-cov

# Ejecutar tests mientras desarrollas
pytest -v

# Verificar estilo
ruff check src/
mypy src/ --ignore-missing-imports
```

### 4. Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
tipo(alcance): descripción breve

Descripción más detallada (opcional).

Refs: #123
```

**Tipos permitidos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formato, sin cambios de código
- `refactor`: Refactorización
- `test`: Añadir o corregir tests
- `chore`: Tareas de mantenimiento

**Ejemplos:**
```bash
git commit -m "feat(pipeline): add async emotion detection

Integrates emotion detector in parallel path for inputs >20 chars.
Reduces P50 latency by 15ms.

Refs: #42"

git commit -m "fix(quantization): handle missing psutil gracefully

Falls back to min_ram_free_gb when psutil unavailable."
```

### 5. Tests

**Todos los PRs deben incluir tests.**

```bash
# Ejecutar suite completa
pytest

# Con coverage
pytest --cov=src --cov-report=term

# Solo tests relacionados con tu cambio
pytest tests/test_pipeline.py -v
```

**Mínimos requeridos:**
- Coverage ≥ 80% en código nuevo
- Todos los tests existentes deben pasar
- Nuevas funcionalidades requieren tests unitarios + integración

### 6. Documentación

Actualizar documentación relevante:

- `CHANGELOG.md`: Añadir entrada bajo `[Unreleased]`
- Docstrings: Seguir formato Google/NumPy
- `docs/`: Actualizar si cambias arquitectura

### 7. Pull Request

```bash
# Push a tu fork
git push origin feat/mi-nueva-caracteristica
```

**En GitHub:**
1. Crear PR desde tu branch → `main` de upstream
2. Título descriptivo (mismo formato que commits)
3. Descripción con:
   - Qué cambia y por qué
   - Screenshots/logs si aplica
   - Checklist de self-review

**Template de PR:**
```markdown
## Descripción
Breve resumen del cambio.

## Tipo de cambio
- [ ] Bug fix (cambio que corrige un issue)
- [ ] Nueva característica (cambio que añade funcionalidad)
- [ ] Breaking change (fix o feature que rompe compatibilidad)
- [ ] Documentación

## Checklist
- [ ] Mi código sigue el estilo del proyecto
- [ ] He realizado self-review de mi código
- [ ] He comentado código complejo
- [ ] He actualizado la documentación
- [ ] Mis cambios no generan nuevos warnings
- [ ] He añadido tests que prueban mi fix/feature
- [ ] Tests nuevos y existentes pasan localmente
- [ ] He actualizado CHANGELOG.md
```

### 8. Review

El equipo revisará tu PR. Es posible que pidan cambios:

```bash
# Hacer cambios solicitados
git add .
git commit -m "fix: address review comments"
git push origin feat/mi-nueva-caracteristica
```

### 9. Merge

Una vez aprobado, un maintainer hará merge (squash merge preferido para mantener historia limpia).

## Versionado

- **Patch** (v3.5.1 → v3.5.2): Bugfixes, mejoras menores
- **Minor** (v3.5.1 → v3.6.0): Nuevas características, backward compatible
- **Major** (v3.5.1 → v4.0.0): Breaking changes

Los maintainers se encargan de bumping de versión y releases.

## Estilo de Código

### Python

```python
# Imports ordenados
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from ..configuration import load_settings

# Docstrings Google-style
def my_function(param: str, optional: Optional[int] = None) -> bool:
    """Breve descripción de una línea.

    Descripción más detallada si es necesario. Puede tener múltiples
    párrafos.

    Args:
        param: Descripción del parámetro.
        optional: Parámetro opcional.

    Returns:
        True si exitoso, False si falla.

    Raises:
        ValueError: Si param está vacío.
    """
    pass
```

### Convenciones

- Snake_case para funciones/variables
- PascalCase para clases
- SCREAMING_SNAKE_CASE para constantes
- Prefijo `_` para métodos/variables privadas
- Type hints obligatorios
- Límite 100 caracteres por línea

## Testing

### Estructura

```
tests/
├── test_pipeline.py          # Tests de pipeline
├── test_quantization.py      # Tests de quantization
└── test_integration.py       # Tests E2E
```

### Fixtures

```python
import pytest

@pytest.fixture
def sample_config():
    return {
        "enable_parallelization": True,
        "min_input_length": 20,
    }

def test_pipeline_respects_config(sample_config):
    pipeline = create_parallel_pipeline(deps, config=sample_config)
    assert pipeline.enable_parallel is True
```

### Mocking

```python
from unittest.mock import Mock, patch

def test_quantization_without_psutil():
    with patch('src.sarai_agi.model.quantization.HAS_PSUTIL', False):
        selector = create_dynamic_quantization_selector()
        decision = selector.select_quantization("test", 0.5)
        # Debe usar min_ram_free_gb por defecto
        assert decision.metadata.ram_available_gb == 1.5
```

## Comunicación

- **Issues**: Para bugs, features, preguntas
- **Discussions**: Para ideas, diseño, arquitectura
- **PRs**: Para código listo para review

## Código de Conducta

- Sé respetuoso y profesional
- Acepta feedback constructivo
- Ayuda a otros contributors
- Enfócate en el código, no en las personas

## Preguntas

Si tienes dudas, abre un issue con la etiqueta `question` o pregunta en Discussions.

¡Gracias por contribuir! 🚀
