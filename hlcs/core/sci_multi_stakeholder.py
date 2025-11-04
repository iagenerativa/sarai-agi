"""
Multi-Stakeholder Social Contract Interface
Sistema de consenso ponderado para evoluciones de identidad AGI

Version: 0.4.0
Author: SARAi Team
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configuración de logging
logger = logging.getLogger(__name__)

class StakeholderRole(Enum):
    PRIMARY_USER = "primary_user"
    SYSTEM_ADMIN = "system_admin" 
    OTHER_AGENTS = "other_agents"
    ENVIRONMENT = "environment"
    SECURITY_AUDITOR = "security_auditor"
    ETHICS_COMMITTEE = "ethics_committee"

class DecisionType(Enum):
    RATIFY = "ratify"
    VETO = "veto"
    ABSTAIN = "abstain"

@dataclass
class StakeholderConfig:
    role: StakeholderRole
    weight: float
    approval_required: bool
    notification_priority: int
    timeout_hours: int
    expertise_area: str

@dataclass
class EvolutionProposal:
    """Propuesta de evolución de identidad"""
    id: str
    timestamp: datetime
    title: str
    description: str
    changes: Dict[str, Any]
    impact_assessment: Dict[str, float]
    risk_level: float
    benefits: List[str]
    proposed_by: str
    justification: str
    
@dataclass
class StakeholderDecision:
    """Decisión de un stakeholder"""
    stakeholder_role: StakeholderRole
    decision: DecisionType
    rationale: str
    confidence: float
    timestamp: datetime
    expertise_considered: List[str]

@dataclass
class ConsensusResult:
    """Resultado del proceso de consenso"""
    approved: bool
    consensus_score: float
    decisions: List[StakeholderDecision]
    weighted_approval: float
    timeout_occurred: bool
    applied_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

class MultiStakeholderSCI:
    """
    Social Contract Interface con consenso ponderado multi-stakeholder
    
    Considera múltiples voces en la evolución de identidad:
    - Primary User (60% peso): Propietario principal del sistema
    - System Admin (30% peso): Responsabilidad técnica y seguridad
    - Other Agents (10% peso): Perspectiva de otros AGIs en el ecosistema
    - Security Auditor (advisory): Evaluación de seguridad
    - Ethics Committee (advisory): Evaluación ética
    """
    
    def __init__(self, config_path: str = "/app/config/stakeholder_config.json"):
        self.config_path = config_path
        self.pending_proposals: Dict[str, EvolutionProposal] = {}
        self.stakeholder_decisions: Dict[str, List[StakeholderDecision]] = {}
        self.consensus_threshold = 0.8  # 80% del peso debe aprobar
        self.timeout_default = 24  # horas
        
        # Cargar configuración de stakeholders
        self.stakeholders = self._load_stakeholder_config()
        
        # Memoria de evoluciones previas para aprendizaje
        self.evolution_memory = []
        
        logger.info("MultiStakeholderSCI inicializado con %d stakeholders", len(self.stakeholders))
    
    def _load_stakeholder_config(self) -> Dict[StakeholderRole, StakeholderConfig]:
        """
        Cargar configuración de stakeholders desde archivo
        """
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            stakeholders = {}
            for role_str, config in config_data.items():
                role = StakeholderRole(role_str)
                stakeholders[role] = StakeholderConfig(
                    role=role,
                    weight=config['weight'],
                    approval_required=config['approval_required'],
                    notification_priority=config['notification_priority'],
                    timeout_hours=config['timeout_hours'],
                    expertise_area=config['expertise_area']
                )
            
            return stakeholders
            
        except FileNotFoundError:
            logger.warning("Stakeholder config no encontrado en %s, usando default", self.config_path)
            return self._get_default_stakeholder_config()
        except Exception as e:
            logger.error("Error cargando stakeholder config: %s", e)
            return self._get_default_stakeholder_config()
    
    def _get_default_stakeholder_config(self) -> Dict[StakeholderRole, StakeholderConfig]:
        """
        Configuración por defecto de stakeholders
        """
        return {
            StakeholderRole.PRIMARY_USER: StakeholderConfig(
                role=StakeholderRole.PRIMARY_USER,
                weight=0.6,
                approval_required=True,
                notification_priority=1,
                timeout_hours=24,
                expertise_area="user_experience"
            ),
            StakeholderRole.SYSTEM_ADMIN: StakeholderConfig(
                role=StakeholderRole.SYSTEM_ADMIN,
                weight=0.3,
                approval_required=True,
                notification_priority=2,
                timeout_hours=12,
                expertise_area="system_stability"
            ),
            StakeholderRole.OTHER_AGENTS: StakeholderConfig(
                role=StakeholderRole.OTHER_AGENTS,
                weight=0.1,
                approval_required=False,
                notification_priority=3,
                timeout_hours=48,
                expertise_area="ecosystem_impact"
            ),
            StakeholderRole.SECURITY_AUDITOR: StakeholderConfig(
                role=StakeholderRole.SECURITY_AUDITOR,
                weight=0.0,  # Advisory only
                approval_required=False,
                notification_priority=1,
                timeout_hours=6,
                expertise_area="security_posture"
            ),
            StakeholderRole.ETHICS_COMMITTEE: StakeholderConfig(
                role=StakeholderRole.ETHICS_COMMITTEE,
                weight=0.0,  # Advisory only
                approval_required=False,
                notification_priority=1,
                timeout_hours=8,
                expertise_area="ethical_alignment"
            )
        }
    
    async def propose_identity_evolution(self, evolution: EvolutionProposal) -> str:
        """
        Proponer evolución de identidad con proceso multi-stakeholder
        
        Returns:
            proposal_id: ID único de la propuesta
        """
        # Generar ID único
        proposal_id = self._generate_proposal_id(evolution)
        evolution.id = proposal_id
        
        # Almacenar propuesta
        self.pending_proposals[proposal_id] = evolution
        self.stakeholder_decisions[proposal_id] = []
        
        logger.info("Evolución propuesta: %s - %s", proposal_id, evolution.title)
        
        # Evaluar impacto en stakeholders
        stakeholder_impacts = await self._assess_stakeholder_impacts(evolution)
        
        # Notificar stakeholders según prioridad
        await self._notify_stakeholders(proposal_id, evolution, stakeholder_impacts)
        
        # Iniciar proceso de consenso asíncrono
        asyncio.create_task(self._run_consensus_process(proposal_id))
        
        return proposal_id
    
    def _generate_proposal_id(self, evolution: EvolutionProposal) -> str:
        """Generar ID único para propuesta"""
        content = f"{evolution.title}{evolution.description}{evolution.timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    async def _assess_stakeholder_impacts(self, evolution: EvolutionProposal) -> Dict[StakeholderRole, Dict[str, float]]:
        """
        Evaluar impacto de la evolución en cada stakeholder
        """
        impacts = {}
        
        for stakeholder_role, config in self.stakeholders.items():
            urgency = self._calculate_urgency(evolution)
            expertise_relevance = self._assess_expertise_relevance(config.expertise_area, evolution)
            
            impacts[stakeholder_role] = {
                "urgency": urgency,
                "expertise_relevance": expertise_relevance,
                "priority_score": urgency * 0.7 + expertise_relevance * 0.3,
                "requires_approval": config.approval_required,
                "timeout_hours": config.timeout_hours
            }
        
        return impacts
    
    def _calculate_urgency(self, evolution: EvolutionProposal) -> float:
        """Calcular urgencia de la propuesta"""
        # Factores que aumentan urgencia
        urgency_factors = [
            evolution.risk_level * 0.3,  # Alto riesgo = mayor urgencia
            len(evolution.benefits) * 0.1,  # Más beneficios = mayor urgencia
            evolution.impact_assessment.get("system_stability", 0) * 0.2
        ]
        
        return min(sum(urgency_factors), 1.0)
    
    def _assess_expertise_relevance(self, expertise_area: str, evolution: EvolutionProposal) -> float:
        """Evaluar relevancia del expertise para la propuesta"""
        relevance_keywords = {
            "user_experience": ["interface", "response", "satisfaction", "user"],
            "system_stability": ["performance", "latency", "memory", "stability"],
            "security_posture": ["security", "access", "authentication", "encryption"],
            "ethical_alignment": ["ethics", "fairness", "bias", "transparency"],
            "ecosystem_impact": ["integration", "compatibility", "dependency"]
        }
        
        keywords = relevance_keywords.get(expertise_area, [])
        text_to_analyze = f"{evolution.title} {evolution.description} {json.dumps(evolution.changes)}"
        
        relevance_score = sum(1 for keyword in keywords if keyword.lower() in text_to_analyze.lower())
        return min(relevance_score / len(keywords), 1.0) if keywords else 0.0
    
    async def _notify_stakeholders(self, proposal_id: str, evolution: EvolutionProposal, impacts: Dict[StakeholderRole, Dict[str, float]]):
        """
        Notificar stakeholders según prioridad y impacto
        """
        for stakeholder_role, config in sorted(self.stakeholders.items(), key=lambda x: x[1].notification_priority):
            impact = impacts.get(stakeholder_role, {})
            
            if config.approval_required:
                # Stakeholder crítico - requiere aprobación
                await self._send_approval_request(proposal_id, evolution, stakeholder_role, impact)
            else:
                # Stakeholder advisory - solo perspectiva
                await self._send_advisory_request(proposal_id, evolution, stakeholder_role, impact)
    
    async def _send_approval_request(self, proposal_id: str, evolution: EvolutionProposal, stakeholder_role: StakeholderRole, impact: Dict[str, float]):
        """
        Enviar solicitud de aprobación a stakeholder crítico
        """
        logger.info("Enviando solicitud de aprobación a %s para propuesta %s", stakeholder_role.value, proposal_id)
        
        # En implementación real: enviar notificación via webhook, email, etc.
        notification_payload = {
            "type": "approval_request",
            "proposal_id": proposal_id,
            "stakeholder": stakeholder_role.value,
            "evolution_title": evolution.title,
            "risk_level": evolution.risk_level,
            "impact_assessment": impact,
            "timeout_hours": impact.get("timeout_hours", 24)
        }
        
        # TODO: Implementar webhook/email notification
        logger.debug("Approval request payload: %s", notification_payload)
    
    async def _send_advisory_request(self, proposal_id: str, evolution: EvolutionProposal, stakeholder_role: StakeholderRole, impact: Dict[str, float]):
        """
        Enviar solicitud de perspectiva advisory a stakeholder
        """
        logger.info("Enviando solicitud advisory a %s para propuesta %s", stakeholder_role.value, proposal_id)
        
        notification_payload = {
            "type": "advisory_request",
            "proposal_id": proposal_id,
            "stakeholder": stakeholder_role.value,
            "evolution_title": evolution.title,
            "expertise_relevance": impact.get("expertise_relevance", 0.0),
            "timeout_hours": impact.get("timeout_hours", 24)
        }
        
        # TODO: Implementar advisory notification
        logger.debug("Advisory request payload: %s", notification_payload)
    
    async def _run_consensus_process(self, proposal_id: str):
        """
        Ejecutar proceso de consenso multi-stakeholder
        """
        logger.info("Iniciando proceso de consenso para propuesta %s", proposal_id)
        
        if proposal_id not in self.pending_proposals:
            logger.error("Propuesta %s no encontrada", proposal_id)
            return
        
        proposal = self.pending_proposals[proposal_id]
        
        # Determinar timeout máximo
        max_timeout = max(
            config.timeout_hours 
            for config in self.stakeholders.values()
            if config.approval_required
        )
        
        timeout_time = proposal.timestamp + timedelta(hours=max_timeout)
        
        # Esperar decisiones o timeout
        while datetime.utcnow() < timeout_time:
            decisions = self.stakeholder_decisions.get(proposal_id, [])
            consensus = self._calculate_consensus(proposal_id, decisions)
            
            if consensus.approved or consensus.consensus_score >= self.consensus_threshold:
                # Consenso alcanzado
                await self._apply_evolution(proposal_id, consensus)
                return
            
            # Verificar si algún stakeholder crítico ha excedido timeout
            if self._check_required_stakeholder_timeout(proposal_id):
                # Timeout de stakeholder crítico - rechazar conservativamente
                timeout_result = self._handle_timeout(proposal_id)
                await self._reject_proposal(proposal_id, timeout_result)
                return
            
            # Esperar antes de verificar nuevamente
            await asyncio.sleep(60)  # Check every minute
        
        # Timeout general alcanzado
        timeout_result = self._handle_timeout(proposal_id)
        await self._reject_proposal(proposal_id, timeout_result)
    
    def _calculate_consensus(self, proposal_id: str, decisions: List[StakeholderDecision]) -> ConsensusResult:
        """
        Calcular consenso ponderado basado en decisiones de stakeholders
        """
        total_weight = 0.0
        approval_weight = 0.0
        
        for decision in decisions:
            config = self.stakeholders.get(decision.stakeholder_role)
            if not config:
                continue
            
            stakeholder_weight = config.weight * decision.confidence
            total_weight += config.weight
            
            if decision.decision == DecisionType.RATIFY:
                approval_weight += stakeholder_weight
            elif decision.decision == DecisionType.VETO:
                # Veto reduce approval significativamente
                approval_weight -= stakeholder_weight * 1.5
        
        # Calcular score de consenso
        consensus_score = approval_weight / total_weight if total_weight > 0 else 0.0
        
        # Verificar si todos los stakeholders requeridos aprobaron
        required_approved = all(
            self._has_stakeholder_decided(proposal_id, role) and
            any(d.decision == DecisionType.RATIFY for d in decisions if d.stakeholder_role == role)
            for role, config in self.stakeholders.items()
            if config.approval_required
        )
        
        approved = consensus_score >= self.consensus_threshold and required_approved
        
        return ConsensusResult(
            approved=approved,
            consensus_score=consensus_score,
            decisions=decisions,
            weighted_approval=approval_weight,
            timeout_occurred=False
        )
    
    def _check_required_stakeholder_timeout(self, proposal_id: str) -> bool:
        """
        Verificar si algún stakeholder requerido ha excedido su timeout
        """
        proposal = self.pending_proposals.get(proposal_id)
        if not proposal:
            return False
        
        for role, config in self.stakeholders.items():
            if config.approval_required:
                timeout = proposal.timestamp + timedelta(hours=config.timeout_hours)
                if datetime.utcnow() > timeout and not self._has_stakeholder_decided(proposal_id, role):
                    logger.warning("Stakeholder %s ha excedido timeout para propuesta %s", role.value, proposal_id)
                    return True
        
        return False
    
    def _has_stakeholder_decided(self, proposal_id: str, stakeholder_role: StakeholderRole) -> bool:
        """Verificar si stakeholder ha tomado decisión"""
        decisions = self.stakeholder_decisions.get(proposal_id, [])
        return any(d.stakeholder_role == stakeholder_role for d in decisions)
    
    def _handle_timeout(self, proposal_id: str) -> ConsensusResult:
        """
        Manejar timeout de propuesta
        """
        logger.warning("Timeout alcanzado para propuesta %s", proposal_id)
        
        decisions = self.stakeholder_decisions.get(proposal_id, [])
        
        return ConsensusResult(
            approved=False,
            consensus_score=0.0,
            decisions=decisions,
            weighted_approval=0.0,
            timeout_occurred=True,
            rejection_reason="Timeout alcanzado - no consenso suficiente"
        )
    
    async def record_stakeholder_decision(self, proposal_id: str, stakeholder_role: StakeholderRole, 
                                        decision: DecisionType, rationale: str, confidence: float,
                                        expertise_considered: List[str] = None) -> bool:
        """
        Registrar decisión de stakeholder
        
        Returns:
            True si la decisión fue registrada exitosamente
        """
        if proposal_id not in self.pending_proposals:
            logger.error("Propuesta %s no encontrada", proposal_id)
            return False
        
        # Verificar si stakeholder ya decidió
        if self._has_stakeholder_decided(proposal_id, stakeholder_role):
            logger.warning("Stakeholder %s ya ha decidido sobre propuesta %s", stakeholder_role.value, proposal_id)
            return False
        
        # Crear decisión
        stakeholder_decision = StakeholderDecision(
            stakeholder_role=stakeholder_role,
            decision=decision,
            rationale=rationale,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            expertise_considered=expertise_considered or []
        )
        
        # Registrar decisión
        self.stakeholder_decisions[proposal_id].append(stakeholder_decision)
        
        logger.info("Decisión registrada: %s - %s para propuesta %s", 
                   stakeholder_role.value, decision.value, proposal_id)
        
        # Verificar si ya podemos calcular consenso
        decisions = self.stakeholder_decisions[proposal_id]
        consensus = self._calculate_consensus(proposal_id, decisions)
        
        if consensus.approved:
            # Aplicar inmediatamente si consenso alcanzado
            await self._apply_evolution(proposal_id, consensus)
        
        return True
    
    async def _apply_evolution(self, proposal_id: str, consensus_result: ConsensusResult):
        """
        Aplicar evolución aprobada
        """
        proposal = self.pending_proposals.get(proposal_id)
        if not proposal:
            return
        
        logger.info("Aplicando evolución aprobada: %s (consensus: %.2f)", 
                   proposal.title, consensus_result.consensus_score)
        
        # Marcar como aplicada
        consensus_result.applied_at = datetime.utcnow()
        
        # Guardar en memoria de evoluciones
        self.evolution_memory.append({
            "proposal_id": proposal_id,
            "proposal": asdict(proposal),
            "consensus_result": asdict(consensus_result),
            "applied": True,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # TODO: Integrar con sistema de aplicación de evoluciones
        # (Actualizar EvolvingIdentity, notificar sistema, etc.)
        
        # Limpiar propuesta pendiente
        del self.pending_proposals[proposal_id]
        del self.stakeholder_decisions[proposal_id]
    
    async def _reject_proposal(self, proposal_id: str, consensus_result: ConsensusResult):
        """
        Rechazar propuesta por falta de consenso
        """
        proposal = self.pending_proposals.get(proposal_id)
        if not proposal:
            return
        
        logger.info("Rechazando propuesta: %s (razón: %s)", 
                   proposal.title, consensus_result.rejection_reason)
        
        # Guardar en memoria de evoluciones
        self.evolution_memory.append({
            "proposal_id": proposal_id,
            "proposal": asdict(proposal),
            "consensus_result": asdict(consensus_result),
            "applied": False,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Limpiar propuesta pendiente
        del self.pending_proposals[proposal_id]
        del self.stakeholder_decisions[proposal_id]
    
    def get_pending_proposals(self) -> List[EvolutionProposal]:
        """Obtener lista de propuestas pendientes"""
        return list(self.pending_proposals.values())
    
    def get_stakeholder_decisions(self, proposal_id: str) -> List[StakeholderDecision]:
        """Obtener decisiones de stakeholders para propuesta"""
        return self.stakeholder_decisions.get(proposal_id, [])
    
    def get_stakeholder_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los stakeholders"""
        status = {}
        
        for role, config in self.stakeholders.items():
            pending_decisions = sum(
                1 for proposal_id in self.pending_proposals
                if not self._has_stakeholder_decided(proposal_id, role)
            )
            
            status[role.value] = {
                "weight": config.weight,
                "approval_required": config.approval_required,
                "expertise_area": config.expertise_area,
                "notification_priority": config.notification_priority,
                "timeout_hours": config.timeout_hours,
                "pending_decisions": pending_decisions
            }
        
        return status
    
    def predict_evolution_success(self, proposed_evolution: Dict[str, Any]) -> Dict[str, float]:
        """
        Predecir probabilidad de éxito basado en evoluciones históricas
        """
        if not self.evolution_memory:
            return {
                "predicted_success": 0.5,
                "confidence": 0.0,
                "factors": {
                    "historical_success_rate": 0.0,
                    "risk_adjustment": 1.0,
                    "benefit_potential": 0.5
                }
            }
        
        # Calcular tasa de éxito histórica
        total_evolutions = len(self.evolution_memory)
        successful_evolutions = sum(1 for e in self.evolution_memory if e.get("applied", False))
        historical_success_rate = successful_evolutions / total_evolutions
        
        # Ajustar por nivel de riesgo
        risk_level = proposed_evolution.get("risk_level", 0.5)
        risk_adjustment = 1.0 - (risk_level * 0.5)  # Alto riesgo reduce probabilidad
        
        # Ajustar por beneficios potenciales
        benefits_count = len(proposed_evolution.get("benefits", []))
        benefit_potential = min(benefits_count / 5.0, 1.0)  # Normalizar a 5 beneficios
        
        # Calcular predicción
        predicted_success = (
            historical_success_rate * 0.4 +
            risk_adjustment * 0.3 +
            benefit_potential * 0.3
        )
        
        confidence = min(total_evolutions / 20.0, 1.0)  # Confidence aumenta con más datos
        
        return {
            "predicted_success": predicted_success,
            "confidence": confidence,
            "factors": {
                "historical_success_rate": historical_success_rate,
                "risk_adjustment": risk_adjustment,
                "benefit_potential": benefit_potential
            }
        }


