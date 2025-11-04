# Próximos Pasos - SARAi_AGI Development Plan

**Fecha**: 4 de noviembre de 2025  
**Versión actual**: v3.5.2  
**Estado migración**: 56% (4,485 LOC core)  
**Tests**: 35/35 passing (100% de lo migrado)  

---

## 🎯 Fase Actual: Estabilización v3.5.2

### ✅ Completado (4 Nov 2025)

1. **Infraestructura CI/CD**
   - ✅ Workflow de CI con tests automáticos (Python 3.10 + 3.11)
   - ✅ Workflow de documentación (GitHub Pages)
   - ✅ Workflow de releases automáticas
   - ✅ Dependencias opcionales manejadas correctamente
   - ✅ Imports condicionales (torch, langchain_core)

2. **Componentes Core Migrados** (9/15)
   - ✅ Configuration System
   - ✅ Pipeline Paralela
   - ✅ Quantization Selector
   - ✅ TRM Classifier
   - ✅ MCP Core
   - ✅ Model Pool
   - ✅ Emotional Context Engine
   - ✅ Security & Resilience System
   - ✅ Advanced Telemetry

### 🔄 En Progreso

1. **CI Pipeline** ⏳ EJECUTANDO AHORA
   - Estado: Workflow corriendo con fixes aplicados
   - Próximo: Verificar que todos los 257 tests pasen
   - Esperado: 100% passing en ambas versiones de Python

---

## 📋 Fase 1: Completar v3.5.2 (Esta semana - Nov 4-8)

### Prioridad ALTA

#### 1.1 Validar CI Pipeline
- [ ] Confirmar que CI pasa con 257 tests
- [ ] Verificar cobertura de código >80%
- [ ] Documentar tests que requieren dependencias opcionales
- [ ] Añadir badge de coverage en README.md

#### 1.2 Completar Migración de Componentes Pendientes (6/15)
**Pendientes del core v3.5.1**:
- [ ] **Unified Model Wrapper** (1,626 LOC estimadas)
  - Abstracción de 8 backends
  - Integración LangChain opcional
  - Tests de overhead <5%
  
- [ ] **Graph Orchestrator** (estimado 800 LOC)
  - LangGraph workflow
  - Routing multimodal 7-priority
  - Skills Phoenix integration
  
- [ ] **Layer Architecture** (estimado 600 LOC)
  - Layer1: I/O (emotion detection)
  - Layer2: Memory (tone persistence)
  - Layer3: Fluidity (smoothing)
  
- [ ] **Agents** (estimado 900 LOC)
  - Expert Agent (SOLAR)
  - Tiny Agent (LFM2)
  - Vision Agent (Qwen3-VL)
  - Code Expert (VisCoder2)
  - Audio Router
  
- [ ] **Feedback System** (estimado 400 LOC)
  - Logging asíncrono
  - Embeddings implícitos
  - MCP evolution triggers
  
- [ ] **Health Dashboard** (estimado 300 LOC)
  - FastAPI endpoints
  - Content negotiation
  - Prometheus metrics

**Estrategia de migración**:
1. Migrar de menos a más dependencias (wrapper → graph → agents)
2. Añadir tests para cada componente antes de integrar
3. Mantener backward compatibility con SARAi_v2
4. Documentar breaking changes si existen

#### 1.3 Documentación Crítica
- [ ] **MIGRATION_STATUS.md**: Actualizar progreso 56% → 100%
- [ ] **CHANGELOG.md**: Añadir entrada v3.5.2 completa
- [ ] **API.md**: Documentar interfaces públicas migradas
- [ ] **TESTING.md**: Guía de cómo ejecutar tests localmente

#### 1.4 Release v3.5.2
- [ ] Verificar que VERSION file está en 3.5.2
- [ ] Crear tag `v3.5.2` con GPG signature
- [ ] Generar release notes automáticas
- [ ] Publicar en GitHub Releases con SBOM

---

## 📋 Fase 2: Iteración v3.6.0 (Nov 11 - Dic 5, 2025)

### Objetivo: Sistema de Plugins + TTS Real

#### 2.1 Arquitectura de Plugins

**Diseño**:
```python
# Estructura propuesta
plugins/
├── __init__.py
├── base.py              # Plugin base class
├── loader.py            # Plugin discovery y carga
├── registry.py          # Plugin registry con versioning
└── skills/
    ├── sql_executor/    # Firejailed SQL skill
    ├── bash_runner/     # Sandboxed bash skill
    └── network_diag/    # Network diagnostics skill
```

**Características**:
- [ ] Plugin discovery automático (entry points)
- [ ] Versioning de plugins (semver)
- [ ] Sandboxing con Firejail para plugins peligrosos
- [ ] API estable para plugin development
- [ ] Documentación de Plugin Development Kit (PDK)

**Tests**:
- [ ] Plugin loading/unloading
- [ ] Plugin isolation (security)
- [ ] Plugin communication (IPC)
- [ ] Plugin versioning conflicts

