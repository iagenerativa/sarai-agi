# Tareas Semana 1 - SARAi_AGI v3.5.2

**Período**: 4-8 de noviembre de 2025  
**Objetivo**: Completar migración core y release v3.5.2  
**Estado**: 🟡 En progreso

---

## 🎯 Objetivo de la Semana

Completar la migración del 56% → 100% de los componentes core de SARAi_v2, asegurar que todos los tests pasen en CI, y publicar release v3.5.2 con documentación completa.

---

## 📋 Lunes 4 de Noviembre ✅

### ✅ Completado

1. **Fix CI Pipeline** ✅
   - [x] Instalar dependencias dev con `pip install -e ".[dev]"`
   - [x] Hacer imports de langchain opcionales
   - [x] Hacer imports de TRMClassifier condicionales
   - [x] Verificar instalación de sarai_agi y numpy
   - **Commits**: 
     - `6b5ef64`: fix(ci): install dev dependencies and add verification steps
     - `c12b636`: fix(model): make langchain imports optional
     - `54a102c`: fix(classifier): make TRMClassifier import conditional
   - **Estado**: Workflow ejecutándose con 257 tests

---

## 📋 Martes 5 de Noviembre

### Migrar Unified Model Wrapper

**Archivos origen** (SARAi_v2):
- `core/unified_model_wrapper.py` (1,626 LOC)
- `docs/UNIFIED_WRAPPER_GUIDE.md`
- `examples/unified_wrapper_examples.py`
- Tests relacionados

**Tareas**:
- [ ] Copiar `unified_model_wrapper.py` a `src/sarai_agi/model/wrapper.py`
- [ ] Adaptar imports para nueva estructura
- [ ] Hacer todos los imports externos opcionales (torch, transformers, langchain)
- [ ] Crear tests en `tests/test_model_wrapper.py`
- [ ] Verificar overhead <5% (benchmark)
- [ ] Documentar 8 backends soportados en README

**Tests a migrar**:
- Test de 8 backends (GGUF, Transformers, Multimodal, Ollama, OpenAI, Embeddings, PyTorch, Config)
- Test de overhead (<5%)
- Test de fallback automático

**Estimado**: 4-5 horas

**Criterios de éxito**:
- ✅ Wrapper carga sin errores con dependencias opcionales
- ✅ Tests pasan para backends disponibles
- ✅ Overhead validado <5%
- ✅ CI verde

---

## 📋 Miércoles 6 de Noviembre

### Migrar Graph Orchestrator

**Archivos origen** (SARAi_v2):
- `core/graph.py` (~800 LOC estimadas)
- Skills Phoenix integration
- Layer Architecture integration

**Tareas**:
- [ ] Copiar `graph.py` a `src/sarai_agi/orchestration/graph.py`
- [ ] Adaptar imports de LangGraph (condicional)
- [ ] Integrar con TRM Classifier ya migrado
- [ ] Integrar con MCP Core ya migrado
- [ ] Crear tests en `tests/test_orchestration.py`
- [ ] Validar routing de 7 prioridades

**Componentes del Graph**:
1. TRM Router → clasificación hard/soft/web_query
2. MCP → cálculo de pesos α/β
3. Routing multimodal (7 priority levels)
4. Skills Phoenix detection
5. Feedback logging

**Tests a crear**:
- Test de routing básico (hard → expert, soft → tiny)
- Test de skills detection
- Test de multimodal routing
- Test de fallback chain

**Estimado**: 5-6 horas

**Criterios de éxito**:
- ✅ Graph ejecuta workflow completo
- ✅ Routing funciona correctamente
- ✅ Skills se detectan y aplican
- ✅ Tests pasan
- ✅ CI verde

---

## 📋 Jueves 7 de Noviembre

### Migrar Agents

**Archivos origen** (SARAi_v2):
- `agents/expert_agent.py` (SOLAR)
- `agents/tiny_agent.py` (LFM2)
- `agents/multimodal_agent.py` (Qwen-Omni)
- `agents/audio_router.py`

**Tareas**:

#### Morning: Expert + Tiny Agents
- [ ] Copiar agents a `src/sarai_agi/agents/`
- [ ] Adaptar imports
- [ ] Integrar con Model Pool ya migrado
- [ ] Tests básicos de generación

#### Afternoon: Multimodal + Audio
- [ ] Migrar multimodal_agent.py
- [ ] Migrar audio_router.py
- [ ] Hacer imports de audio/visión opcionales
- [ ] Tests de routing audio (LID)

**Tests a crear**:
- Test expert agent con SOLAR (mock si no disponible)
- Test tiny agent con LFM2
- Test multimodal processing
- Test audio routing (Omni vs NLLB vs LFM2)

**Estimado**: 6-7 horas

**Criterios de éxito**:
- ✅ Agents generan respuestas
- ✅ Multimodal procesa audio/imagen
- ✅ Audio router funciona
- ✅ Tests pasan con mocks
- ✅ CI verde

