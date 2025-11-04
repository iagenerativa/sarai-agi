# Changelog

Todos los cambios notables de este repositorio se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto adhiere a [SemVer 2.0](https://semver.org/).

## [3.5.1] - 2025-11-04

### Added - Migración Base Completa
- **Pipeline paralela** (`src/sarai_agi/pipeline/`): Orquestación async con ThreadPoolExecutor configurable
- **Cuantización dinámica** (`src/sarai_agi/model/quantization.py`): Selector heurístico IQ3_XXS/Q4_K_M/Q5_K_M
- **Sistema de configuración** (`src/sarai_agi/configuration.py`): Carga YAML con alias bilingües
- **Test suite completo**: 11 pruebas (pipeline routing, quantization, config integrity)

### Migrated from SARAi_v2
- Pipeline paralela v3.5.1 (desacoplada de dependencias legacy)
- Selector de cuantización con historial EMA y scoring multi-factor
- Estructura de proyecto lista para GitHub con SemVer + CHANGELOG

### Infrastructure
- Documentación completa en español (ARCHITECTURE_OVERVIEW, MIGRATION_PLAN, ROADMAP)
- Bootstrap script para entorno virtualenv reproducible
- Configuración YAML con valores por defecto validados

[3.5.1]: https://github.com/iagenerativa/SARAi_AGI/releases/tag/v3.5.1


## Componentes v3.5.0 Pendientes de Migración

✅ **IMPLEMENTADO v3.5.0 ULTRA-LEAN + ADVANCED SYSTEMS** (última versión):
- **5 Micro-Mejoras (v3.4.1)**:
  - Streaming-TTS: Latencia -10ms TTFB (`core/streaming_tts_v341.py`)
  - Shared Cache: -0.2GB RAM con cache distribuido local (`core/shared_tts_cache.py`)
  - Auto-Quantization: -0.25GB RAM dinámico (`core/model_pool_v34.py`)
  - Predictive Confirmation: -50% mensajes confirmación (`core/predictive_confirmation_v341.py`)
  - Log Compression: -85% espacio disco (`scripts/log_compactor_v341.sh`)

- **3 Sistemas Avanzados (v3.5.0)**:
  - Security & Resilience: Detector amenazas, fallback automático, sanitización (`core/security_resilience_system.py`)
  - Emotional Context: 16 emociones, 8 culturas, perfiles usuario (`core/emotional_context_engine.py`)
  - Advanced Telemetry: Métricas Prometheus, alertas automáticas (`core/advanced_telemetry.py`)

- **Integrador Unificado**: 4 modos operacionales (BASIC/ADVANCED/SECURE/ENTERPRISE) en `core/sarai_advanced_integrator.py`
- **Configuración**: `config/advanced_system.json` con todos los parámetros v3.5

✅ **IMPLEMENTADO v3.4.0 CASCADE ORACLE** (base estable):
- **CASCADE 3-Tier**: LFM2-1.2B (Tier 1, LOCAL) + MiniCPM-4.1 (Tier 2, REMOTO) + Qwen-3-8B (Tier 3, REMOTO)
- **Confidence Router**: Selección automática de tier por confidence score (≥0.6 → LFM2, 0.3-0.6 → MiniCPM, <0.3 → Qwen-3)
- **Think Mode Classifier**: Detección automática de queries que requieren razonamiento profundo (fuerza Tier 3)
- **Multimodal Routing 7-Priority**: Vision→Code→RAG→Omni→Audio→CASCADE→Tiny
- **Vision Agent**: Qwen3-VL-4B (LOCAL, swapping con LFM2, TTL 60s)
- **Code Expert**: VisCoder2-7B (REMOTO Ollama, self-debug loop 3-shot)
- **Model Distribution**: LOCAL (LFM2 + Qwen3-VL swapping) vs REMOTO (MiniCPM + Qwen-3 + VisCoder2)
- **Tests Completos**: 5 suites (1,020 LOC) - tier selection, fallback, vision, code expert, E2E latency
- **Unified Model Wrapper** (8 backends) con overhead ≤5%
- **Skills Phoenix** (7 skills) con enrutamiento por TRM-Router y MCP v2 con fast-cache
- **Layers v2.13**: I/O (detección emoción), Memoria (RAG/tone), Fluidez (smoothing)
- **Auditoría**: logs SHA-256/HMAC para decisiones CASCADE, /health con content negotiation, /metrics Prometheus
- **DevSecOps**: releases firmadas (Cosign), SBOM (Syft), build attestation

⏳ **PRÓXIMO/ROADMAP** (post v3.5):
- Omni-Loop completo con skills containerizados
- Entrenamiento nocturno LoRA para Confidence Router
- MCP online tuning para ajuste dinámico de umbrales
- Benchmarks completos v3.5 con métricas de producción

---
