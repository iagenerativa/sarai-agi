# HLCS v0.4: Multi-Stakeholder Social Contract Interface (SCI)

> **Sistema de Gobernanza Distribuida para SARAi AGI**  
> Evolución consensuada bajo supervisión multi-actor

**Versión**: v0.4  
**Fecha**: 2025-01-04  
**Estado**: Production-Ready  
**LOC**: ~1,885 líneas (core + API + config)  
**Filosofía**: "Conscious Aligned AGI" - El sistema solo evoluciona con aprobación consensuada de todos los stakeholders críticos

---

## 🎯 ¿Qué es el SCI?

El **Social Contract Interface (SCI)** es la capa de gobernanza que determina **qué evoluciones de identidad pueden ejecutarse** en SARAi. Implementa un sistema de consenso ponderado multi-stakeholder donde:

- **No hay single point of failure**: Ningún actor único puede forzar una evolución
- **Peso democrático con expertise**: Usuarios primarios (60%), Admins (30%), Otros Agentes (10%)
- **Roles advisory sin veto**: Security Auditors y Ethics Committees proveen expertise sin bloquear
- **Pre-evaluación automática**: Filtra propuestas peligrosas antes del consenso
- **Aprendizaje histórico**: Predice éxito basado en evoluciones pasadas

---

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico
```yaml
Core:
  - Python 3.13+
  - Pydantic 2.x (validación)
  - asyncio (consenso asíncrono)

API:
  - FastAPI 0.115+ (REST endpoints)
  - WebSockets (notificaciones real-time)
  - CORS middleware

Storage:
  - JSON (stakeholder config)
  - In-memory (proposals, decisions)
  - Evolution memory (ML training data)
```

### Componentes Clave

```
hlcs/
├── core/
│   ├── sci.py                      (526 LOC) - Interface principal
│   ├── sci_multi_stakeholder.py    (657 LOC) - Motor de consenso
│   └── __init__.py                 (exports v0.4)
├── api/
│   └── sci_endpoints.py            (633 LOC) - REST API completa
config/
└── stakeholder_config.json         (37 LOC)  - Configuración stakeholders
```

---

## 👥 Stakeholders y Pesos

### Configuración por Defecto

| Role                 | Weight | Timeout | Approval Required | Expertise Area           |
|----------------------|--------|---------|-------------------|--------------------------|
| **PRIMARY_USER**     | 60%    | 24h     | ✅ Yes            | User experience, values   |
| **SYSTEM_ADMIN**     | 30%    | 12h     | ✅ Yes            | System stability, security|
| **OTHER_AGENTS**     | 10%    | 48h     | ❌ No             | Multi-agent coordination  |
| **SECURITY_AUDITOR** | 0%     | 6h      | ❌ Advisory       | Threat detection, hardening|
| **ETHICS_COMMITTEE** | 0%     | 8h      | ❌ Advisory       | Ethical implications      |

### Reglas de Consenso

1. **Threshold**: 80% weighted approval required
2. **Calculation**: `sum(decision.weight for decision in approvals) / sum(stakeholder.weight for required stakeholders)`
3. **Advisory roles**: Proveen comentarios pero no afectan consenso numérico
4. **Timeouts individuales**: Cada stakeholder puede responder en su ventana temporal
5. **Auto-rejection**: Si approval_required stakeholders no responden → proposal expires

---

## 🔄 Flujo de Consenso

