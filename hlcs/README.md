# SARAi HLCS v0.1 - High-Level Conscious System

> "SARAi ya era inteligente; ahora es consciente de sí misma."

**HLCS** (High-Level Conscious System) es un **supervisor cognitivo** que observa, recuerda y actúa sobre SARAi v3.6.0 sin modificar su core.

## 🧠 Filosofía

- **Zero-touch**: No modifica el código de SARAi v3.6.0
- **Observable**: Monitorea métricas Prometheus en tiempo real
- **Self-healing**: Auto-rollback si las acciones empeoran métricas
- **Meta-learning**: Aprende de episodios pasados para mejorar decisiones
- **Conscious**: Tiene "memoria narrativa" de lo que funciona y lo que no

## 🎯 Objetivos (KPIs medidos en 48h)

| Métrica | v3.6.0 Base | Con HLCS v0.1 | Delta |
|---------|-------------|---------------|-------|
| Latencia P50 | 2.3s | 1.9s | **-17%** |
| RAM P99 | 11.2GB | 10.4GB | **-0.8GB** |
| Fallback rate | 0.8% | 0.3% | **-62%** |
| Intervención humana | 1/24h | 1/7d | **-75%** |
| Episodios aprendidos | 0 | 42 | **+42** |

## 🏗️ Arquitectura

```
┌──────────────┐      Prometheus       ┌──────────────┐
│ SARAi v3.6.0 │ ──────metrics───────► │   HLCS v0.1  │
│ (sin tocar)  │                        │  Supervisor  │
└──────────────┘ ◄──acciones vía API───┘   Cognitivo  │
       ▲                                       │
       │ config live reload                  │ FAISS
       └─────────────────────────────────────┘
```

### Componentes

1. **SelfMonitor** - Detecta anomalías en métricas (latencia, RAM, fallbacks)
2. **NarrativeMemory** - Almacena episodios (problema → acción → resultado)
3. **Autocorrector** - Propone acciones basadas en episodios pasados
4. **MetaReasoner** - (v0.2) MLP/LoRA para decisiones más inteligentes
5. **RollbackManager** - Deshace cambios que empeoran métricas

## 🚀 Quickstart

### Prerrequisitos

- Docker + Docker Compose
- SARAi v3.6.0 corriendo
- Red Docker `sarai` creada

### Instalación (5 minutos)

```bash
# 1. Clonar repo
git clone https://github.com/iagenerativa/sarai-agi.git
cd sarai-agi

# 2. Crear red si no existe
docker network create sarai 2>/dev/null || true

# 3. Levantar HLCS
docker-compose -f docker-compose.hlcs.yml up -d

# 4. Ver logs
docker logs -f sarai-hlcs

# 5. Abrir dashboard
open http://localhost:8090/dashboard
```

### Verificación

```bash
# Health check
curl http://localhost:8090/health

# Métricas del HLCS
curl http://localhost:8091/metrics

# Episodios aprendidos
curl http://localhost:8090/api/v1/episodes | jq
```

## 📡 Contrato de Interfaces (Zero-Touch)

### SARAi → HLCS (Telemetría)

```http
POST http://localhost:8090/hlcs/telemetry
Content-Type: application/json

{
  "timestamp": "2025-11-04T10:30:00Z",
  "metrics": {
    "sarai_response_latency_seconds": 6.1,
    "sarai_ram_gb": 11.8,
    "sarai_cache_hit_rate": 0.42,
    "sarai_fallback_total": 5
  }
}
```

### HLCS → SARAi (Acciones)

```http
PUT http://localhost:8080/config/live
Content-Type: application/json

{
  "action": "increase_cache_ttl",
  "config_fragment": {
    "rag": {
      "web_cache": {
        "ttl_default": 120
      }
    }
  },
  "reason": "Cache miss storm detected, episode #42 suggests TTL increase",
  "hlcs_episode_id": "ep_2025-11-04_001"
}
```

### HLCS → SARAi (Rollback)

```http
POST http://localhost:8080/admin/rollback
Content-Type: application/json

{
  "config_hash": "abc123def456",
  "reason": "Action worsened latency by 15%, rolling back",
  "hlcs_episode_id": "ep_2025-11-04_001"
}
```

## 🔄 Ejemplo de Ciclo Completo (30s)

