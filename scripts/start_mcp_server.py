#!/usr/bin/env python3
"""Script para iniciar SARAi MCP Server.

Inicializa el servidor MCP con los módulos configurados en sarai.yaml.

Uso:
    python scripts/start_mcp_server.py
    python scripts/start_mcp_server.py --port 3001
    python scripts/start_mcp_server.py --config config/custom.yaml

Versión: 3.7.0 (Feature: MCP Server)
"""

import argparse
import logging
import sys
from pathlib import Path

# Añadir src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sarai_agi.mcp.protocol_server import create_mcp_server
from sarai_agi.modules import create_saul_module
from sarai_agi.configuration import get_section, load_settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SARAi MCP Server - Orquestador de módulos cognitivos"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/sarai.yaml",
        help="Ruta al archivo de configuración YAML (default: config/sarai.yaml)"
    )

    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host a escuchar (override config)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Puerto a escuchar (override config)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error"],
        default=None,
        help="Nivel de logging (override config)"
    )

    args = parser.parse_args()

    # Cargar configuración
    logger.info("Loading configuration from: %s", args.config)
    settings = load_settings(args.config)

    mcp_config = get_section(settings, "mcp_server", {})

    # Verificar si MCP está habilitado
    if not mcp_config.get("enabled", True):
        logger.error("MCP Server is disabled in configuration (mcp_server.enabled = false)")
        sys.exit(1)

    # Override con argumentos CLI
    host = args.host or mcp_config.get("host", "0.0.0.0")
    port = args.port or mcp_config.get("port", 3000)
    log_level = args.log_level or mcp_config.get("log_level", "info")

    # Configurar log level
    logging.getLogger().setLevel(log_level.upper())

    # Crear servidor MCP
    logger.info("Creating MCP Server...")
    server = create_mcp_server(args.config)

    # Cargar módulos desde configuración
    modules_config = mcp_config.get("modules", {})

    logger.info("Loading modules...")

    # SAUL Module
    if modules_config.get("saul", {}).get("enabled", True):
        logger.info("Loading SAUL module...")
        saul_config = modules_config["saul"]
        
        saul_module = create_saul_module({
            "host": saul_config.get("host", "localhost"),
            "port": saul_config.get("port", 50051),
            "timeout": saul_config.get("timeout", 5.0),
            "fallback_mode": saul_config.get("fallback_mode", True),
        })

        server.register_module(saul_module)
        logger.info("✅ SAUL module registered")
    else:
        logger.info("SAUL module disabled in configuration")

    # TODO: Cargar otros módulos (Vision, Audio, RAG, etc.)
    # if modules_config.get("vision", {}).get("enabled", False):
    #     logger.info("Loading Vision module...")
    #     vision_module = create_vision_module(modules_config["vision"])
    #     server.register_module(vision_module)

    # Mostrar resumen
    logger.info("")
    logger.info("=" * 80)
    logger.info("  SARAi MCP Server - Ready")
    logger.info("=" * 80)
    logger.info("  Host: %s", host)
    logger.info("  Port: %d", port)
    logger.info("  Tools: %d", len(server.tool_registry.tools))
    logger.info("  Resources: %d", len(server.resource_registry.resources))
    logger.info("=" * 80)
    logger.info("")
    logger.info("Available tools:")
    for tool_name in server.tool_registry.tools.keys():
        logger.info("  - %s", tool_name)
    logger.info("")
    logger.info("Starting server on http://%s:%d", host, port)
    logger.info("Health endpoint: http://%s:%d/health", host, port)
    logger.info("Metrics endpoint: http://%s:%d/metrics", host, port)
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("")

    # Iniciar servidor
    try:
        server.run(host=host, port=port)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("Received interrupt signal - shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error("Server error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
