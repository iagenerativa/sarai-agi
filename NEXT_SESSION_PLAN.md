# Próxima Sesión - Plan de Trabajo

**Fecha**: 6 Nov 2025  
**Sesión**: Week 2 Day 6-7  
**Objetivo**: Qdrant Vector DB - Sistema de Memoria Semántica

---

## ✅ Estado Actual (5 Nov 2025)

### Week 1 COMPLETADA 100% 🎉
- ✅ Day 1-2: STT + VAD + Audio Utils (1,420 LOC)
- ✅ Day 3-4: MeloTTS + Expresividad (730 LOC)
- ✅ Day 5: Fillers System (730 LOC)
- **Total**: 2,880 LOC + 31 tests
- **Status**: Production-ready ✅

---

## 📋 NEXT SESSION PLAN - SARAi v3.8.0

**Fecha**: 6 Nov 2025  
**Contexto**: Week 1 COMPLETADO (2,880 LOC, 29/31 tests passing)  
**Próximo objetivo**: TTS Streaming Queue OPTIMIZADO + Week 2 start

---

## 🎯 PRIORIDAD 1: TTS Streaming Queue con Overlap Prediction (7h) ⭐ **ACTUALIZADO**

### Motivación (User Request)
**"Se puede optimizar incluso el proceso, sabiendo cuanto tarda en procesar el texto a voz y cuanto dura la frase que se está reproduciendo con el fin de ir concatenando las frases de una manera natural, sin que el interlocutor note pausas y mejorando los tiempo de procesamiento globales"**

### Problema Actual
- Respuestas largas tienen 10-20s latencia inicial (blocking synthesis)
- Streaming simple tiene gaps 0.2s entre frases (notable)
- No hay gestión de prioridades (interrupciones lentas)
- No prediction de overlaps (síntesis serial)

### Solución Optimizada
1. **Predictive Overlap**: Calcula duración audio vs tiempo síntesis
2. **EWMA Learning**: Aprende timing real de síntesis
3. **Zero-Gap Playback**: Empieza síntesis siguiente ANTES de terminar actual
4. **Priority Queues**: HIGH/NORMAL/LOW con preemption
5. **LoRA Scheduler**: Predice interrupciones, optimiza queue depth

### Implementación - 5 Fases

#### FASE 1: Core Streaming (2h)
**Archivos**:
- `src/sarai_agi/audio/sentence_splitter.py` (50 LOC)
  - Regex-based splitting
  - Handle Spanish punctuation (¿?¡!)
  - Edge cases: abreviaturas (Dr., Sr.), números (3.14)
  - Tests: 10 test cases
  
- `src/sarai_agi/audio/tts_queue.py` (200 LOC) ⭐
  - TTSQueue class con overlap prediction
  - EWMA timing (avg_synthesis_time con α=0.3)
  - Producer thread: synthesize con timing measurement
  - Consumer thread: playback con gap measurement
  - Overlap calculation: `wait_time = audio_duration - synthesis_time - margin`
  - Methods: synthesize_streaming(), stop(), get_metrics()
  
- `src/sarai_agi/audio/melotts.py` (+50 LOC)
  - New method: synthesize_streaming(text, on_chunk, **kwargs)
  - Returns metrics dict (synthesis_times, gaps, total_time)
  - Backward compatible (keep existing methods)
  
**Tests**: `tests/test_tts_streaming.py` (150 LOC, 8 tests)
- Test sentence splitting
- Test queue operations
- Test overlap prediction accuracy
- Test gap measurement (<0.05s target)
- Test EWMA convergence
- Test interrupt handling
- Test metrics reporting

**Deliverable**: Streaming TTS funcional con CERO gaps ✅

---

#### FASE 2: Optimización Performance (1.5h)
**Archivos**:
- `tests/test_tts_performance.py` (100 LOC, 4 tests)
  - Benchmark latency to first audio (<2s)
  - Benchmark gap promedio (<0.05s)
  - Stress test (50+ frases, estabilidad)
  - Memory leak test (100 iterations)
  
**Tuning**:
- Ajustar `prefetch_margin` (0.3-0.7s testing)
- Ajustar EWMA alpha (0.2-0.4 testing)
- Ajustar queue maxsize (2-4 testing)
- Validar convergencia EWMA (<5 samples)

**Deliverable**: Performance validado, métricas documentadas ✅

---

