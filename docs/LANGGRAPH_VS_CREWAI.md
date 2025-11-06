# 🤖 LangGraph vs CrewAI - Comparación para HLCS

**Fecha**: 5 de noviembre de 2025  
**Contexto**: Decisión de framework para HLCS (High-Level Consciousness System)

---

## 📊 Comparación Directa

| Aspecto | LangGraph | CrewAI |
|---------|-----------|--------|
| **Enfoque** | Graph-based state machines | Multi-agent collaboration |
| **Complejidad** | Media-Alta | Baja-Media |
| **Curva aprendizaje** | Empinada | Suave |
| **Control granular** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Simplicidad** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Flexibilidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Debugging** | Difícil (graph tracing) | Fácil (logs claros) |
| **Dependencias** | LangChain (pesado) | LangChain + extras |
| **Madurez** | Estable (LangChain 0.3+) | En evolución (v0.x) |
| **Comunidad** | Grande (LangChain) | Creciente |
| **Casos de uso ideales** | Workflows complejos, decisiones condicionales | Equipos de agentes, colaboración |

---

## 🧠 LangGraph

### ✅ Ventajas

1. **Control Total del Flujo**
   ```python
   from langgraph.graph import StateGraph
   
   workflow = StateGraph(State)
   workflow.add_node("planner", planning_agent)
   workflow.add_node("researcher", research_agent)
   workflow.add_node("writer", writing_agent)
   
   # Condicional complejo
   workflow.add_conditional_edges(
       "planner",
       should_research,  # Función de decisión
       {
           "research": "researcher",
           "write": "writer",
           "end": END
       }
   )
   ```

2. **Checkpointing y Persistencia**
   - Estado del grafo se guarda automáticamente
   - Puede pausar/reanudar workflows
   - Ideal para tareas largas (debugging, recuperación)

3. **Ciclos y Recursión**
   - Puede implementar loops (ej: "refina hasta que sea bueno")
   - Self-correction automático
   ```python
   workflow.add_edge("writer", "evaluator")
   workflow.add_conditional_edges(
       "evaluator",
       lambda x: "writer" if x["score"] < 0.8 else "end"
   )
   ```

4. **Inspección Profunda**
   - Visualización del grafo de ejecución
   - Debugging paso a paso
   - Métricas por nodo

### ❌ Desventajas

1. **Curva de Aprendizaje Empinada**
   - Concepto de "State" puede confundir
   - Sintaxis verbosa
   - Debugging de grafos complejos es difícil

2. **Overhead de LangChain**
   - Dependencia pesada (50+ paquetes)
   - Abstracción a veces innecesaria
   - Cambios frecuentes en API (breaking changes)

3. **Código Verboso**
   ```python
   # 50+ líneas solo para definir un workflow simple
   from langgraph.graph import StateGraph, END
   from typing import TypedDict, Annotated
   
   class State(TypedDict):
       messages: Annotated[list, operator.add]
       next_action: str
   
   # ... más boilerplate
   ```

---

## 👥 CrewAI

### ✅ Ventajas

1. **Metáfora Intuitiva**
   ```python
   from crewai import Agent, Task, Crew
   
   # Definir agentes como "empleados"
   researcher = Agent(
       role="Research Specialist",
       goal="Find accurate information",
       backstory="Expert in web research...",
       tools=[web_search, rag_search]
   )
   
   writer = Agent(
       role="Content Writer",
       goal="Write engaging content",
       backstory="Creative writer...",
       tools=[text_editor]
   )
   
   # Definir tareas
   research_task = Task(
       description="Research topic X",
       agent=researcher
   )
   
   write_task = Task(
       description="Write article based on research",
       agent=writer,
       context=[research_task]  # Depende de research
   )
   
   # Orquestar
   crew = Crew(
       agents=[researcher, writer],
       tasks=[research_task, write_task],
       process="sequential"  # o "hierarchical"
   )
   
   result = crew.kickoff()
   ```

2. **Colaboración Natural**
   - Agentes se pasan información automáticamente
   - Sistema de "delegación" (agentes piden ayuda a otros)
   - Memoria compartida entre agentes

3. **Menos Código**
   - ~20 líneas para workflow completo
   - YAML support (definir crews en config)
   - Auto-gestión de estado

4. **Procesos Predefinidos**
   - `sequential`: Uno tras otro
   - `hierarchical`: Manager delega a workers
   - Fácil de entender y debuggear

### ❌ Desventajas

1. **Menos Control**
   - No puedes definir lógica condicional compleja
   - Flujo es más "lineal"
   - Difícil implementar loops personalizados

2. **Overhead de Coordinación**
   - Cada agente es un LLM call extra
   - Latencia mayor (N agentes × latencia LLM)
   - Costo mayor en APIs comerciales

