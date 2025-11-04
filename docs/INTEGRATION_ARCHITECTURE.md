# SARAi AGI - Arquitectura de Integración v3.6.0

## 🎯 Visión General

Este documento describe la **arquitectura integrada** de SARAi v3.6.0, donde todos los componentes modulares se conectan en un sistema cohesivo end-to-end.

**Estado:** ✅ PRODUCCIÓN (v3.6.0)
**Última actualización:** 2025-11-04

---

## 🏗️ Arquitectura del Sistema Integrado

### Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INPUT STAGE                                   │
│  • Input parsing y validación                                       │
│  • State initialization                                             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│               CLASSIFICATION STAGE (TRM Classifier)                  │
│  Callable: trm_classifier(state) → scores                           │
│                                                                      │
│  Output:                                                             │
│    - hard: float (0.0-1.0)    # Complejidad técnica                 │
│    - soft: float (0.0-1.0)    # Complejidad emocional               │
│    - web_query: float (0.0-1.0)  # Necesidad de búsqueda web        │
│                                                                      │
│  Implementación:                                                     │
│    - PRIMARY: TRMClassifier (torch, trained model)                  │
│    - FALLBACK: Rule-based classifier (keywords)                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 WEIGHTING STAGE (MCP Core)                           │
│  Callable: mcp_weighter(state) → weights                            │
│                                                                      │
│  Input: hard, soft scores                                           │
│  Output:                                                             │
│    - alpha: float (0.0-1.0)   # Weight para expert agent            │
│    - beta: float (0.0-1.0)    # Weight para empathy agent           │
│                                                                      │
│  Implementación:                                                     │
│    - PRIMARY: MCPCore (rules-based o learned mode)                  │
│    - FALLBACK: Direct mapping (alpha=hard, beta=soft)               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                 ┌─────────┴─────────┐
                 │                   │ (Parallel execution if enabled)
                 ▼                   ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │  EMOTION DETECTION   │  │  MODEL PREFETCH      │
    │  (Optional)          │  │  (Optional)          │
    │                      │  │                      │
    │  Input: state        │  │  Input: state        │
    │  Output: emotion{}   │  │  Output: model_name  │
    └──────────┬───────────┘  └──────────┬───────────┘
               │                         │
               └─────────┬───────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ROUTING STAGE (Cascade Router)                          │
│  Callable: router(state) → agent_key                                │
│                                                                      │
│  Decision Tree (7 priorities):                                      │
│    1. Vision     → "vision"     (imagen/OCR/gráficos)               │
│    2. Code       → "code"       (programming skill)                 │
│    3. RAG        → "rag"        (web_query ≥ 0.7)                   │
│    4. Omni-Loop  → "omni"       (imagen + texto >20 chars)          │
│    5. Audio      → "audio"      (input_type == "audio")             │
│    6. Expert     → "expert"     (alpha ≥ 0.7)                       │
│    7. Empathy    → "empathy"    (beta ≥ 0.7)                        │
│    8. Balanced   → "balanced"   (fallback default)                  │
│                                                                      │
│  Implementación: ConfidenceRouter + custom logic                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│           EXECUTION STAGE (Model Pool + Generators)                  │
│  Callable: response_generator(state, agent_key) → response          │
│                                                                      │
│  Agent-specific execution:                                          │
│                                                                      │
│  ┌─ RAG Agent ────────────────────────────────────────────────┐     │
│  │  1. Safe Mode check                                        │     │
│  │  2. Web search (SearXNG + cache)                           │     │
│  │  3. Audit PRE (SHA-256)                                    │     │
│  │  4. Synthesis prompt                                       │     │
│  │  5. LLM generation (expert model)                          │     │
│  │  6. Audit POST (HMAC)                                      │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌─ Expert Agent ─────────────────────────────────────────────┐     │
│  │  CASCADE 3-Tier Routing:                                   │     │
│  │    - Tier 1: LFM2-1.2B     (confidence ≥0.6) ~1.2s        │     │
│  │    - Tier 2: MiniCPM-4.1   (0.3-0.6)        ~4s           │     │
│  │    - Tier 3: Qwen-3-8B     (<0.3)           ~15s          │     │
│  │                                                            │     │
│  │  Features:                                                 │     │
│  │    - Dynamic quantization (IQ3_XXS/Q4_K_M/Q5_K_M)          │     │
│  │    - Context JIT (adaptive n_ctx)                          │     │
│  │    - LRU/TTL cache (hot: 5min, warm: 45s, cold: 15s)      │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌─ Empathy Agent ────────────────────────────────────────────┐     │
│  │  - Model: LFM2-1.2B (tiny)                                 │     │
│  │  - Mode: Empatía                                           │     │
│  │  - Features: Emotional context awareness                   │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌─ Balanced Agent ───────────────────────────────────────────┐     │
│  │  - Model: expert_short (LFM2 + escalation)                 │     │
│  │  - Mode: Balanceado entre hard/soft                        │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              POST-PROCESSING STAGE (Fluidity - TODO)                 │
│  • Tone smoothing                                                   │
│  • Response enhancement                                             │
│  • Cultural adaptation                                              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        OUTPUT STAGE                                  │
│  State completo con:                                                │
│    - response: str                                                  │
│    - metadata: dict                                                 │
│      - agent: str                                                   │
│      - emotion: dict                                                │
│      - pipeline_metrics: dict                                       │
│    - scores: hard, soft, web_query, alpha, beta                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes Integrados

