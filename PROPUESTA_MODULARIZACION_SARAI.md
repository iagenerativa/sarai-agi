# 🏗️ Propuesta de Modularización SARAi AGI - Arquitectura Completa

**Fecha**: 5 de noviembre de 2025  
**Versión**: 1.0.0  
**Autor**: Equipo SARAi + Análisis IA

---

## 🎯 Visión Arquitectónica

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HLCS (Consciencia Superior)                      │
│              High-Level Consciousness System                        │
│                    [Repositorio: hlcs]                              │
│                    [Docker: hlcs:latest]                            │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ MCP Protocol
                                 │
                    ┌────────────▼────────────┐
                    │    SARAi MCP Server     │
                    │  (Orquestador Central)  │
                    │  [Repo: sarai-agi]      │
                    │  [Docker: sarai:core]   │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
    ┌─────────┐          ┌─────────────┐        ┌──────────┐
    │  SAUL   │          │  Módulos    │        │ Módulos  │
    │ Sistema │          │  Cognitivos │        │ Servicios│
    │ Atención│          │             │        │          │
    │  Ultra  │          │  • Vision   │        │ • RAG    │
    │ Ligero  │          │  • Audio    │        │ • Memory │
    │         │          │  • NLP      │        │ • Skills │
    │[Docker] │          │  • Emotion  │        │ • MCP    │
    └─────────┘          └─────────────┘        └──────────┘
```

---

## 📦 Propuesta de Repositorios Modulares

### 🔷 Repositorio 1: **hlcs** (High-Level Consciousness System)
**GitHub**: `iagenerativa/hlcs`  
**Docker**: `hlcs:latest`

**Responsabilidad**: Consciencia superior, toma de decisiones estratégicas, orquestación de alto nivel

```yaml
Funcionalidades:
  - Razonamiento multi-modal de alto nivel
  - Planificación estratégica
  - Meta-cognición
  - Aprendizaje autónomo
  - Toma de decisiones complejas
  
Dependencias:
  - Ninguna (sistema autónomo)
  - Consume SARAi vía MCP como herramienta

Stack Tecnológico:
  - Python 3.12+ (no-GIL cuando esté disponible)
  - LangGraph / CrewAI (orquestación)
  - LLM de razonamiento (GPT-4, Claude, etc.)
  - Docker + docker-compose

Estructura:
hlcs/
├── src/
│   ├── reasoning/        # Motor de razonamiento
│   ├── planning/         # Planificador estratégico
│   ├── metacognition/    # Auto-reflexión
│   └── orchestration/    # Orquestador de tareas
├── agents/               # Agentes especializados
├── tools/                # Herramientas (incluye SARAi MCP)
├── Dockerfile
└── docker-compose.yml
```

---

### 🔷 Repositorio 2: **sarai-agi** (Core AGI - MCP Server)
**GitHub**: `iagenerativa/sarai-agi` *(actual)*  
**Docker**: `sarai:core`

**Responsabilidad**: Orquestador central, servidor MCP, hub de módulos cognitivos

```yaml
Funcionalidades:
  - MCP Server (Model Context Protocol)
  - Routing inteligente de tareas
  - Gestión de módulos cognitivos
  - API unificada
  - Telemetría y monitoreo
  - Sistema de plugins
  
Expone vía MCP:
  - Tools: Todas las capacidades de módulos conectados
  - Resources: Memoria, conocimiento, estado
  - Prompts: Templates de razonamiento
  
Stack Tecnológico:
  - Python 3.12+ (no-GIL cuando esté disponible)
  - FastAPI (servidor MCP)
  - Pydantic (validación)
  - Docker

Estructura:
sarai-agi/
├── src/sarai_agi/
│   ├── mcp/
│   │   ├── server.py           # MCP Server principal
│   │   ├── tools.py            # Tool registry
│   │   ├── resources.py        # Resource manager
│   │   └── prompts.py          # Prompt templates
│   ├── routing/
│   │   ├── router.py           # Router principal
│   │   ├── cascade.py          # CASCADE ORACLE
│   │   └── confidence.py       # Confidence scoring
│   ├── orchestration/
│   │   ├── pipeline.py         # Pipeline paralelo
│   │   └── graph.py            # Graph-based routing
│   └── telemetry/
│       ├── metrics.py          # Prometheus metrics
│       └── logging.py          # Structured logging
├── modules/                    # Registry de módulos
├── Dockerfile
└── docker-compose.yml
```

**API MCP Expuesta**:
```json
{
  "tools": [
    "saul.respond",           // SAUL - respuesta rápida
    "vision.analyze",         // Análisis de imágenes
    "audio.transcribe",       // Transcripción audio
    "audio.synthesize",       // TTS (Piper)
    "rag.search",             // Búsqueda RAG
    "memory.store",           // Persistencia memoria
    "skills.execute"          // Ejecución de skills
  ],
  "resources": [
    "memory://conversations",
    "knowledge://embeddings",
    "state://current"
  ]
}
```

---

### 🔷 Repositorio 3: **saul** (Sistema de Atención Ultra Ligero)
**GitHub**: `iagenerativa/saul`  
**Docker**: `saul:latest`

**Responsabilidad**: Respuestas ultra-rápidas, templates, interacción básica

```yaml
Funcionalidades:
  - TRM (Template Response Manager)
  - Respuestas < 200ms
  - Detección de intención básica
  - Clasificación rápida
  - TTS ultra-rápido (Piper)
  - Conversación ligera
  
