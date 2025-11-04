# Plan de Migración SARAi_v2 → sarai-agi v3.5

**Fecha**: 4 de noviembre de 2025  
**Objetivo**: Lograr paridad de funcionalidades completa entre SARAi_v2 y sarai-agi

---

## 📊 Estado Actual

### ✅ Componentes Ya Implementados en sarai-agi

- **CASCADE ORACLE**: `cascade/confidence_router.py`, `cascade/think_mode_classifier.py`
- **Model Management**: `model/pool.py`, `model/wrapper.py`, `model/quantization_selector.py`
- **Emotional Context**: `emotion/context_engine.py`
- **Security**: `security/resilience.py`
- **Telemetry**: `telemetry/monitoring.py`
- **TRM Classifier**: `classifier/trm.py`
- **MCP**: `mcp/core.py`, `mcp/skills.py`
- **Pipeline**: `pipeline/parallel.py`

### ❌ Componentes Faltantes (a migrar)

1. **RAG Memory System** (PRIORIDAD 1)
2. **Health Dashboard & Metrics** (PRIORIDAD 1)
3. **Phoenix Skills** (PRIORIDAD 2)
4. **Layer Architecture (Tone)** (PRIORIDAD 2)
5. **Voice Pipeline (Omni-Loop)** (PRIORIDAD 3)
6. **DevSecOps Features** (PRIORIDAD 3)

---

## 🎯 Fase 1: RAG Memory System (ALTA PRIORIDAD)

### Componentes a Migrar

#### 1.1. RAG Agent
- **Origen**: `/home/noel/SARAi_v2/agents/rag_agent.py` (322 líneas)
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/agents/rag.py`
- **Dependencias**: web_cache, web_audit, model pool
- **Funcionalidad**: 
  - Pipeline de 6 pasos con garantías Sentinel
  - Integración con SearXNG
  - Síntesis con SOLAR (context-aware short/long)
  - Fallback a respuestas Sentinel

#### 1.2. Web Cache Module
- **Origen**: `/home/noel/SARAi_v2/core/web_cache.py` (289 líneas)
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/memory/web_cache.py`
- **Dependencias**: diskcache, requests, audit module
- **Funcionalidad**:
  - Cache persistente con diskcache (1GB max)
  - TTL dinámico (1h general, 5min time-sensitive)
  - Timeout 10s por búsqueda
  - Respeto de Safe Mode

#### 1.3. Web Audit Logger
- **Origen**: `/home/noel/SARAi_v2/core/web_audit.py` (693 líneas)
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/memory/web_audit.py`
- **Dependencias**: core.audit (Safe Mode)
- **Funcionalidad**:
  - Logging inmutable con SHA-256
  - HMAC para interacciones de voz
  - Sidecars (.sha256, .hmac)
  - Detección de anomalías

#### 1.4. Vector Database Integration
- **Origen**: `/home/noel/SARAi_v2/core/layer2_memory/` 
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/memory/vector_db.py`
- **Funcionalidad**:
  - Cliente Qdrant (producción)
  - Cliente Chroma (desarrollo)
  - Embedding Gemma integration
  - Top-k retrieval

### Checklist Fase 1

- [ ] Crear directorio `src/sarai_agi/memory/`
- [ ] Migrar `web_cache.py` con adaptaciones
- [ ] Migrar `web_audit.py` con adaptaciones
- [ ] Crear `vector_db.py` con clientes Qdrant/Chroma
- [ ] Migrar `rag.py` agent
- [ ] Crear tests: `tests/test_rag_agent.py`
- [ ] Crear tests: `tests/test_web_cache.py`
- [ ] Crear tests: `tests/test_web_audit.py`
- [ ] Actualizar `config/sarai.yaml` con RAG settings
- [ ] Documentar en `docs/RAG_MEMORY.md`

### Estimación Fase 1
- **Tiempo**: 6-8 horas
- **LOC**: ~1,500 líneas
- **Tests**: ~400 líneas
- **Impacto**: Habilita autoaprendizaje y memoria conversacional

---

## 🏥 Fase 2: Health Dashboard & Metrics (ALTA PRIORIDAD)

### Componentes a Migrar

