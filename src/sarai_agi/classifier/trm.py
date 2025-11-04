"""TRM (Tiny Recursive Model) Classifier para SARAi_AGI.

Clasificador de intenciones basado en arquitectura recursiva que produce
scores independientes para diferentes tipos de queries:
- hard: Tareas técnicas (código, math, configuración)
- soft: Tareas emocionales (empatía, creatividad)
- web_query: Búsquedas que requieren información actualizada

Migrado desde SARAi_v2 manteniendo compatibilidad con el modelo entrenado.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from ..configuration import get_section, load_settings

logger = logging.getLogger(__name__)


if HAS_TORCH:
    class TinyRecursiveLayer(nn.Module):
        """Capa recursiva básica del TRM (Samsung SAIL architecture)."""

        def __init__(self, d_model: int, d_latent: int):
            super().__init__()
            self.d_model = d_model
            self.d_latent = d_latent

            # f_z: actualiza estado latente
            self.f_z = nn.Sequential(
                nn.Linear(d_model + d_model + d_latent, d_latent * 2),
                nn.ReLU(),
                nn.Linear(d_latent * 2, d_latent),
                nn.LayerNorm(d_latent)
            )

            # f_y: refina hipótesis
            self.f_y = nn.Sequential(
                nn.Linear(d_model + d_latent, d_model * 2),
                nn.ReLU(),
                nn.Linear(d_model * 2, d_model),
                nn.LayerNorm(d_model)
            )

        def forward(self, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> tuple:
            """Un paso de recursión."""
            z_input = torch.cat([x, y, z], dim=-1)
            z_new = self.f_z(z_input)

            y_input = torch.cat([y, z_new], dim=-1)
            y_new = self.f_y(y_input)

            return y_new, z_new


    class TRMClassifier(nn.Module):
        """Clasificador TRM con 3 cabezas: hard, soft, web_query."""

        def __init__(
            self,
            d_model: int = 256,
            d_latent: int = 256,
            h_cycles: int = 3,
            l_cycles: int = 4,
            embedding_dim: int = 768,
        ):
            super().__init__()

            self.d_model = d_model
            self.d_latent = d_latent
            self.h_cycles = h_cycles
            self.l_cycles = l_cycles

            # Proyección desde embeddings externos (e.g., EmbeddingGemma 768-D)
            self.input_proj = nn.Linear(embedding_dim, d_model)
            self.input_norm = nn.LayerNorm(d_model)

            # Capa recursiva compartida
            self.recursive_layer = TinyRecursiveLayer(d_model, d_latent)

            # Cabezas de clasificación
            self.head_hard = nn.Linear(d_model, 1)
            self.head_soft = nn.Linear(d_model, 1)
            self.head_web_query = nn.Linear(d_model, 1)

            # Estados iniciales aprendibles
            self.y0 = nn.Parameter(torch.zeros(1, d_model))
            self.z0 = nn.Parameter(torch.zeros(1, d_latent))

            self.device = torch.device("cpu")
            self.to(self.device)

        def forward(self, x_embedding: torch.Tensor) -> Dict[str, float]:
            """Clasifica intención del input.

            Args:
                x_embedding: Tensor [batch, embedding_dim] con embeddings externos.

            Returns:
                Dict con scores hard/soft/web_query en rango [0, 1].
            """
            batch_size = x_embedding.size(0)

            # Proyectar a d_model
            x = self.input_norm(self.input_proj(x_embedding))

            # Inicializar y, z
            y = self.y0.expand(batch_size, -1)
            z = self.z0.expand(batch_size, -1)

            # Ciclos recursivos (h_cycles × l_cycles pasos)
            for _ in range(self.h_cycles):
                for _ in range(self.l_cycles):
                    y, z = self.recursive_layer(x, y, z)

            # Clasificación triple
            hard_logit = self.head_hard(y)
            soft_logit = self.head_soft(y)
            web_query_logit = self.head_web_query(y)

            hard_score = torch.sigmoid(hard_logit).squeeze(-1)
            soft_score = torch.sigmoid(soft_logit).squeeze(-1)
            web_query_score = torch.sigmoid(web_query_logit).squeeze(-1)

            if self.training:
                return {
                    "hard": float(hard_score.item()),
                    "soft": float(soft_score.item()),
                    "web_query": float(web_query_score.item()),
                }
            else:
                # En eval mode retornar scalars para batch size 1, listas para batches
                if batch_size == 1:
                    return {
                        "hard": hard_score.item(),
                        "soft": soft_score.item(),
                        "web_query": web_query_score.item(),
                    }
                else:
                    return {
                        "hard": hard_score.detach().cpu().tolist(),
                        "soft": soft_score.detach().cpu().tolist(),
                        "web_query": web_query_score.detach().cpu().tolist(),
                    }

        def save_checkpoint(self, path: Path) -> None:
            """Guarda checkpoint del modelo."""
            path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'state_dict': self.state_dict(),
                'd_model': self.d_model,
                'd_latent': self.d_latent,
                'h_cycles': self.h_cycles,
                'l_cycles': self.l_cycles,
            }, path)
            logger.info("TRM checkpoint guardado en %s", path)

        def load_checkpoint(self, path: Path) -> bool:
            """Carga checkpoint del modelo."""
            if not path.exists():
                logger.warning("Checkpoint no encontrado: %s", path)
                return False

            checkpoint = torch.load(path, map_location=self.device, weights_only=False)
            self.load_state_dict(checkpoint['state_dict'])
            logger.info("TRM checkpoint cargado desde %s", path)
            return True


class TRMClassifierSimulated:
    """Clasificador simulado basado en keywords para prototipado rápido."""

    HARD_KEYWORDS = [
        "código", "error", "bug", "configurar", "instalar", "ssh", "linux",
        "python", "javascript", "servidor", "api", "base de datos", "sql",
        "git", "docker", "algoritmo", "función", "clase", "variable",
    ]

    SOFT_KEYWORDS = [
        "triste", "feliz", "frustrado", "gracias", "ayuda", "emocionado",
        "preocupado", "cansado", "motivado", "perdido", "confundido",
        "siento", "explicar como", "entender", "difícil de", "no sé",
    ]

    WEB_KEYWORDS = [
        "quién ganó", "quién es", "cuándo fue", "dónde está",
        "clima en", "weather in", "precio de", "noticias de", "resultados del",
        "últimas noticias", "qué pasó", "oscar", "copa del mundo", "bitcoin",
        "stock price", "hoy", "today", "ahora", "now", "actual", "current",
    ]

    def __call__(self, text: str) -> Dict[str, float]:
        """Clasificación basada en heurísticas."""
        low = text.lower()

        hard_count = sum(1 for kw in self.HARD_KEYWORDS if kw in low)
        soft_count = sum(1 for kw in self.SOFT_KEYWORDS if kw in low)
        web_count = sum(1 for kw in self.WEB_KEYWORDS if kw in low)

        return {
            "hard": min(hard_count / 3.0, 1.0) if hard_count > 0 else 0.2,
            "soft": min(soft_count / 3.0, 1.0) if soft_count > 0 else 0.2,
            "web_query": min(web_count / 2.0, 1.0) if web_count > 0 else 0.1,
        }


def create_trm_classifier(
    checkpoint_path: Optional[Path | str] = None,
    use_simulated: bool = False,
) -> TRMClassifier | TRMClassifierSimulated:
    """Factory para crear TRM Classifier.

    Args:
        checkpoint_path: Ruta al checkpoint del modelo entrenado. Si None
            se busca en models/trm_classifier/checkpoint.pt
        use_simulated: Si True retorna clasificador simulado (sin torch).

    Returns:
        Instancia de TRMClassifier o TRMClassifierSimulated.
    """

    if use_simulated or not HAS_TORCH:
        if not HAS_TORCH:
            logger.warning("PyTorch no disponible. Usando clasificador simulado.")
        return TRMClassifierSimulated()

    settings = load_settings()
    classifier_config = get_section(settings, "classifier", default={
        "d_model": 256,
        "d_latent": 256,
        "h_cycles": 3,
        "l_cycles": 4,
        "embedding_dim": 768,
    })

    classifier = TRMClassifier(
        d_model=int(classifier_config.get("d_model", 256)),
        d_latent=int(classifier_config.get("d_latent", 256)),
        h_cycles=int(classifier_config.get("h_cycles", 3)),
        l_cycles=int(classifier_config.get("l_cycles", 4)),
        embedding_dim=int(classifier_config.get("embedding_dim", 768)),
    )

    if checkpoint_path is None:
        root = Path(__file__).resolve().parents[3]
        checkpoint_path = root / "models" / "trm_classifier" / "checkpoint.pt"
    else:
        checkpoint_path = Path(checkpoint_path)

    classifier.load_checkpoint(checkpoint_path)
    return classifier


# Conditional exports
__all__ = [
    "HAS_TORCH",
    "TRMClassifierSimulated",
    "create_trm_classifier",
]

if HAS_TORCH:
    __all__.append("TRMClassifier")