Características:
  - Latencia ultra-baja (< 200ms)
  - Sin LLM pesado (solo templates + Piper TTS)
  - Stateless (puede escalar horizontalmente)
  - Ideal para chatbots, asistentes ligeros
  
Stack Tecnológico:
  - Python 3.12+ (no-GIL cuando esté disponible)
  - FastAPI (REST API)
  - Piper TTS (176ms latencia)
  - Redis (cache opcional)
  - Docker

Estructura:
saul/
├── src/saul/
│   ├── trm/
│   │   ├── template_manager.py
│   │   ├── classifier.py
│   │   └── templates/           # Templates en YAML
│   ├── tts/
│   │   └── pipertts.py          # Piper TTS adapter
│   ├── api/
│   │   └── server.py            # FastAPI server
│   └── cache/
│       └── redis_cache.py       # Cache opcional
├── models/
│   └── piper/                   # Modelos Piper TTS
├── Dockerfile
└── docker-compose.yml

API Endpoints:
  POST /respond                  # Respuesta rápida
  POST /synthesize               # TTS
  GET  /health                   # Health check
  GET  /metrics                  # Prometheus metrics
```

**Caso de uso**:
```bash
# SAUL como servicio independiente
curl -X POST http://localhost:8001/respond \
  -H "Content-Type: application/json" \
  -d '{"query": "hola", "include_audio": true}'

# Respuesta en < 200ms con audio incluido
```

---

### 🔷 Repositorio 4: **sarai-vision** (Módulo de Visión)
**GitHub**: `iagenerativa/sarai-vision`  
**Docker**: `sarai:vision`

**Responsabilidad**: Análisis de imágenes, OCR, detección de objetos

```yaml
Funcionalidades:
  - Análisis de imágenes (Qwen3-VL)
  - OCR (text extraction)
  - Detección de objetos
  - Descripción de escenas
  - Análisis facial (opcional)
  
Expone vía MCP:
  - vision.analyze(image_url)
  - vision.ocr(image_url)
  - vision.detect_objects(image_url)
  
Stack:
  - Python 3.12+
  - Qwen3-VL-4B (o similar)
  - ONNX Runtime
  - Docker + GPU support

Estructura:
sarai-vision/
├── src/sarai_vision/
│   ├── models/
│   │   └── qwen3vl.py
│   ├── mcp_server.py        # MCP Server para Vision
│   └── processors/
│       ├── ocr.py
│       └── object_detection.py
└── Dockerfile
```

---

### 🔷 Repositorio 5: **sarai-audio** (Módulo de Audio)
**GitHub**: `iagenerativa/sarai-audio`  
**Docker**: `sarai:audio`

**Responsabilidad**: Transcripción, síntesis de voz, análisis de audio

```yaml
Funcionalidades:
  - Transcripción (Whisper, Faster-Whisper)
  - TTS (Piper, MeloTTS fallback)
  - Análisis de sentimiento por voz
  - Speaker diarization
  
Expone vía MCP:
  - audio.transcribe(audio_url)
  - audio.synthesize(text, voice)
  - audio.analyze_sentiment(audio_url)
  
Stack:
  - Python 3.12+
  - Whisper / Faster-Whisper
  - Piper TTS
  - Pyannote (diarization)
  - Docker

Estructura:
sarai-audio/
├── src/sarai_audio/
│   ├── transcription/
│   │   └── whisper.py
│   ├── synthesis/
│   │   ├── pipertts.py
│   │   └── melotts.py
│   ├── analysis/
│   │   └── sentiment.py
│   └── mcp_server.py
└── Dockerfile
```

---

### 🔷 Repositorio 6: **sarai-rag** (Módulo RAG)
**GitHub**: `iagenerativa/sarai-rag`  
**Docker**: `sarai:rag`

**Responsabilidad**: Búsqueda web, embeddings, vector DB, síntesis

```yaml
Funcionalidades:
  - Web search (SearXNG)
  - Embeddings (Gemma-300M)
  - Vector DB (ChromaDB/Qdrant)
  - RAG pipeline completo
  - Cache inteligente
  - Audit trail
  
