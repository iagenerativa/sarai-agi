"""
Ejemplos de integración del LLM Gateway en diferentes módulos de SARAi
"""

# ============================================================================
# EJEMPLO 1: Uso básico en cualquier módulo
# ============================================================================

async def ejemplo_basico():
    """Uso más simple del gateway"""
    from sarai_agi.llm_gateway import get_gateway
    
    gateway = get_gateway()
    
    # Chat simple
    response = await gateway.chat(
        messages=[{"role": "user", "content": "Hola, ¿cómo estás?"}]
    )
    
    print(f"Respuesta: {response['content']}")
    print(f"Modelo: {response['model']}")
    print(f"Provider: {response['provider']}")
    print(f"Latencia: {response['latency_ms']:.1f}ms")
    print(f"Cached: {response['cached']}")


# ============================================================================
# EJEMPLO 2: Integración en HLCS (High-Level Consciousness System)
# ============================================================================

class HLCSReasoning:
    """Motor de razonamiento de HLCS usando LLM Gateway"""
    
    def __init__(self):
        from sarai_agi.llm_gateway import get_gateway
        self.gateway = get_gateway()
    
    async def reason(self, task: str, context: dict) -> str:
        """
        Razona sobre una tarea compleja
        
        Args:
            task: Tarea a resolver
            context: Contexto adicional
            
        Returns:
            Plan de acción razonado
        """
        messages = [
            {
                "role": "system",
                "content": "Eres un sistema de razonamiento de alto nivel. "
                          "Analiza la tarea y crea un plan detallado paso a paso."
            },
            {
                "role": "user",
                "content": f"Tarea: {task}\n\nContexto: {context}"
            }
        ]
        
        # Usar modelo más potente para razonamiento complejo
        response = await self.gateway.chat(
            messages=messages,
            model="gpt-4",  # o claude-3-5-sonnet-20241022
            provider="openai",  # o "anthropic"
            temperature=0.2,  # Baja temperatura para razonamiento preciso
            max_tokens=2000,
        )
        
        return response["content"]
    
    async def stream_reasoning(self, task: str):
        """Razonamiento en streaming para tareas largas"""
        messages = [
            {"role": "user", "content": f"Analiza: {task}"}
        ]
        
        print("Razonando", end="", flush=True)
        async for chunk in self.gateway.stream_chat(
            messages=messages,
            model="gpt-4",
            provider="openai"
        ):
            print(chunk, end="", flush=True)
        print()  # Newline al final


# ============================================================================
# EJEMPLO 3: Integración en RAG Module
# ============================================================================

