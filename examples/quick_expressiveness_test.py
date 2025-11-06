"""
Test rápido de expresividad de MeloTTS.

Genera 3 archivos WAV con diferentes niveles de expresividad
para comparación auditiva inmediata.

Uso:
    python3 quick_expressiveness_test.py
    aplay /tmp/melotts_*.wav
"""

import sys
from pathlib import Path

# Intentar import directo de melo
try:
    from melo.api import TTS
    MELO_AVAILABLE = True
except ImportError:
    MELO_AVAILABLE = False
    print("❌ MeloTTS no está disponible")
    print("Instalar: cd models/MeloTTS && pip install -e .")
    sys.exit(1)


def main():
    """Test rápido de 3 estilos."""
    
    print("=" * 70)
    print("MELOTTS - TEST RÁPIDO DE EXPRESIVIDAD")
    print("=" * 70)
    
    # Inicializar
    print("\n🔄 Cargando modelo español...")
    model = TTS(language='ES', device='cpu')
    print("✅ Modelo cargado\n")
    
    speaker_id = model.hps.data.spk2id['ES']
    
    # Texto de prueba
    text = "Hola, soy SARAi, tu asistente de inteligencia artificial. ¿En qué puedo ayudarte hoy?"
    
    # 1. Normal (1.2x, expresiva - default SARAi)
    print("1️⃣  NORMAL (1.2x, expresiva - default SARAi)")
    print(f"   Texto: {text}")
    print("   Parámetros: speed=1.2, sdp=0.2, noise=0.6, noise_w=0.8")
    model.tts_to_file(
        text, speaker_id, '/tmp/melotts_normal.wav',
        speed=1.2, sdp_ratio=0.2, noise_scale=0.6, noise_scale_w=0.8
    )
    print("   ✅ /tmp/melotts_normal.wav\n")
    
    # 2. Muy expresiva (emocional)
    text_expresivo = "¡Hola! ¡Qué alegría verte! ¿Cómo estás? ¿Necesitas ayuda?"
    print("2️⃣  MUY EXPRESIVA (1.3x, emocional)")
    print(f"   Texto: {text_expresivo}")
    print("   Parámetros: speed=1.3, sdp=0.3, noise=0.8, noise_w=0.9")
    model.tts_to_file(
        text_expresivo, speaker_id, '/tmp/melotts_expresivo.wav',
        speed=1.3, sdp_ratio=0.3, noise_scale=0.8, noise_scale_w=0.9
    )
    print("   ✅ /tmp/melotts_expresivo.wav\n")
    
    # 3. Monótona (robot)
    text_monotono = "El sistema está funcionando correctamente. Todos los parámetros están dentro del rango esperado."
    print("3️⃣  MONÓTONA (1.0x, robot-like)")
    print(f"   Texto: {text_monotono}")
    print("   Parámetros: speed=1.0, sdp=0.1, noise=0.2, noise_w=0.3")
    model.tts_to_file(
        text_monotono, speaker_id, '/tmp/melotts_monotono.wav',
        speed=1.0, sdp_ratio=0.1, noise_scale=0.2, noise_scale_w=0.3
    )
    print("   ✅ /tmp/melotts_monotono.wav\n")
    
    print("=" * 70)
    print("✅ 3 ARCHIVOS GENERADOS")
    print("=" * 70)
    print("\n🎧 Escucha las diferencias:")
    print("   aplay /tmp/melotts_normal.wav      # Default SARAi (expresiva)")
    print("   aplay /tmp/melotts_expresivo.wav   # Muy emocional")
    print("   aplay /tmp/melotts_monotono.wav    # Robot-like")
    print("\n   # O todos a la vez:")
    print("   aplay /tmp/melotts_*.wav")
    print("   vlc /tmp/melotts_*.wav")


if __name__ == "__main__":
    main()