#### 2.1. Health Dashboard
- **Origen**: `/home/noel/SARAi_v2/sarai/health_dashboard.py`
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/api/health.py`
- **Funcionalidad**:
  - Endpoint `/health` con content negotiation (HTML/JSON)
  - Endpoint `/metrics` formato Prometheus
  - KPIs: RAM, latency, cache hit rate, etc.
  - Dashboard Chart.js para visualización

#### 2.2. Makefile Integration
- **Origen**: `/home/noel/SARAi_v2/Makefile` (targets health, metrics)
- **Destino**: Actualizar `/home/noel/sarai-agi/Makefile`
- **Funcionalidad**:
  - `make health`: Levanta dashboard (uvicorn)
  - `make metrics`: Muestra métricas actuales
  - `make validate-kpis`: Verifica KPIs contra objetivos

### Checklist Fase 2

- [ ] Crear directorio `src/sarai_agi/api/`
- [ ] Migrar `health.py` con FastAPI
- [ ] Crear templates HTML para dashboard
- [ ] Actualizar Makefile con targets health
- [ ] Crear tests: `tests/test_health_endpoints.py`
- [ ] Configurar uvicorn en `pyproject.toml`
- [ ] Documentar en `docs/HEALTH_MONITORING.md`

### Estimación Fase 2
- **Tiempo**: 3-4 horas
- **LOC**: ~500 líneas
- **Tests**: ~150 líneas
- **Impacto**: Monitoreo en producción

---

## 🦅 Fase 3: Phoenix Skills (MEDIA PRIORIDAD)

### Componentes a Migrar

#### 3.1. Skills Configs
- **Origen**: `/home/noel/SARAi_v2/core/skill_configs.py`
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/skills/configs.py`
- **7 Skills**: programming, diagnosis, financial, creative, reasoning, cto, sre
- **Long-tail patterns**: 35 combinaciones palabra1+palabra2

#### 3.2. Skills Directory Structure
- **Destino**: `/home/noel/sarai-agi/skills/`
- **Estructura**:
  ```
  skills/
  ├── __init__.py
  ├── programming/
  ├── diagnosis/
  ├── financial/
  ├── creative/
  ├── reasoning/
  ├── cto/
  └── sre/
  ```

#### 3.3. Graph Integration
- **Origen**: `/home/noel/SARAi_v2/core/graph.py` (sección skills)
- **Destino**: Actualizar `src/sarai_agi/pipeline/graph.py`
- **Funcionalidad**: Detección y aplicación de skills en nodos

### Checklist Fase 3

- [ ] Crear `src/sarai_agi/skills/configs.py`
- [ ] Crear directorio `skills/` con 7 subdirectorios
- [ ] Migrar long-tail patterns
- [ ] Integrar con graph.py
- [ ] Crear tests: `tests/test_skills_detection.py`
- [ ] Crear tests: `tests/test_skills_integration.py`
- [ ] Documentar en `docs/PHOENIX_SKILLS.md`

### Estimación Fase 3
- **Tiempo**: 4-5 horas
- **LOC**: ~800 líneas
- **Tests**: ~300 líneas
- **Impacto**: Especialización de respuestas

---

## 🎵 Fase 4: Layer Architecture - Tone (MEDIA PRIORIDAD)

### Componentes a Migrar

#### 4.1. Tone Memory Buffer
- **Origen**: `/home/noel/SARAi_v2/core/layer2_memory/tone_memory.py`
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/memory/tone_memory.py`
- **Funcionalidad**: 
  - Persistencia JSONL
  - Buffer in-memory (deque, max 256)
  - Thread-safe

#### 4.2. Tone Bridge (Smoothing)
- **Origen**: `/home/noel/SARAi_v2/core/layer3_fluidity/tone_bridge.py`
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/fluidity/tone_bridge.py`
- **Funcionalidad**:
  - Exponential moving average (α=0.25)
  - 9 estilos inferidos
  - Filler hints para TTS

#### 4.3. Emotion Detection (Layer 1)
- **Origen**: `/home/noel/SARAi_v2/core/layer1_io/audio_emotion_lite.py`
- **Destino**: Integrar con `emotion/context_engine.py` existente
- **Funcionalidad**: Pitch, MFCC, Formants, Energy features