### 1. TRM Classifier (`classifier/trm.py`)

**Responsabilidad:** Clasificar intenciones del input en 3 scores independientes.

**Callable Signature:**
```python
ClassifierCallable = Callable[[Dict[str, Any]], Dict[str, float]]

# Input:
state = {"input": "¿Cómo debuggear código Python?"}

# Output:
scores = {
    "hard": 0.85,      # Alta complejidad técnica
    "soft": 0.15,      # Baja complejidad emocional
    "web_query": 0.10  # No requiere búsqueda web
}
```

**Modos de operación:**
- **PRIMARY:** TRMClassifier con torch (arquitectura recursiva, modelo entrenado)
- **FALLBACK:** Rule-based classifier (keywords, sin dependencias externas)

**Factory:** `create_trm_classifier_callable(config)`

**LOC:** 273 (classifier/trm.py)
**Tests:** test_trm_classifier.py

---

### 2. MCP Core (`mcp/core.py`)

**Responsabilidad:** Calcular weights alpha/beta para routing expert/empathy.

**Callable Signature:**
```python
WeightingCallable = Callable[[Dict[str, Any]], Dict[str, float]]

# Input:
state = {
    "input": "texto original",
    "hard": 0.85,
    "soft": 0.15
}

# Output:
weights = {
    "alpha": 0.82,  # Weight para expert
    "beta": 0.18    # Weight para empathy
}
```

**Modos de operación:**
- **Rules-based:** Heurísticas basadas en hard/soft scores
- **Learned:** Neural network entrenada (requiere torch)
- **Cache:** Vector Quantization para queries similares

**Factory:** `create_mcp_weighter_callable(config)`

**LOC:** 500 (mcp/core.py)
**Tests:** test_mcp.py

---

### 3. Emotional Context Engine (`emotion/context_engine.py`)

**Responsabilidad:** Detectar emociones (16), culturas (8), y proveer recomendaciones de modulación.

**Callable Signature:**
```python
EmotionDetectorCallable = Callable[[bytes], Optional[Dict[str, Any]]]

# Input:
audio_or_text = "Me siento frustrado con este error"

# Output:
emotion = {
    "emotion": "FRUSTRATED",
    "confidence": 0.85,
    "empathy_level": 0.9,
    "cultural_context": "spain",
    "voice_modulation": {
        "speed": 0.9,
        "pitch": 1.0,
        "emotion_intensity": 0.9
    }
}
```

