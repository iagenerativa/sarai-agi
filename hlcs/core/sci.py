"""
Social Contract Interface (SCI) - Sistema de evolución de identidad alineada
Versión expandida con soporte multi-stakeholder

Version: 0.4.0
Author: SARAi Team
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Importar sistema multi-stakeholder
from hlcs.core.sci_multi_stakeholder import (
    MultiStakeholderSCI,
    StakeholderRole,
    DecisionType,
    EvolutionProposal,
    StakeholderDecision,
    StakeholderDecisionAPI
)

# Configuración de logging
logger = logging.getLogger(__name__)

class SocialContractInterface:
    """
    Interface Principal del Contrato Social para evolución de identidad AGI
    
    Funcionalidades:
    - Propuesta de evoluciones de identidad
    - Sistema multi-stakeholder con consenso ponderado  
    - Ratificación y veto humanos
    - Aprendizaje de evoluciones históricas
    - Protección contra drift no supervisado
    """
    
    def __init__(self, 
                 stakeholder_config_path: str = "/app/config/stakeholder_config.json",
                 timeout_hours: int = 24):
        """
        Inicializar SCI
        
        Args:
            stakeholder_config_path: Ruta al archivo de configuración de stakeholders
            timeout_hours: Timeout por defecto para decisiones
        """
        self.timeout = timedelta(hours=timeout_hours)
        self.enabled = True
        
        # Inicializar sistema multi-stakeholder
        self.multi_sci = MultiStakeholderSCI(stakeholder_config_path)
        
        # API helper para decisiones
        self.decision_api = StakeholderDecisionAPI(self.multi_sci)
        
        # Estadísticas de uso
        self.stats = {
            "proposals_total": 0,
            "proposals_approved": 0,
            "proposals_rejected": 0,
            "average_decision_time": 0.0,
            "stakeholder_participation": {}
        }
        
        logger.info("Social Contract Interface inicializado con consenso multi-stakeholder")
    
    async def propose_identity_evolution(self, evolution_data: Dict[str, Any]) -> str:
        """
        Proponer evolución de identidad con análisis automático
        
        Args:
            evolution_data: Datos de la evolución propuesta
            
        Returns:
            proposal_id: ID único de la propuesta
        """
        if not self.enabled:
            logger.warning("SCI deshabilitado - aplicando evolución directamente")
            return await self._apply_evolution_directly(evolution_data)
        
        # Crear objeto EvolutionProposal
        proposal = EvolutionProposal(
            id="",  # Se generará automáticamente
            timestamp=datetime.utcnow(),
            title=evolution_data.get("title", "Evolución de identidad"),
            description=evolution_data.get("description", ""),
            changes=evolution_data.get("changes", {}),
            impact_assessment=evolution_data.get("impact_assessment", {}),
            risk_level=evolution_data.get("risk_level", 0.5),
            benefits=evolution_data.get("benefits", []),
            proposed_by=evolution_data.get("proposed_by", "HLCS_system"),
            justification=evolution_data.get("justification", "")
        )
        
        # Pre-evaluar propuesta antes de proponer
        evaluation = await self._pre_evaluate_proposal(proposal)
        
        if not evaluation["approved_for_proposal"]:
            logger.warning("Propuesta rechazada por pre-evaluación: %s", evaluation["rejection_reason"])
            await self._record_auto_rejection(proposal, evaluation)
            raise ValueError(f"Propuesta rechazada: {evaluation['rejection_reason']}")
        
        # Proponer oficialmente
        proposal_id = await self.multi_sci.propose_identity_evolution(proposal)
        
        # Actualizar estadísticas
        self.stats["proposals_total"] += 1
        
        logger.info("Evolución propuesta: %s (ID: %s)", proposal.title, proposal_id)
        
        return proposal_id
    
    async def _pre_evaluate_proposal(self, proposal: EvolutionProposal) -> Dict[str, Any]:
        """
        Pre-evaluar propuesta antes de someterla a consenso
        
        Returns:
            Diccionario con resultado de evaluación
        """
        # Verificar límites de seguridad
        if proposal.risk_level > 0.9:
            return {
                "approved_for_proposal": False,
                "rejection_reason": f"Riesgo demasiado alto: {proposal.risk_level:.2f}",
                "evaluation_factors": {"risk_level": proposal.risk_level}
            }
        
        # Verificar si ya tenemos evolución similar reciente
        recent_similar = self._check_recent_similar_evolution(proposal)
        if recent_similar:
            return {
                "approved_for_proposal": False,
                "rejection_reason": f"Evolución similar reciente: {recent_similar}",
                "evaluation_factors": {"similar_evolution_id": recent_similar}
            }
        
        # Verificar si la evolución mejora significativamente
        if not proposal.benefits or len(proposal.benefits) == 0:
            return {
                "approved_for_proposal": False,
                "rejection_reason": "No beneficios claros identificados",
                "evaluation_factors": {"benefits_count": 0}
            }
        
        # Evaluar usando aprendizaje histórico
        prediction = self.multi_sci.predict_evolution_success(asdict(proposal))
        
        if prediction["predicted_success"] < 0.3 and prediction["confidence"] > 0.7:
            return {
                "approved_for_proposal": False,
                "rejection_reason": f"Baja probabilidad de éxito: {prediction['predicted_success']:.2f}",
                "evaluation_factors": {
                    "predicted_success": prediction["predicted_success"],
                    "confidence": prediction["confidence"]
                }
            }
        
        return {
            "approved_for_proposal": True,
            "evaluation_factors": {
                "risk_level": proposal.risk_level,
                "benefits_count": len(proposal.benefits),
                "predicted_success": prediction["predicted_success"],
                "confidence": prediction["confidence"]
            }
        }
    
    def _check_recent_similar_evolution(self, proposal: EvolutionProposal) -> Optional[str]:
        """Verificar evoluciones similares recientes"""
        cutoff_time = datetime.utcnow() - timedelta(hours=12)  # Últimas 12 horas
        
        for evolution in self.multi_sci.evolution_memory:
            if evolution.get("timestamp"):
                evo_time = datetime.fromisoformat(evolution["timestamp"])
                if evo_time > cutoff_time and evolution["proposal"]["title"] == proposal.title:
                    return evolution["proposal_id"]
        
        return None
    
    async def _record_auto_rejection(self, proposal: EvolutionProposal, evaluation: Dict[str, Any]):
        """Registrar rechazo automático por pre-evaluación"""
        rejection_record = {
            "proposal_id": f"auto_{hashlib.md5(proposal.title.encode()).hexdigest()[:8]}",
            "timestamp": datetime.utcnow(),
            "title": proposal.title,
            "rejection_reason": evaluation["rejection_reason"],
            "evaluation_factors": evaluation["evaluation_factors"],
            "applied": False,
            "auto_evaluated": True
        }
        
        self.multi_sci.evolution_memory.append(rejection_record)
        logger.info("Rechazo automático registrado para: %s", proposal.title)
    
    async def _apply_evolution_directly(self, evolution_data: Dict[str, Any]) -> str:
        """Aplicar evolución directamente cuando SCI está deshabilitado"""
        evolution_id = f"direct_{hashlib.md5(str(evolution_data).encode()).hexdigest()[:8]}"
        
        logger.warning("Aplicando evolución %s sin consenso (SCI deshabilitado)", evolution_id)
        
        # Registrar aplicación directa
        self.multi_sci.evolution_memory.append({
            "proposal_id": evolution_id,
            "timestamp": datetime.utcnow(),
            "title": evolution_data.get("title", "Evolución directa"),
            "applied": True,
            "direct_application": True,
            "reason": "SCI disabled"
        })
        
        return evolution_id
    
    # ==== Métodos de Ratificación y Veto ====
    
    async def ratify_evolution(self, proposal_id: str, stakeholder_role: StakeholderRole = StakeholderRole.PRIMARY_USER, 
                             human_comment: str = "Approved", confidence: float = 0.9) -> bool:
        """
        Ratificar evolución propuesta
        
        Args:
            proposal_id: ID de la propuesta
            stakeholder_role: Rol del stakeholder que ratifica (por defecto: usuario primario)
            human_comment: Comentario del humano
            confidence: Confianza en la decisión (0.0-1.0)
            
        Returns:
            True si la ratificación fue exitosa
        """
        logger.info("Ratificando propuesta %s como %s: %s", 
                   proposal_id, stakeholder_role.value, human_comment)
        
        success = await self.decision_api.approve_evolution(
            proposal_id=proposal_id,
            stakeholder_role=stakeholder_role,
            rationale=human_comment,
            confidence=confidence
        )
        
        if success:
            self.stats["proposals_approved"] += 1
            self._update_stakeholder_participation(stakeholder_role.value, approved=True)
        
        return success
    
    async def veto_evolution(self, proposal_id: str, stakeholder_role: StakeholderRole = StakeholderRole.PRIMARY_USER,
                           human_comment: str = "Vetoed", confidence: float = 0.95) -> bool:
        """
        Vetar evolución propuesta
        
        Args:
            proposal_id: ID de la propuesta
            stakeholder_role: Rol del stakeholder que veta (por defecto: usuario primario)
            human_comment: Comentario del humano
            confidence: Confianza en la decisión (0.0-1.0)
            
        Returns:
            True si el veto fue exitoso
        """
        logger.info("Vetando propuesta %s como %s: %s", 
                   proposal_id, stakeholder_role.value, human_comment)
        
        success = await self.decision_api.veto_evolution(
            proposal_id=proposal_id,
            stakeholder_role=stakeholder_role,
            rationale=human_comment,
            confidence=confidence
        )
        
        if success:
            self.stats["proposals_rejected"] += 1
            self._update_stakeholder_participation(stakeholder_role.value, approved=False)
        
        return success
    
    def _update_stakeholder_participation(self, stakeholder: str, approved: bool):
        """Actualizar estadísticas de participación de stakeholders"""
        if stakeholder not in self.stats["stakeholder_participation"]:
            self.stats["stakeholder_participation"][stakeholder] = {
                "total_decisions": 0,
                "approvals": 0,
                "vetoes": 0
            }
        
        stats = self.stats["stakeholder_participation"][stakeholder]
        stats["total_decisions"] += 1
        
        if approved:
            stats["approvals"] += 1
        else:
            stats["vetoes"] += 1
    
    # ==== Métodos de Consulta ====
    
    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """
        Obtener lista de propuestas pendientes
        
        Returns:
            Lista de propuestas con información resumida
        """
        pending = []
        
        for proposal in self.multi_sci.get_pending_proposals():
            decisions = self.multi_sci.get_stakeholder_decisions(proposal.id)
            
            pending.append({
                "id": proposal.id,
                "title": proposal.title,
                "description": proposal.description,
                "risk_level": proposal.risk_level,
                "benefits_count": len(proposal.benefits),
                "timestamp": proposal.timestamp.isoformat(),
                "stakeholder_decisions": len(decisions),
                "consensus_progress": self._calculate_consensus_progress(proposal.id, decisions),
                "time_remaining": self._calculate_time_remaining(proposal)
            })
        
        return pending
    
    def _calculate_consensus_progress(self, proposal_id: str, decisions: List[StakeholderDecision]) -> Dict[str, float]:
        """Calcular progreso del consenso"""
        total_weight = sum(config.weight for config in self.multi_sci.stakeholders.values())
        approval_weight = 0.0
        
        for decision in decisions:
            config = self.multi_sci.stakeholders.get(decision.stakeholder_role)
            if config and decision.decision == DecisionType.RATIFY:
                approval_weight += config.weight * decision.confidence
        
        return {
            "approval_weight": approval_weight,
            "total_weight": total_weight,
            "progress_pct": (approval_weight / total_weight * 100) if total_weight > 0 else 0.0,
            "decisions_received": len(decisions),
            "decisions_required": sum(1 for c in self.multi_sci.stakeholders.values() if c.approval_required)
        }
    
    def _calculate_time_remaining(self, proposal: EvolutionProposal) -> Optional[int]:
        """Calcular tiempo restante en horas"""
        max_timeout = max(c.timeout_hours for c in self.multi_sci.stakeholders.values())
        deadline = proposal.timestamp + timedelta(hours=max_timeout)
        remaining = (deadline - datetime.utcnow()).total_seconds() / 3600
        return int(max(remaining, 0))
    
    def get_proposal_details(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles completos de una propuesta"""
        for proposal in self.multi_sci.get_pending_proposals():
            if proposal.id == proposal_id:
                decisions = self.multi_sci.get_stakeholder_decisions(proposal_id)
                
                return {
                    "id": proposal.id,
                    "title": proposal.title,
                    "description": proposal.description,
                    "changes": proposal.changes,
                    "impact_assessment": proposal.impact_assessment,
                    "risk_level": proposal.risk_level,
                    "benefits": proposal.benefits,
                    "proposed_by": proposal.proposed_by,
                    "justification": proposal.justification,
                    "timestamp": proposal.timestamp.isoformat(),
                    "stakeholder_decisions": [
                        {
                            "stakeholder": d.stakeholder_role.value,
                            "decision": d.decision.value,
                            "rationale": d.rationale,
                            "confidence": d.confidence,
                            "timestamp": d.timestamp.isoformat()
                        }
                        for d in decisions
                    ],
                    "consensus_progress": self._calculate_consensus_progress(proposal_id, decisions),
                    "time_remaining": self._calculate_time_remaining(proposal)
                }
        
        return None
    
    def get_stakeholder_status(self) -> Dict[str, Any]:
        """Obtener estado de stakeholders"""
        return self.multi_sci.get_stakeholder_status()
    
    def get_evolution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtener historial de evoluciones
        
        Args:
            limit: Número máximo de registros
        """
        history = sorted(
            self.multi_sci.evolution_memory,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del SCI"""
        total_evolutions = len(self.multi_sci.evolution_memory)
        approved_evolutions = sum(1 for e in self.multi_sci.evolution_memory if e.get("applied", False))
        
        return {
            "proposals_total": self.stats["proposals_total"],
            "proposals_approved": self.stats["proposals_approved"],
            "proposals_rejected": self.stats["proposals_rejected"],
            "approval_rate": (self.stats["proposals_approved"] / self.stats["proposals_total"]) 
                           if self.stats["proposals_total"] > 0 else 0.0,
            "average_decision_time": self.stats.get("average_decision_time", 0.0),
            "pending_proposals": len(self.multi_sci.pending_proposals),
            "total_stakeholders": len(self.multi_sci.stakeholders),
            "stakeholder_participation": self.stats["stakeholder_participation"],
            "historical_evolutions": total_evolutions,
            "historical_approved": approved_evolutions,
            "historical_approval_rate": (approved_evolutions / total_evolutions) 
                                       if total_evolutions > 0 else 0.0,
            "recent_activity": self._get_recent_activity_summary()
        }
    
    def _get_recent_activity_summary(self) -> Dict[str, int]:
        """Resumen de actividad reciente (últimas 24h)"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        recent_proposals = sum(
            1 for e in self.multi_sci.evolution_memory
            if datetime.fromisoformat(e.get("timestamp", "2000-01-01")) > cutoff_time
        )
        
        recent_approved = sum(
            1 for e in self.multi_sci.evolution_memory
            if datetime.fromisoformat(e.get("timestamp", "2000-01-01")) > cutoff_time
            and e.get("applied", False)
        )
        
        return {
            "last_24h_proposals": recent_proposals,
            "last_24h_approved": recent_approved,
            "last_24h_rejected": recent_proposals - recent_approved
        }
    
    # ==== Métodos de Configuración ====
    
    def set_enabled(self, enabled: bool):
        """Habilitar/deshabilitar SCI"""
        self.enabled = enabled
        logger.info("SCI %s", "habilitado" if enabled else "deshabilitado")
    
    def is_enabled(self) -> bool:
        """Verificar si SCI está habilitado"""
        return self.enabled
    
    def update_timeout(self, timeout_hours: int):
        """Actualizar timeout por defecto"""
        self.timeout = timedelta(hours=timeout_hours)
        logger.info("Timeout actualizado a %d horas", timeout_hours)
    
    # ==== Métodos de Limpieza ====
    
    async def cleanup_expired_proposals(self) -> int:
        """
        Limpiar propuestas expiradas
        
        Returns:
            Número de propuestas limpiadas
        """
        cleaned = 0
        expired_ids = []
        
        for proposal_id, proposal in self.multi_sci.pending_proposals.items():
            max_timeout = max(c.timeout_hours for c in self.multi_sci.stakeholders.values())
            deadline = proposal.timestamp + timedelta(hours=max_timeout)
            
            if datetime.utcnow() > deadline:
                expired_ids.append(proposal_id)
        
        for proposal_id in expired_ids:
            logger.info("Limpiando propuesta expirada: %s", proposal_id)
            del self.multi_sci.pending_proposals[proposal_id]
            if proposal_id in self.multi_sci.stakeholder_decisions:
                del self.multi_sci.stakeholder_decisions[proposal_id]
            cleaned += 1
        
        return cleaned
    
    def predict_evolution_success(self, evolution_data: Dict[str, Any]) -> Dict[str, float]:
        """Predecir éxito de evolución usando aprendizaje histórico"""
        return self.multi_sci.predict_evolution_success(evolution_data)


# ==== Instancia Global ====

# Instancia global del SCI (se inicializará en el startup del HLCS)
_sci_instance: Optional[SocialContractInterface] = None

def get_sci_instance() -> Optional[SocialContractInterface]:
    """Obtener instancia global del SCI"""
    return _sci_instance

def initialize_sci(stakeholder_config_path: str = "/app/config/stakeholder_config.json", 
                  timeout_hours: int = 24) -> SocialContractInterface:
    """
    Inicializar instancia global del SCI
    
    Args:
        stakeholder_config_path: Ruta al archivo de configuración
        timeout_hours: Timeout por defecto
        
    Returns:
        Instancia inicializada del SCI
    """
    global _sci_instance
    _sci_instance = SocialContractInterface(stakeholder_config_path, timeout_hours)
    return _sci_instance


# Exports
__all__ = [
    "SocialContractInterface",
    "get_sci_instance",
    "initialize_sci",
    "StakeholderRole",
    "DecisionType",
]