---

## 📋 Viernes 8 de Noviembre

### Finalización v3.5.2

#### Morning: Feedback System + Health Dashboard

**Feedback System**:
- [ ] Migrar `core/feedback.py`
- [ ] Logging asíncrono
- [ ] Embeddings implícitos
- [ ] Tests de feedback

**Health Dashboard**:
- [ ] Migrar `sarai/health_dashboard.py`
- [ ] Endpoints /health y /metrics
- [ ] Content negotiation
- [ ] Tests de API

**Estimado**: 3-4 horas

#### Afternoon: Documentación y Release

**Documentación**:
- [ ] Actualizar `MIGRATION_STATUS.md` (56% → 100%)
- [ ] Completar `CHANGELOG.md` v3.5.2
- [ ] Crear/actualizar `API.md` con interfaces públicas
- [ ] Actualizar `README.md` con estado final

**Release**:
- [ ] Verificar VERSION file = 3.5.2
- [ ] Verificar que todos los tests pasan (CI verde)
- [ ] Crear tag `v3.5.2` con GPG signature
- [ ] Generar release notes
- [ ] Publicar release en GitHub

**Release Checklist**:
```bash
# 1. Verificar tests locales
pytest -v

# 2. Verificar CI está verde
# Ver: https://github.com/iagenerativa/sarai-agi/actions

# 3. Actualizar VERSION
echo "3.5.2" > VERSION

# 4. Commit final
git add .
git commit -m "chore: prepare release v3.5.2

- Complete core migration (100%)
- All tests passing
- Documentation updated
- Ready for production"

# 5. Tag con firma
git tag -s v3.5.2 -m "Release v3.5.2: Complete Core Migration"

# 6. Push
git push origin main --tags

# 7. Crear release en GitHub
gh release create v3.5.2 \
  --title "v3.5.2 - Complete Core Migration" \
  --notes-file RELEASE_NOTES_v3.5.2.md \
  --verify-tag
```

**Estimado**: 2-3 horas

---

## 📊 Métricas de Éxito de la Semana

### Cobertura de Migración
- **Inicio**: 56% (4,485 LOC)
- **Meta**: 100% (~8,000 LOC estimadas)
- **Componentes**: 15/15 migrados

### Tests
- **Inicio**: 35 tests passing
- **Meta**: 257+ tests passing
- **Cobertura**: >80% en módulos core

### CI/CD
- **Inicio**: ✅ Pipeline básico funcional
- **Meta**: ✅ Pipeline completo con todos los tests pasando
- **Versiones Python**: 3.10 y 3.11

### Documentación
- **Inicio**: 4 documentos (README, ROADMAP, ARCHITECTURE, MIGRATION_PLAN)
- **Meta**: +4 documentos (NEXT_STEPS ✅, MIGRATION_STATUS, API, CHANGELOG completo)

---

## 🚨 Bloqueadores Potenciales

### 1. Dependencias Opcionales
**Problema**: Componentes que requieren torch, transformers, langchain  
**Solución**: Imports condicionales + fallbacks + tests con mocks  
**Prioridad**: Alta

### 2. Tests que Fallan en CI
**Problema**: Diferencias entre entorno local y CI  
**Solución**: Debugging con logs detallados, verificación de dependencias  
**Prioridad**: Alta

### 3. Tiempo de Migración Subestimado
**Problema**: Componentes más complejos de lo estimado  
**Solución**: Priorizar componentes críticos, aceptar migración parcial documentada  
**Prioridad**: Media

---

## 📞 Daily Standup Questions

### ¿Qué hice ayer?
- [Lunes] Arreglé CI pipeline, hice imports opcionales
- [Martes] Migré Unified Model Wrapper
- [Miércoles] Migré Graph Orchestrator
- [Jueves] Migré Agents (expert, tiny, multimodal, audio)
- [Viernes AM] Migré Feedback System + Health Dashboard

### ¿Qué haré hoy?
- [Ver tareas del día correspondiente arriba]

### ¿Hay bloqueadores?
- [Reportar aquí cualquier bloqueador]

---

## 🎯 Entregables de la Semana

1. **Código**:
   - ✅ CI pipeline funcional
   - [ ] 6 componentes migrados (wrapper, graph, 4 agents)
   - [ ] 2 sistemas complementarios (feedback, health)
   - [ ] 200+ tests nuevos

2. **Documentación**:
   - ✅ NEXT_STEPS.md (este documento)
   - [ ] MIGRATION_STATUS.md actualizado
   - [ ] CHANGELOG.md v3.5.2
   - [ ] API.md con interfaces públicas

3. **Release**:
   - [ ] Tag v3.5.2 firmado
   - [ ] Release notes publicadas
   - [ ] SBOM generado
   - [ ] CI badge verde en README

---

**Última actualización**: 4 de noviembre de 2025, 13:30  
**Próxima revisión**: 5 de noviembre de 2025, 09:00