**Características:**
- 16 emociones: neutral, excited, frustrated, urgent, confused, etc.
- 8 culturas: Spain, Mexico, Argentina, Colombia, USA, UK, France, Germany
- User profiling (últimas 20 interacciones)
- Voice modulation recommendations

**Factory:** `create_emotion_detector_callable(config)`

**LOC:** 700 (emotion/context_engine.py)
**Tests:** test_emotional_context.py

---

### 4. Cascade Router (`cascade/confidence_router.py`)

**Responsabilidad:** Routing inteligente basado en confianza y especialización.

**Callable Signature:**
```python
RouterCallable = Callable[[Dict[str, Any]], str]

# Input:
state = {
    "input": "¿Cuál es el clima en Madrid?",
    "alpha": 0.3,
    "beta": 0.2,
    "web_query": 0.9
}

# Output:
agent_key = "rag"  # One of: rag, expert, empathy, balanced, vision, code, omni, audio
```

**Decision Tree (7 priorities):**
1. **Vision:** imagen/OCR/gráficos → "vision"
2. **Code:** programming skill → "code"
3. **RAG:** web_query ≥ 0.7 → "rag"
4. **Omni-Loop:** imagen + texto >20 chars → "omni"
5. **Audio:** input_type == "audio" → "audio"
6. **Expert:** alpha ≥ 0.7 → "expert"
7. **Empathy:** beta ≥ 0.7 → "empathy"
8. **Balanced:** fallback default → "balanced"

**Factory:** `create_router_callable(config)`

**LOC:** 541 (cascade/confidence_router.py)
**Tests:** test_cascade.py

---

### 5. Model Pool (`model/pool.py`)

**Responsabilidad:** Gestión inteligente de modelos con cache, quantization, y fallback.

**Características:**
- **LRU/TTL Cache:** hot (5min), warm (45s), cold (15s)
- **Dynamic Quantization:** IQ3_XXS (450MB), Q4_K_M (700MB), Q5_K_M (850MB)
- **Context JIT:** Adaptive n_ctx basado en prompt length
- **Fallback Chain:** expert_long → expert_short → tiny
- **Working-set Detection:** ≥3 accesos en 5min = hot

**API Principal:**
```python
pool = ModelPool()

# Get model con auto-context
model = pool.get_for_prompt("expert_short", "What is Python?")
# → Loads with n_ctx=512 (short prompt)

# Auto-quantization
params = pool.get_model_params("Write a 2000 word essay...")
# → {'quantization': 'Q5_K_M', 'n_ctx': 4096}
```

**LOC:** 831 (model/pool.py)
**Tests:** test_model_pool.py

---

### 6. RAG Agent (`agents/rag.py`)

**Responsabilidad:** Pipeline completa de búsqueda web + síntesis.

**Pipeline (6 pasos):**
1. **SAFE MODE CHECK:** Verificar Safe Mode
2. **BÚSQUEDA CACHEADA:** SearXNG + WebCache (TTL dinámico)
3. **AUDITORÍA PRE:** log_web_query() con SHA-256
4. **SÍNTESIS PROMPT:** Prompt engineering con snippets
5. **LLM GENERATION:** Expert model (short/long según contexto)
6. **AUDITORÍA POST:** log_web_query() con response + HMAC

**API Principal:**
```python
from sarai_agi.agents.rag import execute_rag

state = {
    "input": "¿Cómo está el clima en Tokio?",
    "scores": {"web_query": 0.9}
}

result_state = execute_rag(state, model_pool)
# → state updated with 'response' and 'rag_metadata'
```

**LOC:** 337 (agents/rag.py)
**Tests:** test_rag_system.py (22 tests)

---

## 🔄 Flujo de Ejecución Detallado

### Ejemplo 1: Query Técnica