### Checklist Fase 4

- [ ] Migrar `tone_memory.py`
- [ ] Crear directorio `src/sarai_agi/fluidity/`
- [ ] Migrar `tone_bridge.py`
- [ ] Extender `emotion/context_engine.py` con audio features
- [ ] Crear tests: `tests/test_tone_memory.py`
- [ ] Crear tests: `tests/test_tone_bridge.py`
- [ ] Documentar en `docs/LAYER_ARCHITECTURE.md`

### Estimación Fase 4
- **Tiempo**: 5-6 horas
- **LOC**: ~700 líneas
- **Tests**: ~250 líneas
- **Impacto**: Transiciones emocionales suaves

---

## 🎙️ Fase 5: Voice Pipeline (BAJA PRIORIDAD)

### Componentes a Migrar

#### 5.1. Audio Router
- **Origen**: `/home/noel/SARAi_v2/agents/audio_router.py`
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/audio/router.py`
- **Funcionalidad**: Routing Omni-3B vs NLLB vs LFM2

#### 5.2. Omni Pipeline
- **Origen**: `/home/noel/SARAi_v2/agents/audio_omni_pipeline.py`
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/audio/omni_pipeline.py`
- **Funcionalidad**: Pipeline completo voz-a-voz

#### 5.3. TTS Streaming
- **Origen**: `/home/noel/SARAi_v2/core/streaming_tts_v341.py`
- **Destino**: `/home/noel/sarai-agi/src/sarai_agi/audio/tts_streaming.py`
- **Funcionalidad**: Streaming -10ms TTFB

### Checklist Fase 5

- [ ] Crear directorio `src/sarai_agi/audio/`
- [ ] Migrar `router.py`
- [ ] Migrar `omni_pipeline.py`
- [ ] Migrar `tts_streaming.py`
- [ ] Integrar NLLB translator
- [ ] Crear tests: `tests/test_audio_router.py`
- [ ] Crear tests: `tests/test_omni_pipeline.py`
- [ ] Documentar en `docs/VOICE_PIPELINE.md`

### Estimación Fase 5
- **Tiempo**: 6-8 horas
- **LOC**: ~1,200 líneas
- **Tests**: ~350 líneas
- **Impacto**: Interacción por voz completa

---

## 🔐 Fase 6: DevSecOps Features (BAJA PRIORIDAD)

### Componentes a Migrar

#### 6.1. CI/CD Workflows
- **Origen**: `/home/noel/SARAi_v2/.github/workflows/release.yml`
- **Destino**: `/home/noel/sarai-agi/.github/workflows/release.yml`
- **Funcionalidad**: SBOM (Syft), Cosign signing, attestation

#### 6.2. Docker Hardening
- **Origen**: `/home/noel/SARAi_v2/docker-compose.override.yml`
- **Destino**: `/home/noel/sarai-agi/docker-compose.override.yml`
- **Funcionalidad**: cap_drop, read_only, no-new-privileges

#### 6.3. Verification Scripts
- **Origen**: `/home/noel/SARAi_v2/scripts/verify_*.sh`
- **Destino**: `/home/noel/sarai-agi/scripts/verify_*.sh`
- **Funcionalidad**: Verificación SBOM, signatures, hardening

### Checklist Fase 6

- [ ] Crear `.github/workflows/release.yml`
- [ ] Actualizar `docker-compose.override.yml` con hardening
- [ ] Crear scripts de verificación
- [ ] Configurar Cosign en CI/CD
- [ ] Crear tests: `tests/test_security_hardening.py`
- [ ] Documentar en `docs/DEVSECOPS.md`

### Estimación Fase 6
- **Tiempo**: 3-4 horas
- **LOC**: ~400 líneas (scripts + workflows)
- **Tests**: ~100 líneas
- **Impacto**: Supply chain security

---

## 📈 Resumen de Estimaciones

