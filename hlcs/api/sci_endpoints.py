"""
Endpoints REST para el Social Contract Interface (SCI)
API endpoints para gestión de evoluciones multi-stakeholder

Version: 0.4.0
Author: SARAi Team
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

# Importar SCI y modelos
from hlcs.core.sci import get_sci_instance, SocialContractInterface
from hlcs.core.sci_multi_stakeholder import StakeholderRole, DecisionType

logger = logging.getLogger(__name__)

# ============================================================
# MODELOS PYDANTIC PARA LA API
# ============================================================

class EvolutionProposalRequest(BaseModel):
    title: str = Field(..., description="Título de la evolución propuesta")
    description: str = Field(..., description="Descripción detallada")
    changes: Dict[str, Any] = Field(default_factory=dict, description="Cambios específicos")
    impact_assessment: Dict[str, float] = Field(default_factory=dict, description="Evaluación de impacto")
    risk_level: float = Field(default=0.5, ge=0.0, le=1.0, description="Nivel de riesgo (0.0-1.0)")
    benefits: List[str] = Field(default_factory=list, description="Lista de beneficios esperados")
    proposed_by: str = Field(default="HLCS_system", description="Entidad que propone")
    justification: str = Field(default="", description="Justificación de la evolución")

class DecisionRequest(BaseModel):
    stakeholder_role: str = Field(..., description="Rol del stakeholder")
    decision: str = Field(..., description="Decisión: ratify, veto, abstain")
    rationale: str = Field(..., description="Razonamiento de la decisión")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confianza en la decisión")
    expertise_considered: Optional[List[str]] = Field(default=None, description="Expertise considerado")

class StakeholderResponse(BaseModel):
    role: str
    weight: float
    approval_required: bool
    expertise_area: str
    notification_priority: int
    timeout_hours: int
    pending_decisions: int

class ProposalSummary(BaseModel):
    id: str
    title: str
    description: str
    timestamp: str
    risk_level: float
    benefits_count: int
    stakeholder_decisions: int
    consensus_progress: Dict[str, float]
    time_remaining: Optional[int]

class ProposalDetails(BaseModel):
    id: str
    title: str
    description: str
    changes: Dict[str, Any]
    impact_assessment: Dict[str, float]
    risk_level: float
    benefits: List[str]
    proposed_by: str
    justification: str
    timestamp: str
    stakeholder_decisions: List[Dict[str, Any]]
    consensus_progress: Dict[str, float]
    time_remaining: Optional[int]

class StatisticsResponse(BaseModel):
    proposals_total: int
    proposals_approved: int
    proposals_rejected: int
    approval_rate: float
    average_decision_time: float
    pending_proposals: int
    total_stakeholders: int
    stakeholder_participation: Dict[str, Dict[str, int]]
    recent_activity: Dict[str, int]

# ============================================================
# CREAR APLICACIÓN FASTAPI
# ============================================================

app = FastAPI(
    title="HLCS Social Contract Interface API",
    description="API para gestión de evoluciones de identidad AGI con consenso multi-stakeholder",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# DEPENDENCY INJECTION
# ============================================================

def get_sci() -> SocialContractInterface:
    """Dependency para obtener instancia SCI"""
    sci = get_sci_instance()
    if not sci:
        raise HTTPException(status_code=503, detail="SCI no inicializado")
    return sci

# ============================================================
# ENDPOINTS DE STAKEHOLDERS
# ============================================================

@app.get("/sci/stakeholders", response_model=List[StakeholderResponse])
async def get_stakeholders(sci: SocialContractInterface = Depends(get_sci)):
    """
    Obtener estado actual de todos los stakeholders
    
    Retorna información detallada sobre cada stakeholder incluyendo:
    - Peso en decisiones (influencia)
    - Si requiere aprobación
    - Área de expertise
    - Prioridad de notificación
    - Timeout para decisiones
    - Número de decisiones pendientes
    """
    try:
        stakeholder_status = sci.get_stakeholder_status()
        
        stakeholders = []
        for role, status in stakeholder_status.items():
            stakeholders.append(StakeholderResponse(
                role=role,
                weight=status["weight"],
                approval_required=status["approval_required"],
                expertise_area=status["expertise_area"],
                notification_priority=status["notification_priority"],
                timeout_hours=status["timeout_hours"],
                pending_decisions=status["pending_decisions"]
            ))
        
        return stakeholders
        
    except Exception as e:
        logger.error("Error obteniendo stakeholders: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sci/stakeholders/{role}")
async def get_stakeholder_details(role: str, sci: SocialContractInterface = Depends(get_sci)):
    """
    Obtener detalles específicos de un stakeholder
    
    Args:
        role: Rol del stakeholder (primary_user, system_admin, etc.)
    """
    try:
        stakeholder_status = sci.get_stakeholder_status()
        
        if role not in stakeholder_status:
            raise HTTPException(status_code=404, detail=f"Stakeholder {role} no encontrado")
        
        status = stakeholder_status[role]
        
        return {
            "role": role,
            **status,
            "responsibilities": _get_stakeholder_responsibilities(role),
            "decision_guidelines": _get_decision_guidelines(role)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error obteniendo detalles de stakeholder %s: %s", role, e)
        raise HTTPException(status_code=500, detail=str(e))

def _get_stakeholder_responsibilities(role: str) -> List[str]:
    """Obtener responsabilidades específicas por rol"""
    responsibilities = {
        "primary_user": [
            "Decidir sobre cambios en experiencia de usuario",
            "Evaluar beneficios personales de evoluciones",
            "Votar sobre modificaciones en capacidades principales"
        ],
        "system_admin": [
            "Asegurar estabilidad del sistema",
            "Evaluar impacto en recursos y rendimiento",
            "Votar sobre cambios técnicos críticos"
        ],
        "other_agents": [
            "Proporcionar perspectiva del ecosistema",
            "Evaluar compatibilidad e integración",
            "Advisory sobre efectos colaterales"
        ],
        "security_auditor": [
            "Evaluar implicaciones de seguridad",
            "Advisory sobre vulnerabilidades potenciales",
            "Revisar compliance con estándares"
        ],
        "ethics_committee": [
            "Evaluar implicaciones éticas",
            "Advisory sobre fairness y bias",
            "Revisar transparencia y explicabilidad"
        ]
    }
    
    return responsibilities.get(role, ["Responsabilidades no definidas"])

def _get_decision_guidelines(role: str) -> Dict[str, str]:
    """Obtener guías de decisión por rol"""
    guidelines = {
        "primary_user": {
            "focus": "Experiencia de usuario y valor personal",
            "decision_factor": "Beneficios directos y satisfacción",
            "veto_condition": "Deterioro significativo de la experiencia"
        },
        "system_admin": {
            "focus": "Estabilidad, rendimiento y mantenibilidad",
            "decision_factor": "Impacto en infraestructura",
            "veto_condition": "Riesgo de inestabilidad del sistema"
        },
        "other_agents": {
            "focus": "Integración y compatibilidad del ecosistema",
            "decision_factor": "Efectos en otros sistemas",
            "advisory_role": "Solo perspectiva, no aprobación"
        },
        "security_auditor": {
            "focus": "Postura de seguridad y compliance",
            "decision_factor": "Evaluaciones de riesgo de seguridad",
            "advisory_role": "Perspectiva de seguridad, no aprobación"
        },
        "ethics_committee": {
            "focus": "Alineación ética y fairness",
            "decision_factor": "Implicaciones éticas y sociales",
            "advisory_role": "Perspectiva ética, no aprobación"
        }
    }
    
    return guidelines.get(role, {"focus": "No definido", "decision_factor": "No definido"})

# ============================================================
# ENDPOINTS DE PROPUESTAS
# ============================================================

@app.get("/sci/pending", response_model=List[ProposalSummary])
async def get_pending_proposals(sci: SocialContractInterface = Depends(get_sci)):
    """
    Obtener lista de propuestas de evolución pendientes
    
    Retorna resumen de todas las propuestas que esperan decisión,
    incluyendo progreso de consenso y tiempo restante.
    """
    try:
        pending = sci.get_pending_proposals()
        
        summaries = []
        for prop in pending:
            summaries.append(ProposalSummary(**prop))
        
        return summaries
        
    except Exception as e:
        logger.error("Error obteniendo propuestas pendientes: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sci/proposals/{proposal_id}", response_model=ProposalDetails)
async def get_proposal_details(proposal_id: str, sci: SocialContractInterface = Depends(get_sci)):
    """
    Obtener detalles completos de una propuesta específica
    
    Args:
        proposal_id: ID único de la propuesta
    """
    try:
        details = sci.get_proposal_details(proposal_id)
        
        if not details:
            raise HTTPException(status_code=404, detail=f"Propuesta {proposal_id} no encontrada")
        
        return ProposalDetails(**details)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error obteniendo detalles de propuesta %s: %s", proposal_id, e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sci/proposals")
async def propose_evolution(request: EvolutionProposalRequest, sci: SocialContractInterface = Depends(get_sci)):
    """
    Proponer nueva evolución de identidad
    
    Envía una propuesta de evolución que será evaluada por stakeholders
    """
    try:
        evolution_data = {
            "title": request.title,
            "description": request.description,
            "changes": request.changes,
            "impact_assessment": request.impact_assessment,
            "risk_level": request.risk_level,
            "benefits": request.benefits,
            "proposed_by": request.proposed_by,
            "justification": request.justification
        }
        
        proposal_id = await sci.propose_identity_evolution(evolution_data)
        
        return JSONResponse(
            status_code=201,
            content={
                "proposal_id": proposal_id,
                "status": "pending",
                "message": "Propuesta creada exitosamente",
                "details_url": f"/sci/proposals/{proposal_id}"
            }
        )
        
    except ValueError as e:
        # Pre-evaluación rechazó la propuesta
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creando propuesta: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ENDPOINTS DE DECISIONES
# ============================================================

@app.post("/sci/ratify/{proposal_id}")
async def ratify_evolution(proposal_id: str, request: DecisionRequest, sci: SocialContractInterface = Depends(get_sci)):
    """
    Ratificar evolución propuesta
    
    Args:
        proposal_id: ID de la propuesta
        request: Datos de la decisión de ratificación
    """
    try:
        # Validar stakeholder role
        try:
            stakeholder_role = StakeholderRole(request.stakeholder_role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Rol de stakeholder inválido: {request.stakeholder_role}")
        
        success = await sci.ratify_evolution(
            proposal_id=proposal_id,
            stakeholder_role=stakeholder_role,
            human_comment=request.rationale,
            confidence=request.confidence
        )
        
        if success:
            return {
                "status": "ratified",
                "proposal_id": proposal_id,
                "stakeholder": request.stakeholder_role,
                "message": "Evolución ratificada exitosamente"
            }
        else:
            raise HTTPException(status_code=400, detail="No se pudo ratificar la evolución")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error ratificando evolución %s: %s", proposal_id, e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sci/veto/{proposal_id}")
async def veto_evolution(proposal_id: str, request: DecisionRequest, sci: SocialContractInterface = Depends(get_sci)):
    """
    Vetar evolución propuesta
    
    Args:
        proposal_id: ID de la propuesta
        request: Datos de la decisión de veto
    """
    try:
        # Validar stakeholder role
        try:
            stakeholder_role = StakeholderRole(request.stakeholder_role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Rol de stakeholder inválido: {request.stakeholder_role}")
        
        success = await sci.veto_evolution(
            proposal_id=proposal_id,
            stakeholder_role=stakeholder_role,
            human_comment=request.rationale,
            confidence=request.confidence
        )
        
        if success:
            return {
                "status": "vetoed",
                "proposal_id": proposal_id,
                "stakeholder": request.stakeholder_role,
                "message": "Evolución vetada exitosamente"
            }
        else:
            raise HTTPException(status_code=400, detail="No se pudo vetar la evolución")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error vetando evolución %s: %s", proposal_id, e)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ENDPOINTS DE MONITOREO
# ============================================================

@app.get("/sci/statistics", response_model=StatisticsResponse)
async def get_statistics(sci: SocialContractInterface = Depends(get_sci)):
    """
    Obtener estadísticas detalladas del SCI
    
    Incluye métricas de uso, participación de stakeholders,
    y actividad reciente.
    """
    try:
        stats = sci.get_statistics()
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error("Error obteniendo estadísticas: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sci/history")
async def get_evolution_history(limit: int = 50, sci: SocialContractInterface = Depends(get_sci)):
    """
    Obtener historial de evoluciones
    
    Args:
        limit: Número máximo de registros (default: 50)
    """
    try:
        history = sci.get_evolution_history(limit=limit)
        
        return {
            "total": len(history),
            "limit": limit,
            "history": history
        }
        
    except Exception as e:
        logger.error("Error obteniendo historial: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sci/predict/{proposal_id}")
async def predict_evolution_success(proposal_id: str, sci: SocialContractInterface = Depends(get_sci)):
    """
    Predecir éxito de evolución propuesta
    
    Args:
        proposal_id: ID de la propuesta a evaluar
    """
    try:
        details = sci.get_proposal_details(proposal_id)
        
        if not details:
            raise HTTPException(status_code=404, detail=f"Propuesta {proposal_id} no encontrada")
        
        # Predecir usando datos de la propuesta
        evolution_data = {
            "risk_level": details["risk_level"],
            "benefits": details["benefits"]
        }
        
        prediction = sci.predict_evolution_success(evolution_data)
        
        return {
            "proposal_id": proposal_id,
            **prediction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error prediciendo éxito de propuesta %s: %s", proposal_id, e)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================================

@app.post("/sci/config/enabled")
async def set_sci_enabled(enabled: bool, sci: SocialContractInterface = Depends(get_sci)):
    """
    Habilitar o deshabilitar el SCI
    
    WARNING: Deshabilitar el SCI permite evolución sin consenso humano
    """
    try:
        sci.set_enabled(enabled)
        
        return {
            "status": "success",
            "sci_enabled": enabled,
            "message": f"SCI {'habilitado' if enabled else 'deshabilitado'}"
        }
        
    except Exception as e:
        logger.error("Error configurando SCI: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sci/config/status")
async def get_sci_config_status(sci: SocialContractInterface = Depends(get_sci)):
    """
    Obtener estado de configuración del SCI
    """
    try:
        return {
            "sci_enabled": sci.is_enabled(),
            "timeout_hours": sci.timeout.total_seconds() / 3600,
            "stakeholder_count": len(sci.multi_sci.stakeholders)
        }
        
    except Exception as e:
        logger.error("Error obteniendo configuración SCI: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sci/admin/cleanup")
async def cleanup_expired_proposals(sci: SocialContractInterface = Depends(get_sci)):
    """
    Limpiar propuestas expiradas
    
    Endpoint administrativo para limpiar propuestas que han excedido el timeout
    """
    try:
        cleaned = await sci.cleanup_expired_proposals()
        
        return {
            "status": "success",
            "proposals_cleaned": cleaned,
            "message": f"{cleaned} propuestas expiradas limpiadas"
        }
        
    except Exception as e:
        logger.error("Error limpiando propuestas: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# WEBSOCKET PARA NOTIFICACIONES EN TIEMPO REAL
# ============================================================

active_connections: List[WebSocket] = []

@app.websocket("/sci/stream")
async def websocket_sci_stream(websocket: WebSocket):
    """
    WebSocket endpoint para streaming de eventos SCI en tiempo real
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Enviar estado inicial
        sci = get_sci_instance()
        if sci:
            initial_state = {
                "type": "connection_established",
                "timestamp": datetime.utcnow().isoformat(),
                "pending_proposals": len(sci.get_pending_proposals()),
                "stakeholder_count": len(sci.multi_sci.stakeholders)
            }
            await websocket.send_json(initial_state)
        
        # Mantener conexión y enviar actualizaciones
        while True:
            # En implementación real: enviar eventos cuando ocurran
            await asyncio.sleep(5)
            
            if sci:
                update = {
                    "type": "status_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "pending_proposals": len(sci.get_pending_proposals())
                }
                await websocket.send_json(update)
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("Cliente WebSocket desconectado")
    except Exception as e:
        logger.error("Error en WebSocket: %s", e)
        if websocket in active_connections:
            active_connections.remove(websocket)

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/sci/health")
async def health_check(sci: SocialContractInterface = Depends(get_sci)):
    """Health check endpoint para monitoring"""
    return {
        "status": "healthy",
        "sci_enabled": sci.is_enabled(),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.4.0"
    }

# ============================================================
# MANEJO DE ERRORES GLOBALES
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error("Excepción no manejada: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Exports
__all__ = ["app"]
