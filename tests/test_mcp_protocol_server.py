"""Tests para SARAi MCP Protocol Server.

Versión: 3.7.0 (Feature: MCP Server)
"""

import pytest
from fastapi.testclient import TestClient

from sarai_agi.mcp.protocol_server import (
    MCPServer,
    ToolRegistry,
    ResourceRegistry,
    create_mcp_server,
)
from sarai_agi.modules import create_saul_module


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mcp_server():
    """Crea servidor MCP para tests."""
    server = MCPServer(config={"host": "127.0.0.1", "port": 3000})
    return server


@pytest.fixture
def mcp_with_saul():
    """Crea servidor MCP con módulo SAUL registrado."""
    server = MCPServer(config={"host": "127.0.0.1", "port": 3000})
    
    # Registrar SAUL module (fallback mode)
    saul_module = create_saul_module({
        "host": "localhost",
        "port": 50051,
        "fallback_mode": True,
    })
    
    server.register_module(saul_module)
    
    return server


@pytest.fixture
def client(mcp_with_saul):
    """Cliente HTTP para tests."""
    return TestClient(mcp_with_saul.app)


# ============================================================================
# Tests - Endpoints Básicos
# ============================================================================


def test_root_endpoint(client):
    """Test endpoint raíz."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["service"] == "SARAi MCP Server"
    assert data["version"] == "3.7.0"
    assert data["status"] == "running"
    assert data["tools"] >= 2  # saul.respond, saul.synthesize
    assert data["resources"] >= 0


def test_health_endpoint(client):
    """Test health check."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["uptime_seconds"] > 0
    assert data["tools"] >= 2
    assert data["requests_total"] >= 0


def test_metrics_endpoint(client):
    """Test métricas Prometheus."""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    
    # Verificar formato Prometheus
    text = response.text
    assert "sarai_mcp_uptime_seconds" in text
    assert "sarai_mcp_requests_total" in text
    assert "sarai_mcp_tools_registered" in text


# ============================================================================
# Tests - Tools List
# ============================================================================


def test_tools_list(client):
    """Test listar tools."""
    response = client.post("/tools/list")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "tools" in data
    assert len(data["tools"]) >= 2
    
    # Verificar estructura de tools
    tool_names = [t["name"] for t in data["tools"]]
    assert "saul.respond" in tool_names
    assert "saul.synthesize" in tool_names
    
    # Verificar tool completo
    saul_respond = next(t for t in data["tools"] if t["name"] == "saul.respond")
    assert "description" in saul_respond
    assert "parameters" in saul_respond
    assert "query" in saul_respond["parameters"]["properties"]


def test_tools_list_empty_server():
    """Test listar tools en servidor sin módulos."""
    server = MCPServer()
    client = TestClient(server.app)
    
    response = client.post("/tools/list")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["tools"] == []


# ============================================================================
# Tests - Tool Call (SAUL)
# ============================================================================


@pytest.mark.asyncio
async def test_tool_call_saul_respond(client):
    """Test llamar saul.respond."""
    request = {
        "name": "saul.respond",
        "parameters": {
            "query": "hola",
            "include_audio": False
        }
    }
    
    response = client.post("/tools/call", json=request)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar respuesta MCP
    assert data["success"] is True
    assert "result" in data
    assert data["latency_ms"] > 0
    
    # Verificar respuesta SAUL
    result = data["result"]
    assert "response" in result
    assert "confidence" in result
    assert "template_matched" in result
    assert "latency_ms" in result
    
    # Query "hola" debería matchear template "greeting"
    assert result["template_id"] == "greeting"
    assert result["confidence"] > 0.7


@pytest.mark.asyncio
async def test_tool_call_saul_respond_with_audio(client):
    """Test llamar saul.respond con audio."""
    request = {
        "name": "saul.respond",
        "parameters": {
            "query": "¿cómo estás?",
            "include_audio": True
        }
    }
    
    response = client.post("/tools/call", json=request)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    result = data["result"]
    
    # Verificar audio presente
    assert "audio" in result
    assert len(result["audio"]) > 0
    assert "audio_size_bytes" in result


@pytest.mark.asyncio
async def test_tool_call_saul_synthesize(client):
    """Test llamar saul.synthesize."""
    request = {
        "name": "saul.synthesize",
        "parameters": {
            "text": "Hola, esto es una prueba de síntesis de voz.",
            "voice_model": "es_ES-sharvard-medium",
            "speed": 1.0
        }
    }
    
    response = client.post("/tools/call", json=request)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    result = data["result"]
    
    # Verificar audio
    assert "audio" in result
    assert "duration" in result
    assert "sample_rate" in result
    assert result["sample_rate"] == 22050


@pytest.mark.asyncio
async def test_tool_call_unknown_tool(client):
    """Test llamar tool inexistente."""
    request = {
        "name": "unknown.tool",
        "parameters": {}
    }
    
    response = client.post("/tools/call", json=request)
    
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "not found" in detail.lower()


@pytest.mark.asyncio
async def test_tool_call_missing_parameter(client):
    """Test llamar tool sin parámetro requerido."""
    request = {
        "name": "saul.respond",
        "parameters": {
            # Falta 'query'
            "include_audio": False
        }
    }
    
    response = client.post("/tools/call", json=request)
    
    # Debería fallar porque 'query' es requerido
    assert response.status_code in [422, 500]  # Validation error o execution error


# ============================================================================
# Tests - Resources
# ============================================================================