```python
Input: "¿Cómo implementar quicksort en Python?"

1. TRM Classifier:
   scores = {
       "hard": 0.88,
       "soft": 0.12,
       "web_query": 0.05
   }

2. MCP Weighter:
   weights = {
       "alpha": 0.85,  # Alta confianza en expert
       "beta": 0.15
   }

3. Emotion Detector:
   emotion = {
       "emotion": "NEUTRAL",
       "confidence": 0.75,
       "empathy_level": 0.3
   }

4. Router:
   agent_key = "expert"  # alpha ≥ 0.7

5. Response Generator (Expert):
   - Model Pool selecciona: expert_short
   - Cascade Router analiza confidence
   - Tier 1 (LFM2): confidence=0.7 → responde directamente
   - Latency: ~1.2s

Output: Respuesta técnica con código quicksort
```

### Ejemplo 2: Query Emocional

```python
Input: "Me siento triste y necesito apoyo"

1. TRM Classifier:
   scores = {
       "hard": 0.10,
       "soft": 0.85,
       "web_query": 0.05
   }

2. MCP Weighter:
   weights = {
       "alpha": 0.15,
       "beta": 0.82  # Alta confianza en empathy
   }

3. Emotion Detector:
   emotion = {
       "emotion": "FRUSTRATED",
       "confidence": 0.88,
       "empathy_level": 0.95,
       "cultural_context": "spain"
   }

4. Router:
   agent_key = "empathy"  # beta ≥ 0.7

5. Response Generator (Empathy):
   - Model Pool selecciona: tiny (LFM2 modo empatía)
   - Response adaptada con empathy_level=0.95
   - Latency: ~1.5s

Output: Respuesta empática y de apoyo emocional
```

### Ejemplo 3: Query Web

```python
Input: "¿Cuál es el clima actual en Madrid?"

1. TRM Classifier:
   scores = {
       "hard": 0.15,
       "soft": 0.10,
       "web_query": 0.92  # Alta necesidad de búsqueda web
   }

2. MCP Weighter:
   weights = {
       "alpha": 0.35,
       "beta": 0.25
   }

3. Router:
   agent_key = "rag"  # web_query ≥ 0.7 (Priority 3)

4. RAG Agent:
   a. Safe Mode check: OK
   b. Web search: SearXNG + cache
      - Query: "clima Madrid actual"
      - Results: 5 snippets (cached, TTL=5min)
   c. Audit PRE: SHA-256 logged
   d. Synthesis prompt:
      """
      Basándote en los siguientes resultados de búsqueda:
      1. "Madrid: 18°C, parcialmente nublado..."
      2. "Pronóstico para hoy: máxima 20°C..."
      ...
      Responde: ¿Cuál es el clima actual en Madrid?
      """
   e. LLM generation: expert_short
   f. Audit POST: HMAC logged

5. Response:
   "En Madrid, la temperatura actual es de 18°C con cielo
    parcialmente nublado. Se espera una máxima de 20°C."

Output: Respuesta sintetizada con información actualizada
```

---

## 🧩 Integración de Componentes

### Factory Pattern

Todos los componentes se integran mediante **factory functions** que devuelven callables compatibles con `PipelineDependencies`:

```python
from sarai_agi.core import create_integrated_pipeline

# Create fully integrated pipeline
pipeline = create_integrated_pipeline(config={
    "enable_parallelization": True,
    "min_input_length": 20,
})

# Execute
result = await pipeline.run({"input": "Your query here"})

# Cleanup
await pipeline.shutdown()
```

### Dependency Injection

La pipeline usa **dependency injection** explícita:

```python
@dataclass
class PipelineDependencies:
    trm_classifier: ClassifierCallable          # TRM Classifier
    mcp_weighter: WeightingCallable             # MCP Core
    response_generator: ResponseGeneratorCallable  # Model Pool + Agents
    emotion_detector: Optional[EmotionDetectorCallable] = None
    prefetch_model: Optional[PrefetchCallable] = None
    router: Optional[RouterCallable] = None
```

Cada factory crea el callable correspondiente:

