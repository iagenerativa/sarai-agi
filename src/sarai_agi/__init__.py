"""SARAi_AGI - Sistema de AGI autónomo, modular y auditable.

Versión actual: 3.6.0
Baseline: Python 3.13+
Licencia: MIT
Repositorio: https://github.com/iagenerativa/sarai-agi

Este paquete contiene los módulos core migrados desde SARAi_v2 con arquitectura
limpia y versionado riguroso. Diseñado para evolucionar hacia v4.0 manteniendo
trazabilidad completa de cambios y compatibilidad semántica.

Características principales v3.6.0:
- Python 3.13+ requerido (migración completa)
- Memory infrastructure (WebCache, WebAuditLogger, VectorDB)
- Phoenix Architecture (Skills como prompts, no modelos)
- Layer Architecture (I/O, Memory, Fluidity)
- CI/CD con testing Python 3.13 y 3.14
"""

__all__ = ["__version__", "pipeline", "model", "configuration"]

# Version is read from VERSION file at package root
from pathlib import Path

_version_file = Path(__file__).parent.parent.parent / "VERSION"
if _version_file.exists():
    # Read only the first line (version number)
    __version__ = _version_file.read_text().strip().split('\n')[0]
else:
    __version__ = "unknown"
