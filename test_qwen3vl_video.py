#!/usr/bin/env python3
"""
Test Qwen3-VL:4B análisis de video real
Prueba con: https://www.youtube.com/shorts/2DPegb5QkEU
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sarai_agi.model.wrapper import get_model


async def test_video_analysis():
    """Test análisis de video con Qwen3-VL"""
    
    print("🎬 Iniciando análisis de video con Qwen3-VL:4B...")
    print("=" * 60)
    
    # URL del video
    video_url = "https://www.youtube.com/shorts/2DPegb5QkEU"
    
    # Obtener modelo Qwen3-VL
    print("\n📦 Cargando modelo Qwen3-VL:4B...")
    try:
        vision_model = get_model("qwen3_vl")
        print("✅ Modelo cargado exitosamente")
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return
    
    # Preparar prompt
    prompt = """Analiza este video de YouTube y describe:

1. ¿Qué está pasando en el video?
2. ¿Qué elementos visuales ves?
3. ¿Cuál es el tema o mensaje principal?
4. ¿Qué emociones transmite?

Responde en español de forma detallada."""
    
    # Preparar input multimodal
    multimodal_input = {
        "text": prompt,
        "video": video_url  # Qwen3-VL puede procesar URLs de video
    }
    
    print(f"\n🎥 Analizando video: {video_url}")
    print("\n⏳ Procesando... (esto puede tardar 10-30 segundos)")
    
    try:
        # Ejecutar análisis
        result = await asyncio.to_thread(
            vision_model.invoke,
            multimodal_input,
            {"max_tokens": 1024}
        )
        
        print("\n" + "=" * 60)
        print("📊 RESULTADO DEL ANÁLISIS:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error durante análisis: {e}")
        print(f"Tipo: {type(e).__name__}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_video_analysis())