3. **Abstracciones Opinadas**
   - Fuerza modelo "jefe-empleados"
   - Difícil personalizar comportamiento interno
   - Menos transparencia en decisiones

4. **Inmadurez**
   - Proyecto joven (v0.x)
   - Breaking changes frecuentes
   - Bugs en casos edge

---

## 🎯 Recomendación para HLCS

### ✨ **Estrategia Híbrida** (mejor opción)

```
HLCS Architecture:
┌─────────────────────────────────────────────┐
│         LangGraph (Orchestration Layer)     │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │   Planning Phase                    │   │
│  │   - Analyze query complexity        │   │
│  │   - Decide strategy                 │   │
│  └─────────────────────────────────────┘   │
│                 │                           │
│                 ▼                           │
│  ┌─────────────────────────────────────┐   │
│  │   Execution Phase (CrewAI)          │   │
│  │                                     │   │
│  │   ┌─────────┐  ┌─────────┐        │   │
│  │   │Researcher│  │ Writer  │        │   │
│  │   │  Agent  │  │  Agent  │        │   │
│  │   └─────────┘  └─────────┘        │   │
│  │                                     │   │
│  │   CrewAI Crew trabajando           │   │
│  └─────────────────────────────────────┘   │
│                 │                           │
│                 ▼                           │
│  ┌─────────────────────────────────────┐   │
│  │   Refinement Phase                  │   │
│  │   - Quality check                   │   │
│  │   - Loop back if needed             │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Implementación**:

```python
from langgraph.graph import StateGraph, END
from crewai import Agent, Task, Crew

# ===== LangGraph para control de flujo =====
class HLCSState(TypedDict):
    query: str
    complexity: float
    strategy: str
    crew_result: dict
    final_result: str
    quality_score: float

workflow = StateGraph(HLCSState)

# Nodo 1: Clasificar complejidad
def classify_complexity(state):
    # Usa SARAi MCP (trm.classify)
    complexity = calculate_complexity(state["query"])
    strategy = "simple" if complexity < 0.5 else "crew"
    return {"complexity": complexity, "strategy": strategy}

# Nodo 2: Ejecutar CrewAI (solo si es complejo)
def execute_crew(state):
    # ===== CrewAI para colaboración multi-agente =====
    researcher = Agent(
        role="Research Specialist",
        goal="Find accurate information",
        tools=[sarai_mcp.rag_search, sarai_mcp.web_search]
    )
    
    analyst = Agent(
        role="Data Analyst",
        goal="Analyze information",
        tools=[sarai_mcp.vision_analyze]
    )
    
    writer = Agent(
        role="Content Writer",
        goal="Synthesize final response",
        tools=[sarai_mcp.saul_respond]
    )
    
    research_task = Task(
        description=f"Research: {state['query']}",
        agent=researcher
    )
    
    analysis_task = Task(
        description="Analyze research findings",
        agent=analyst,
        context=[research_task]
    )
    
    write_task = Task(
        description="Write final response",
        agent=writer,
        context=[research_task, analysis_task]
    )
    
    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, write_task],
        process="sequential"
    )
    
    result = crew.kickoff()
    return {"crew_result": result}

# Nodo 3: Simple response (bypass CrewAI)
def simple_response(state):
    # Llamar directo a SARAi MCP
    result = sarai_mcp.saul_respond(state["query"])
    return {"final_result": result}

# Nodo 4: Quality check
def check_quality(state):
    score = evaluate_quality(state.get("final_result") or state["crew_result"])
    return {"quality_score": score}

# ===== Construir grafo =====
workflow.add_node("classify", classify_complexity)
workflow.add_node("execute_crew", execute_crew)
workflow.add_node("simple_response", simple_response)
workflow.add_node("quality_check", check_quality)

# Condicional: ¿simple o crew?
workflow.add_conditional_edges(
    "classify",
    lambda x: x["strategy"],
    {
        "simple": "simple_response",
        "crew": "execute_crew"
    }
)

workflow.add_edge("execute_crew", "quality_check")
workflow.add_edge("simple_response", "quality_check")

# Loop de refinamiento
workflow.add_conditional_edges(
    "quality_check",
    lambda x: "execute_crew" if x["quality_score"] < 0.7 else "end",
    {
        "execute_crew": "execute_crew",
        "end": END
    }
)

workflow.set_entry_point("classify")

# Compilar
hlcs = workflow.compile()

# Ejecutar
result = hlcs.invoke({"query": "Analyze this complex scenario..."})
```

---

## 📋 Decisión Final

### 🏆 Recomendación: **LangGraph + CrewAI Híbrido**

**Razones**:

1. ✅ **LangGraph** para:
   - Control de flujo condicional
   - Loops de refinamiento
   - Checkpointing
   - Decisiones estratégicas

2. ✅ **CrewAI** para:
   - Colaboración multi-agente
   - Tareas que requieren "especialistas"
   - Workflows simples (research → analyze → write)
   - Código limpio y mantenible

3. ✅ **Mejor de ambos mundos**:
   - Flexibilidad de LangGraph
   - Simplicidad de CrewAI
   - Control cuando lo necesitas
   - Abstracción cuando es conveniente

---

## 🚀 Alternativa Minimalista (si odias LangChain)

Si prefieres **código puro sin frameworks pesados**:

```python
# hlcs/src/hlcs/orchestrator.py (100% custom, 0 frameworks)

