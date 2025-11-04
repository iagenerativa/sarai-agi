#!/usr/bin/env python3
"""
SARAi AGI - CLI Integrada
==========================

Interfaz de línea de comandos para demostración del sistema integrado.

Conecta todos los componentes:
- TRM Classifier
- MCP Core
- Emotional Context Engine
- Cascade Router
- Model Pool
- RAG Agent

Usage:
    python cli.py "¿Cómo funciona el aprendizaje por refuerzo?"
    python cli.py --interactive
    python cli.py --verbose "¿Qué es Python?"

Version: v3.6.0
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from sarai_agi.core import create_integrated_pipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_query(query: str, pipeline, verbose: bool = False):
    """
    Procesa una query con el pipeline integrado.

    Args:
        query: Query de usuario
        pipeline: Pipeline integrada
        verbose: Si mostrar información detallada

    Returns:
        Dict con resultado completo
    """
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}")

    result = await pipeline.run({"input": query})

    # Extract info
    response = result.get("response", "")
    metadata = result.get("metadata", {})
    agent = metadata.get("agent", "unknown")
    emotion = metadata.get("emotion", {})
    pipeline_metrics = metadata.get("pipeline_metrics", {})

    # Display response
    print(f"\n📝 RESPONSE ({agent} agent):")
    print(f"{'-'*80}")
    print(response)
    print(f"{'-'*80}")

    if verbose:
        print(f"\n🔍 METADATA:")
        print(f"  Agent: {agent}")

        if emotion:
            print(f"\n  Emotion:")
            print(f"    Detected: {emotion.get('emotion', 'N/A')}")
            print(f"    Confidence: {emotion.get('confidence', 0.0):.2f}")
            print(f"    Empathy Level: {emotion.get('empathy_level', 0.0):.2f}")
            print(f"    Cultural Context: {emotion.get('cultural_context', 'N/A')}")

        print(f"\n  Scores:")
        print(f"    Hard: {result.get('hard', 0.0):.2f}")
        print(f"    Soft: {result.get('soft', 0.0):.2f}")
        print(f"    Web Query: {result.get('web_query', 0.0):.2f}")
        print(f"    Alpha: {result.get('alpha', 0.0):.2f}")
        print(f"    Beta: {result.get('beta', 0.0):.2f}")

        if pipeline_metrics:
            print(f"\n  Pipeline Metrics:")
            print(f"    Classify: {pipeline_metrics.get('classify_ms', 0.0):.2f}ms")
            print(f"    Weights: {pipeline_metrics.get('weights_ms', 0.0):.2f}ms")
            print(f"    Emotion: {pipeline_metrics.get('emotion_ms', 0.0):.2f}ms")
            print(f"    Routing: {pipeline_metrics.get('routing_ms', 0.0):.2f}ms")
            print(f"    Generation: {pipeline_metrics.get('generation_ms', 0.0):.2f}ms")
            print(f"    Total: {pipeline_metrics.get('response_latency_ms', 0.0):.2f}ms")

    return result


async def interactive_mode(verbose: bool = False):
    """
    Modo interactivo de la CLI.

    Args:
        verbose: Si mostrar información detallada
    """
    print("\n" + "="*80)
    print("SARAi AGI - Sistema Integrado v3.6.0")
    print("="*80)
    print("\nCreando pipeline integrada...")

    pipeline = create_integrated_pipeline()

    print("✅ Pipeline creada exitosamente")
    print("\nComandos disponibles:")
    print("  - Escribe tu query y presiona Enter")
    print("  - 'exit' o 'quit' para salir")
    print("  - 'verbose on/off' para alternar modo detallado")
    print("  - 'help' para mostrar esta ayuda")
    print("\n" + "="*80)

    try:
        while True:
            try:
                query = input("\n🤖 SARAi> ").strip()

                if not query:
                    continue

                if query.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 ¡Hasta luego!")
                    break

                if query.lower() == 'help':
                    print("\nComandos disponibles:")
                    print("  - Escribe tu query y presiona Enter")
                    print("  - 'exit' o 'quit' para salir")
                    print("  - 'verbose on/off' para alternar modo detallado")
                    print("  - 'help' para mostrar esta ayuda")
                    continue

                if query.lower().startswith('verbose'):
                    parts = query.split()
                    if len(parts) > 1:
                        if parts[1] == 'on':
                            verbose = True
                            print("✅ Modo verbose activado")
                        elif parts[1] == 'off':
                            verbose = False
                            print("✅ Modo verbose desactivado")
                    else:
                        verbose = not verbose
                        print(f"✅ Modo verbose {'activado' if verbose else 'desactivado'}")
                    continue

                await process_query(query, pipeline, verbose)

            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as exc:
                logger.exception("Error procesando query: %s", exc)
                print(f"\n❌ Error: {exc}")

    finally:
        print("\n🔄 Cerrando pipeline...")
        await pipeline.shutdown()
        print("✅ Pipeline cerrada")


async def single_query_mode(query: str, verbose: bool = False):
    """
    Modo de query única.

    Args:
        query: Query a procesar
        verbose: Si mostrar información detallada
    """
    print("\nCreando pipeline integrada...")
    pipeline = create_integrated_pipeline()
    print("✅ Pipeline creada exitosamente")

    try:
        await process_query(query, pipeline, verbose)
    finally:
        await pipeline.shutdown()


def main():
    """Entry point de la CLI."""
    parser = argparse.ArgumentParser(
        description='SARAi AGI - Sistema Integrado v3.6.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s "¿Cómo funciona el aprendizaje por refuerzo?"
  %(prog)s --interactive
  %(prog)s --verbose "¿Qué es Python?"
  %(prog)s -i -v

Para más información: https://github.com/iagenerativa/sarai-agi
        """
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='Query a procesar (si no se proporciona, inicia modo interactivo)'
    )

    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Modo interactivo'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mostrar información detallada (metadata, métricas, etc.)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='SARAi AGI v3.6.0'
    )

    args = parser.parse_args()

    # Configure logging level based on verbose flag
    if args.verbose:
        logging.getLogger('sarai_agi').setLevel(logging.DEBUG)
    else:
        logging.getLogger('sarai_agi').setLevel(logging.INFO)

    # Determine mode
    if args.interactive or not args.query:
        # Interactive mode
        asyncio.run(interactive_mode(verbose=args.verbose))
    else:
        # Single query mode
        asyncio.run(single_query_mode(args.query, verbose=args.verbose))


if __name__ == '__main__':
    main()
