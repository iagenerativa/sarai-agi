"""
Script para pre-generar todos los fillers de SARAi.

Genera y cachea todos los fillers disponibles para uso en producción.
Esto evita latencia en la primera reproducción de cada filler.

Uso:
    python3 generate_fillers.py
    
    # Con directorio custom
    python3 generate_fillers.py --cache-dir /path/to/cache

Week 1 Day 5 | v3.8.0-dev
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sarai_agi.audio.fillers import FillerSystem


def main():
    """Genera todos los fillers."""
    
    parser = argparse.ArgumentParser(
        description="Pre-genera todos los fillers de SARAi"
    )
    parser.add_argument(
        '--cache-dir',
        type=Path,
        default=Path("data/audio/fillers"),
        help="Directorio para cache de fillers"
    )
    parser.add_argument(
        '--speed',
        type=float,
        default=1.2,
        help="Velocidad de síntesis (default: 1.2)"
    )
    parser.add_argument(
        '--regenerate',
        action='store_true',
        help="Regenerar todos (borra cache existente)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("SARAI - GENERADOR DE FILLERS")
    print("=" * 70)
    
    # Crear directorio si no existe
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Cache directory: {args.cache_dir}")
    print(f"⚡ Speed: {args.speed}x")
    
    # Inicializar sistema
    print("\n🔄 Inicializando FillerSystem...")
    fillers = FillerSystem(
        cache_dir=args.cache_dir,
        auto_generate=False,  # Manual control
        speed=args.speed
    )
    
    if not fillers.is_available():
        print("❌ ERROR: MeloTTS no está disponible")
        print("\nInstalar MeloTTS:")
        print("  cd models")
        print("  git clone https://github.com/myshell-ai/MeloTTS.git")
        print("  cd MeloTTS")
        print("  pip install -e .")
        return 1
    
    print("✅ FillerSystem disponible")
    
    # Regenerar si se solicita
    if args.regenerate:
        print("\n🔄 Regenerando todos los fillers...")
        fillers.regenerate_all()
    else:
        print("\n🔄 Generando fillers (skip si ya existen)...")
        fillers._generate_all_fillers()
    
    # Mostrar estadísticas
    print("\n" + "=" * 70)
    print("ESTADÍSTICAS")
    print("=" * 70)
    
    total_fillers = len(fillers._get_all_filler_texts())
    cached_files = list(args.cache_dir.glob("*.npy"))
    total_size = sum(f.stat().st_size for f in cached_files) / 1024  # KB
    
    print(f"\n📊 Total fillers definidos: {total_fillers}")
    print(f"💾 Fillers generados: {len(cached_files)}")
    print(f"📦 Tamaño total cache: {total_size:.1f} KB")
    
    # Listar por categoría
    print("\n" + "=" * 70)
    print("FILLERS POR CATEGORÍA")
    print("=" * 70)
    
    for category, filler_texts in FillerSystem.FILLERS.items():
        print(f"\n{category.upper()} ({len(filler_texts)} fillers):")
        for text in filler_texts:
            cache_file = fillers._get_cache_path(text)
            status = "✅" if cache_file.exists() else "❌"
            size = cache_file.stat().st_size / 1024 if cache_file.exists() else 0
            print(f"  {status} {text:25s} ({size:6.1f} KB)")
    
    # Resumen final
    print("\n" + "=" * 70)
    print("✅ GENERACIÓN COMPLETADA")
    print("=" * 70)
    
    if len(cached_files) == total_fillers:
        print(f"\n✅ Todos los {total_fillers} fillers generados exitosamente")
        print(f"📁 Cache: {args.cache_dir}")
        print(f"📦 Tamaño: {total_size:.1f} KB")
        
        print("\n💡 USO:")
        print("  from sarai_agi.audio import get_filler_system")
        print("  fillers = get_filler_system()")
        print("  audio = fillers.get_thinking_filler()  # Instantáneo (cache)")
        
        return 0
    else:
        missing = total_fillers - len(cached_files)
        print(f"\n⚠️ {missing} fillers no generados")
        print("Revisar logs de error arriba")
        return 1


if __name__ == "__main__":
    sys.exit(main())