class RAGPipeline:
    """Pipeline RAG usando LLM Gateway para síntesis"""
    
    def __init__(self):
        from sarai_agi.llm_gateway import get_gateway
        self.gateway = get_gateway()
    
    async def synthesize_results(
        self,
        query: str,
        search_results: list[str]
    ) -> str:
        """
        Sintetiza resultados de búsqueda usando LLM
        
        Args:
            query: Query original del usuario
            search_results: Resultados de búsqueda web
            
        Returns:
            Respuesta sintetizada
        """
        context = "\n\n".join([
            f"Resultado {i+1}:\n{result}"
            for i, result in enumerate(search_results)
        ])
        
        messages = [
            {
                "role": "system",
                "content": "Sintetiza la información de los resultados de búsqueda "
                          "para responder la pregunta del usuario de forma precisa."
            },
            {
                "role": "user",
                "content": f"Pregunta: {query}\n\nResultados:\n{context}"
            }
        ]
        
        # Usar Ollama (local) para síntesis rápida
        response = await self.gateway.chat(
            messages=messages,
            provider="ollama",
            model="llama3.2:latest",
            temperature=0.7,
        )
        
        return response["content"]
    
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para textos"""
        embeddings = []
        for text in texts:
            embedding = await self.gateway.embed(
                text=text,
                provider="ollama",
                model="nomic-embed-text"
            )
            embeddings.append(embedding)
        return embeddings


# ============================================================================
# EJEMPLO 4: Integración en SAUL (respuestas rápidas)
# ============================================================================

class SAULEnhanced:
    """SAUL con fallback a LLM para queries complejas"""
    
    def __init__(self):
        from sarai_agi.llm_gateway import get_gateway
        self.gateway = get_gateway()
        self.trm_classifier = None  # Template Response Manager
    
    async def respond(self, query: str) -> dict:
        """
        Genera respuesta - usa TRM si es simple, LLM si es compleja
        
        Args:
            query: Query del usuario
            
        Returns:
            Dict con respuesta y metadata
        """
        # Clasificar complejidad
        complexity = self._classify_complexity(query)
        
        if complexity == "simple":
            # Usar TRM (template-based, ultra-rápido <1ms)
            return {
                "content": self._trm_response(query),
                "method": "template",
                "latency_ms": 0.8,
            }
        else:
            # Fallback a LLM (más lento pero mejor calidad)
            response = await self.gateway.chat(
                messages=[{"role": "user", "content": query}],
                provider="ollama",
                model="llama3.2:latest",
                temperature=0.7,
                max_tokens=150,  # Respuestas concisas
            )
            
            return {
                "content": response["content"],
                "method": "llm",
                "latency_ms": response["latency_ms"],
                "cached": response["cached"],
            }
    
    def _classify_complexity(self, query: str) -> str:
        """Clasifica query como simple/compleja"""
        # Implementación simplificada
        if len(query.split()) < 5:
            return "simple"
        return "complex"
    
    def _trm_response(self, query: str) -> str:
        """Respuesta basada en templates"""
        # Implementación simplificada
        return "Template response placeholder"


# ============================================================================
# EJEMPLO 5: Comparar múltiples providers (testing/benchmarking)
# ============================================================================

async def compare_providers():
    """Compara la misma query en diferentes providers"""
    from sarai_agi.llm_gateway import get_gateway
    
    gateway = get_gateway()
    
    messages = [{"role": "user", "content": "Explica qué es la inteligencia artificial en 50 palabras"}]
    
    providers = ["ollama", "openai", "anthropic"]
    
    results = {}
    for provider in providers:
        try:
            response = await gateway.chat(
                messages=messages,
                provider=provider,
                temperature=0.7,
            )
            
            results[provider] = {
                "content": response["content"],
                "latency_ms": response["latency_ms"],
                "tokens": response["usage"]["total_tokens"],
                "model": response["model"],
            }
        except Exception as e:
            results[provider] = {"error": str(e)}
    
    # Imprimir comparación
    for provider, result in results.items():
        print(f"\n{'='*60}")
        print(f"Provider: {provider}")
        print(f"{'='*60}")
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Modelo: {result['model']}")
            print(f"Latencia: {result['latency_ms']:.1f}ms")
            print(f"Tokens: {result['tokens']}")
            print(f"Respuesta:\n{result['content']}")


# ============================================================================
# EJEMPLO 6: Monitoreo y estadísticas
# ============================================================================

async def monitor_gateway():
    """Obtiene estadísticas de uso del gateway"""
    from sarai_agi.llm_gateway import get_gateway
    
    gateway = get_gateway()
    
    # Hacer algunas requests
    for i in range(5):
        await gateway.chat(
            messages=[{"role": "user", "content": f"Test query {i}"}]
        )
    
    # Obtener estadísticas
    stats = gateway.get_stats()
    
    print("\n" + "="*60)
    print("LLM GATEWAY STATISTICS")
    print("="*60)
    print(f"Total requests: {stats['total_requests']}")
    print(f"Total errors: {stats['total_errors']}")
    print(f"Total fallbacks: {stats['total_fallbacks']}")
    print(f"Error rate: {stats['error_rate']:.1%}")
    
    print("\nCache:")
    if "cache" in stats:
        cache = stats["cache"]
        print(f"  Size: {cache['size']}/{cache['max_size']}")
        print(f"  Hit rate: {cache['hit_rate']:.1%}")
        print(f"  Hits: {cache['hits']}")
        print(f"  Misses: {cache['misses']}")
        print(f"  Evictions: {cache['evictions']}")
    
    print("\nProviders:")
    for provider, provider_stats in stats["providers"].items():
        print(f"  {provider}:")
        print(f"    Requests: {provider_stats['requests']}")
        print(f"    Errors: {provider_stats['errors']}")
        print(f"    Error rate: {provider_stats['error_rate']:.1%}")
    
    # Health check
    health = await gateway.health_check()
    print("\nHealth:")
    for provider, is_healthy in health.items():
        status = "✅ HEALTHY" if is_healthy else "❌ UNHEALTHY"
        print(f"  {provider}: {status}")


# ============================================================================
# EJEMPLO 7: Uso en docker-compose.yml
# ============================================================================

DOCKER_COMPOSE_EXAMPLE = """
# docker-compose.yml (fragmento)

services:
  # Ollama compartido por todos los módulos
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-models:/root/.ollama
    networks:
      - sarai-network
    deploy:
      resources:
        limits:
          memory: 8G  # Una sola instancia = 4-8GB
  
  # SARAi Core (usa gateway)
  sarai-core:
    image: sarai:core
    environment:
      - LLM_GATEWAY_PRIMARY_PROVIDER=ollama
      - LLM_GATEWAY_OLLAMA_BASE_URL=http://ollama:11434
      - LLM_GATEWAY_OLLAMA_MODEL=llama3.2:latest
    depends_on:
      - ollama
    networks:
      - sarai-network
  
  # HLCS (usa gateway)
  hlcs:
    image: hlcs:latest
    environment:
      - LLM_GATEWAY_PRIMARY_PROVIDER=openai
      - LLM_GATEWAY_OPENAI_API_KEY=${OPENAI_API_KEY}
      - LLM_GATEWAY_FALLBACK_PROVIDERS=ollama
      - LLM_GATEWAY_OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
    networks:
      - sarai-network
  
  # RAG Module (usa gateway)
  sarai-rag:
    image: sarai:rag
    environment:
      - LLM_GATEWAY_PRIMARY_PROVIDER=ollama
      - LLM_GATEWAY_OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
    networks:
      - sarai-network

networks:
  sarai-network:
    driver: bridge

volumes:
  ollama-models:
"""


# ============================================================================
# MAIN - Ejecutar ejemplos
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    print("="*60)
    print("EJEMPLOS LLM GATEWAY")
    print("="*60)
    
    # Ejecutar ejemplo básico
    asyncio.run(ejemplo_basico())
    
    # Descomentar para ejecutar otros ejemplos:
    # asyncio.run(compare_providers())
    # asyncio.run(monitor_gateway())