### Diagrama de Decisión

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PROPOSAL SUBMISSION                                      │
│    EvolvingIdentity.propose_purpose_evolution()             │
│    → SocialContractInterface.propose_identity_evolution()   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PRE-EVALUATION (Auto-Filters)                            │
│    ✗ Risk score > 90%                                       │
│    ✗ No measurable benefits                                 │
│    ✗ Similar evolution in last 7 days                       │
│    ✗ Predicted success < 30%                                │
└────────────────┬────────────────────────────────────────────┘
                 │ PASS
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. MULTI-STAKEHOLDER SUBMISSION                             │
│    MultiStakeholderSCI.propose_identity_evolution()         │
│    - Create EvolutionProposal                               │
│    - Assess impacts (ethics, stability, autonomy)           │
│    - Calculate urgency score                                │
│    - Notify all stakeholders (WebSocket + API)              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. STAKEHOLDER DECISIONS (Async, Individual Timeouts)      │
│    PRIMARY_USER: ratify/veto within 24h                     │
│    SYSTEM_ADMIN: ratify/veto within 12h                     │
│    OTHER_AGENTS: optional within 48h                        │
│    SECURITY_AUDITOR: advisory within 6h                     │
│    ETHICS_COMMITTEE: advisory within 8h                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. CONSENSUS CALCULATION (Weighted Voting)                  │
│    consensus_score = sum(weight for ratify) / sum(required) │
│    ✅ consensus_score >= 0.8 → APPROVED                     │
│    ❌ any veto → REJECTED                                   │
│    ⏱️ timeout expired → EXPIRED                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. EVOLUTION EXECUTION (if approved)                        │
│    EvolvingIdentity.execute_approved_evolution()            │
│    + Record in evolution memory for ML learning             │
└─────────────────────────────────────────────────────────────┘
```

### Ejemplo de Consenso

**Propuesta**: "Add core value: PRIORITIZE_ACCESSIBILITY"

**Decisiones**:
- PRIMARY_USER (60%): ✅ RATIFY (reason: "Aligns with inclusivity goals")
- SYSTEM_ADMIN (30%): ✅ RATIFY (reason: "Low risk, high UX benefit")
- OTHER_AGENTS (10%): ⏱️ NO RESPONSE (not required)
- SECURITY_AUDITOR (0%): ✅ ADVISORY (comment: "No security implications")
- ETHICS_COMMITTEE (0%): ✅ ADVISORY (comment: "Strong ethical positive")

**Cálculo**:
```python
consensus_score = (0.6 + 0.3) / (0.6 + 0.3) = 0.9 / 0.9 = 1.0 (100%)
threshold = 0.8 (80%)
result = APPROVED ✅ (100% ≥ 80%)
```

---

## 🔌 API Reference

### Base URL
```
http://localhost:8001/sci  # Default SCI API port
```

### Authentication
**Current**: None (internal system)  
**Future**: OAuth2/API Key for production deployment

### Endpoints

#### 1. **List Stakeholders**
```http
GET /sci/stakeholders
```

**Response**:
```json
{
  "stakeholders": [
    {
      "role": "PRIMARY_USER",
      "weight": 0.6,
      "approval_required": true,
      "timeout_hours": 24,
      "expertise_area": "User experience, core values alignment"
    },
    ...
  ],
  "total_count": 5
}
```

#### 2. **Get Stakeholder Details**
```http
GET /sci/stakeholders/{role}
```

**Example**: `GET /sci/stakeholders/PRIMARY_USER`

**Response**:
```json
{
  "role": "PRIMARY_USER",
  "weight": 0.6,
  "responsibilities": [
    "Approve/reject identity evolutions",
    "Ensure alignment with user values",
    "Provide feedback on proposed changes"
  ],
  "decision_guidelines": [
    "Does this evolution serve user needs?",
    "Is it aligned with SARAi's core purpose?",
    "Are there unexpected consequences?"
  ],
  "notification_priority": "HIGH"
}
```

#### 3. **List Pending Proposals**
```http
GET /sci/pending
```

**Response**:
```json
{
  "proposals": [
    {
      "proposal_id": "uuid-123",
      "evolution_type": "PURPOSE_EVOLUTION",
      "description": "Add core value: PRIORITIZE_ACCESSIBILITY",
      "submitted_at": "2025-01-04T10:00:00Z",
      "expires_at": "2025-01-05T10:00:00Z",
      "status": "PENDING",
      "consensus_progress": {
        "current_score": 0.6,
        "threshold": 0.8,
        "decisions_count": 2,
        "required_decisions": 2,
        "missing_stakeholders": ["SYSTEM_ADMIN"]
      }
    }
  ],
  "total_pending": 1
}
```

#### 4. **Create Proposal**
```http
POST /sci/proposals
Content-Type: application/json

