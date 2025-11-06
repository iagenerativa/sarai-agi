"""
Ejemplo de uso del sistema de Fillers para SARAi.

Demuestra cómo usar fillers para mejorar la experiencia de usuario
durante procesamiento de consultas complejas.

Week 1 Day 5 | v3.8.0-dev
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sarai_agi.audio.fillers import get_filler_system


def simulate_complex_processing():
    """Simula procesamiento complejo (búsqueda web, RAG, etc.)."""
    print("      [Simulando procesamiento complejo...]")
    time.sleep(2)  # Simular 2 segundos de procesamiento


def main():
    """Ejemplo de uso de fillers en diferentes contextos."""
    
    print("=" * 70)
    print("FILLER SYSTEM - Ejemplo de Uso")
    print("=" * 70)
    
    # Inicializar sistema
    print("\n1️⃣ Inicializando FillerSystem...")
    fillers = get_filler_system()
    
    if not fillers.is_available():
        print("❌ ERROR: FillerSystem no está disponible")
        print("Instalar MeloTTS primero (ver docs/WEEK1_DAY3-4_RESUMEN.md)")
        return
    
    print(f"✅ FillerSystem disponible")
    print(f"   Cache: {fillers._cache_dir}")
    print(f"   Categorías: {list(fillers.FILLERS.keys())}")
    
    # Escenario 1: Usuario hace pregunta compleja
    print("\n" + "=" * 70)
    print("ESCENARIO 1: Pregunta compleja que requiere búsqueda")
    print("=" * 70)
    print("\n👤 Usuario: '¿Cuáles son las últimas noticias sobre IA?'")
    print("🤖 SARAi: ", end="", flush=True)
    
    # Reproducir filler de pensamiento
    audio = fillers.get_thinking_filler()
    if audio is not None:
        print("[FILLER: 'déjame pensar...']")
        # En producción: play_audio(audio)
    
    simulate_complex_processing()
    print("🤖 SARAi: 'Aquí están las últimas noticias sobre IA...'")
    
    # Escenario 2: Esperar respuesta de API externa
    print("\n" + "=" * 70)
    print("ESCENARIO 2: Consulta que requiere API externa")
    print("=" * 70)
    print("\n👤 Usuario: 'Dame el clima de Madrid'")
    print("🤖 SARAi: ", end="", flush=True)
    
    # Reproducir filler de espera
    audio = fillers.get_waiting_filler()
    if audio is not None:
        print("[FILLER: 'un momento...']")
        # En producción: play_audio(audio)
    
    simulate_complex_processing()
    print("🤖 SARAi: 'El clima en Madrid es soleado, 22°C'")
    
    # Escenario 3: Confirmación de comando
    print("\n" + "=" * 70)
    print("ESCENARIO 3: Confirmación de comando")
    print("=" * 70)
    print("\n👤 Usuario: 'Guarda esto en mi lista de tareas'")
    print("🤖 SARAi: ", end="", flush=True)
    
    # Reproducir filler de confirmación
    audio = fillers.get_confirming_filler()
    if audio is not None:
        print("[FILLER: 'entiendo']")
        # En producción: play_audio(audio)
    
    time.sleep(0.5)
    print("🤖 SARAi: 'Guardado en tu lista de tareas'")
    
    # Escenario 4: Múltiples fillers (evitar repetición)
    print("\n" + "=" * 70)
    print("ESCENARIO 4: Variación de fillers (evitar repetición)")
    print("=" * 70)
    
    print("\nSolicitando 5 thinking fillers...")
    used_fillers = []
    
    for i in range(5):
        audio = fillers.get_thinking_filler()
        if audio is not None:
            # En producción tendríamos el texto del filler
            # Por ahora mostramos longitud como proxy de identidad
            duration = len(audio) / 44100  # Asumiendo 44100Hz
            used_fillers.append(duration)
            print(f"   Filler {i+1}: {duration:.2f}s de audio")
    
    if len(set(used_fillers)) > 1:
        print("✅ Sistema varía los fillers (evita repetición)")
    else:
        print("⚠️ Todos los fillers son iguales (categoría con un solo filler)")
    
    # Mostrar todas las categorías
    print("\n" + "=" * 70)
    print("CATEGORÍAS DE FILLERS DISPONIBLES")
    print("=" * 70)
    
    for category, filler_texts in fillers.FILLERS.items():
        print(f"\n{category.upper()}:")
        for text in filler_texts:
            print(f"  • {text}")
    
    # Generar ejemplos de cada categoría
    print("\n" + "=" * 70)
    print("GENERANDO EJEMPLOS DE CADA CATEGORÍA")
    print("=" * 70)
    
    output_dir = Path("/tmp/filler_examples")
    output_dir.mkdir(exist_ok=True)
    
    examples_generated = 0
    
    for category in fillers.FILLERS.keys():
        print(f"\n📁 Categoría: {category}")
        
        # Generar 2 ejemplos por categoría
        for i in range(2):
            audio = fillers.get_filler(category)
            
            if audio is not None:
                output_file = output_dir / f"{category}_{i+1}.wav"
                
                # Guardar como WAV (requiere scipy o soundfile)
                try:
                    import scipy.io.wavfile as wavfile
                    wavfile.write(output_file, 44100, audio)
                    print(f"   ✅ {output_file.name}")
                    examples_generated += 1
                except ImportError:
                    # Guardar como numpy si no hay scipy
                    np_file = output_dir / f"{category}_{i+1}.npy"
                    import numpy as np
                    np.save(np_file, audio)
                    print(f"   ✅ {np_file.name} (numpy)")
                    examples_generated += 1
    
    print("\n" + "=" * 70)
    print(f"✅ {examples_generated} EJEMPLOS GENERADOS")
    print("=" * 70)
    print(f"\n📁 Archivos en: {output_dir}")
    
    if examples_generated > 0:
        print("\n🎧 Reproducir ejemplos:")
        print(f"   aplay {output_dir}/*.wav 2>/dev/null || echo 'Instalar aplay'")
        print(f"   vlc {output_dir}/*.wav")
    
    # Estadísticas finales
    print("\n" + "=" * 70)
    print("ESTADÍSTICAS DEL SISTEMA")
    print("=" * 70)
    
    total_fillers = len(fillers._get_all_filler_texts())
    cached_fillers = len(list(fillers._cache_dir.glob("*.npy")))
    memory_cached = len(fillers._audio_cache)
    
    print(f"\n📊 Total fillers definidos: {total_fillers}")
    print(f"💾 Fillers en cache (disco): {cached_fillers}")
    print(f"🧠 Fillers en cache (memoria): {memory_cached}")
    print(f"📁 Directorio cache: {fillers._cache_dir}")
    
    print("\n" + "=" * 70)
    print("✅ EJEMPLO COMPLETADO")
    print("=" * 70)
    
    print("\n💡 USO EN PRODUCCIÓN:")
    print("""
    # En el loop de procesamiento de SARAi:
    
    from sarai_agi.audio import get_filler_system
    
    fillers = get_filler_system()
    
    # Antes de búsqueda web
    play_audio(fillers.get_thinking_filler())
    results = search_web(query)
    
    # Antes de API externa
    play_audio(fillers.get_waiting_filler())
    data = call_external_api()
    
    # Confirmar acción del usuario
    play_audio(fillers.get_confirming_filler())
    execute_command(action)
    """)


if __name__ == "__main__":
    main()