Expone vía MCP:
  - rag.search(query)
  - rag.embed(text)
  - rag.store(text, metadata)
  
Stack:
  - Python 3.12+
  - SearXNG (búsqueda)
  - ChromaDB / Qdrant
  - Sentence Transformers
  - Docker

Estructura:
sarai-rag/
├── src/sarai_rag/
│   ├── search/
│   │   └── searxng.py
│   ├── embeddings/
│   │   └── gemma.py
│   ├── vectordb/
│   │   ├── chromadb.py
│   │   └── qdrant.py
│   ├── pipeline.py
│   └── mcp_server.py
├── config/
│   └── searxng/
└── Dockerfile
```

---

### 🔷 Repositorio 7: **sarai-memory** (Módulo de Memoria)
**GitHub**: `iagenerativa/sarai-memory`  
**Docker**: `sarai:memory`

**Responsabilidad**: Memoria conversacional, persistencia, contexto

```yaml
Funcionalidades:
  - Memoria a corto plazo (Redis)
  - Memoria a largo plazo (Vector DB)
  - Memoria episódica
  - Resumen automático de conversaciones
  - Retrieval contextual
  
Expone vía MCP:
  - memory.store(conversation)
  - memory.recall(query, k=5)
  - memory.summarize(conversation_id)
  
Stack:
  - Python 3.12+
  - Redis (short-term)
  - ChromaDB (long-term)
  - Docker

Estructura:
sarai-memory/
├── src/sarai_memory/
│   ├── short_term/
│   │   └── redis.py
│   ├── long_term/
│   │   └── vectordb.py
│   ├── episodic/
│   │   └── episodes.py
│   └── mcp_server.py
└── Dockerfile
```

---

### 🔷 Repositorio 8: **sarai-skills** (Módulo de Skills)
**GitHub**: `iagenerativa/sarai-skills`  
**Docker**: `sarai:skills`

**Responsabilidad**: Ejecución de skills containerizados, sandboxing

```yaml
Funcionalidades:
  - Skills containerizados (SQL, Bash, Network)
  - Sandboxing (Firejail)
  - gRPC API
  - Gestión de recursos
  
Expone vía MCP:
  - skills.execute(skill_name, code)
  - skills.list()
  
Stack:
  - Python 3.12+
  - gRPC
  - Firejail
  - Docker-in-Docker (skills como containers)

Estructura:
sarai-skills/
├── src/sarai_skills/
│   ├── executors/
│   │   ├── sql.py
│   │   ├── bash.py
│   │   └── network.py
│   ├── sandbox/
│   │   └── firejail.py
│   └── mcp_server.py
├── skills/                   # Skills definitions
└── Dockerfile
```

---

## 🔗 Comunicación Inter-Módulos

### Opción 1: **MCP (Model Context Protocol)** ⭐ RECOMENDADO

Todos los módulos exponen **MCP Servers** que SARAi-AGI consume como **tools**.

```python
# En HLCS
from mcp import Client

# Conectar a SARAi MCP Server
sarai = Client("http://sarai-agi:3000")

# Usar tools expuestos
result = await sarai.call_tool("saul.respond", {
    "query": "¿Qué tiempo hace?",
    "include_audio": True
})

result = await sarai.call_tool("vision.analyze", {
    "image_url": "https://example.com/image.jpg"
})

result = await sarai.call_tool("rag.search", {
    "query": "información sobre Python 3.13"
})
```

### Opción 2: **gRPC** (Para latencia crítica)

Para módulos que requieren latencia ultra-baja (ej: SAUL).

```protobuf
// saul.proto
service SAULService {
  rpc Respond(QueryRequest) returns (ResponseReply);
  rpc Synthesize(TextRequest) returns (AudioReply);
}
```

### Opción 3: **REST API** (Para servicios HTTP simples)

Cada módulo puede exponer también REST API para compatibilidad.

---

## 🐳 Estrategia de Dockerización

### Docker Compose Completo

```yaml
# docker-compose.yml (orquestación completa)
version: '3.8'