```python
dependencies = PipelineDependencies(
    trm_classifier=create_trm_classifier_callable(),
    mcp_weighter=create_mcp_weighter_callable(),
    response_generator=create_response_generator_callable(),
    emotion_detector=create_emotion_detector_callable(),
    prefetch_model=create_prefetch_callable(),
    router=create_router_callable(),
)
```

### Graceful Degradation

Todos los componentes tienen **fallbacks** para degradación graceful:

| Component | Primary | Fallback |
|-----------|---------|----------|
| TRM Classifier | TRMClassifier (torch) | Rule-based (keywords) |
| MCP Weighter | MCPCore (rules/learned) | Direct mapping (alpha=hard) |
| Emotion Detector | EmotionalContextEngine | None (optional component) |
| Router | ConfidenceRouter | Default balanced |
| Model Pool | Full cache + quantization | Simple model loading |
| RAG Agent | Full pipeline | Sentinel response |

---

## 📊 Métricas del Pipeline

### Pipeline Metrics

El pipeline recopila métricas detalladas en cada ejecución:

```python
result["metadata"]["pipeline_metrics"] = {
    "classify_ms": 12.5,      # TRM Classifier latency
    "weights_ms": 3.2,        # MCP weighter latency
    "emotion_ms": 8.7,        # Emotion detection latency
    "routing_ms": 0.8,        # Router latency
    "generation_ms": 1250.0,  # Response generation latency
    "response_latency_ms": 1285.3,  # Total latency
    "prefetch_target": "expert_short"  # Prefetched model
}
```

### Performance Targets (v3.6.0)

| Metric | Target | Actual |
|--------|--------|--------|
| Classification latency | <50ms | ~12ms |
| Weighting latency | <20ms | ~3ms |
| Emotion detection | <50ms | ~9ms |
| Routing latency | <5ms | ~1ms |
| Total overhead | <150ms | ~30ms |
| Response latency P50 | <3s | ~1.3s (LFM2), ~25s (RAG) |
| Response latency P99 | <30s | ~18s (Qwen-3) |

---

## 🧪 Testing de Integración

### Test Suite Completo

**Archivo:** `tests/test_integration_e2e.py`

**Cobertura:**
- ✅ Pipeline creation
- ✅ Technical query routing (expert)
- ✅ Emotional query routing (empathy)
- ✅ Web query routing (RAG)
- ✅ Emotion detection
- ✅ Metrics collection
- ✅ Parallel/sequential execution
- ✅ Scores propagation
- ✅ Multiple sequential queries
- ✅ Error handling
- ✅ State immutability
- ✅ Component integration
- ✅ Performance tests

**Ejecución:**
```bash
# Suite completa
pytest tests/test_integration_e2e.py -v

# Con coverage
pytest tests/test_integration_e2e.py --cov=src/sarai_agi/core --cov-report=html

# Clase específica
pytest tests/test_integration_e2e.py::TestIntegratedPipeline -v
```

---

## 🚀 Uso desde CLI

### Instalación

```bash
# Clonar repo
git clone https://github.com/iagenerativa/sarai-agi.git
cd sarai-agi

# Setup environment
./scripts/bootstrap_env.sh
source .venv/bin/activate

# Instalar dependencias
pip install -e .
```

### CLI Integrada

```bash
# Query única
python cli.py "¿Cómo funciona el aprendizaje por refuerzo?"

# Query con verbose
python cli.py --verbose "¿Qué es Python?"

# Modo interactivo
python cli.py --interactive

# Modo interactivo con verbose
python cli.py -i -v
```

**Output ejemplo:**
```
================================================================================
QUERY: ¿Cómo funciona el aprendizaje por refuerzo?
================================================================================

📝 RESPONSE (expert agent):
--------------------------------------------------------------------------------
El aprendizaje por refuerzo es una técnica de machine learning donde un agente
aprende a tomar decisiones óptimas a través de prueba y error, recibiendo
recompensas o penalizaciones por sus acciones...
--------------------------------------------------------------------------------

🔍 METADATA:
  Agent: expert

  Emotion:
    Detected: NEUTRAL
    Confidence: 0.75
    Empathy Level: 0.30
    Cultural Context: neutral

  Scores:
    Hard: 0.82
    Soft: 0.18
    Web Query: 0.05
    Alpha: 0.80
    Beta: 0.20

  Pipeline Metrics:
    Classify: 12.34ms
    Weights: 3.21ms
    Emotion: 8.76ms
    Routing: 0.87ms
    Generation: 1234.56ms
    Total: 1265.43ms
```