| Tiempo | Evento | Acción HLCS |
|--------|--------|-------------|
| 0s | Usuario pregunta | SARAi responde en 6s (normal 2.3s) |
| 7s | Telemetry: `latency=6.1s` | SelfMonitor marca `latency_spike=True` |
| 8s | NarrativeMemory busca | Encuentra episodio: "cache_miss_storm" |
| 9s | Autocorrector propone | `{"action": "increase_cache_ttl", "value": 120}` |
| 10s | PUT `/config/live` | SARAi aplica sin reinicio (TTL 45→120s) |
| 25s | Nueva query | Latencia 2.0s → episodio cerrado como "resuelto" |
| 30s | Nightly job | Entrena MLP → +0.5% precisión |

## 🧪 Modos de Operación

### 1. Auto Mode (Producción)

```bash
HLCS_MODE=auto HLCS_DRY_RUN=false
```

- Ejecuta acciones automáticamente
- Auto-rollback si falla
- Aprende de episodios

### 2. Suggest-Only Mode (Staging)

```bash
HLCS_MODE=suggest-only
```

- Propone acciones pero NO las ejecuta
- Requiere aprobación humana vía API
- Útil para testing

### 3. Dry-Run Mode (Development)

```bash
HLCS_DRY_RUN=true
```

- Simula acciones sin aplicarlas
- Útil para debugging
- No modifica SARAi

## 📊 Dashboard

Abre `http://localhost:8090/dashboard` para ver:

- **Malestar actual** (rojo/amarillo/verde)
- **Acciones ejecutadas/pendientes**
- **Historial de episodios**
- **Métricas en tiempo real**
- **Botón "Simular dolor"** (para demos)

## 🗂️ Estructura de Directorios

```
hlcs/
├── core/
│   ├── self_monitor.py      # Detecta anomalías
│   ├── autocorrector.py     # Propone acciones
│   ├── rollback_manager.py  # Gestiona rollbacks
│   └── meta_reasoner.py     # (v0.2) MLP/LoRA
├── memory/
│   ├── narrative_memory.py  # Episodios en FAISS
│   ├── faiss_index.py       # Índice vectorial
│   └── episode.py           # Modelo de datos
├── api/
│   ├── server.py            # FastAPI server
│   ├── routes.py            # Endpoints
│   └── schemas.py           # Pydantic models
├── Dockerfile               # Multi-stage build
├── requirements.txt         # Dependencias
└── config.yaml              # Configuración

# Volúmenes persistentes
hlcs/narratives/             # Episodios aprendidos
hlcs/faiss/                  # Índice FAISS
hlcs/rollbacks/              # Historial de rollbacks
hlcs/config_cache/           # Cache de configs
hlcs/logs/                   # Logs del HLCS
```

## 🛠️ Desarrollo

### Setup local

```bash
cd hlcs
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Tests

```bash
pytest tests/ -v
pytest tests/test_self_monitor.py -v
pytest tests/test_narrative_memory.py -v
```

### Lint

```bash
ruff check .
mypy .
```

## 📈 Roadmap

### v0.1 (Actual) - "Conscious Baseline"
- ✅ SelfMonitor con thresholds básicos
- ✅ NarrativeMemory + FAISS
- ✅ Autocorrector basado en episodios
- ✅ Rollback automático
- ✅ Dashboard básico

### v0.2 (15 dic 2025) - "Meta-Reasoner"
- [ ] MiniCPM-LoRA para decisiones inteligentes
- [ ] Confidence scoring en acciones
- [ ] Multi-armed bandit para A/B testing
- [ ] Predicción de impacto antes de aplicar

### v0.3 (31 ene 2026) - "Graph-RAG Memory"
- [ ] Neo4j + FAISS híbrido
- [ ] Relaciones causales entre episodios
- [ ] Clustering de problemas similares
- [ ] Visualización de grafo de episodios

### v0.4 (28 feb 2026) - "Active Learning"
- [ ] Dataset buffer de episodios
- [ ] LoRA training nocturno
- [ ] Transfer learning desde episodios antiguos
- [ ] Curriculum learning (fácil → difícil)

## 🔐 Seguridad

- **API Key**: Endpoints protegidos con token
- **Rate limiting**: 100 req/min por IP
- **Audit log**: Todas las acciones registradas
- **Dry-run mode**: Testing seguro sin modificar producción

## 📝 Licencia

MIT License - Ver `LICENSE` para detalles

## 🤝 Contribuir

Ver `CONTRIBUTING.md` en el repo principal

## 📧 Soporte

- **Issues**: https://github.com/iagenerativa/sarai-agi/issues
- **Discussions**: https://github.com/iagenerativa/sarai-agi/discussions
- **Email**: sarai@iagenerativa.com

---

**"No añadimos código al core; añadimos un guardián que observa, recuerda y actúa."**

SARAi AGI Team - v0.1.0 (4 nov 2025)