#### FASE 3: Priority Queue System (1h) ⭐
**Archivos**:
- `src/sarai_agi/audio/priority_tts_queue.py` (150 LOC)
  - PriorityTTSQueue class
  - 3 niveles: HIGH (interrupts), NORMAL (responses), LOW (fillers)
  - Preemptive interruption: HIGH can stop NORMAL/LOW
  - Starvation prevention: LOW max wait 30s
  - Methods: enqueue(text, priority), interrupt(), get_queue_stats()

**Tests**: `tests/test_priority_queue.py` (120 LOC, 6 tests)
- Test HIGH priority preemption
- Test interrupt latency (<100ms)
- Test starvation prevention
- Test queue ordering
- Test multi-priority concurrent

**Deliverable**: Sistema de prioridades robusto ✅

---

#### FASE 4: LoRA Scheduler Integration (1.5h) ⭐
**Archivos**:
- `src/sarai_agi/audio/lora_scheduler.py` (100 LOC)
  - LoRAScheduler class
  - predict_interrupt_probability(sentence, context)
  - update_from_feedback(interrupted, context)
  - Adaptive queue depth based on prediction
  - Re-train every 50 samples
  
- `src/sarai_agi/audio/scheduler_integration.py` (50 LOC)
  - Integration PriorityQueue + LoRAScheduler
  - Auto-adjust priorities based on predictions
  - Feedback loop: track actual interrupts

**Tests**: `tests/test_lora_scheduler.py` (80 LOC, 4 tests)
- Test prediction accuracy (>70% target)
- Test feedback loop convergence
- Test adaptive queue depth
- Test edge cases (no training data)

**Deliverable**: Sistema adaptativo que aprende de usuario ✅

---

#### FASE 5: Demo Conversación Real (1h) ⭐ **CRÍTICO UX**
**Archivos**:
- `examples/interactive_conversation_test.py` (250 LOC)
  - Micrófono en vivo (Vosk STT)
  - VAD para detectar silencio (Sherpa)
  - Processing pipeline (STT → LLM → TTS streaming)
  - Visualización en tiempo real:
    * Métricas: latency, gaps, synthesis time
    * Progress bar: frase actual / total
    * Gap indicator: visual de pausas
  - 5 test scenarios implementados:
    1. Consulta corta (1 frase)
    2. Explicación media (3-5 frases)
    3. Respuesta larga (10+ frases)
    4. Interrupción usuario
    5. Multi-turn conversation
  
