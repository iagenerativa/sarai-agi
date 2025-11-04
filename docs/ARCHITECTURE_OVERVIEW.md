# SARAi_AGI - Arquitectura Inicial

**Versión base:** v3.5.1  
**Objetivo:** Establecer la arquitectura modular que servirá como puente hacia v4.0.

## Capas Principales

1. **Orquestación (LangGraph/Async):**  
   - Mantiene compatibilidad con el pipeline paralelo introducido en v3.5.1.
   - Exposición mediante API interna para agentes especializados y telemetría.

2. **Gestión de Modelos (Model Pool Dinámico):**  
   - Selección de cuantización IQ3/Q4/Q5 basada en heurísticas multi-factor.
   - Encapsula la carga, swapping y métricas de consumo.

3. **Sistemas Avanzados (Security, Emotional, Telemetry):**  
   - Persisten los módulos de seguridad, contexto emocional y telemetría avanzada.
   - Se parametrizan vía `config/default_settings.yaml`.

4. **Entrega Multimodal:**  
   - Preparada para integrar TTS/TTV reales (MeloTTS, Piper, Sherpa-ONNX) en v3.6.0.
   - Elimina mocks presentes en versiones anteriores.

## Principios de Diseño

- **Explicitness over Implicitness:** Todo placeholder debe anunciarse con logs y TODOs.
- **Fail-Fast:** Ante dependencias faltantes, abortar con mensajes accionables.
- **Auditabilidad:** Cada release debe contar con SBOM, firmas y métricas asociadas.
- **Modularidad Progresiva:** Plugins y componentes opcionales viven fuera del core.

## Próximos Pasos

1. Documentar diagramas actualizados para pipeline paralelo y quantización dinámica.
2. Definir interfaces públicas (API y CLI) que sobrevivirán a v4.0.
3. Incluir sección de "modo degradado" y fallback de seguridad.
4. Alinear la arquitectura con los planes de Sidecars (v4.0).