| Fase | Prioridad | Tiempo | LOC | Tests LOC | Impacto |
|------|-----------|--------|-----|-----------|---------|
| 1. RAG Memory | ALTA | 6-8h | ~1,500 | ~400 | Crítico |
| 2. Health Dashboard | ALTA | 3-4h | ~500 | ~150 | Alto |
| 3. Phoenix Skills | MEDIA | 4-5h | ~800 | ~300 | Alto |
| 4. Layer Tone | MEDIA | 5-6h | ~700 | ~250 | Medio |
| 5. Voice Pipeline | BAJA | 6-8h | ~1,200 | ~350 | Medio |
| 6. DevSecOps | BAJA | 3-4h | ~400 | ~100 | Bajo |
| **TOTAL** | - | **27-35h** | **~5,100** | **~1,550** | - |

---

## 🚀 Plan de Ejecución

### Semana 1 (4-8 Nov 2025)
- ✅ **Día 1**: Fase 1.1-1.2 (RAG Agent + Web Cache)
- ✅ **Día 2**: Fase 1.3-1.4 (Web Audit + Vector DB)
- ✅ **Día 3**: Fase 2 completa (Health Dashboard)
- ✅ **Día 4**: Fase 3.1-3.2 (Skills Configs + Directory)
- ✅ **Día 5**: Fase 3.3 (Skills Integration + Tests)

### Semana 2 (11-15 Nov 2025)
- ✅ **Día 6**: Fase 4.1-4.2 (Tone Memory + Bridge)
- ✅ **Día 7**: Fase 4.3 (Emotion Integration + Tests)
- ✅ **Día 8**: Fase 5.1-5.2 (Audio Router + Omni)
- ✅ **Día 9**: Fase 5.3 (TTS Streaming + Tests)
- ✅ **Día 10**: Fase 6 completa (DevSecOps)

### Validación Final
- **Tests end-to-end**: Ejecutar suite completa
- **Benchmarks**: Validar KPIs (RAM, latency, etc.)
- **Documentación**: Actualizar README.md, QUICKSTART.md
- **Release**: Tag v3.5.0 con firma Cosign

---

## 🎯 Criterios de Éxito

### KPIs Objetivo

| KPI | SARAi_v2 v3.5 | sarai-agi Target | Método Validación |
|-----|---------------|------------------|-------------------|
| RAM P50 | 5.3GB | ≤5.5GB | `pytest tests/test_kpis.py` |
| RAM P99 | 10.8GB | ≤11GB | Benchmarks bajo carga |
| Latency P50 | 2.3s | ≤2.5s | E2E tests |
| TTFB (Voice) | 295ms | ≤300ms | Audio pipeline tests |
| Cache Hit Rate | 97% | ≥95% | Web cache metrics |
| Tests Passing | 100% | 100% | CI/CD pipeline |
| Feature Parity | 100% | 100% | Manual checklist |

### Checklist Final

- [ ] Todos los tests passing (pytest -v)
- [ ] KPIs validados contra objetivos
- [ ] Documentación completa actualizada
- [ ] CI/CD workflows funcionando
- [ ] Docker images building correctamente
- [ ] Health dashboard accesible
- [ ] RAG memory operativo con Qdrant
- [ ] Skills detectando correctamente
- [ ] Voice pipeline con fallbacks
- [ ] DevSecOps verificado (SBOM, signatures)

---

## 📝 Notas de Implementación

### Adaptaciones Necesarias

1. **Imports**: Ajustar paths de `core.*` a `sarai_agi.*`
2. **Config**: Usar `config/sarai.yaml` en lugar de múltiples archivos
3. **Tests**: Estructura `tests/` con pytest fixtures compartidos
4. **Logs**: Directorio `logs/` con estructura similar
5. **State**: Directorio `state/` para persistencia

### Dependencias Nuevas

```toml
# Añadir a pyproject.toml
dependencies = [
    # ... existentes ...
    "diskcache>=5.6.0",  # Web cache
    "qdrant-client>=1.7.0",  # Vector DB
    "chromadb>=0.4.0",  # Vector DB alternativo
    "fastapi>=0.104.0",  # Health dashboard
    "uvicorn>=0.24.0",  # ASGI server
    "jinja2>=3.1.0",  # Templates HTML
]
```

### Breaking Changes

**NINGUNO**: La migración es aditiva, no rompe código existente.

---

**Autor**: Sistema SARAi  
**Versión Plan**: 1.0  
**Última Actualización**: 4 Nov 2025