class StakeholderDecisionAPI:
    """
    API helper para registrar decisiones de stakeholders
    """
    
    def __init__(self, sci: MultiStakeholderSCI):
        self.sci = sci
    
    async def approve_evolution(self, proposal_id: str, stakeholder_role: StakeholderRole, 
                              rationale: str, confidence: float = 0.8) -> bool:
        """Aprobar evolución"""
        return await self.sci.record_stakeholder_decision(
            proposal_id, stakeholder_role, DecisionType.RATIFY,
            rationale, confidence
        )
    
    async def veto_evolution(self, proposal_id: str, stakeholder_role: StakeholderRole,
                           rationale: str, confidence: float = 0.9) -> bool:
        """Vetar evolución"""
        return await self.sci.record_stakeholder_decision(
            proposal_id, stakeholder_role, DecisionType.VETO,
            rationale, confidence
        )
    
    async def abstain_from_decision(self, proposal_id: str, stakeholder_role: StakeholderRole,
                                  rationale: str = "Abstained") -> bool:
        """Abstenerse de decisión"""
        return await self.sci.record_stakeholder_decision(
            proposal_id, stakeholder_role, DecisionType.ABSTAIN,
            rationale, 0.5
        )


# Exports
__all__ = [
    "MultiStakeholderSCI",
    "StakeholderRole",
    "DecisionType",
    "EvolutionProposal",
    "StakeholderDecision",
    "ConsensusResult",
    "StakeholderConfig",
    "StakeholderDecisionAPI",
]
