"""SARAi_AGI - Sistema de AGI autónomo, modular y auditable.

Versión baseline: 3.5.1
Licencia: MIT
Repositorio: https://github.com/iagenerativa/SARAi_AGI

Este paquete contiene los módulos core migrados desde SARAi_v2 con arquitectura
limpia y versionado riguroso. Diseñado para evolucionar hacia v4.0 manteniendo
trazabilidad completa de cambios y compatibilidad semántica.
"""

__all__ = ["__version__", "pipeline", "model", "configuration"]

# Version is read from VERSION file at package root
from pathlib import Path

_version_file = Path(__file__).parent.parent.parent / "VERSION"
__version__ = _version_file.read_text().strip() if _version_file.exists() else "unknown"
