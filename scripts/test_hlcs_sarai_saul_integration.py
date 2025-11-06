#!/usr/bin/env python3
"""
Test de Integración E2E: HLCS → SARAi MCP Server → SAUL

Este script valida el flujo completo de la arquitectura modular:
1. HLCS hace una petición a SARAi MCP Server
2. SARAi enruta la petición a SAUL (vía gRPC)
3. SAUL responde con template + TTS (opcional)
4. SARAi devuelve respuesta a HLCS

Autor: Equipo SARAi AGI
Fecha: 6 de noviembre de 2025
"""

import asyncio
import grpc
import subprocess
import time
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Add SAUL to path for imports
SAUL_PATH = Path("/home/noel/saul")
sys.path.insert(0, str(SAUL_PATH / "src"))

try:
    from saul.client import SAULClient
    SAUL_CLIENT_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: SAULClient no disponible, algunos tests fallarán")
    SAUL_CLIENT_AVAILABLE = False

# Configuración
SAUL_GRPC_HOST = "localhost"
SAUL_GRPC_PORT = 50051
SARAI_MCP_URL = "http://localhost:3000"  # Futuro
HLCS_TIMEOUT = 30  # segundos


class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(msg: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(msg: str):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")


def print_error(msg: str):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")


def print_info(msg: str):
    print(f"{Colors.OKCYAN}ℹ️  {msg}{Colors.ENDC}")


def print_warning(msg: str):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")


class SAULServer:
    """Gestor del servidor SAUL gRPC"""
    
    def __init__(self, saul_path: Path):
        self.saul_path = saul_path
        self.process: Optional[subprocess.Popen] = None
    
    def start(self) -> bool:
        """Arranca el servidor SAUL"""
        print_info("Arrancando servidor SAUL (gRPC)...")
        
        try:
            # Verificar que existe el servidor
            server_file = self.saul_path / "start_server.py"
            if not server_file.exists():
                print_error(f"No se encuentra {server_file}")
                return False
            
            # Arrancar servidor en background
            self.process = subprocess.Popen(
                [sys.executable, "start_server.py"],
                cwd=str(self.saul_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "PYTHON_GIL": "0", "PORT_GRPC": str(SAUL_GRPC_PORT)}
            )
            
            # Esperar a que esté listo
            print_info("Esperando a que SAUL esté listo...")
            max_retries = 15
            for i in range(max_retries):
                try:
                    if SAUL_CLIENT_AVAILABLE:
                        client = SAULClient(host=SAUL_GRPC_HOST, port=SAUL_GRPC_PORT)
                        health = client.health_check()
                        client.close()
                        if health and health.get('healthy'):
                            print_success(f"SAUL listo en {SAUL_GRPC_HOST}:{SAUL_GRPC_PORT}")
                            return True
                except Exception as e:
                    time.sleep(1)
            
            print_error("SAUL no respondió después de 15 segundos")
            
            # Mostrar stderr si hay
            if self.process.stderr:
                stderr = self.process.stderr.read()
                if stderr:
                    print_error(f"STDERR: {stderr[:500]}")
            
            return False
            
        except Exception as e:
            print_error(f"Error arrancando SAUL: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop(self):
        """Detiene el servidor SAUL"""
        if self.process:
            print_info("Deteniendo servidor SAUL...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                print_success("SAUL detenido correctamente")
            except subprocess.TimeoutExpired:
                self.process.kill()
                print_warning("SAUL forzado a detenerse")


class SARAiMCPServerMock:
    """
    Mock simple de SARAi MCP Server
    
    En producción, esto sería un servidor FastAPI completo con:
    - MCP protocol implementation
    - Tool registry
    - Resource management
    - Routing inteligente
    
    Para la prueba, simplemente enruta a SAUL vía gRPC
    """
    
    def __init__(self):
        self.saul_client: Optional[SAULClient] = None
    
    def connect(self):
        """Conecta al servidor SAUL"""
        if SAUL_CLIENT_AVAILABLE:
            self.saul_client = SAULClient(host=SAUL_GRPC_HOST, port=SAUL_GRPC_PORT)
        else:
            raise RuntimeError("SAULClient no disponible")
    
    def disconnect(self):
        """Desconecta del servidor SAUL"""
        if self.saul_client:
            self.saul_client.close()
    
    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simula el MCP Server enrutando a SAUL
        
        Args:
            tool_name: Nombre del tool (ej: "saul.respond")
            params: Parámetros del tool
        
        Returns:
            Respuesta del tool
        """
        print_info(f"SARAi MCP: Enrutando tool '{tool_name}' a SAUL...")
        
        if tool_name == "saul.respond":
            # Llamar a SAUL vía gRPC
            try:
                query = params.get("query", "")
                include_audio = params.get("include_audio", False)
                
                start_time = time.time()
                response = self.saul_client.respond(query, include_audio=include_audio)
                latency_ms = (time.time() - start_time) * 1000
                
                result = {
                    "response": response.get("response", ""),
                    "latency_ms": latency_ms,
                }
                
                if include_audio and "audio" in response:
                    result["audio"] = response["audio"]
                
                print_success(f"SAUL respondió en {latency_ms:.1f}ms")
                return result
                
            except Exception as e:
                print_error(f"Error llamando a SAUL: {e}")
                raise
        else:
            raise ValueError(f"Tool desconocido: {tool_name}")


class HLCSClient:
    """
    Cliente HLCS simulado
    
    En producción, esto sería el sistema completo de consciencia superior con:
    - LangGraph/CrewAI orchestration
    - Meta-cognición
    - Planificación estratégica
    - Razonamiento multi-modal
    
    Para la prueba, simplemente hace peticiones a SARAi MCP
    """
    
    def __init__(self, sarai_mcp: SARAiMCPServerMock):
        self.sarai = sarai_mcp
    
    def ask(self, query: str, include_audio: bool = False) -> Dict[str, Any]:
        """
        Hace una pregunta a través de SARAi MCP
        
        Args:
            query: Pregunta del usuario
            include_audio: Si incluir audio TTS
        
        Returns:
            Respuesta completa
        """
        print_info(f"HLCS: Procesando query '{query}'...")
        
        # En producción, aquí habría:
        # 1. Análisis de la query
        # 2. Planificación de tareas
        # 3. Selección de tools apropiados
        # 4. Orquestación de múltiples llamadas si necesario
        
        # Para esta prueba, simplemente llamamos a SAUL
        result = self.sarai.call_tool(
            "saul.respond",
            {
                "query": query,
                "include_audio": include_audio
            }
        )
        
        return result


def test_simple_query(sarai_mcp):
    """Test 1: Query simple sin audio"""
    print_header("TEST 1: Query Simple (sin audio)")
    
    hlcs = HLCSClient(sarai_mcp)
    
    result = hlcs.ask("hola", include_audio=False)
    
    assert "response" in result, "Falta campo 'response'"
    assert "latency_ms" in result, "Falta campo 'latency_ms'"
    assert result["latency_ms"] < 500, f"Latencia muy alta: {result['latency_ms']}ms"
    
    print_success(f"Respuesta: {result['response']}")
    print_success(f"Latencia: {result['latency_ms']:.1f}ms")
    
    return True


def test_query_with_audio(sarai_mcp):
    """Test 2: Query con audio TTS"""
    print_header("TEST 2: Query con Audio TTS")
    
    hlcs = HLCSClient(sarai_mcp)
    
    result = hlcs.ask("¿cómo estás?", include_audio=True)
    
    assert "response" in result, "Falta campo 'response'"
    # Audio puede ser opcional si Piper no está disponible
    if "audio" in result:
        print_success(f"Audio generado: {len(result.get('audio', ''))} bytes")
    
    print_success(f"Respuesta: {result['response']}")
    print_success(f"Latencia: {result['latency_ms']:.1f}ms")
    
    return True


def test_complex_query(sarai_mcp):
    """Test 3: Query compleja"""
    print_header("TEST 3: Query Compleja")
    
    hlcs = HLCSClient(sarai_mcp)
    
    result = hlcs.ask(
        "¿Cuál es la diferencia entre Python 3.12 y 3.13?",
        include_audio=False
    )
    
    assert "response" in result, "Falta campo 'response'"
    assert len(result["response"]) > 10, "Respuesta muy corta"
    
    print_success(f"Respuesta: {result['response'][:100]}...")
    print_success(f"Latencia: {result['latency_ms']:.1f}ms")
    
    return True


def test_multiple_queries(sarai_mcp):
    """Test 4: Múltiples queries en secuencia"""
    print_header("TEST 4: Múltiples Queries (stress test)")
    
    hlcs = HLCSClient(sarai_mcp)
    
    queries = [
        "hola",
        "¿qué hora es?",
        "cuéntame un chiste",
        "¿cómo estás?",
        "gracias"
    ]
    
    total_time = 0
    for i, query in enumerate(queries, 1):
        print_info(f"Query {i}/5: {query}")
        result = hlcs.ask(query, include_audio=False)
        latency = result["latency_ms"]
        total_time += latency
        print_success(f"  → {result['response']} ({latency:.1f}ms)")
    
    avg_latency = total_time / len(queries)
    print_success(f"\nLatencia promedio: {avg_latency:.1f}ms")
    print_success(f"Throughput: {1000/avg_latency:.1f} req/s")
    
    assert avg_latency < 500, f"Latencia promedio muy alta: {avg_latency}ms"
    
    return True


def run_all_tests(sarai_mcp):
    """Ejecuta todos los tests"""
    print_header("🚀 INICIO DE TESTS E2E: HLCS → SARAi → SAUL")
    
    tests = [
        ("Query Simple", lambda: test_simple_query(sarai_mcp)),
        ("Query con Audio", lambda: test_query_with_audio(sarai_mcp)),
        ("Query Compleja", lambda: test_complex_query(sarai_mcp)),
        ("Múltiples Queries", lambda: test_multiple_queries(sarai_mcp)),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print_error(f"Test '{name}' falló: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Resumen
    print_header("📊 RESUMEN DE TESTS")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        if success:
            print_success(f"{name}: PASS")
        else:
            print_error(f"{name}: FAIL")
    
    print(f"\n{Colors.BOLD}Resultado: {passed}/{total} tests pasando{Colors.ENDC}")
    
    if passed == total:
        print_success("\n🎉 TODOS LOS TESTS PASARON")
        return 0
    else:
        print_error(f"\n❌ {total - passed} tests fallaron")
        return 1


def main():
    """Main function"""
    print_header("🏗️ ARQUITECTURA MODULAR SARAi AGI - TEST E2E")
    
    # Verificar que SAUL existe
    saul_path = Path("/home/noel/saul")
    if not saul_path.exists():
        print_error(f"No se encuentra el directorio SAUL en {saul_path}")
        return 1
    
    if not SAUL_CLIENT_AVAILABLE:
        print_error("SAULClient no está disponible. Instala las dependencias de SAUL.")
        return 1
    
    # Arrancar SAUL
    saul_server = SAULServer(saul_path)
    sarai_mcp = SARAiMCPServerMock()
    
    try:
        if not saul_server.start():
            print_error("No se pudo arrancar SAUL")
            return 1
        
        # Conectar SARAi MCP a SAUL
        print_info("Conectando SARAi MCP a SAUL...")
        sarai_mcp.connect()
        print_success("SARAi MCP conectado")
        
        # Ejecutar tests
        exit_code = run_all_tests(sarai_mcp)
        
        return exit_code
        
    except KeyboardInterrupt:
        print_warning("\nInterrumpido por usuario")
        return 130
        
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Siempre limpiar
        print_info("\nLimpiando...")
        sarai_mcp.disconnect()
        saul_server.stop()


if __name__ == "__main__":
    sys.exit(main())