#### 2.2 Integración TTS Real

**Componentes**:
- [ ] **MeloTTS Integration**
  - Instalación y configuración
  - Tests de latencia (<100ms TTFB)
  - Soporte multi-idioma (es, en)
  
- [ ] **Sherpa-ONNX Integration** (alternativa ligera)
  - Instalación y tests
  - Comparativa de latencia vs MeloTTS
  - Selección automática según hardware

**Configuración**:
```yaml
# config/tts.yaml (propuesta)
tts:
  default_engine: "melo"  # melo | sherpa | mock
  melo:
    model_path: "models/tts/melo_tts.onnx"
    sample_rate: 22050
    streaming: true
  sherpa:
    model_path: "models/tts/sherpa_onnx.onnx"
    sample_rate: 16000
```

#### 2.3 Observabilidad Básica

- [ ] **Prometheus Exporter**
  - Métricas de latencia (P50, P95, P99)
  - Métricas de RAM (current, peak, P99)
  - Métricas de throughput (req/min)
  
- [ ] **Grafana Dashboard**
  - Dashboard básico con 6 paneles
  - Alertas configurables
  - Exportación a JSON versionada
  
- [ ] **Health Checks Avanzados**
  - Liveness probe
  - Readiness probe
  - Dependency checks (Ollama, models)

**Entregables v3.6.0**:
- Sistema de plugins funcional con ≥3 plugins de ejemplo
- TTS real integrado (MeloTTS o Sherpa-ONNX)
- Dashboard de observabilidad básico
- Documentación completa de plugins y TTS
- CHANGELOG.md actualizado

---

## 📋 Fase 3: Preparación v4.0.0 (Dic 6, 2025 - Ene 31, 2026)

### Objetivo: Arquitectura Sidecars + Despliegue Híbrido

#### 3.1 Arquitectura Sidecars

**Concepto**:
- Separar capacidades avanzadas en containers independientes
- Comunicación vía gRPC o HTTP/2
- Escalado independiente por sidecar
- Despliegue flexible (local, Docker, Kubernetes)

**Sidecars Propuestos**:

1. **Vision Sidecar**
   - Qwen3-VL-4B servido independiente
   - API gRPC de procesamiento de imágenes
   - Swapping automático con modelo base
   
2. **Code Expert Sidecar**
   - VisCoder2-7B dedicado
   - Self-debug loop
   - API de code generation/review
   
3. **RAG Sidecar**
   - SearXNG + síntesis LLM
   - Cache web persistente
   - Auditoría HMAC de búsquedas

4. **Audio Processing Sidecar**
   - Omni-3B + NLLB + TTS
   - Pipeline completo de audio
   - Detección de idioma (LID)

**Infraestructura**:
- [ ] Protocolo gRPC definido (.proto files)
- [ ] Docker Compose para orquestación local
- [ ] Helm charts para Kubernetes (opcional)
- [ ] Service discovery automático
- [ ] Health checks y circuit breakers

#### 3.2 Despliegue Híbrido

**Estrategia**:
```
LOCAL (siempre):
  - LFM2-1.2B (Tier 1 CASCADE)
  - Embeddings (EmbeddingGemma)
  - TRM Classifier
  - MCP Core

REMOTO (Ollama/Sidecars):
  - MiniCPM-4.1 (Tier 2 CASCADE)
  - Qwen-3-8B (Tier 3 CASCADE)
  - Vision Sidecar (bajo demanda)
  - Code Expert Sidecar
  - RAG Sidecar
```

**Configuración**:
```yaml
# config/deployment.yaml (propuesta)
deployment:
  mode: "hybrid"  # local | remote | hybrid
  
  local:
    max_ram_gb: 4.0
    models:
      - lfm2
      - embeddings
      - trm_classifier
  
  remote:
    ollama_url: "${OLLAMA_BASE_URL}"
    sidecars:
      vision:
        url: "${VISION_SIDECAR_URL}"
        enabled: true
        fallback: "local"
      code:
        url: "${CODE_SIDECAR_URL}"
        enabled: true
```

#### 3.3 Auditoría y Firmado

- [ ] **Cosign Integration**
  - Firmar releases automáticamente
  - SBOM generation con Syft
  - Build attestation
  
- [ ] **Logs Inmutables**
  - HMAC por línea de log
  - Verificación de integridad
  - Scripts de auditoría
  
- [ ] **Compliance Checks**
  - GDPR compliance para logs
  - Data retention policies
  - Anonymization de datos sensibles

**Entregables v4.0.0**:
- Arquitectura sidecars completa y funcional
- Despliegue híbrido probado (local + remoto)
- Sistema de auditoría end-to-end
- KPIs validados: Latencia P50 <200ms, RAM <4.5GB
- Documentación de deployment
- CHANGELOG.md v4.0.0

---

## 🎯 KPIs por Fase

