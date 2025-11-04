"""Utilidades de configuración para SARAi_AGI.

Este módulo abstrae la carga de archivos de configuración YAML y
proporciona funciones auxiliares para obtener secciones específicas de
la configuración. La idea es mantener el acceso a la configuración en un
solo lugar mientras se migra el resto del código desde el repositorio
histórico.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# La estructura del repo es `SARAi_AGI/src/sarai_agi/...`, por lo que el
# directorio raíz se encuentra tres niveles arriba de este archivo.
_ROOT_PATH = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = _ROOT_PATH / "config" / "default_settings.yaml"


def load_settings(config_path: Optional[Path | str] = None) -> Dict[str, Any]:
    """Carga el archivo de configuración principal.

    Args:
        config_path: Ruta alternativa al archivo YAML. Si no se indica se
            utiliza ``config/default_settings.yaml``.

    Returns:
        Diccionario con la configuración cargada. Si el archivo no existe
        o está vacío se devuelve un diccionario vacío en lugar de propagar
        excepciones para mantener compatible la inicialización temprana.
    """

    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    if not path.exists():
        # No levantamos excepción para permitir que los módulos llamantes
        # utilicen valores por defecto sensatos.
        return {}

    with path.open("r", encoding="utf-8") as handler:
        data = yaml.safe_load(handler) or {}

    if not isinstance(data, dict):
        raise ValueError("El archivo de configuración debe representar un diccionario YAML")

    return data


def get_section(settings: Dict[str, Any], section: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Obtiene una sección de la configuración manejando alias comunes.

    Se añaden alias para facilitar la migración desde configuraciones en
    español y en inglés (por ejemplo ``quantizacion`` vs. ``quantization``).
    """

    if section in settings:
        value = settings[section]
    else:
        # Alias útiles para mantener retrocompatibilidad con documentos
        # previos que alternaban idiomas.
        aliases = {
            "quantization": ["quantizacion", "cuantizacion"],
            "pipeline": ["orquestacion", "pipeline_settings"],
            # v3.7.0 Multi-Source Search aliases
            "multi_source_search": ["busqueda_multi_fuente", "multi_source"],
            "source_verification": ["verificacion_fuentes", "verification"],
            "consensus_score": ["puntuacion_consenso", "consensus"],
            # v3.7.0 Social Learning aliases
            "social_learning": ["aprendizaje_social", "social"],
            "learning_domain": ["dominio_aprendizaje", "domain"],
            "cultural_adaptation": ["adaptacion_cultural", "cultural"],
            # v3.7.0 YouTube Learning aliases
            "youtube_learning": ["aprendizaje_youtube", "youtube"],
            "content_category": ["categoria_contenido", "category"],
        }
        alias_names = aliases.get(section, [])
        value = next((settings[name] for name in alias_names if name in settings), None)

    if value is None:
        return dict(default or {})

    if not isinstance(value, dict):
        raise ValueError(f"La sección '{section}' debe ser un objeto YAML (dict)")

    merged = dict(default or {})
    merged.update(value)
    return merged


__all__ = ["load_settings", "get_section"]