---

## 📚 Referencias

### Documentación de Componentes

- **TRM Classifier:** `src/sarai_agi/classifier/trm.py`
- **MCP Core:** `src/sarai_agi/mcp/core.py`
- **Emotional Context:** `src/sarai_agi/emotion/context_engine.py`
- **Cascade Router:** `src/sarai_agi/cascade/confidence_router.py`
- **Model Pool:** `src/sarai_agi/model/pool.py`
- **RAG Agent:** `src/sarai_agi/agents/rag.py`
- **Pipeline:** `src/sarai_agi/pipeline/parallel.py`

### Tests

- **Integration E2E:** `tests/test_integration_e2e.py`
- **TRM Classifier:** `tests/test_trm_classifier.py`
- **MCP Core:** `tests/test_mcp.py`
- **Emotion:** `tests/test_emotional_context.py`
- **Cascade:** `tests/test_cascade.py`
- **Model Pool:** `tests/test_model_pool.py`
- **RAG System:** `tests/test_rag_system.py`

### Documentación Adicional

- **Arquitectura General:** `docs/ARCHITECTURE_OVERVIEW.md`
- **RAG Memory:** `docs/RAG_MEMORY.md`
- **Estado v3.4:** `docs/ESTADO_ACTUAL_v3.4.md`
- **Estado v3.5:** `docs/ESTADO_ACTUAL_v3.5.md`
- **Migration Plan:** `docs/MIGRATION_PLAN_v3_5_1.md`

---

## 🎯 Roadmap de Integración

### ✅ Completado (v3.6.0)

- [x] TRM Classifier integration
- [x] MCP weighting system
- [x] Emotional Context Engine
- [x] Cascade Router
- [x] Model Pool con cache LRU/TTL
- [x] RAG Agent completo
- [x] Pipeline paralela
- [x] Factory functions para todos los componentes
- [x] CLI integrada
- [x] Tests E2E completos
- [x] Documentación de arquitectura

### 🔄 En Progreso (v3.7.0)

- [ ] Fluidity Layer (Layer3 - tone smoothing)
- [ ] Vision integration (Qwen3-VL-4B)
- [ ] Code integration (VisCoder2-7B)
- [ ] Audio integration (Omni-3B + NLLB)
- [ ] Omni-Loop refinement
- [ ] Skills integration (SQL, Bash, Network)

### 📋 Pendiente (v4.0+)

- [ ] Sidecars architecture
- [ ] Ethics Guard pre/post filtering
- [ ] Meta-learning feedback loop
- [ ] Advanced telemetry dashboard
- [ ] Multi-user support
- [ ] Production deployment guides

---

## 📝 Changelog

### v3.6.0 (2025-11-04)

- ✨ **NEW:** Sistema integrado completo
- ✨ **NEW:** Factory functions para todos los componentes
- ✨ **NEW:** CLI integrada con modo interactivo
- ✨ **NEW:** Tests E2E completos (24 tests)
- ✨ **NEW:** Documentación de arquitectura integrada
- 🐛 **FIX:** Graceful degradation en todos los componentes
- 🐛 **FIX:** Error handling completo
- 📚 **DOCS:** INTEGRATION_ARCHITECTURE.md
- 🧪 **TESTS:** test_integration_e2e.py (24 tests, 100% passing)

---

**Autor:** SARAi Team
**Licencia:** MIT
**Repositorio:** https://github.com/iagenerativa/sarai-agi
**Versión:** v3.6.0
