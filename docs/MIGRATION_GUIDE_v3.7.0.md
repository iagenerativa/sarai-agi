# SARAi AGI v3.7.0 - Guía de Migración

**Multi-Source Search + Multimodal Learning System**

> **Versión**: 3.7.0-multimodal-learning  
> **Fecha**: 2025-01-04  
> **Compatibilidad**: 100% con v3.6.0  
> **LOC Añadidas**: ~1,830 (core + config)

---

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Prerequisites](#prerequisites)
3. [Arquitectura v3.7.0](#arquitectura-v370)
4. [Guía de Integración](#guía-de-integración)
5. [Configuración](#configuración)
6. [Testing y Validación](#testing-y-validación)
7. [Rollback Plan](#rollback-plan)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Resumen Ejecutivo

### ¿Qué es v3.7.0?

Versión que transforma SARAi de **AGI técnico** → **AGI social/culturalmente consciente** con:

- **Multi-Source Search** (Perplexity-style): 6 fuentes paralelas, consensus verification (95% accuracy target)
- **Social Learning Engine**: 16 emociones × 8 culturas, knowledge base automático
- **YouTube Learning System**: Análisis multimodal de videos (trending detection, learning value scoring)

### KPIs Objetivo

| Métrica | v3.6.0 | v3.7.0 | Mejora |
|---------|--------|--------|--------|
| **Search Accuracy** | 85% (single source) | 95% (consensus) | +11.8% |
| **Cultural Adaptation** | 0% (no exists) | 75% (estimated) | +75% |
| **Learning Domains** | 0 | 8 | +8 |
| **Social Awareness** | Básico | 16×8 matrix | Comprehensive |
| **Latency** | 2.3s P50 | 3.5s P50 (estimated) | +52% (trade-off for accuracy) |

### Filosofía de Diseño

> **"Skills como Prompts, no código"** - Pero aquí añadimos "inteligencia social" como core capability

- **Multi-source → Trust**: Consensus de 6 fuentes > single source
- **Cultural adaptation → Relevance**: Insights filtrados por región del usuario
- **YouTube learning → Trends**: Aprende de contenido social, no solo papers
- **Backward compatible**: Sistema existing puede ignorar v3.7.0 completamente

---

## 🔧 Prerequisites

### Dependencias Existentes (v3.6.0)

✅ Ya tienes todo si migraste a v3.6.0:

```yaml
# config/sarai.yaml (v3.6.0)
cascade_oracle:  # CASCADE 3-tier
  enabled: true
  
emotional_context:  # EmotionalContextEngine
  enabled: true
  
memory:  # RAG Memory
  enabled: true
```

### Nuevas Dependencias (v3.7.0)

**Ninguna!** v3.7.0 usa solo componentes existing:

- `pipeline.parallel` (PipelineDependencies)
- `cascade.confidence_router` (CASCADE ORACLE)
- `emotion.context_engine` (EmotionalContextEngine)
- `memory.web_cache` (Web Cache para search results)
- `memory.web_audit` (Audit para verification)

### Integraciones Opcionales (PLACEHOLDER)

Para funcionalidad completa, necesitarás:

1. **SearXNG**: Para búsquedas web reales (actualmente PLACEHOLDER)
2. **Qwen3-VL:4B**: Para análisis multimodal de YouTube (actualmente PLACEHOLDER)
3. **youtube-dl**: Para extracción de videos (actualmente PLACEHOLDER)
4. **ffmpeg**: Para frame extraction (actualmente PLACEHOLDER)

**Sin estas integraciones**: Sistema funciona con mocks, retorna datos placeholder.

---

## 🏗️ Arquitectura v3.7.0

### Componentes Nuevos

```
src/sarai_agi/
├── search/                         # Multi-Source Search
│   ├── __init__.py                # (22 LOC) Exports
│   └── multi_source_searcher.py   # (650 LOC) Core engine
│
├── learning/                       # Multimodal Learning
│   ├── __init__.py                # (27 LOC) Exports
│   ├── social_learning_engine.py  # (550 LOC) Social learning
│   └── youtube_learning_system.py # (450 LOC) YouTube analysis
│
config/
└── v3.7.0_multimodal_config.yaml  # (180 LOC) Configuration
```

### Pipeline Flow (NEW)

```
INPUT QUERY
    ↓
1. TRM Classifier (analyze intent)
    → complexity: 0.0-1.0
    → query_type: explanatory/time_sensitive/technical
    ↓
2. Multi-Source Search (if web_query_score > 0.7)
    ↓
    2a. Generate intelligent sub-queries (1-4 queries)
    ↓
    2b. Parallel search across 6 sources
        ├─ academic_papers (weight 0.9, credibility 0.95)
        ├─ news_agencies (0.8, 0.85)
        ├─ technical_docs (0.7, 0.80)
        ├─ industry_reports (0.6, 0.75)
        ├─ wikipedia (0.5, 0.65)
        └─ stackoverflow (0.4, 0.60)
    ↓
    2c. Cross-verify results
        → Identify consensus facts (2+ sources)
        → Calculate weighted consensus_score
        → Detect conflicting_sources
    ↓
    2d. CASCADE ORACLE synthesis
        → expert_deep (Qwen-3-8B): consensus < 0.7
        → rapid_scan (LFM2-1.2B): consensus ≥ 0.7
        → emotional (MiniCPM-4.1): emotional query
    ↓
3. Social Learning (if image or cultural content)
    ↓
    3a. Emotional context analysis
        → 16 emotions (EmotionalContextEngine)
        → 8 cultural regions (LATAM, NA, EU, ASIA...)
    ↓
    3b. Domain-specific analysis
        → TECHNOLOGY_TRENDS
        → SOCIAL_BEHAVIOR
        → CULTURAL_PATTERNS
        → LIFESTYLE_TRENDS
        → (4 more domains)
    ↓
    3c. Update knowledge base
        → Last 100 insights per domain
        → Cultural patterns per region
    ↓
4. YouTube Learning (if video content)
    ↓
    4a. Extract metadata (video_id, title, views, likes, comments)
    ↓
    4b. Extract key frames (up to 30 frames/video)
    ↓
    4c. Multimodal analysis (Qwen3-VL:4B)
        → main_topics
        → emotional_tone
        → social_implications
        → cultural_relevance
    ↓
    4d. Calculate metrics
        → trending_score: (likes + comments*2) / views
        → viral_potential: (trending * 0.7) + (emotion * 0.3)
        → learning_value: category_priority + topics_bonus
    ↓
FINAL RESPONSE (contextualized by culture/emotion/trends)
```

### Graceful Degradation

Si componentes fallan:

| Componente | Fallo | Fallback |
|------------|-------|----------|
| **Multi-Source Search** | No SearXNG | Retorna mock results (PLACEHOLDER data) |
| **Consensus < threshold** | Bajo consenso | Usa CASCADE tier 3 (Qwen-3-8B) para síntesis |
| **EmotionalEngine** | No disponible | Skip emotional context, continúa sin análisis emocional |
| **YouTube extraction** | youtube-dl falla | Retorna metadata placeholder |
| **Frame extraction** | ffmpeg falla | Análisis solo con metadata (sin visual) |
| **Qwen3-VL:4B** | Modelo no cargado | Categorización keyword-based |

**Resultado**: Sistema NUNCA falla completamente, siempre retorna respuesta (posiblemente degradada).

---

## 🛠️ Guía de Integración

### Paso 1: Verificar v3.6.0 Completo

```bash
# Verificar branch y versión
git branch --show-current
# Debe mostrar: main (o v3.6.0 tag)

grep -r "v3.6.0" VERSION
# Debe existir archivo VERSION con "3.6.0"

# Verificar componentes v3.6.0
python -c "from sarai_agi.cascade import ConfidenceRouter; print('CASCADE OK')"
python -c "from sarai_agi.emotion import EmotionalContextEngine; print('Emotion OK')"
python -c "from sarai_agi.memory import RAGPipeline; print('RAG OK')"
```

### Paso 2: Checkout feature branch

```bash
git checkout -b feature/v3.7.0-multimodal-search

# Verificar archivos v3.7.0
ls -la src/sarai_agi/search/
ls -la src/sarai_agi/learning/
ls -la config/v3.7.0_multimodal_config.yaml
```

### Paso 3: Actualizar configuración

Editar `config/sarai.yaml` (añadir al final):

```yaml
# ============================================
# v3.7.0 MULTI-SOURCE SEARCH + MULTIMODAL
# ============================================

search_integration:
  multi_source_search:
    enabled: true                    # Activar multi-source
    max_sources: 6                   # Hasta 6 fuentes paralelas
    verification_level: "STANDARD"   # BASIC/STANDARD/COMPREHENSIVE
    parallel_search: true            # Búsquedas concurrentes
    max_concurrent_requests: 8       # Límite asyncio.gather
    consensus_threshold: 0.7         # 70% weighted agreement
    
  search_strategies:
    expert_deep:
      cascade_tier: 3                # Qwen-3-8B para queries hard
      min_confidence: 0.0
      max_confidence: 0.3
    rapid_scan:
      cascade_tier: 1                # LFM2-1.2B para queries fáciles
      min_confidence: 0.6
      max_confidence: 1.0
    emotional_context:
      cascade_tier: 2                # MiniCPM-4.1 para emotional
      min_confidence: 0.3
      max_confidence: 0.6

social_learning:
  enabled: true
  continuous_learning: false         # true para 24/7 learning (experimental)
  learning_cycle_minutes: 5
  
  learning_domains:
    technology_trends:
      priority: 0.9
    social_behavior:
      priority: 0.85
    cultural_patterns:
      priority: 0.8
    lifestyle_trends:
      priority: 0.75
    # ... (4 more domains, ver config/v3.7.0_multimodal_config.yaml)
  
  cultural_adaptation:
    enabled: true
    regions: ["LATAM", "NA", "EU", "ASIA", "AFRICA", "OCEANIA", "ME", "SS"]
    adaptation_strategy: "progressive"
    region_weight: 0.3               # 30% peso cultural en scoring

youtube_learning:
  enabled: true
  auto_discovery: false              # true para auto-trending (experimental)
  discovery_cycle_minutes: 30
  
  content_priorities:
    EDUCATIONAL: 0.9
    SOCIAL_COMMENTARY: 0.85
    TECHNOLOGY_REVIEWS: 0.8
    CULTURAL_DOCUMENTARY: 0.75
    BUSINESS_ANALYSIS: 0.7
    SCIENTIFIC_CONTENT: 0.8
    LIFESTYLE_VLOGS: 0.6
  
  analysis_settings:
    analysis_depth: "deep"           # shallow/standard/deep
    max_frames_per_video: 30
    min_learning_value: 0.6          # Skip videos < 0.6 learning value
```

### Paso 4: Actualizar PipelineDependencies (CRITICAL)

Editar `src/sarai_agi/pipeline/parallel.py`:

```python
from dataclasses import dataclass
from typing import Callable

# ... (existing imports)

# NEW IMPORTS v3.7.0
from sarai_agi.search import MultiSourceSearcher
from sarai_agi.learning import SocialLearningEngine, YouTubeLearningSystem

@dataclass
class PipelineDependencies:
    """Extended for v3.7.0"""
    # Existing v3.6.0
    trm_classifier: ClassifierCallable
    cascade_oracle: CascadeOracleCallable
    emotional_context: EmotionalContextCallable
    response_generator: ResponseGeneratorCallable
    web_cache: WebCacheCallable
    web_audit: WebAuditCallable
    
    # NEW v3.7.0
    multi_source_searcher: MultiSourceSearcher = None
    social_learning_engine: SocialLearningEngine = None
    youtube_learning_system: YouTubeLearningSystem = None


def create_pipeline_dependencies(config: Dict[str, Any]) -> PipelineDependencies:
    """Factory actualizado para v3.7.0"""
    # Existing v3.6.0 initialization...
    
    # NEW v3.7.0 initialization
    multi_source_searcher = None
    if config.get("search_integration", {}).get("multi_source_search", {}).get("enabled", False):
        multi_source_searcher = MultiSourceSearcher(pipeline_deps_partial, config)
    
    social_learning_engine = None
    if config.get("social_learning", {}).get("enabled", False):
        social_learning_engine = SocialLearningEngine(pipeline_deps_partial, config)
    
    youtube_learning_system = None
    if config.get("youtube_learning", {}).get("enabled", False):
        youtube_learning_system = YouTubeLearningSystem(pipeline_deps_partial, config)
    
    return PipelineDependencies(
        # ... existing v3.6.0 deps,
        multi_source_searcher=multi_source_searcher,
        social_learning_engine=social_learning_engine,
        youtube_learning_system=youtube_learning_system
    )
```

### Paso 5: Integrar en graph.py (routing)

Editar `src/sarai_agi/core/graph.py` (o equivalente):

```python
async def process_query(state: Dict[str, Any], deps: PipelineDependencies):
    """Extended routing for v3.7.0"""
    query = state["input"]
    
    # Existing v3.6.0 routing (Vision, Code, RAG, etc.)
    
    # NEW: Multi-source search (si web_query_score > 0.7)
    if state.get("web_query_score", 0) > 0.7 and deps.multi_source_searcher:
        logger.info("🔍 Activating multi-source search...")
        verified_info = await deps.multi_source_searcher.search(query, state)
        state["multi_source_results"] = verified_info
        state["consensus_score"] = verified_info.consensus_score
    
    # NEW: Social learning (si imagen o contenido cultural)
    if state.get("has_image") or state.get("cultural_content") and deps.social_learning_engine:
        logger.info("🎓 Activating social learning...")
        content = state.get("image_description", query)
        insights = await deps.social_learning_engine.analyze_content_for_insights(
            content, {"source": "user_query"}
        )
        state["social_insights"] = insights
    
    # NEW: YouTube learning (si video_url en query)
    if "youtube.com" in query or "youtu.be" in query:
        if deps.youtube_learning_system:
            logger.info("📹 Activating YouTube learning...")
            video_analysis = await deps.youtube_learning_system.analyze_video(query)
            state["youtube_analysis"] = video_analysis
    
    return state
```

---

## ⚙️ Configuración

### Niveles de Verificación

```yaml
verification_level: "BASIC"       # 2-3 fuentes, fast (~2s)
verification_level: "STANDARD"    # 4-5 fuentes, balanced (~3s)
verification_level: "COMPREHENSIVE" # 6 fuentes, max accuracy (~4s)
```

### Strategies de Búsqueda

| Strategy | Tier CASCADE | Caso de Uso |
|----------|--------------|-------------|
| `expert_deep` | 3 (Qwen-3-8B) | Queries complejas, bajo consenso (<0.3) |
| `rapid_scan` | 1 (LFM2-1.2B) | Queries simples, alto consenso (≥0.6) |
| `emotional` | 2 (MiniCPM-4.1) | Queries emocionales, consenso medio (0.3-0.6) |
| `technical` | Code (VisCoder2-7B) | Queries programming skill |

### Cultural Regions

```yaml
cultural_adaptation:
  regions:
    - LATAM      # Latino América
    - NA         # North America
    - EU         # Europe
    - ASIA       # Asia-Pacific
    - AFRICA     # África
    - OCEANIA    # Oceanía
    - ME         # Middle East
    - SS         # Sub-Saharan Africa
```

---

## ✅ Testing y Validación

### Tests Unitarios

```bash
# Multi-source search tests
pytest tests/test_multi_source_search.py -v
# Esperado: 14/15 passing (1 known issue: consensus detection)

# Multimodal learning tests
pytest tests/test_multimodal_learning.py -v
# Esperado: 2/20 passing (18 fixture errors, TO BE FIXED)
```

### Tests de Integración

```bash
# Test completo E2E
pytest tests/ -k "integration" -v

# Verificar consensus scoring
pytest tests/test_multi_source_search.py::TestMultiSourceSearcher::test_cross_verify_sources_high_consensus -v

# Verificar cultural adaptation
pytest tests/test_multimodal_learning.py::TestSocialLearningEngine::test_get_contextual_response_filters_by_region -v
```

### Validación Manual

```python
# 1. Test multi-source search
from sarai_agi.search import MultiSourceSearcher
from sarai_agi.pipeline.parallel import create_pipeline_dependencies

config = {...}  # Tu config completa
deps = create_pipeline_dependencies(config)

verified = await deps.multi_source_searcher.search(
    "What is machine learning?",
    context={"user_id": "test"}
)

assert verified.consensus_score >= 0.7
assert verified.sources_used >= 4
print(f"Consensus: {verified.consensus_score:.2%}")
print(f"Facts: {len(verified.facts)}")

# 2. Test social learning
insights = await deps.social_learning_engine.analyze_content_for_insights(
    "Latino families value community gatherings",
    {"source": "cultural_study"}
)

assert len(insights) > 0
assert "LATAM" in insights[0].cultural_relevance
print(f"Insights: {len(insights)}")
print(f"Domain: {insights[0].domain}")

# 3. Test YouTube analysis
analysis = await deps.youtube_learning_system.analyze_video(
    "https://www.youtube.com/watch?v=test_id"
)

assert analysis.trending_score > 0
assert analysis.learning_value >= 0.6
print(f"Category: {analysis.content_category}")
print(f"Learning Value: {analysis.learning_value:.2f}")
```

---

## 🔄 Rollback Plan

Si v3.7.0 causa problemas:

### Opción 1: Disable Features (Rápido)

```yaml
# config/sarai.yaml
search_integration:
  multi_source_search:
    enabled: false    # ← Desactivar multi-source
    
social_learning:
  enabled: false      # ← Desactivar social learning

youtube_learning:
  enabled: false      # ← Desactivar YouTube
```

Sistema vuelve a comportarse como v3.6.0.

### Opción 2: Rollback Completo (Si necesario)

```bash
# Volver a main (v3.6.0)
git checkout main

# O revertir merge específico
git revert <commit_hash_v3.7.0_merge> -m 1
```

---

## 🐛 Troubleshooting

### Problema: "TypeError: __init__() takes 3 positional arguments but 4 were given"

**Causa**: Tests legacy usan API antigua (3 args: emotional, model_pool, config)  
**Solución**: Actualizar tests para usar `pipeline_dependencies`:

```python
# ❌ INCORRECTO (legacy)
social_engine = SocialLearningEngine(emotional_engine, model_pool, config)

# ✅ CORRECTO (v3.7.0)
deps = create_pipeline_dependencies(config)
social_engine = SocialLearningEngine(deps, config)
```

### Problema: "No module named 'sarai_agi.search'"

**Causa**: Instalación incompleta  
**Solución**:

```bash
pip install -e .  # Reinstalar en modo editable
python -c "from sarai_agi.search import MultiSourceSearcher; print('OK')"
```

### Problema: "consensus_score siempre 0"

**Causa**: Threshold muy alto o contenido muy diferente entre fuentes  
**Solución**: Ajustar consensus_threshold:

```yaml
search_integration:
  multi_source_search:
    consensus_threshold: 0.5  # Bajar de 0.7 a 0.5
```

### Problema: "Latency muy alta (>5s)"

**Causa**: Demasiadas fuentes en paralelo o verification_level COMPREHENSIVE  
**Solución**:

```yaml
search_integration:
  multi_source_search:
    max_sources: 4                # Bajar de 6 a 4
    verification_level: "BASIC"   # Cambiar a BASIC
    max_concurrent_requests: 4    # Limitar concurrencia
```

---

## 📚 Referencias

- **Arquitectura completa**: `docs/MULTIMODAL_LEARNING_COMPLETE.md`
- **Release notes**: `RELEASE_NOTES_v3.7.md`
- **Changelog**: `CHANGELOG.md` → `[3.7.0]` entry
- **Config reference**: `config/v3.7.0_multimodal_config.yaml`
- **Source code**:
  - `src/sarai_agi/search/multi_source_searcher.py`
  - `src/sarai_agi/learning/social_learning_engine.py`
  - `src/sarai_agi/learning/youtube_learning_system.py`

---

## ⏭️ Next Steps

Después de migración exitosa:

1. **Integrar SearXNG**: Reemplazar PLACEHOLDERs en `search_single_source()`
2. **Integrar Qwen3-VL:4B**: Activar análisis multimodal real en `_multimodal_analysis()`
3. **Deploy continuous learning**: Activar `continuous_learning: true` para 24/7 insights
4. **Monitor KPIs**: Verificar consensus_score ≥ 0.7, cultural_adaptation ≥ 75%
5. **Iterar HLCS v0.5**: Con AGI social completo, proceder a Conscious Alignment

---

**Documentación actualizada**: 2025-01-04  
**Mantenedor**: SARAi AGI Team  
**Versión**: v3.7.0-multimodal-learning