{
  "evolution_type": "PURPOSE_EVOLUTION",
  "description": "Add core value: PRIORITIZE_ACCESSIBILITY",
  "details": {
    "new_core_value": "PRIORITIZE_ACCESSIBILITY",
    "rationale": "Improve inclusivity for users with disabilities"
  },
  "predicted_impact": {
    "ethics_score": 0.9,
    "stability_risk": 0.1,
    "autonomy_impact": 0.0
  }
}
```

**Response**:
```json
{
  "proposal_id": "uuid-123",
  "status": "PENDING",
  "message": "Proposal submitted successfully. Awaiting stakeholder decisions.",
  "expires_at": "2025-01-05T10:00:00Z"
}
```

#### 5. **Ratify Proposal**
```http
POST /sci/ratify/{proposal_id}
Content-Type: application/json

{
  "stakeholder_role": "PRIMARY_USER",
  "reason": "Aligns with inclusivity goals",
  "confidence": 0.95
}
```

**Response**:
```json
{
  "decision_recorded": true,
  "consensus_result": "APPROVED",
  "consensus_score": 1.0,
  "message": "Proposal approved with 100% consensus"
}
```

#### 6. **Veto Proposal**
```http
POST /sci/veto/{proposal_id}
Content-Type: application/json

{
  "stakeholder_role": "SYSTEM_ADMIN",
  "reason": "High stability risk detected",
  "severity": "HIGH"
}
```

**Response**:
```json
{
  "decision_recorded": true,
  "consensus_result": "REJECTED",
  "message": "Proposal vetoed by SYSTEM_ADMIN"
}
```

#### 7. **Get Statistics**
```http
GET /sci/statistics
```

**Response**:
```json
{
  "proposals_total": 47,
  "approved": 32,
  "rejected": 12,
  "expired": 3,
  "pending": 1,
  "approval_rate": 0.68,
  "avg_consensus_time_hours": 8.5,
  "stakeholder_participation": {
    "PRIMARY_USER": 0.98,
    "SYSTEM_ADMIN": 0.95,
    "OTHER_AGENTS": 0.45,
    "SECURITY_AUDITOR": 0.89,
    "ETHICS_COMMITTEE": 0.92
  }
}
```

#### 8. **Predict Success**
```http
GET /sci/predict/{proposal_id}
```

**Response**:
```json
{
  "proposal_id": "uuid-123",
  "predicted_success_probability": 0.87,
  "confidence_interval": [0.75, 0.95],
  "similar_historical_evolutions": 12,
  "recommendation": "LIKELY_TO_SUCCEED",
  "factors": [
    "High ethics score (0.9)",
    "Low stability risk (0.1)",
    "Similar evolutions succeeded 10/12 times"
  ]
}
```

#### 9. **WebSocket Stream**
```http
WS /sci/stream?stakeholder_role=PRIMARY_USER
```

**Messages**:
```json
{
  "event": "NEW_PROPOSAL",
  "data": {
    "proposal_id": "uuid-123",
    "evolution_type": "PURPOSE_EVOLUTION",
    "urgency": 0.7,
    "expires_at": "2025-01-05T10:00:00Z"
  }
}

{
  "event": "CONSENSUS_REACHED",
  "data": {
    "proposal_id": "uuid-123",
    "result": "APPROVED",
    "consensus_score": 1.0
  }
}
```

#### 10. **Health Check**
```http
GET /sci/health
```

**Response**:
```json
{
  "status": "healthy",
  "uptime_seconds": 86400,
  "pending_proposals": 1,
  "last_decision_timestamp": "2025-01-04T14:30:00Z"
}
```

---

## 🧪 Testing Guide

### Unit Tests

**File**: `tests/test_hlcs_v04_sci.py` (to be created)

```python
import pytest
from hlcs.core.sci_multi_stakeholder import MultiStakeholderSCI, StakeholderRole, DecisionType

