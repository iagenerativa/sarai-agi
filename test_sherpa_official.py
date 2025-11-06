#!/usr/bin/env python3
"""
Test rápido de Sherpa-ONNX + TEN-VAD (método oficial).
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from sarai_agi.audio.sherpa_vad import SherpaVAD
    import numpy as np
    
    print("=" * 60)
    print("🎤 TEST: Sherpa-ONNX + TEN-VAD (Oficial)")
    print("=" * 60)
    
    # Inicializar VAD
    print("\n1. Inicializando SherpaVAD...")
    vad = SherpaVAD()
    
    if not vad.is_available():
        print("❌ VAD no disponible (falta modelo o deps)")
        sys.exit(1)
    
    print("✅ VAD inicializado correctamente")
    
    # Test 1: Detección en chunk sintético
    print("\n2. Test detección chunk (30ms silencio)...")
    silence_chunk = np.zeros(480, dtype=np.float32)  # 30ms @ 16kHz
    is_speech = vad.detect(silence_chunk)
    print(f"   Resultado: {'🗣️ VOZ' if is_speech else '🔇 SILENCIO'}")
    
    # Test 2: Detección en chunk con señal
    print("\n3. Test detección chunk (30ms señal aleatoria)...")
    noise_chunk = np.random.randn(480).astype(np.float32) * 0.1
    is_speech = vad.detect(noise_chunk)
    print(f"   Resultado: {'🗣️ VOZ' if is_speech else '🔇 SILENCIO'}")
    
    # Test 3: Detección de segmentos en audio sintético
    print("\n4. Test detección segmentos (2s audio)...")
    # 2 segundos de audio: 1s silencio + 0.5s ruido + 0.5s silencio
    audio_data = np.concatenate([
        np.zeros(16000, dtype=np.float32),  # 1s silencio
        np.random.randn(8000).astype(np.float32) * 0.3,  # 0.5s ruido
        np.zeros(8000, dtype=np.float32),  # 0.5s silencio
    ])
    
    segments = vad.detect_segments(audio_data)
    print(f"   Segmentos detectados: {len(segments)}")
    for i, (start, end) in enumerate(segments):
        print(f"   - Segmento {i+1}: {start:.2f}s - {end:.2f}s")
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)

except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("\nInstalación requerida:")
    print("  pip install sherpa-onnx soundfile numpy")
    sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
