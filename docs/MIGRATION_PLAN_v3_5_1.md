# Plan de Migración desde SARAi_v2 (v3.5.1)

El objetivo de este plan es migrar gradualmente los componentes estables de `SARAi_v2` al nuevo repositorio `SARAi_AGI`, preservando el histórico funcional y evitando la arrastre de deuda técnica.

## Fases

### Fase 0 - Preparación (🟢 Completada)
- Crear repositorio limpio con estructura mínima.
- Definir política de versionado y documentación base.

### Fase 1 - Núcleo Operativo (⏳ En progreso)
1. **Pipeline Paralelo:**
   - Portar `core/pipeline_parallel_v351.py` sin mocks.
   - Añadir pruebas unitarias y de integración.
2. **Quantización Dinámica:**
   - Migrar selector y configuración (`core/dynamic_quantization.py`).
   - Validar heurísticas con benchmarks reproducibles.
3. **Model Pool Base:**
   - Llevar `core/model_pool_v34.py` asegurando locks thread-safe.

### Fase 2 - Sistemas Avanzados
- Security & Resilience.
- Emotional Context Engine.
- Advanced Telemetry.
- Documentación y tests asociados.

### Fase 3 - Interfaces y Agentes
- Integración de agentes especializados (visión, código, tiny).
- Reemplazo de placeholders TTS/ASR por implementaciones reales.
- Exposición de API pública y CLI.

### Fase 4 - Preparación v4.0
- Sistema de Sidecars y Plugins.
- Observabilidad completa (Prometheus/Grafana).
- Estrategia de release firmados con artefactos reproducibles.

## Reglas de Migración

- Cada traslado debe incluir:
  - Código fuente + tests + documentación.
  - Registro en `CHANGELOG.md` y actualización de `VERSION` si aplica.
- No mover archivos con mocks o dependencias incompletas.
- Ejecutar benchmarks relevantes previo a cerrar cada fase.

## Seguimiento

| Componente | Estado | Última revisión | Responsable |
|------------|--------|-----------------|-------------|
| Pipeline paralelo | ⏳ Pendiente | - | - |
| Quantización dinámica | ⏳ Pendiente | - | - |
| Model Pool | ⏳ Pendiente | - | - |
| Sistemas avanzados | ⏳ Pendiente | - | - |

> Actualizar esta tabla en cada sesión y enlazar PRs correspondientes.