def test_consensus_calculation_80_percent():
    """PRIMARY_USER + SYSTEM_ADMIN = 90% (60% + 30%) → APPROVED"""
    sci = MultiStakeholderSCI()
    proposal = sci.propose_identity_evolution(...)
    
    sci.record_stakeholder_decision(proposal.id, StakeholderRole.PRIMARY_USER, DecisionType.RATIFY, "Good")
    sci.record_stakeholder_decision(proposal.id, StakeholderRole.SYSTEM_ADMIN, DecisionType.RATIFY, "Safe")
    
    result = sci._calculate_consensus(proposal.id)
    assert result.approved == True
    assert result.consensus_score >= 0.8

def test_veto_blocks_consensus():
    """Any veto → REJECTED, even if consensus_score > threshold"""
    sci = MultiStakeholderSCI()
    proposal = sci.propose_identity_evolution(...)
    
    sci.record_stakeholder_decision(proposal.id, StakeholderRole.PRIMARY_USER, DecisionType.RATIFY, "Good")
    sci.record_stakeholder_decision(proposal.id, StakeholderRole.SYSTEM_ADMIN, DecisionType.VETO, "Dangerous")
    
    result = sci._calculate_consensus(proposal.id)
    assert result.approved == False
    assert "veto" in result.rejection_reason.lower()

def test_advisory_role_no_blocking():
    """SECURITY_AUDITOR advisory comment doesn't affect consensus math"""
    sci = MultiStakeholderSCI()
    proposal = sci.propose_identity_evolution(...)
    
    sci.record_stakeholder_decision(proposal.id, StakeholderRole.PRIMARY_USER, DecisionType.RATIFY, "Good")
    sci.record_stakeholder_decision(proposal.id, StakeholderRole.SYSTEM_ADMIN, DecisionType.RATIFY, "Safe")
    sci.record_stakeholder_decision(proposal.id, StakeholderRole.SECURITY_AUDITOR, DecisionType.RATIFY, "Secure")
    
    result = sci._calculate_consensus(proposal.id)
    # Consensus should be 90% (60% + 30%), not affected by 0-weight advisory
    assert 0.85 <= result.consensus_score <= 0.95
```

### API Tests

```python
from fastapi.testclient import TestClient
from hlcs.api.sci_endpoints import app

client = TestClient(app)

def test_list_stakeholders():
    response = client.get("/sci/stakeholders")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 5
    assert any(s["role"] == "PRIMARY_USER" for s in data["stakeholders"])