**Output Esperado**:
```
🎤 USER: "Explícame la teoría de la relatividad"
⏱️  Pipeline: STT=0.8s | LLM=1.2s | TTS_START=2.0s

🔊 SARAI [1/8]: "La teoría de la relatividad fue propuesta por Einstein."
   📊 Synthesis: 2.1s | Audio: 3.2s | Gap: 0.00s ✅
   
🔊 SARAI [2/8]: "Consta de dos partes principales."
   📊 Synthesis: 1.9s | Audio: 2.8s | Gap: 0.01s ✅
   
... (continúa fluidamente)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 FINAL METRICS:
   Total sentences: 8
   Avg synthesis time: 2.04s (EWMA converged ✅)
   Avg gap: 0.012s (TARGET: <0.05s ✅)
   Latency (first audio): 2.0s (TARGET: <2s ✅)
   Total time: 28.3s
   vs Blocking: 45s → -37% improvement ✅
   
💯 USER EXPERIENCE: FLUENT & NATURAL ✨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Deliverable**: Demo completo para validación UX mañana ✅

---

### Resumen TTS Streaming

**Total Estimado**: 7 horas
- FASE 1 Core: 2h
- FASE 2 Performance: 1.5h
- FASE 3 Priorities: 1h
- FASE 4 LoRA: 1.5h
- FASE 5 Demo: 1h

**LOC Total**: ~650 LOC
- sentence_splitter.py: 50
- tts_queue.py: 200 (con overlap)
- priority_tts_queue.py: 150
- lora_scheduler.py: 100
- melotts.py updates: 50
- interactive demo: 250

**Tests**: 22 tests
- Core streaming: 8
- Performance: 4
- Priority queue: 6
- LoRA scheduler: 4

**Benefits**:
- ✅ Latencia percibida: -90% (20s → 2s)
- ✅ Gaps entre frases: 0.0s (zero pausas)
- ✅ Flujo natural: Como humano hablando
- ✅ Interrupciones: <100ms response
- ✅ Adaptive: Aprende de usuario con LoRA
- ✅ Production-ready: Demo validado

---

## 📅 PRIORIDAD 2: Week 2 Day 6-7 - Qdrant Vector DB (4-5h)

**DESPUÉS** de TTS Streaming Optimizado (7h)  
**Tiempo restante Day 6**: ~1-2h (si día completo 8h)  
**Day 7 completo**: 8h  
**Total disponible**: 9-10h para Qdrant + preparación LoRA

---

### Qdrant Vector DB Implementation

**Objetivo**: Sistema de memoria semántica para contexto a largo plazo

**Componentes a Implementar**:

1. **qdrant_client.py** (~200 LOC)
   - Cliente Qdrant local/cloud
   - Vector store management
   - Collection management
   - STRICT MODE graceful degradation

2. **embeddings.py** (~150 LOC)
   - EmbeddingGemma-300M integration
   - Text → Vector conversion
   - Batch processing
   - Cache de embeddings

3. **semantic_search.py** (~100 LOC)
   - Query processing
   - Similarity search
   - Context retrieval
   - Result ranking

4. **Tests** (10-12 tests)
   - Qdrant connection
   - Vector operations
   - Semantic search
   - Edge cases

**Features**:
- ✅ Semantic search en conversaciones pasadas
- ✅ Context retrieval para respuestas coherentes
- ✅ Long-term memory persistente
- ✅ Vector similarity search
- ✅ Automatic embedding generation

**Estimado**: 6-8 horas

---

## 📋 Checklist Day 6-7

### ⚡ PRIORIDAD: TTS Streaming (2-3 horas)
- [ ] Implementar sentence_splitter.py
- [ ] Implementar tts_queue.py
- [ ] Update melotts.py con streaming mode
- [ ] Tests streaming (8-10 tests)
- [ ] Demo streaming vs blocking

### Setup Qdrant (30 min)
- [ ] Instalar qdrant-client
- [ ] Setup Qdrant local (Docker o in-memory)
- [ ] Verificar EmbeddingGemma disponible
- [ ] Crear estructura de directorios

### Implementación (4-5 horas)
- [ ] qdrant_client.py (conexión + CRUD)
- [ ] embeddings.py (generación + cache)
- [ ] semantic_search.py (búsqueda + ranking)
- [ ] Integration con pipeline existente

### Tests (1-2 horas)
- [ ] Test connection + collections
- [ ] Test vector operations
- [ ] Test semantic search
- [ ] Test edge cases
- [ ] Target: 10-12 tests passing

### Documentación (1 hora)
- [ ] WEEK2_DAY6-7_RESUMEN.md
- [ ] Code documentation (docstrings)
- [ ] Usage examples
- [ ] Integration guide

---

## 🔧 Dependencias Necesarias

```bash
# Qdrant
pip install qdrant-client==1.7.0

# Embeddings (si no está)
# EmbeddingGemma-300M ya disponible en models/cache/
```

---

## 📚 Referencias

- **Qdrant Docs**: https://qdrant.tech/documentation/
- **Python Client**: https://github.com/qdrant/qdrant-client
- **EmbeddingGemma**: Ya integrado en v3.7.0

---

## 🚀 Roadmap Completo Week 2

- **Day 6**: TTS Streaming Queue (2-3h) ← CRÍTICO
- **Day 6-7**: Qdrant Vector DB (4-5h)
- **Day 8-9**: LoRA Optimizer (6-8h)
- **Day 10-11**: TRM Supervised Learning (6-8h)
- **Day 12**: Integration Testing (4h)

**Total Week 2**: ~24-28 horas estimadas

---

## 💡 Notas Importantes

1. **TTS Streaming es CRÍTICO** para buena UX - implementar primero
2. **Sentence-level mejor que word-level** (balance latencia/calidad)
3. **Queue thread-safe** necesaria para concurrencia
4. **Qdrant puede correr local** (sin cloud) para desarrollo
5. **EmbeddingGemma ya está disponible** (300M parámetros)
6. **Integration con audio pipeline** será automática
7. **Vector DB será base** para RAG avanzado en Week 3

---

**Última actualización**: 5 Nov 2025, 23:50  
**Preparado por**: SARAi AGI Team  
**Estado**: Ready to start Week 2 🚀
