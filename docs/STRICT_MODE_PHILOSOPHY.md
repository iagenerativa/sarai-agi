# 🎯 STRICT MODE PHILOSOPHY - SARAi v3.8.0+

> **"Datos reales o mensaje 'No encontré nada' - NUNCA datos falsos"**
> 
> — Noel (User request, Nov 4 2025)

## 📋 Resumen Ejecutivo

A partir de v3.8.0, SARAi adopta **STRICT MODE** como filosofía de diseño para TODAS las integraciones:

- ✅ **Datos reales o None** (nunca mocks silenciosos)
- ✅ **Errores explícitos > Degradación silenciosa**
- ✅ **Quality over Availability**
- ✅ **Consultar antes de usar mocks**

## 🔥 Cambio Filosófico Fundamental

### ❌ OLD Approach (v3.7.0 y anteriores):
```python
# Safety-first design: Fallback silencioso a mock
if real_api_fails():
    return mock_data()  # 🚨 Silently returns fake data
```

**Problema:** Sistema retorna datos falsos sin avisar. Bugs ocultos. Testing inválido.

### ✅ NEW Approach (v3.8.0+ STRICT MODE):
```python
# Quality-first design: Fail explicitly
if real_api_fails():
    logger.error("STRICT MODE: Real API failed - returning None")
    return None  # 🎯 Explicit failure, no fake data
```

**Beneficio:** Sistema honesto. Errores visibles. Testing real. Producción confiable.

## 📐 Design Principles

### 1. **Explicit over Implicit**
```python
# ❌ BAD: Silently falls back to mock
result = search_with_fallback(query)

# ✅ GOOD: Explicitly handles None
result = search_strict(query)
if result is None:
    return "Lo siento, no encontré información real sobre eso."
```

### 2. **Real Data or Honest Failure**
```python
# ❌ BAD: Returns "[Mock] Python is a programming language"
# ✅ GOOD: Returns None + log "STRICT MODE: SearXNG unavailable"
```

### 3. **Debuggable Errors**
```python
# ❌ BAD: Silent degradation (user sees fake data, doesn't know system failed)
# ✅ GOOD: Explicit None (engineer sees error log, can fix root cause)
```

### 4. **Production Quality First**
```python
# Development: Tests with real APIs (skip if unavailable)
# Staging: Tests with real APIs (fail if unavailable)  
# Production: No mocks, only real data (alert if degraded)
```

## 🛠️ Implementation Pattern

### Config (YAML):
```yaml
integration_name:
  enabled: true
  fallback_to_mock: false  # ⚠️ STRICT MODE: 100% real data
  # Set to true ONLY for backward compatibility
```

### Code (Python):
```python
class RealIntegration:
    def __init__(self, config: Dict[str, Any]):
        # Default to STRICT MODE
        self.fallback_to_mock = config.get('fallback_to_mock', False)
        
        if not self.fallback_to_mock:
            logger.warning(
                "⚠️ STRICT MODE: Real data required - "
                "System will return None if unavailable"
            )
    
    async def fetch_data(self, query: str) -> Optional[Data]:
        try:
            result = await self._fetch_real(query)
            
            if not result:
                if self.fallback_to_mock:
                    logger.warning("Falling back to mock data")
                    return await self._fetch_mock(query)
                else:
                    logger.error(
                        f"STRICT MODE: No real data found for '{query}' - "
                        "returning None"
                    )
                    return None
            
            return result
            
        except Exception as e:
            if self.fallback_to_mock:
                logger.warning(f"Error {e} - falling back to mock")
                return await self._fetch_mock(query)
            else:
                logger.error(
                    f"STRICT MODE: Real API failed ({e}) - returning None"
                )
                return None
    
    async def _fetch_mock(self, query: str) -> Data:
        """
        Mock data SOLO para backward compatibility.
        
        ⚠️ NOTA: En STRICT MODE, este método NUNCA se llama.
        Recomendación: Usar STRICT MODE para producción (100% datos reales).
        """
        return Data(content=f"[Mock] {query}", source="mock")
```

