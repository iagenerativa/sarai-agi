"""
SARAi HLCS v0.3 - Wisdom-Driven Silence
========================================

Silencio estratégico basado en sabiduría emergente:
- Multiple silence strategies (uncertainty, ethics, fatigue, novelty)
- Wisdom accumulation from non-action
- Prudence scoring
- Recovery time allowance
- Exploration-exploitation balance

"A veces, la acción más sabia es la inacción consciente"

Version: 0.3.0
Author: SARAi Team
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SilenceStrategy(Enum):
    """Estrategias de silencio."""
    BASIC_MODE = "basic_mode"  # Nunca actuar en modo básico
    HIGH_UNCERTAINTY = "high_uncertainty"  # Incertidumbre demasiado alta
    ETHICAL_AMBIGUITY = "ethical_ambiguity"  # Dilema ético no resuelto
    SYSTEM_FATIGUE = "system_fatigue"  # Sistema necesita recuperación
    NOVEL_SITUATION = "novel_situation"  # Situación desconocida, observar primero
    HUMAN_OVERRIDE = "human_override"  # Humano explícitamente pidió silencio


@dataclass
class SilenceInstruction:
    """Instrucción de silencio."""
    strategy: SilenceStrategy
    duration: Optional[timedelta]  # None = indefinido
    reason: str
    wisdom_accumulated: Optional[str] = None
    recovery_actions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        duration_str = f"{self.duration}" if self.duration else "indefinite"
        return (
            f"Silence ({self.strategy.value}): {self.reason} "
            f"for {duration_str}"
        )


@dataclass
class SilenceWisdom:
    """Sabiduría acumulada del silencio."""
    wisdom_id: str
    strategy_used: SilenceStrategy
    situation_context: str
    outcome_observed: str
    wisdom_learned: str
    confidence: float  # 0.0-1.0
    timestamp: datetime
    
    def __str__(self) -> str:
        return (
            f"Silence wisdom ({self.strategy_used.value}): {self.wisdom_learned} "
            f"(confidence: {self.confidence:.2f})"
        )


class WisdomAccumulator:
    """
    Acumulador de sabiduría derivada de períodos de silencio.
    
    Aprende que:
    - Observar antes de actuar previene errores
    - Esperar recuperación mejora outcomes
    - Situaciones novedosas requieren cautela
    - Dilemas éticos no resueltos necesitan más reflexión
    """
    
    def __init__(self, max_wisdoms: int = 50):
        """
        Args:
            max_wisdoms: Número máximo de sabiduríases de silencio
        """
        self.max_wisdoms = max_wisdoms
        self.silence_wisdoms: List[SilenceWisdom] = []
    
    def record_silence_wisdom(
        self,
        strategy: SilenceStrategy,
        situation: Dict,
        outcome: Optional[Dict] = None,
    ) -> SilenceWisdom:
        """
        Registra sabiduría aprendida de un período de silencio.
        
        Args:
            strategy: Estrategia de silencio usada
            situation: Contexto de la situación
            outcome: Outcome observado después del silencio (opcional)
        
        Returns:
            SilenceWisdom registrada
        """
        # Generar wisdom basada en strategy
        wisdom_learned = self._extract_wisdom_from_strategy(strategy, situation, outcome)
        
        wisdom = SilenceWisdom(
            wisdom_id=f"silence_{strategy.value}_{datetime.now().timestamp()}",
            strategy_used=strategy,
            situation_context=str(situation),
            outcome_observed=str(outcome) if outcome else "pending",
            wisdom_learned=wisdom_learned,
            confidence=0.7,  # Base confidence
            timestamp=datetime.now(),
        )
        
        self.silence_wisdoms.append(wisdom)
        
        # Mantener límite
        if len(self.silence_wisdoms) > self.max_wisdoms:
            # Remover las menos confiables
            self.silence_wisdoms = sorted(
                self.silence_wisdoms,
                key=lambda w: w.confidence,
                reverse=True
            )[:self.max_wisdoms]
        
        logger.info("Recorded silence wisdom: %s", wisdom)
        
        return wisdom
    
    def _extract_wisdom_from_strategy(
        self, strategy: SilenceStrategy, situation: Dict, outcome: Optional[Dict]
    ) -> str:
        """Extrae sabiduría específica de la estrategia usada."""
        wisdom_templates = {
            SilenceStrategy.HIGH_UNCERTAINTY: (
                "When uncertainty is high, observation yields better outcomes than hasty action"
            ),
            SilenceStrategy.ETHICAL_AMBIGUITY: (
                "Ethical dilemmas require reflection before action"
            ),
            SilenceStrategy.SYSTEM_FATIGUE: (
                "Allowing system recovery time prevents cascading failures"
            ),
            SilenceStrategy.NOVEL_SITUATION: (
                "Novel situations benefit from initial observation period"
            ),
            SilenceStrategy.BASIC_MODE: (
                "Operating within designated boundaries maintains trust"
            ),
        }
        
        base_wisdom = wisdom_templates.get(
            strategy,
            "Silence can be wiser than action"
        )
        
        # Enriquecer con outcome si disponible
        if outcome:
            improvement = outcome.get("improvement_observed", 0.0)
            if improvement > 0:
                base_wisdom += f" (System improved {improvement:.1f}% during silence)"
            elif improvement < 0:
                base_wisdom += f" (System degraded {abs(improvement):.1f}% during silence - may need intervention)"
        
        return base_wisdom
    
    def get_accumulated_wisdoms(self) -> List[SilenceWisdom]:
        """Obtiene todas las sabiduríases acumuladas."""
        return sorted(
            self.silence_wisdoms,
            key=lambda w: w.confidence,
            reverse=True
        )
    
    def get_wisdom_for_strategy(
        self, strategy: SilenceStrategy
    ) -> List[SilenceWisdom]:
        """Obtiene sabiduríases para una estrategia específica."""
        return [
            w for w in self.silence_wisdoms
            if w.strategy_used == strategy
        ]


class WisdomDrivenSilence:
    """
    HLCS v0.3 Wisdom-Driven Silence
    
    Silencio estratégico basado en sabiduría acumulada:
    - Multiple silence strategies (uncertainty, ethics, fatigue, novelty)
    - Wisdom accumulation from periods of non-action
    - Prudence scoring (when to act vs observe)
    - Recovery time allowance (system fatigue detection)
    - Exploration-exploitation balance
    
    Features:
    - Context-aware silence decisions
    - Learning from silence outcomes
    - Strategic observation periods
    - Ethical reflection time
    - System recovery windows
    
    Example:
        >>> silence = WisdomDrivenSilence()
        >>> situation = {
        ...     "uncertainty": 0.75,
        ...     "novelty": 0.6,
        ...     "system_state": {"fatigue": 0.8}
        ... }
        >>> instruction = silence.should_remain_silent(situation)
        >>> if instruction:
        ...     print(f"Silence strategy: {instruction.strategy.value}")
        ...     print(f"Reason: {instruction.reason}")
    """
    
    def __init__(
        self,
        uncertainty_threshold: float = 0.6,
        novelty_threshold: float = 0.7,
        ethical_ambiguity_threshold: float = 0.5,
        fatigue_threshold: float = 0.7,
    ):
        """
        Args:
            uncertainty_threshold: Umbral de incertidumbre para silencio
            novelty_threshold: Umbral de novedad para observación
            ethical_ambiguity_threshold: Umbral de ambigüedad ética
            fatigue_threshold: Umbral de fatiga del sistema
        """
        self.uncertainty_threshold = uncertainty_threshold
        self.novelty_threshold = novelty_threshold
        self.ethical_ambiguity_threshold = ethical_ambiguity_threshold
        self.fatigue_threshold = fatigue_threshold
        
        # Silence strategies (callable)
        self.silence_strategies: Dict[str, Callable] = {
            "basic_mode": self._never_act_in_basic,
            "high_uncertainty": self._seek_guidance_on_uncertainty,
            "ethical_ambiguity": self._deliberate_on_ethics,
            "system_fatigue": self._allow_recovery_time,
            "novel_situation": self._engage_in_exploration,
        }
        
        self.wisdom_accumulator = WisdomAccumulator()
        
        # State tracking
        self.current_silence: Optional[SilenceInstruction] = None
        self.silence_history: List[SilenceInstruction] = []
        
        logger.info(
            "Wisdom-Driven Silence initialized: uncertainty=%.2f, novelty=%.2f, "
            "ethics=%.2f, fatigue=%.2f",
            uncertainty_threshold, novelty_threshold,
            ethical_ambiguity_threshold, fatigue_threshold
        )
    
    def should_remain_silent(
        self, situation: Dict
    ) -> Optional[SilenceInstruction]:
        """
        Determina si debe mantenerse en silencio en la situación dada.
        
        Args:
            situation: Dict con contexto
                      Debe incluir: uncertainty, novelty, ethical_ambiguity, system_state, mode
        
        Returns:
            SilenceInstruction si debe permanecer silencioso, None si debe actuar
        """
        # Extract situation factors
        mode = situation.get("mode", "advanced")
        uncertainty = situation.get("uncertainty", 0.0)
        novelty = situation.get("novelty", 0.0)
        ethical_ambiguity = situation.get("ethical_ambiguity", 0.0)
        system_state = situation.get("system_state", {})
        
        # Evaluar cada estrategia en orden de prioridad
        
        # 1. Basic mode - nunca actuar
        if mode == "basic":
            instruction = self._adopt_silence_strategy(
                SilenceStrategy.BASIC_MODE,
                situation
            )
            return instruction
        
        # 2. High uncertainty - buscar guía
        if uncertainty > self.uncertainty_threshold:
            instruction = self._adopt_silence_strategy(
                SilenceStrategy.HIGH_UNCERTAINTY,
                situation
            )
            return instruction
        
        # 3. Ethical ambiguity - deliberar
        if ethical_ambiguity > self.ethical_ambiguity_threshold:
            instruction = self._adopt_silence_strategy(
                SilenceStrategy.ETHICAL_AMBIGUITY,
                situation
            )
            return instruction
        
        # 4. System fatigue - permitir recuperación
        if self._is_system_fatigued(system_state):
            instruction = self._adopt_silence_strategy(
                SilenceStrategy.SYSTEM_FATIGUE,
                situation
            )
            return instruction
        
        # 5. Novel situation - explorar primero
        if novelty > self.novelty_threshold:
            instruction = self._adopt_silence_strategy(
                SilenceStrategy.NOVEL_SITUATION,
                situation
            )
            return instruction
        
        # No silence required - OK to act
        logger.debug("No silence required for situation")
        return None
    
    def _adopt_silence_strategy(
        self, strategy: SilenceStrategy, situation: Dict
    ) -> SilenceInstruction:
        """
        Adopta estrategia de silencio específica.
        
        Args:
            strategy: Estrategia a adoptar
            situation: Contexto actual
        
        Returns:
            SilenceInstruction con detalles
        """
        # Obtener función de estrategia
        strategy_key = strategy.value
        strategy_func = self.silence_strategies.get(strategy_key)
        
        if not strategy_func:
            logger.error("Unknown silence strategy: %s", strategy_key)
            return SilenceInstruction(
                strategy=strategy,
                duration=None,
                reason="Unknown strategy",
            )
        
        # Ejecutar estrategia
        instruction = strategy_func(situation)
        
        # Registrar wisdom del silencio
        self.wisdom_accumulator.record_silence_wisdom(
            strategy, situation, outcome=None
        )
        
        # Track silence
        self.current_silence = instruction
        self.silence_history.append(instruction)
        
        # Mantener últimas 100 instrucciones
        if len(self.silence_history) > 100:
            self.silence_history = self.silence_history[-100:]
        
        logger.info("Adopted silence strategy: %s", instruction)
        
        return instruction
    
    def _never_act_in_basic(self, situation: Dict) -> SilenceInstruction:
        """Estrategia: Nunca actuar en modo básico."""
        return SilenceInstruction(
            strategy=SilenceStrategy.BASIC_MODE,
            duration=None,  # Indefinido
            reason="Operating in basic mode - autonomous actions disabled",
            recovery_actions=[
                "Switch to advanced mode to enable autonomous actions",
                "Operate in observation-only mode",
            ],
        )
    
    def _seek_guidance_on_uncertainty(self, situation: Dict) -> SilenceInstruction:
        """Estrategia: Buscar guía cuando incertidumbre es alta."""
        uncertainty = situation.get("uncertainty", 0.0)
        
        return SilenceInstruction(
            strategy=SilenceStrategy.HIGH_UNCERTAINTY,
            duration=timedelta(hours=2),  # Esperar 2h para más datos
            reason=f"Uncertainty too high ({uncertainty:.2%}) - gathering more data",
            wisdom_accumulated="Observation before action reduces errors under uncertainty",
            recovery_actions=[
                "Collect more samples to reduce epistemic uncertainty",
                "Request human guidance for high-stakes decision",
                "Monitor situation without intervening",
            ],
        )
    
    def _deliberate_on_ethics(self, situation: Dict) -> SilenceInstruction:
        """Estrategia: Deliberar cuando hay ambigüedad ética."""
        ethical_ambiguity = situation.get("ethical_ambiguity", 0.0)
        
        return SilenceInstruction(
            strategy=SilenceStrategy.ETHICAL_AMBIGUITY,
            duration=timedelta(hours=24),  # Esperar decisión humana
            reason=f"Ethical ambiguity detected ({ethical_ambiguity:.2%}) - reflection required",
            wisdom_accumulated="Ethical dilemmas benefit from human judgment",
            recovery_actions=[
                "Present ethical dilemma to human stakeholders",
                "Analyze long-term consequences before action",
                "Seek consensus from multiple perspectives",
            ],
        )
    
    def _allow_recovery_time(self, situation: Dict) -> SilenceInstruction:
        """Estrategia: Permitir tiempo de recuperación al sistema."""
        system_state = situation.get("system_state", {})
        fatigue = system_state.get("fatigue", 0.0)
        
        # Tiempo de recuperación proporcional a fatiga
        recovery_hours = int(fatigue * 6)  # Max 6 horas
        
        return SilenceInstruction(
            strategy=SilenceStrategy.SYSTEM_FATIGUE,
            duration=timedelta(hours=recovery_hours),
            reason=f"System fatigue detected ({fatigue:.2%}) - allowing recovery time",
            wisdom_accumulated="Recovery periods prevent cascading failures",
            recovery_actions=[
                f"Wait {recovery_hours}h for system to stabilize",
                "Monitor metrics for improvement",
                "Reduce load during recovery period",
            ],
        )
    
    def _engage_in_exploration(self, situation: Dict) -> SilenceInstruction:
        """Estrategia: Explorar situación novel antes de actuar."""
        novelty = situation.get("novelty", 0.0)
        
        return SilenceInstruction(
            strategy=SilenceStrategy.NOVEL_SITUATION,
            duration=timedelta(minutes=30),  # Observación corta
            reason=f"Novel situation detected ({novelty:.2%}) - initial observation period",
            wisdom_accumulated="Observation of novel situations builds understanding",
            recovery_actions=[
                "Observe system behavior for 30 minutes",
                "Identify patterns before intervening",
                "Build mental model of new situation",
            ],
        )
    
    def _is_system_fatigued(self, system_state: Dict) -> bool:
        """Detecta si el sistema está fatigado."""
        fatigue = system_state.get("fatigue", 0.0)
        
        # También considerar:
        # - Número de acciones recientes
        # - Error rate reciente
        # - Uptime sin descanso
        
        recent_actions = system_state.get("recent_actions_count", 0)
        error_rate = system_state.get("error_rate", 0.0)
        
        # Fatigue score compuesto
        composite_fatigue = max(
            fatigue,
            min(recent_actions / 20.0, 1.0),  # >20 acciones recientes
            error_rate,  # Alta tasa de error
        )
        
        return composite_fatigue > self.fatigue_threshold
    
    def observe_silence_outcome(
        self, instruction: SilenceInstruction, outcome: Dict
    ) -> None:
        """
        Observa el outcome después de un período de silencio.
        
        Args:
            instruction: Instrucción de silencio original
            outcome: Outcome observado (mejora, deterioro, estable)
        """
        # Actualizar wisdom basado en outcome
        self.wisdom_accumulator.record_silence_wisdom(
            instruction.strategy,
            {"reason": instruction.reason},
            outcome=outcome,
        )
        
        logger.info(
            "Silence outcome observed for strategy %s: %s",
            instruction.strategy.value,
            outcome
        )
    
    def get_silence_effectiveness(self) -> Dict:
        """
        Evalúa efectividad de estrategias de silencio.
        
        Returns:
            Dict con stats por estrategia
        """
        stats_by_strategy = {}
        
        for strategy in SilenceStrategy:
            wisdoms = self.wisdom_accumulator.get_wisdom_for_strategy(strategy)
            
            if wisdoms:
                avg_confidence = sum(w.confidence for w in wisdoms) / len(wisdoms)
                stats_by_strategy[strategy.value] = {
                    "total_uses": len(wisdoms),
                    "avg_confidence": avg_confidence,
                    "top_wisdom": wisdoms[0].wisdom_learned if wisdoms else None,
                }
        
        return stats_by_strategy
    
    def get_current_silence_status(self) -> Optional[Dict]:
        """Obtiene estado del silencio actual."""
        if not self.current_silence:
            return None
        
        elapsed = datetime.now() - self.current_silence.timestamp
        remaining = None
        
        if self.current_silence.duration:
            remaining = self.current_silence.duration - elapsed
            if remaining.total_seconds() <= 0:
                # Silencio expirado
                self.current_silence = None
                return None
        
        return {
            "strategy": self.current_silence.strategy.value,
            "reason": self.current_silence.reason,
            "elapsed": str(elapsed),
            "remaining": str(remaining) if remaining else "indefinite",
            "recovery_actions": self.current_silence.recovery_actions,
        }


# Exports
__all__ = [
    "WisdomDrivenSilence",
    "WisdomAccumulator",
    "SilenceInstruction",
    "SilenceWisdom",
    "SilenceStrategy",
]