services:
  # Core SARAi AGI (MCP Server Hub)
  sarai-core:
    image: sarai:core
    build: ./sarai-agi
    ports:
      - "3000:3000"  # MCP Server
    environment:
      - MCP_ENABLED=true
      - LOG_LEVEL=info
    volumes:
      - ./config:/app/config
    networks:
      - sarai-network

  # SAUL - Sistema de Atención Ultra Ligero
  saul:
    image: saul:latest
    build: ./saul
    ports:
      - "8001:8001"  # REST API
      - "50051:50051"  # gRPC
    environment:
      - TTS_ENGINE=piper
      - PIPER_MODEL=es_ES-sharvard-medium
    volumes:
      - ./saul/models:/app/models
    networks:
      - sarai-network
    deploy:
      resources:
        limits:
          memory: 512M  # Ultra-ligero

  # Vision Module
  sarai-vision:
    image: sarai:vision
    build: ./sarai-vision
    ports:
      - "3001:3001"
    environment:
      - MODEL=qwen3-vl-4b
      - DEVICE=cpu  # o cuda
    volumes:
      - ./sarai-vision/models:/app/models
    networks:
      - sarai-network
    deploy:
      resources:
        limits:
          memory: 8G

  # Audio Module
  sarai-audio:
    image: sarai:audio
    build: ./sarai-audio
    ports:
      - "3002:3002"
    environment:
      - WHISPER_MODEL=base
      - TTS_ENGINE=piper
    networks:
      - sarai-network

  # RAG Module
  sarai-rag:
    image: sarai:rag
    build: ./sarai-rag
    ports:
      - "3003:3003"
    environment:
      - VECTOR_DB=chromadb
      - SEARXNG_URL=http://searxng:8080
    depends_on:
      - searxng
      - chromadb
    networks:
      - sarai-network

  # Memory Module
  sarai-memory:
    image: sarai:memory
    build: ./sarai-memory
    ports:
      - "3004:3004"
    environment:
      - REDIS_URL=redis://redis:6379
      - VECTOR_DB_URL=http://chromadb:8000
    depends_on:
      - redis
      - chromadb
    networks:
      - sarai-network

  # Skills Module
  sarai-skills:
    image: sarai:skills
    build: ./sarai-skills
    ports:
      - "3005:3005"
    privileged: true  # Para Firejail
    networks:
      - sarai-network

  # HLCS - High-Level Consciousness System
  hlcs:
    image: hlcs:latest
    build: ./hlcs
    ports:
      - "4000:4000"
    environment:
      - SARAI_MCP_URL=http://sarai-core:3000
      - LLM_PROVIDER=openai  # o local
    depends_on:
      - sarai-core
    networks:
      - sarai-network

  # Servicios de soporte
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - sarai-network

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chromadb-data:/chroma/chroma
    networks:
      - sarai-network

  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ./config/searxng:/etc/searxng
    networks:
      - sarai-network

networks:
  sarai-network:
    driver: bridge

volumes:
  chromadb-data:
```

---

## 🎯 Flujo de Trabajo Modular

### Ejemplo 1: Query Simple

```
Usuario: "Hola"
  ↓
HLCS → SARAi MCP Server → saul.respond("hola")
  ↓
SAUL (176ms)
  ↓
Respuesta: "Hola. ¿En qué puedo ayudarte?" + audio
```

### Ejemplo 2: Query Compleja Multi-Modal

```
Usuario: "¿Qué hay en esta imagen?" + imagen.jpg
  ↓
HLCS → Planifica:
  1. Analizar imagen
  2. Buscar contexto si necesario
  3. Generar respuesta
  ↓
SARAi MCP Server orquesta:
  - vision.analyze(imagen.jpg)
  - rag.search("contexto sobre lo detectado") [opcional]
  - saul.respond(respuesta_generada)
  ↓
Respuesta con contexto + audio
```

### Ejemplo 3: Conversación con Memoria

```
Usuario: "Recuerda que me gusta el café"
  ↓
HLCS → SARAi MCP:
  - memory.store({user: "noel", preference: "café"})
  - saul.respond("recordado")
  ↓
[... más tarde ...]
  ↓
Usuario: "¿Qué me gusta?"
  ↓
HLCS → SARAi MCP:
  - memory.recall({user: "noel", query: "preferencias"})
  - saul.respond("te gusta el café")
```

---

## 📊 Ventajas de Esta Arquitectura

### ✅ Escalabilidad
- Cada módulo escala independientemente
- SAUL puede tener 10 instancias (stateless)
- Vision puede tener GPU dedicada
- Memory puede tener cluster Redis

### ✅ Mantenibilidad
- Código separado por responsabilidad
- CI/CD independiente por repo
- Versionado independiente (SAUL v1.2, Vision v2.0)
- Tests aislados

### ✅ Despliegue Flexible
```bash
# Solo SAUL (asistente ligero)
docker-compose up saul redis