def test_resources_list_empty(client):
    """Test listar resources (vacío por ahora)."""
    response = client.post("/resources/list")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "resources" in data
    # Por ahora no hay resources registrados
    assert isinstance(data["resources"], list)


def test_resources_read_not_found(client):
    """Test leer resource inexistente."""
    request = {
        "uri": "unknown://resource"
    }
    
    response = client.post("/resources/read", json=request)
    
    assert response.status_code == 404


# ============================================================================
# Tests - Tool Registry
# ============================================================================


def test_tool_registry_register():
    """Test registrar tool."""
    registry = ToolRegistry()
    
    async def dummy_tool(arg1: str):
        return f"Result: {arg1}"
    
    registry.register_tool(
        name="test.tool",
        description="Test tool",
        handler=dummy_tool,
        parameters={
            "type": "object",
            "properties": {"arg1": {"type": "string"}},
            "required": ["arg1"]
        }
    )
    
    assert "test.tool" in registry.tools
    assert registry.tools["test.tool"].name == "test.tool"
    assert registry.handlers["test.tool"] == dummy_tool


@pytest.mark.asyncio
async def test_tool_registry_call():
    """Test ejecutar tool registrado."""
    registry = ToolRegistry()
    
    async def echo_tool(message: str):
        return {"echo": message}
    
    registry.register_tool(
        name="test.echo",
        description="Echo tool",
        handler=echo_tool
    )
    
    result = await registry.call_tool("test.echo", {"message": "hello"})
    
    assert result == {"echo": "hello"}


# ============================================================================
# Tests - Resource Registry
# ============================================================================


def test_resource_registry_register():
    """Test registrar resource."""
    registry = ResourceRegistry()
    
    async def dummy_resource():
        return {"data": "example"}
    
    registry.register_resource(
        uri="test://resource",
        name="Test Resource",
        handler=dummy_resource,
        mime_type="application/json"
    )
    
    assert "test://resource" in registry.resources
    assert registry.resources["test://resource"].uri == "test://resource"
    assert registry.handlers["test://resource"] == dummy_resource


@pytest.mark.asyncio
async def test_resource_registry_read():
    """Test leer resource registrado."""
    registry = ResourceRegistry()
    
    async def memory_resource():
        return {"conversations": ["conv1", "conv2"]}
    
    registry.register_resource(
        uri="memory://conversations",
        name="Conversation Memory",
        handler=memory_resource
    )
    
    result = await registry.read_resource("memory://conversations")
    
    assert result == {"conversations": ["conv1", "conv2"]}


# ============================================================================
# Tests - Multiple Queries (Stress)
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_tool_calls(client):
    """Test múltiples llamadas a tools."""
    queries = [
        "hola",
        "¿cómo estás?",
        "gracias",
        "¿qué hora es?",
        "necesito ayuda"
    ]
    
    results = []
    
    for query in queries:
        request = {
            "name": "saul.respond",
            "parameters": {"query": query, "include_audio": False}
        }
        
        response = client.post("/tools/call", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        results.append(data["result"])
    
    # Verificar que todas las queries respondieron
    assert len(results) == 5
    
    # Verificar latencias razonables (< 500ms en fallback mode)
    for result in results:
        assert result["latency_ms"] < 500


# ============================================================================
# Tests - Integration (Server Creation)
# ============================================================================


def test_create_mcp_server_from_config():
    """Test crear servidor desde configuración."""
    # Esto usa config/sarai.yaml
    server = create_mcp_server("config/sarai.yaml")
    
    assert isinstance(server, MCPServer)
    assert server.config is not None


def test_register_module():
    """Test registrar módulo completo."""
    server = MCPServer()
    
    # Crear SAUL module
    saul = create_saul_module({"fallback_mode": True})
    
    # Registrar
    server.register_module(saul)
    
    # Verificar tools registrados
    assert len(server.tool_registry.tools) == 2
    assert "saul.respond" in server.tool_registry.tools
    assert "saul.synthesize" in server.tool_registry.tools


# ============================================================================
# Tests - Performance
# ============================================================================


def test_latency_saul_respond(client):
    """Test latencia de saul.respond."""
    import time
    
    request = {
        "name": "saul.respond",
        "parameters": {"query": "hola", "include_audio": False}
    }
    
    start = time.time()
    response = client.post("/tools/call", json=request)
    end = time.time()
    
    assert response.status_code == 200
    
    # Latencia total (HTTP + procesamiento)
    total_latency = (end - start) * 1000
    
    # En modo fallback debería ser < 300ms
    assert total_latency < 300
    
    # Latencia reportada por SAUL
    data = response.json()
    saul_latency = data["result"]["latency_ms"]
    
    # Latencia SAUL < 200ms
    assert saul_latency < 200


@pytest.mark.asyncio
async def test_concurrent_requests(client):
    """Test requests concurrentes."""
    import asyncio
    
    async def make_request(query):
        request = {
            "name": "saul.respond",
            "parameters": {"query": query, "include_audio": False}
        }
        # Note: TestClient es síncrono, este test es ilustrativo
        response = client.post("/tools/call", json=request)
        return response.json()
    
    # Simular 5 requests concurrentes
    queries = ["query" + str(i) for i in range(5)]
    
    # En tests reales con servidor async real, esto sería:
    # results = await asyncio.gather(*[make_request(q) for q in queries])
    
    # Con TestClient síncrono:
    results = [await make_request(q) for q in queries]
    
    assert len(results) == 5
    assert all(r["success"] for r in results)
