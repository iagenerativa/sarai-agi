# Roadmap SARAi_AGI

## Horizonte inmediato (Q4 2025)
- ✅ Crear repositorio limpio con línea base v3.5.1.
- ⏳ Migrar núcleo operativo (pipeline + quantización + model pool).
- ⏳ Establecer pipeline de CI/CD y verificación de versión.
- ⏳ Publicar release `v3.5.2` con primeras mejoras en entorno nuevo.

## Horizonte cercano (Q1 2026)
- Implementar sistema de plugins y sidecars (preparación v4.0).
- Integrar TTS/ASR reales (MeloTTS, Sherpa-ONNX) sin mocks.
- Habilitar observabilidad avanzada (Prometheus + Grafana + alertas).
- Completar migración de sistemas avanzados (seguridad, emoción, telemetría).

## Horizonte medio (v4.0)
- Arquitectura Sidecars para capacidades extendidas.
- Plugins firmados y verificables.
- Estrategia de despliegue híbrida (local + remoto) auditada.
- Consolidación de KPIs: latencia <200ms P50, RAM <4.5GB P50.

## Principios Clave
- Versionado semántico estricto (`vX.Y.Z`).
- Releases firmados y auditables.
- Benchmarks reproducibles para cada release.
- Documentación obligatoria antes de merge a `main`.

## Próximos hitos
| Fecha estimada | Hito | Descripción |
|----------------|------|-------------|
| 2025-11-10 | v3.5.2 | Migración núcleo operativo + CI básico |
| 2025-12-05 | v3.6.0 | Plugins, TTS real, observabilidad base |
| 2026-01-31 | v4.0.0 | Sidecars completos + despliegue híbrido |
