# SARAi_AGI

**Baseline version:** `v3.5.1`

SARAi_AGI es el nuevo repositorio canónico para la evolución de SARAi hacia la versión 4.0 y posteriores. El objetivo es mantener un control de versiones claro, trazable y alineado con las prácticas de ingeniería modernas, evitando la confusión histórica que existía en `SARAi_v2`.

## Objetivos iniciales

- Migrar progresivamente los módulos estables de `SARAi_v2`.
- Consolidar la arquitectura de v3.5.1 como línea base auditable.
- Preparar las iteraciones de v3.6.0 → v4.0 con documentación y planeación rigurosa.
- Garantizar que cada versión tenga tag, changelog y paquete reproducible.

## Estructura del repositorio

```
SARAi_AGI/
├── README.md
├── VERSION
├── CHANGELOG.md
├── docs/
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── MIGRATION_PLAN_v3_5_1.md
│   ├── ROADMAP.md
│   └── VERSIONING_POLICY.md
├── config/
│   └── default_settings.yaml
├── scripts/
│   └── bootstrap_env.sh
├── src/
│   └── __init__.py
└── tests/
    ├── __init__.py
    └── test_placeholder.py
```

## Lineamientos de versionado

- Se adopta [SemVer 2.0](https://semver.org/).
- Cada release debe tener un tag firmado `vX.Y.Z` y un changelog asociado.
- Los branches activos se nombran `release/vX.Y` (estables) y `feat/<feature>` para trabajo incremental.
- Los hotfixes se gestionan en `hotfix/vX.Y.Z`.

## Primeros pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/iagenerativa/SARAi_AGI.git
cd SARAi_AGI

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar instalación
pytest

# 5. Verificar versión
python -c "from src.sarai_agi import __version__; print(__version__)"
```

### Quickstart: Pipeline Paralela

```python
import asyncio
from src.sarai_agi.pipeline import PipelineDependencies, create_parallel_pipeline

# Definir dependencias (placeholders para este ejemplo)
def classifier(state):
    return {"hard": 0.8, "soft": 0.2}

def weighter(state):
    return {"alpha": 0.8, "beta": 0.2}

def generator(state, agent_key):
    return f"Respuesta del agente {agent_key}"

deps = PipelineDependencies(
    trm_classifier=classifier,
    mcp_weighter=weighter,
    response_generator=generator,
)

# Crear pipeline
pipeline = create_parallel_pipeline(deps)

# Ejecutar
async def main():
    result = await pipeline.run({"input": "¿Cómo funciona la cuantización?"})
    print(result["response"])
    await pipeline.shutdown()

asyncio.run(main())
```

### Quickstart: Cuantización Dinámica

```python
from src.sarai_agi.model import create_dynamic_quantization_selector

selector = create_dynamic_quantization_selector(
    min_ram_free_gb=1.5,
    force_quality_threshold=0.9,
)

decision = selector.select_quantization(
    prompt="Explica la teoría de la relatividad en detalle",
    task_complexity=0.95,  # Query compleja
)

print(f"Nivel: {decision.level}")  # Q5_K_M (alta calidad)
print(f"RAM: {decision.metadata.ram_required_mb} MB")
print(f"Latencia estimada: {decision.metadata.estimated_latency_ms} ms")
```

## Documentación

- **[ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md)**: Diseño de capas y componentes
- **[MIGRATION_PLAN_v3_5_1.md](docs/MIGRATION_PLAN_v3_5_1.md)**: Estrategia de migración desde SARAi_v2
- **[ROADMAP.md](docs/ROADMAP.md)**: Hoja de ruta v3.6 → v4.0
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Guía para contribuidores

## Estado del Proyecto

**Versión actual:** `v3.5.1` (Baseline estable)

**Módulos migrados:**
- ✅ Pipeline paralela con orquestación async
- ✅ Selector de cuantización dinámica
- ✅ Sistema de configuración YAML
- ✅ Test suite completo (11 pruebas)

**Próximos pasos (v3.6.0):**
- [ ] TRM Classifier integration
- [ ] MCP weighting system
- [ ] Model pool con cache LRU/TTL
- [ ] Emotional context engine
- [ ] Telemetría avanzada

Ver [ROADMAP.md](docs/ROADMAP.md) para detalles.

## Tests

```bash
# Suite completa
pytest

# Con coverage
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/test_pipeline.py -v
pytest tests/test_quantization.py -v

# Con output detallado
pytest -vv -s
```

**Coverage objetivo:** ≥80%

## Contribuir

¡Las contribuciones son bienvenidas! Por favor lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir un PR.

**Flujo rápido:**
1. Fork el repo
2. Crea branch: `git checkout -b feat/mi-feature`
3. Commit: `git commit -m 'feat: añade mi feature'`
4. Push: `git push origin feat/mi-feature`
5. Abre Pull Request

## Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## Equipo

- **Maintainer principal:** @iagenerativa
- **Contributors:** Ver [GitHub Contributors](https://github.com/iagenerativa/SARAi_AGI/graphs/contributors)

## Enlaces

- [GitHub Repository](https://github.com/iagenerativa/SARAi_AGI)
- [Issue Tracker](https://github.com/iagenerativa/SARAi_AGI/issues)
- [Discussions](https://github.com/iagenerativa/SARAi_AGI/discussions)
- [Releases](https://github.com/iagenerativa/SARAi_AGI/releases)

---

**SARAi_AGI** - Sistema de AGI autónomo con arquitectura limpia y versionado riguroso.


## Estado actual

- ✅ Estructura inicial creada.
- ✅ Política de versionado definida.
- ⏳ Migración de código pendiente.
- ⏳ Configuración de CI/CD pendiente.

Para cualquier actualización de versión, modificar el archivo `VERSION` y registrar los cambios en `CHANGELOG.md`.