### v3.5.2 (Baseline)
- ✅ Tests: 100% passing de componentes migrados
- ✅ CI: 2 versiones Python (3.10, 3.11)
- ⏳ Cobertura: >80% en core modules
- ⏳ Migración: 100% (vs 56% actual)

### v3.6.0 (Plugins + TTS)
- Plugins: ≥3 plugins funcionales
- TTS Latency: <100ms TTFB
- Dashboard: 6 paneles operativos
- Documentación: PDK completo

### v4.0.0 (Sidecars + Híbrido)
- Latencia P50: <200ms (vs 2.3s actual)
- RAM Local P50: <4.5GB (vs 5.3GB actual)
- Sidecars: 4 operativos
- Auditoría: 100% verificable

---

## 📅 Cronograma Detallado

### Semana 1 (Nov 4-8): Finalizar v3.5.2
- **Lunes 4**: ✅ Fix CI pipeline
- **Martes 5**: Migrar Unified Model Wrapper + tests
- **Miércoles 6**: Migrar Graph Orchestrator + tests
- **Jueves 7**: Migrar Agents (expert, tiny, vision) + tests
- **Viernes 8**: Release v3.5.2 + documentación

### Semana 2-4 (Nov 11 - Dic 5): Desarrollo v3.6.0
- **Semana 2**: Diseño arquitectura plugins + POC
- **Semana 3**: Integración TTS + tests de latencia
- **Semana 4**: Dashboard observabilidad + release v3.6.0

### Mes 2 (Dic 6 - Ene 5): Desarrollo v4.0.0
- **Semana 5-6**: Implementación sidecars (Vision + Code)
- **Semana 7**: Sidecars RAG + Audio
- **Semana 8**: Testing integración, documentación

### Semana 9-10 (Ene 6-31): Estabilización v4.0.0
- **Semana 9**: Benchmarks completos, optimización
- **Semana 10**: Auditoría, firmado, release v4.0.0

---

## 🚨 Riesgos y Mitigaciones

### Riesgo 1: Migración lenta de componentes
**Impacto**: Retraso en v3.5.2  
**Probabilidad**: Media  
**Mitigación**: 
- Priorizar componentes críticos
- Aceptar migración parcial si tests pasan
- Documentar componentes legacy no migrados

### Riesgo 2: CI inestable
**Impacto**: Bloquea desarrollo  
**Probabilidad**: Baja (ya mitigado hoy)  
**Mitigación**:
- Mantener imports condicionales
- Tests locales antes de push
- CI badge en README para visibilidad

### Riesgo 3: Cambios arquitectura en v4.0
**Impacto**: Breaking changes, reescritura  
**Probabilidad**: Media  
**Mitigación**:
- Diseño incremental (v3.6.0 como bridge)
- Backward compatibility layers
- Deprecation warnings en v3.6.0

### Riesgo 4: Dependencias externas (Ollama, sidecars)
**Impacto**: Sistema no funcional sin infraestructura  
**Probabilidad**: Alta  
**Mitigación**:
- Fallbacks locales siempre disponibles
- Modo degradado documentado
- Health checks robustos

---

## 📚 Recursos Necesarios

### Desarrollo
- Python 3.10+ environment
- Docker + Docker Compose
- Ollama server (para tests de integración)
- GitHub Actions (CI/CD gratuito)

### Testing
- pytest + pytest-cov
- Hardware: 16GB RAM mínimo para tests locales
- GPU opcional (acelera tests de vision)

### Documentación
- MkDocs + Material theme
- Mermaid para diagramas
- PlantUML para arquitectura (opcional)

### Infraestructura (v4.0)
- Kubernetes cluster (opcional, para sidecars)
- Prometheus + Grafana (observabilidad)
- SearXNG instance (para RAG)

---

## 🎓 Aprendizajes y Mejores Prácticas

### De la migración v3.5.1 → v3.5.2
1. **Imports condicionales son críticos** para dependencias opcionales
2. **Tests exhaustivos** previenen regresiones en CI
3. **Versionado estricto** facilita trazabilidad
4. **Documentación incremental** > documentación al final

### Para v3.6.0 y v4.0.0
1. **Diseño antes de código**: Especificar APIs antes de implementar
2. **Tests primero**: TDD para componentes críticos
3. **Benchmarks continuos**: Validar KPIs en cada commit
4. **Feedback loops cortos**: Iteraciones semanales > sprints largos

---

## 📞 Contacto y Colaboración

**Repository**: [github.com/iagenerativa/sarai-agi](https://github.com/iagenerativa/sarai-agi)  
**Issues**: Reportar bugs y propuestas de features  
**Discussions**: Arquitectura y diseño  
**Pull Requests**: Contribuciones bienvenidas (ver CONTRIBUTING.md)

---

**Última actualización**: 4 de noviembre de 2025  
**Próxima revisión**: 8 de noviembre de 2025 (post v3.5.2)
