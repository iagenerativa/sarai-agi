"""MCP (Meta Control Plane) para SARAi_AGI.

Sistema adaptativo que calcula pesos α/β para routing entre modelos
hard-skill (experto) y soft-skill (empático).

Características:
- Dual mode: Rules-based (inicial) → Learned (tras feedback)
- Fast semantic cache con Vector Quantization
- Atomic reload sin downtime
- MoE routing para skills especializados

Migrado desde SARAi_v2 con mejoras de modularidad.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from ..configuration import get_section, load_settings

logger = logging.getLogger(__name__)


class MCPCache:
    """Cache semántico con Vector Quantization.

    Evita recalcular α/β para queries similares usando embeddings cuantizados.
    """

    def __init__(self, embedder, ttl: int = 60, quant_levels: int = 32):
        """
        Args:
            embedder: Instancia de embedder con método encode()
            ttl: Tiempo de vida del cache (segundos)
            quant_levels: Niveles de cuantización (5 bits = 32 niveles)
        """
        self.cache: Dict[bytes, Tuple[float, float, float]] = {}
        self.embedder = embedder
        self.ttl = ttl
        self.quant_levels = quant_levels

        logger.info("MCPCache initialized (TTL=%ds, quant_levels=%d)", ttl, quant_levels)

    def _quantize(self, emb: "np.ndarray") -> "np.ndarray":
        """Cuantiza embedding a 5 bits por dimensión."""
        if not HAS_TORCH:
            return emb  # Fallback sin cuantización

        # Normalizar a [0, 1]
        emb_norm = (emb - emb.min()) / (emb.max() - emb.min() + 1e-8)

        # Cuantizar
        emb_quant = (emb_norm * (self.quant_levels - 1)).astype(np.uint8)
        return np.clip(emb_quant, 0, self.quant_levels - 1)  # type: ignore[no-any-return]

    def get(self, context: str) -> Optional[Tuple[float, float]]:
        """Busca en cache por similitud semántica."""
        if not self.embedder:
            return None

        emb = self.embedder.encode(context)
        key = self._quantize(emb).tobytes()

        if key in self.cache:
            alpha, beta, ts = self.cache[key]

            if time.time() - ts < self.ttl:
                logger.debug("Cache HIT: α=%.2f, β=%.2f", alpha, beta)
                return alpha, beta
            else:
                del self.cache[key]

        return None

    def set(self, context: str, alpha: float, beta: float):
        """Guarda en cache."""
        if not self.embedder:
            return

        emb = self.embedder.encode(context)
        key = self._quantize(emb).tobytes()
        self.cache[key] = (alpha, beta, time.time())

    def clear_expired(self):
        """Limpia entradas expiradas."""
        current_time = time.time()
        expired_keys = [
            k for k, (_, _, ts) in self.cache.items()
            if current_time - ts >= self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.debug("Cleared %d expired cache entries", len(expired_keys))


class MCPRules:
    """MCP basado en reglas heurísticas (fase inicial)."""

    def __init__(self, config: Optional[Dict] = None, embedder=None):
        settings = load_settings()
        self.config = get_section(settings, "mcp", default={
            "cache_ttl": 60,
            "feedback_buffer_size": 1000,
        }) if config is None else config

        self.cache = MCPCache(embedder, ttl=self.config.get("cache_ttl", 60)) if embedder else None

    def compute_weights(
        self,
        hard: float,
        soft: float,
        context: str = "",
        feedback_buffer: Optional[List[Dict]] = None
    ) -> Tuple[float, float]:
        """Calcula pesos α (hard) y β (soft) según reglas heurísticas."""

        # Verificar cache semántico
        if self.cache and context:
            cached = self.cache.get(context)
            if cached:
                return cached

        # Reglas de routing
        if hard > 0.8 and soft < 0.3:
            alpha, beta = 0.95, 0.05  # Técnico puro
        elif soft > 0.7 and hard < 0.4:
            alpha, beta = 0.2, 0.8  # Emocional puro
        elif hard > 0.6 and soft < 0.5:
            alpha, beta = 0.85, 0.15  # Urgencia técnica
        elif 0.4 < hard < 0.7 and 0.4 < soft < 0.7:
            alpha, beta = 0.5, 0.5  # Explicación híbrida
        else:
            alpha, beta = 0.6, 0.4  # Default

        # Ajuste con feedback si existe
        if feedback_buffer and len(feedback_buffer) >= 10:
            alpha, beta = self._adjust_with_feedback(alpha, beta, feedback_buffer)

        # Normalizar
        total = alpha + beta
        alpha, beta = alpha / total, beta / total

        # Guardar en cache
        if self.cache and context:
            self.cache.set(context, alpha, beta)

        return alpha, beta

    def _adjust_with_feedback(
        self,
        alpha: float,
        beta: float,
        buffer: List[Dict]
    ) -> Tuple[float, float]:
        """Ajusta pesos basándose en feedback reciente."""
        recent = buffer[-10:]

        hard_success = sum(1 for x in recent if x.get('alpha', 0) > 0.7 and x.get('feedback', 0) > 0)
        soft_success = sum(1 for x in recent if x.get('beta', 0) > 0.7 and x.get('feedback', 0) > 0)

        hard_total = sum(1 for x in recent if x.get('alpha', 0) > 0.7)
        soft_total = sum(1 for x in recent if x.get('beta', 0) > 0.7)

        if hard_total > 0 and (hard_success / hard_total) < 0.5:
            beta = min(beta + 0.1, 0.8)
            alpha = 1.0 - beta

        if soft_total > 0 and (soft_success / soft_total) < 0.5:
            alpha = min(alpha + 0.1, 0.8)
            beta = 1.0 - alpha

        return alpha, beta


if HAS_TORCH:
    class MCPLearned(nn.Module):
        """MCP con red neuronal entrenable."""

        def __init__(self, config: Optional[Dict] = None):
            super().__init__()

            settings = load_settings()
            self.config = get_section(settings, "mcp", default={}) if config is None else config

            # MLP ligero: [hard, soft, avg_hard_success, avg_soft_success, urgency] → [α, β]
            self.mlp = nn.Sequential(
                nn.Linear(5, 32),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(32, 16),
                nn.ReLU(),
                nn.Linear(16, 2),
                nn.Softmax(dim=-1)
            )

            self.device = torch.device("cpu")
            self.to(self.device)

        def forward(self, features: torch.Tensor) -> Tuple[float, float]:
            """Calcula pesos α, β."""
            with torch.no_grad():
                weights = self.mlp(features.unsqueeze(0))
                alpha, beta = weights[0, 0].item(), weights[0, 1].item()
            return alpha, beta

        def train_step(self, batch: List[Dict], optimizer: torch.optim.Optimizer) -> float:
            """Un paso de entrenamiento con policy gradient."""
            self.train()
            losses = []

            for item in batch:
                features = torch.tensor([
                    item['hard'],
                    item['soft'],
                    item.get('avg_hard_success', 0.5),
                    item.get('avg_soft_success', 0.5),
                    item.get('urgency', 0.0)
                ], dtype=torch.float32).to(self.device)

                weights = self.mlp(features.unsqueeze(0))
                alpha_pred, beta_pred = weights[0, 0], weights[0, 1]

                feedback = item.get('feedback', 0.0)
                alpha_used = item.get('alpha', 0.5)

                if alpha_used > 0.7:
                    loss = -feedback * torch.log(alpha_pred + 1e-8)
                else:
                    loss = -feedback * torch.log(beta_pred + 1e-8)

                losses.append(loss)

            total_loss = torch.stack(losses).mean()
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()

            self.eval()
            return total_loss.item()

        def save_checkpoint(self, path: Path) -> None:
            """Guarda checkpoint."""
            path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(self.state_dict(), path)
            logger.info("MCP checkpoint saved to %s", path)

        def load_checkpoint(self, path: Path) -> bool:
            """Carga checkpoint."""
            if not path.exists():
                logger.warning("MCP checkpoint not found: %s", path)
                return False

            self.load_state_dict(torch.load(path, map_location=self.device, weights_only=False))
            logger.info("MCP checkpoint loaded from %s", path)
            return True


class MCP:
    """Meta Control Plane adaptativo.

    Usa reglas inicialmente, evoluciona a MLP tras suficiente feedback.
    """

    def __init__(self, config: Optional[Dict] = None, embedder=None):
        settings = load_settings()
        self.config = get_section(settings, "mcp", default={
            "mode": "rules",
            "feedback_buffer_size": 1000,
            "training": {
                "min_samples": 100,
                "learning_rate": 0.001,
            },
        }) if config is None else config

        self.mode = self.config.get("mode", "rules")
        self.rules_mcp = MCPRules(self.config, embedder)

        if HAS_TORCH:
            self.learned_mcp: Optional[MCPLearned] = MCPLearned(self.config)

            # Intentar cargar checkpoint
            checkpoint_path = Path("models") / "mcp" / "checkpoint.pt"
            if self.learned_mcp.load_checkpoint(checkpoint_path):
                self.mode = "learned"
                logger.info("MCP initialized in learned mode")
            else:
                logger.info("MCP initialized in rules mode")
        else:
            self.learned_mcp = None
            logger.info("PyTorch not available, MCP in rules-only mode")

        self.feedback_buffer: List[Dict] = []

    def compute_weights(
        self,
        scores_or_hard: Any,
        soft: Optional[float] = None,
        context: str = "",
        feedback_buffer: Optional[List[Dict]] = None
    ) -> Tuple[float, float]:
        """Calcula pesos α/β con compatibilidad retro.

        Acepta:
        - ``compute_weights({'hard': 0.8, 'soft': 0.2}, context="...")``
        - ``compute_weights(0.8, 0.2, context="...")``
        """
        # Parsear argumentos (dict o posicional)
        if isinstance(scores_or_hard, dict):
            hard = float(scores_or_hard.get('hard', 0.5))
            soft_score = float(scores_or_hard.get('soft', 0.5))

            if isinstance(soft, str) and not context:
                context_param = soft
                custom_buffer = feedback_buffer
            else:
                context_param = context
                custom_buffer = feedback_buffer
        else:
            hard = float(scores_or_hard)
            if soft is None:
                raise ValueError("soft score required when using positional arguments")
            soft_score = float(soft)
            context_param = context
            custom_buffer = feedback_buffer

        active_buffer = custom_buffer if custom_buffer is not None else self.feedback_buffer

        # Delegar al modo activo
        if self.mode == "learned" and HAS_TORCH:
            avg_hard_success = self._compute_avg_success(branch='hard')
            avg_soft_success = self._compute_avg_success(branch='soft')
            urgency = 1.0 if hard > 0.8 else 0.0

            features = torch.tensor([
                hard,
                soft_score,
                avg_hard_success,
                avg_soft_success,
                urgency
            ], dtype=torch.float32)

            if self.learned_mcp is not None:
                alpha, beta = self.learned_mcp(features)
            else:
                # Fallback to rules if learned MCP is None
                alpha, beta = self.rules_mcp.compute_weights(
                    hard,
                    soft_score,
                    context=context_param,
                    feedback_buffer=active_buffer
                )
        else:
            alpha, beta = self.rules_mcp.compute_weights(
                hard,
                soft_score,
                context=context_param,
                feedback_buffer=active_buffer
            )

        return alpha, beta

    def add_feedback(self, interaction: Dict):
        """Agrega interacción al buffer de feedback."""
        self.feedback_buffer.append(interaction)

        max_size = self.config.get("feedback_buffer_size", 1000)
        if len(self.feedback_buffer) > max_size:
            self.feedback_buffer = self.feedback_buffer[-max_size:]

        # Cambiar a learned si suficientes datos
        min_samples = self.config.get("training", {}).get("min_samples", 100)
        if len(self.feedback_buffer) >= min_samples and self.mode == "rules" and HAS_TORCH:
            logger.info("Sufficient feedback accumulated. Training learned MCP...")
            self._train_learned_mcp()
            self.mode = "learned"

    def _compute_avg_success(self, branch: str) -> float:
        """Calcula tasa de éxito promedio de una rama."""
        if not self.feedback_buffer:
            return 0.5

        recent = self.feedback_buffer[-20:]

        if branch == 'hard':
            relevant = [x for x in recent if x.get('alpha', 0) > 0.7]
        else:
            relevant = [x for x in recent if x.get('beta', 0) > 0.7]

        if not relevant:
            return 0.5

        success = sum(1 for x in relevant if x.get('feedback', 0) > 0)
        return success / len(relevant)

    def _train_learned_mcp(self):
        """Entrena el MCP con el buffer de feedback."""
        if not HAS_TORCH:
            return

        lr = self.config.get("training", {}).get("learning_rate", 0.001)
        optimizer = torch.optim.Adam(self.learned_mcp.parameters(), lr=lr)

        logger.info("Training MCP...")
        for epoch in range(10):
            loss = self.learned_mcp.train_step(self.feedback_buffer, optimizer)
            if epoch % 3 == 0:
                logger.info("  Epoch %d: loss = %.4f", epoch, loss)

        checkpoint_path = Path("models") / "mcp" / "checkpoint.pt"
        self.learned_mcp.save_checkpoint(checkpoint_path)
        logger.info("MCP training complete")


# ========== Singleton global para atomic reload ==========

_mcp_active: Optional[MCP] = None
_mcp_lock = threading.RLock()


def reload_mcp() -> bool:
    """Recarga MCP desde disco de forma atómica (doble buffer)."""
    global _mcp_active

    signal_file = Path("state") / "mcp_reload_signal"

    if not signal_file.exists():
        return False

    new_model_path = Path("models") / "mcp" / "mcp_active.pkl"

    if not new_model_path.exists():
        logger.warning("Reload signal found but mcp_active.pkl missing")
        signal_file.unlink()
        return False

    try:
        if not HAS_TORCH:
            logger.warning("PyTorch not available, cannot reload MCP")
            return False

        logger.info("Loading new MCP from disk...")
        mcp_new = torch.load(new_model_path, weights_only=False)

        with _mcp_lock:
            _mcp_active = mcp_new
            logger.info("Atomic MCP reload complete")

        signal_file.unlink()
        return True

    except Exception as e:
        logger.error("MCP reload failed: %s", e)
        signal_file.unlink()
        return False


def get_mcp_weights(scores: Dict[str, float], context: str = "") -> Tuple[float, float]:
    """Obtiene pesos α/β de forma thread-safe."""
    global _mcp_active

    reload_mcp()  # Verificar señal de recarga

    with _mcp_lock:
        if _mcp_active is None:
            _mcp_active = create_mcp()

        hard = scores.get('hard', 0.5)
        soft = scores.get('soft', 0.5)
        return _mcp_active.compute_weights(hard, soft, context)


def create_mcp(embedder=None) -> MCP:
    """Factory para crear MCP."""
    return MCP(embedder=embedder)


__all__ = [
    "MCP",
    "MCPRules",
    "MCPCache",
    "create_mcp",
    "get_mcp_weights",
    "reload_mcp",
]