class HLCSOrchestrator:
    def __init__(self, sarai_mcp_client):
        self.sarai = sarai_mcp_client
        self.state = {}
    
    async def process(self, query: str) -> dict:
        # 1. Classify
        complexity = await self._classify(query)
        
        # 2. Route
        if complexity < 0.5:
            result = await self._simple_path(query)
        else:
            result = await self._complex_path(query)
        
        # 3. Refine loop
        quality = await self._evaluate(result)
        iterations = 0
        while quality < 0.7 and iterations < 3:
            result = await self._refine(result, query)
            quality = await self._evaluate(result)
            iterations += 1
        
        return {
            "result": result,
            "quality": quality,
            "iterations": iterations
        }
    
    async def _classify(self, query: str) -> float:
        # Usa SARAi MCP trm.classify
        response = await self.sarai.call_tool("trm.classify", {"query": query})
        return response["complexity"]
    
    async def _simple_path(self, query: str) -> str:
        # Direct call to SAUL
        response = await self.sarai.call_tool("saul.respond", {"query": query})
        return response["text"]
    
    async def _complex_path(self, query: str) -> str:
        # Multi-step workflow (custom agents)
        
        # Step 1: Research
        research = await self.sarai.call_tool("rag.search", {"query": query})
        
        # Step 2: Analyze (if vision needed)
        if self._has_image(query):
            analysis = await self.sarai.call_tool("vision.analyze", {...})
        else:
            analysis = research
        
        # Step 3: Synthesize
        synthesis = await self.sarai.call_tool("llm.chat", {
            "messages": [
                {"role": "system", "content": "You are a synthesizer"},
                {"role": "user", "content": f"Research: {research}\nAnalysis: {analysis}\nSynthesize response for: {query}"}
            ]
        })
        
        return synthesis["text"]
    
    async def _refine(self, result: str, original_query: str) -> str:
        # Self-refinement
        refinement_prompt = f"Original query: {original_query}\nPrevious attempt: {result}\nImprove this response."
        refined = await self.sarai.call_tool("llm.chat", {
            "messages": [{"role": "user", "content": refinement_prompt}]
        })
        return refined["text"]
    
    async def _evaluate(self, result: str) -> float:
        # Quality evaluation (custom logic or LLM-as-judge)
        eval_prompt = f"Rate quality 0-1: {result}"
        score = await self.sarai.call_tool("llm.chat", {
            "messages": [{"role": "user", "content": eval_prompt}]
        })
        return float(score["text"])  # Assumes LLM returns "0.85"

# Uso
orchestrator = HLCSOrchestrator(sarai_mcp_client)
result = await orchestrator.process("complex query here")
```

**Ventajas**:
- ✅ 0 dependencias pesadas (solo MCP client)
- ✅ 100% control
- ✅ Código limpio (~150 LOC)
- ✅ Fácil debugging
- ✅ No breaking changes de frameworks

**Desventajas**:
- ❌ Reinventas la rueda (checkpointing, parallelism, etc.)
- ❌ Más código a mantener

---

## 🎯 Resumen Ejecutivo

| Opción | Complejidad | Control | Mantenibilidad | Recomendación |
|--------|-------------|---------|----------------|---------------|
| **Solo LangGraph** | Alta | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Si workflows MUY complejos |
| **Solo CrewAI** | Baja | ⭐⭐⭐ | ⭐⭐⭐⭐ | Si colaboración es clave |
| **Híbrido** | Media | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ **MEJOR OPCIÓN** |
| **Custom (sin frameworks)** | Baja | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Si odias dependencias |

---

## 💡 Mi Recomendación Personal

Para **HLCS de SARAi**:

```
1. Empezar con Custom Orchestrator (100% tuyo, 150 LOC)
2. Si crece complejidad → Agregar LangGraph solo para control de flujo
3. Si necesitas colaboración → Agregar CrewAI para agents específicos
```

**No empieces con LangGraph/CrewAI si no los necesitas**. El custom orchestrator es:
- Más simple
- Más rápido (menos overhead)
- Más mantenible (tú controlas todo)
- Compatible con SARAi MCP (que ya es tu abstracción)

**Solo agrega frameworks cuando sientas el dolor** de:
- Workflows complejos con 10+ pasos condicionales → LangGraph
- Equipos de 5+ agentes colaborando → CrewAI

---

¿Qué enfoque prefieres para HLCS? 🚀