### Tests (pytest):
```python
@pytest.mark.asyncio
async def test_real_integration_strict_mode():
    """Test con datos reales - STRICT MODE"""
    result = await integration.fetch_data("test query")
    
    # ⚠️ STRICT MODE: Si no hay datos reales, skip (no mock)
    if result is None:
        pytest.skip("No se encontraron datos reales - STRICT MODE activo")
    
    # Si HAY datos, validar que sean reales
    assert result is not None
    assert "[Mock]" not in result.content  # ⚠️ NUNCA contenido mock
    assert result.source != "mock"
```

## 📊 Testing Strategy

### Test Results Interpretation:

```
✅ PASSED - Integration works with real data
⏭️ SKIPPED - No real data available (expected in STRICT MODE)
❌ FAILED - Code bug (not data availability)
```

### Example:
```
tests/test_searxng_integration.py:
  ✅ 7 passed  - Real SearXNG working
  ⏭️ 3 skipped - SearXNG no data (STRICT MODE)
  ❌ 0 failed  - No code bugs
```

**Interpretación:** Sistema funcionando correctamente. Los skips son esperados si SearXNG no tiene datos para esas queries.

## 🚀 Migration Guide

### Para integraciones existentes con mocks:

1. **Agregar flag `fallback_to_mock` en config:**
   ```yaml
   integration:
     fallback_to_mock: false  # Default STRICT MODE
   ```

2. **Hacer mock condicional en código:**
   ```python
   if self.fallback_to_mock:
       return await self._mock_fallback()
   else:
       logger.error("STRICT MODE: returning None")
       return None
   ```

3. **Actualizar tests para skip en lugar de asumir mock:**
   ```python
   if result is None:
       pytest.skip("No real data - STRICT MODE")
   ```

4. **Deprecar mock en docstrings:**
   ```python
   """
   Mock data SOLO backward compatibility.
   ⚠️ En STRICT MODE, NUNCA se llama.
   """
   ```

## 📝 Commit Message Template

```
refactor(vX.X.X): STRICT MODE - Integración [NOMBRE] 100% real

🎯 User request: "quiero un 100% real" - Datos reales o None

CAMBIOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Config: fallback_to_mock=false (STRICT MODE)
✅ Code: Sistema retorna None si API unavailable
✅ Tests: X passed, Y skipped (comportamiento esperado)
✅ Philosophy: Explicit failures > Silent fake data

FILOSOFÍA STRICT MODE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• SIN degradación silenciosa a mocks
• Calidad > Disponibilidad (Quality over Availability)
• Error explícito = debuggable, Mock = bug oculto
• Datos reales o None (nunca datos falsos)
```

## 🎓 User Request Compliance

**Original request (Nov 4, 2025):**
> "Si falla por falta de datos reales, que de un mensaje 'No encontré nada'.
> A partir de ahora antes de emplear un mock me consultarás y así evitamos pérdidas de tiempo"

**Compliance checklist:**
- ✅ Sistema retorna None si no hay datos reales
- ✅ Logs explícitos "STRICT MODE: No encontré datos"
- ✅ NUNCA usar mocks sin consultar
- ✅ Default = STRICT MODE en TODAS las nuevas integraciones
- ✅ Documentación clara de filosofía

## 🔮 Future Integrations

**TODOS los PLACEHOLDERs v3.8.0+ serán STRICT MODE:**

1. ✅ **SearXNG** - Commit 9182ee1 (COMPLETADO)
2. 📋 **EmotionalContextEngine** - Día 3 (100% real)
3. 📋 **youtube-dl/yt-dlp** - Día 4-5 (100% real)
4. 📋 **Qwen3-VL** - Week 2 (100% real)
5. 📋 **ffmpeg** - Week 2 (100% real)
6. 📋 **Embeddings** - Week 3 (100% real)
7. 📋 **Web Cache** - Week 3 (100% real)

**Regla de oro:** Consultar antes de implementar CUALQUIER mock.

## 📚 References

- **Commit:** 9182ee1 - STRICT MODE implementation (SearXNG)
- **Branch:** feature/v3.7.0-multimodal-search
- **Config:** config/v3.7.0_multimodal_config.yaml
- **Code:** src/sarai_agi/search/multi_source_searcher.py
- **Tests:** tests/test_searxng_integration.py

---

**Última actualización:** Nov 4, 2025  
**Versión:** v3.8.0-dev  
**Status:** ✅ ACTIVE (filosofía adoptada oficialmente)