# SARAi completo sin HLCS
docker-compose up sarai-core saul sarai-vision sarai-audio

# Sistema completo AGI
docker-compose up
```

### ✅ Evolución Independiente
- SAUL puede migrar a Rust (performance)
- Vision puede cambiar a modelo nuevo
- RAG puede cambiar ChromaDB → Qdrant
- **Sin afectar otros módulos** (API MCP estable)

### ✅ Reutilización
```python
# Otros proyectos pueden usar SAUL standalone
docker run -p 8001:8001 saul:latest

# O solo Vision
docker run -p 3001:3001 sarai:vision
```

---

## 🗓️ Plan de Migración Sugerido

### Fase 1: Separación SAUL (1-2 semanas)
- [ ] Crear repo `saul`
- [ ] Migrar TRM + Piper TTS
- [ ] Dockerizar
- [ ] Tests E2E
- [ ] Documentación
- [ ] CI/CD GitHub Actions

### Fase 2: Refactor SARAi Core como MCP Server (2-3 semanas)
- [ ] Implementar MCP Server
- [ ] Exponer tools registry
- [ ] Conectar SAUL como módulo
- [ ] Dockerizar SARAi Core
- [ ] Tests MCP

### Fase 3: Separación de Módulos (1 módulo/semana)
- [ ] Semana 1: sarai-vision
- [ ] Semana 2: sarai-audio
- [ ] Semana 3: sarai-rag
- [ ] Semana 4: sarai-memory
- [ ] Semana 5: sarai-skills

### Fase 4: Integración HLCS (2 semanas)
- [ ] Conectar HLCS a SARAi MCP
- [ ] Orquestación de alto nivel
- [ ] Tests integración completa

### Fase 5: Optimización y Producción (ongoing)
- [ ] Monitoreo (Prometheus + Grafana)
- [ ] Logging centralizado (ELK)
- [ ] Alertas
- [ ] Documentación usuario final

---

## 📋 Estructura de Carpetas Propuesta (GitHub)

```
~/projects/
├── hlcs/                      # Repositorio 1
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── src/
│   └── README.md
│
├── sarai-agi/                 # Repositorio 2 (actual)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── src/sarai_agi/
│   │   ├── mcp/
│   │   ├── routing/
│   │   └── orchestration/
│   └── README.md
│
├── saul/                      # Repositorio 3 (NUEVO)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── src/saul/
│   │   ├── trm/
│   │   ├── tts/
│   │   └── api/
│   ├── models/piper/
│   └── README.md
│
├── sarai-vision/              # Repositorio 4
├── sarai-audio/               # Repositorio 5
├── sarai-rag/                 # Repositorio 6
├── sarai-memory/              # Repositorio 7
└── sarai-skills/              # Repositorio 8

# Docker Compose Orquestador (puede estar en sarai-agi o repo aparte)
~/projects/sarai-agi/docker-compose.full.yml
```

---

## 🎯 Resumen Ejecutivo

| Componente | Repo | Docker | Responsabilidad | Latencia |
|-----------|------|--------|-----------------|----------|
| **HLCS** | `hlcs` | `hlcs:latest` | Consciencia superior | N/A (orquestador) |
| **SARAi Core** | `sarai-agi` | `sarai:core` | MCP Server hub | < 50ms (routing) |
| **SAUL** | `saul` | `saul:latest` | Respuestas ultra-rápidas | < 200ms |
| **Vision** | `sarai-vision` | `sarai:vision` | Análisis de imágenes | 1-3s |
| **Audio** | `sarai-audio` | `sarai:audio` | Transcripción + TTS | 0.2-2s |
| **RAG** | `sarai-rag` | `sarai:rag` | Búsqueda + síntesis | 5-30s |
| **Memory** | `sarai-memory` | `sarai:memory` | Persistencia | < 100ms |
| **Skills** | `sarai-skills` | `sarai:skills` | Ejecución código | Variable |

---

## 💡 Recomendaciones Finales

1. **Empezar con SAUL**: Es el más pequeño y autocontenido
2. **MCP como estándar**: Facilita integración futura
3. **Docker desde día 1**: No esperar a producción
4. **CI/CD automático**: GitHub Actions para cada repo
5. **Documentación clara**: README con ejemplos de uso
6. **Versionado semántico**: SemVer estricto
7. **Tests obligatorios**: > 80% coverage por módulo

---

**¿Estás de acuerdo con esta propuesta? ¿Por dónde empezamos?** 🚀

Sugiero comenzar con **SAUL** esta misma semana - es pequeño, funcional, y puedes tenerlo en producción rápido como prueba de concepto de la arquitectura modular.