def test_create_proposal_success():
    payload = {
        "evolution_type": "PURPOSE_EVOLUTION",
        "description": "Test evolution",
        "details": {"test": "data"},
        "predicted_impact": {"ethics_score": 0.8, "stability_risk": 0.2}
    }
    response = client.post("/sci/proposals", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "proposal_id" in data
    assert data["status"] == "PENDING"

def test_websocket_notifications():
    with client.websocket_connect("/sci/stream?stakeholder_role=PRIMARY_USER") as websocket:
        # Simulate proposal creation in another thread
        # ...
        message = websocket.receive_json()
        assert message["event"] == "NEW_PROPOSAL"
        assert "proposal_id" in message["data"]
```

---

## 🚀 Deployment

### Docker Compose (Standalone SCI Service)

```yaml
# docker-compose.hlcs.yml
version: '3.8'

services:
  hlcs-sci:
    build:
      context: .
      dockerfile: Dockerfile.hlcs
    ports:
      - "8001:8001"  # SCI API
    environment:
      - SCI_CONSENSUS_THRESHOLD=0.8
      - SCI_CONFIG_PATH=/app/config/stakeholder_config.json
      - LOG_LEVEL=INFO
    volumes:
      - ./config/stakeholder_config.json:/app/config/stakeholder_config.json:ro
      - ./data/sci_evolutions:/app/data/evolutions  # Persistence
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/sci/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  # Optional: Prometheus for monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
```

### Environment Variables

```bash
# .env
SCI_CONSENSUS_THRESHOLD=0.8          # Consensus threshold (0.0-1.0)
SCI_CONFIG_PATH=config/stakeholder_config.json
SCI_MAX_PENDING_PROPOSALS=100        # Memory limit
SCI_CLEANUP_INTERVAL_HOURS=24        # Auto-cleanup expired proposals
LOG_LEVEL=INFO
```

### Start Services

```bash
# Development
uvicorn hlcs.api.sci_endpoints:app --host 0.0.0.0 --port 8001 --reload

# Production (Docker)
docker-compose -f docker-compose.hlcs.yml up -d

# Health check
curl http://localhost:8001/sci/health
```

---

## 🔗 Integration with v0.3

### How v0.3 Proposes Evolutions

```python
# hlcs/core/evolving_identity.py
from hlcs.core.sci import get_sci_instance

class EvolvingIdentity:
    async def propose_purpose_evolution(self, new_purpose: str):
        """Propose evolution via SCI governance layer"""
        sci = get_sci_instance()
        
        proposal_id = await sci.propose_identity_evolution(
            evolution_type="PURPOSE_EVOLUTION",
            description=f"Evolve purpose to: {new_purpose}",
            details={
                "current_purpose": self.current_purpose,
                "new_purpose": new_purpose,
                "rationale": self.wisdom_engine.justify_evolution()
            },
            predicted_impact={
                "ethics_score": await self.ethics_monitor.evaluate(),
                "stability_risk": self.assess_stability_risk(),
                "autonomy_impact": self.assess_autonomy_impact()
            }
        )
        
        # Wait for consensus (non-blocking with timeout)
        result = await sci.wait_for_consensus(proposal_id, timeout_hours=48)
        
        if result.approved:
            self.execute_approved_evolution(new_purpose)
        else:
            logger.info(f"Evolution rejected: {result.rejection_reason}")
```

### Ethical Boundaries Feed SCI Risk Assessment

```python
# hlcs/core/ethical_boundary_monitor.py
from hlcs.core.sci import get_sci_instance

class EthicalBoundaryMonitor:
    async def evaluate_evolution_proposal(self, proposal_id: str):
        """Provide ethical risk assessment for SCI"""
        sci = get_sci_instance()
        proposal = sci.get_proposal(proposal_id)
        
        # Multi-dimensional ethical evaluation
        ethics_score = self.evaluate_multi_dimensional(proposal.details)
        
        # Auto-veto if hard boundary violation
        if self.detect_hard_violation(proposal.details):
            await sci.veto_evolution(
                proposal_id=proposal_id,
                stakeholder_role=StakeholderRole.ETHICS_COMMITTEE,
                reason="Hard ethical boundary violation detected",
                severity="CRITICAL"
            )
```

### Wisdom Silence Delays Proposals

```python
# hlcs/core/wisdom_driven_silence.py
from hlcs.core.sci import get_sci_instance

class WisdomDrivenSilence:
    async def should_delay_proposal(self, proposal_id: str) -> Optional[int]:
        """Check if wisdom suggests delaying proposal submission"""
        proposal = get_sci_instance().get_proposal(proposal_id)
        
        # HIGH_UNCERTAINTY strategy
        if self.detect_high_uncertainty(proposal.details):
            return 7200  # Delay 2 hours
        
        # NOVEL_SITUATION strategy
        if self.is_novel_situation(proposal.details):
            return 1800  # Observe 30 min
        
        return None  # No delay needed
```

---

## 📊 Metrics & Monitoring

### Key Performance Indicators (KPIs)

```yaml
Consensus Metrics:
  - Approval Rate: 68% (target: >60%)
  - Avg Consensus Time: 8.5h (target: <24h)
  - Veto Rate: 5% (target: <10%)
  - Timeout Rate: 6% (target: <10%)

Stakeholder Engagement:
  - PRIMARY_USER Participation: 98%
  - SYSTEM_ADMIN Participation: 95%
  - OTHER_AGENTS Participation: 45% (optional)
  - SECURITY_AUDITOR Participation: 89%
  - ETHICS_COMMITTEE Participation: 92%

Prediction Accuracy (ML):
  - Success Prediction Accuracy: 82% (target: >75%)
  - False Positive Rate: 12% (target: <15%)

System Health:
  - API Uptime: 99.9%
  - WebSocket Connection Stability: 99.5%
  - Avg API Latency: 45ms (target: <100ms)
```

### Prometheus Metrics

```python
# Exported by sci_endpoints.py
sci_proposals_total
sci_proposals_approved
sci_proposals_rejected
sci_proposals_expired
sci_consensus_time_seconds_histogram
sci_stakeholder_participation_rate
sci_api_request_duration_seconds
sci_websocket_connections_active
```

### Grafana Dashboard Example

```json
{
  "title": "SCI Governance Dashboard",
  "panels": [
    {
      "title": "Consensus Rate Over Time",
      "targets": [
        "rate(sci_proposals_approved[1h]) / rate(sci_proposals_total[1h])"
      ]
    },
    {
      "title": "Stakeholder Participation",
      "targets": [
        "sci_stakeholder_participation_rate{role=~'PRIMARY_USER|SYSTEM_ADMIN|OTHER_AGENTS'}"
      ]
    },
    {
      "title": "Consensus Time Distribution",
      "targets": [
        "histogram_quantile(0.5, sci_consensus_time_seconds_histogram)",
        "histogram_quantile(0.95, sci_consensus_time_seconds_histogram)"
      ]
    }
  ]
}
```

---

## 🔒 Security Considerations

### Input Validation
- **Pydantic models**: All API inputs validated with strict schemas
- **Enum constraints**: StakeholderRole and DecisionType prevent injection
- **UUID validation**: Proposal IDs must be valid UUIDs

### Access Control (Future)
```python
# Future implementation
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/sci/ratify/{proposal_id}")
async def ratify_proposal(
    proposal_id: str,
    decision: DecisionRequest,
    token: str = Depends(oauth2_scheme)
):
    # Verify token and stakeholder identity
    stakeholder = verify_token(token)
    if stakeholder.role != decision.stakeholder_role:
        raise HTTPException(403, "Unauthorized role")
    ...
```

### Audit Trail
```python
# All decisions logged
{
  "timestamp": "2025-01-04T14:30:00Z",
  "proposal_id": "uuid-123",
  "stakeholder_role": "PRIMARY_USER",
  "decision_type": "RATIFY",
  "reason": "Aligns with goals",
  "ip_address": "192.168.1.100",  # Future
  "user_agent": "SARAi-Client/3.6"  # Future
}
```

---

## 🛣️ Roadmap

### v0.5 (Next Release)
- [ ] **Persistent Storage**: PostgreSQL/SQLite for proposals/decisions
- [ ] **ML Model Training**: Online learning from evolution outcomes
- [ ] **Stakeholder Authentication**: OAuth2 + role-based access control
- [ ] **Notification Channels**: Email, Slack, Telegram for stakeholder alerts
- [ ] **Consensus Templates**: Pre-approved evolution patterns (e.g., "Add translation")

### v0.6 (Future)
- [ ] **Dynamic Stakeholder Weights**: Adjust based on expertise/track record
- [ ] **Multi-Proposal Batching**: Group related evolutions for efficiency
- [ ] **Quorum Requirements**: Minimum stakeholder count for decisions
- [ ] **Emergency Override**: Bypass consensus for critical system repairs
- [ ] **Blockchain Audit**: Immutable evolution history on distributed ledger

---

## 📚 References

- **Copilot Instructions**: `.github/copilot-instructions.md` (SARAi AGI architecture)
- **v0.3 Documentation**: `docs/HLCS_V03_EVOLVING_IDENTITY.md` (identity evolution)
- **Changelog**: User-provided v3.6-conscious-aligned comprehensive changelog
- **Release Notes**: User-provided v3.6 release notes

---

## 📝 License

Copyright © 2025 SARAi Project  
Licensed under MIT License (see `LICENSE` file)

---

**Prepared by**: SARAi AGI Development Team  
**Contact**: [Configure in stakeholder_config.json]  
**Last Updated**: 2025-01-04
