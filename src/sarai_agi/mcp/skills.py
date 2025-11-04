"""Skills routing para MCP MoE (Mixture of Experts)."""

from __future__ import annotations

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def route_to_skills(
    scores: Dict[str, float],
    threshold: float = 0.3,
    top_k: int = 3
) -> List[str]:
    """Enrutamiento top-k por umbral para skills MoE.
    
    Política:
    1. Filtrar skills con score > threshold
    2. Seleccionar top-k por score descendente
    3. Excluir 'hard', 'soft', 'web_query' (son base, no skills)
    
    Args:
        scores: Dict {skill_name: score} desde TRM-Router
        threshold: Umbral mínimo de activación (default: 0.3)
        top_k: Máximo número de skills (default: 3)
    
    Returns:
        Lista de nombres de skills a activar
    
    Example:
        >>> scores = {'hard': 0.9, 'soft': 0.2, 'sql': 0.85, 'code': 0.7, 'math': 0.1}
        >>> route_to_skills(scores)
        ['sql', 'code']
    """
    # Filtrar skills (excluir base)
    active_skills = {
        skill: score
        for skill, score in scores.items()
        if score > threshold and skill not in ["hard", "soft", "web_query"]
    }
    
    # Top-k por score descendente
    top_skills = sorted(active_skills.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    return [skill for skill, _ in top_skills]


__all__ = ["route_to_skills"]
