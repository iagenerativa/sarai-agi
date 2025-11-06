#!/usr/bin/env python3
"""
Ejemplo de preprocesamiento de audio para STT + VAD.

Demuestra cómo convertir diferentes formatos de audio
a la configuración estándar requerida:
- 16,000 Hz (16 kHz)
- Mono (1 canal)
- PCM 16-bit / float32

Soporta: MP3, M4A, OGG, FLAC, WAV (cualquier frecuencia)
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from sarai_agi.audio import (
        VoskSTT,
        SherpaVAD,
        preprocess_audio,
        detect_sample_rate,
        is_audio_valid,
        normalize_audio
    )
    import numpy as np
    
    print("=" * 70)
    print("🎙️ EJEMPLO: Preprocesamiento de Audio para STT + VAD")
    print("=" * 70)
    
    # PASO 1: Generar audio de ejemplo con diferentes configuraciones
    print("\n📝 PASO 1: Generando archivos de audio de prueba...")
    
    import soundfile as sf
    
    # Audio 1: 44.1kHz estéreo (típico de música)
    print("   - Creando audio_44k_stereo.wav (44.1kHz, estéreo)")
    sr_high = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr_high * duration))
    tone = np.sin(2 * np.pi * 200 * t) * 0.3
    stereo = np.column_stack([tone, tone * 0.8])  # Estéreo
    sf.write('/tmp/audio_44k_stereo.wav', stereo, sr_high)
    
    # Audio 2: 8kHz mono (típico de telefonía)
    print("   - Creando audio_8k_mono.wav (8kHz, mono)")
    sr_low = 8000
    t_low = np.linspace(0, duration, int(sr_low * duration))
    tone_low = np.sin(2 * np.pi * 150 * t_low) * 0.5
    sf.write('/tmp/audio_8k_mono.wav', tone_low, sr_low)
    
    # Audio 3: 16kHz mono (formato correcto)
    print("   - Creando audio_16k_mono.wav (16kHz, mono) ✅")
    sr_correct = 16000
    t_correct = np.linspace(0, duration, int(sr_correct * duration))
    tone_correct = np.sin(2 * np.pi * 180 * t_correct) * 0.6
    sf.write('/tmp/audio_16k_mono.wav', tone_correct, sr_correct)
    
    print("   ✅ 3 archivos de prueba creados en /tmp/")
    
    # PASO 2: Detectar sample rate de cada archivo
    print("\n📊 PASO 2: Detectando configuración de archivos...")
    
    for filename in ['audio_44k_stereo.wav', 'audio_8k_mono.wav', 'audio_16k_mono.wav']:
        filepath = f'/tmp/{filename}'
        sr = detect_sample_rate(filepath)
        info = sf.info(filepath)
        print(f"   - {filename}:")
        print(f"     Sample rate: {sr}Hz, Canales: {info.channels}, Duración: {info.duration:.2f}s")
    
    # PASO 3: Preprocesar cada archivo a formato estándar
    print("\n🔧 PASO 3: Preprocesando a formato estándar (16kHz mono float32)...")
    
    for filename in ['audio_44k_stereo.wav', 'audio_8k_mono.wav', 'audio_16k_mono.wav']:
        filepath = f'/tmp/{filename}'
        
        print(f"\n   Procesando: {filename}")
        
        # Preprocesar
        audio, sr = preprocess_audio(
            filepath,
            target_sr=16000,
            target_channels=1,
            target_dtype='float32'
        )
        
        print(f"   ✅ Resultado: {len(audio)} samples @ {sr}Hz")
        print(f"      Tipo: {audio.dtype}, Shape: {audio.shape}, Min: {audio.min():.3f}, Max: {audio.max():.3f}")
        
        # Validar
        is_valid = is_audio_valid(audio, sr, min_duration_ms=100)
        print(f"      Válido para STT/VAD: {'✅ SÍ' if is_valid else '❌ NO'}")
        
        # Normalizar (opcional)
        normalized = normalize_audio(audio, target_level=0.7)
        print(f"      Normalizado: Max={np.max(np.abs(normalized)):.3f} (target=0.7)")
    
    # PASO 4: Usar con Vosk STT
    print("\n🎤 PASO 4: Probando con Vosk STT...")
    
    # Preprocesar y transcribir
    audio, sr = preprocess_audio('/tmp/audio_44k_stereo.wav')
    
    # Guardar versión preprocesada
    sf.write('/tmp/audio_preprocessed.wav', audio, sr, subtype='PCM_16')
    print(f"   ✅ Audio preprocesado guardado: /tmp/audio_preprocessed.wav")
    
    # Inicializar STT
    stt = VoskSTT()
    if stt.is_available():
        result = stt.transcribe_file('/tmp/audio_preprocessed.wav')
        print(f"   📝 Transcripción: {result}")
    else:
        print("   ⚠️  Vosk STT no disponible (modelo no cargado)")
    
    # PASO 5: Usar con Sherpa VAD
    print("\n🔊 PASO 5: Probando con Sherpa VAD...")
    
    vad = SherpaVAD()
    if vad.is_available():
        segments = vad.detect_segments(audio)
        print(f"   🎯 Segmentos detectados: {len(segments)}")
        for i, (start, end) in enumerate(segments):
            print(f"      - Segmento {i+1}: {start:.3f}s - {end:.3f}s")
        
        if len(segments) == 0:
            print("   ⚠️  No se detectaron segmentos (audio sintético, no voz real)")
    else:
        print("   ⚠️  Sherpa VAD no disponible (modelo no cargado)")
    
    # RESUMEN
    print("\n" + "=" * 70)
    print("✅ RESUMEN DE CAPACIDADES")
    print("=" * 70)
    print("""
Formatos soportados para conversión automática:
  ✅ WAV (cualquier sample rate: 8kHz, 22.05kHz, 44.1kHz, 48kHz → 16kHz)
  ✅ MP3 (requiere librosa o ffmpeg)
  ✅ M4A (requiere librosa)
  ✅ OGG, FLAC (requiere soundfile)
  ✅ Estéreo → Mono (promedio de canales)
  ✅ int16 ↔ float32 (conversión automática)

Herramientas de preprocesamiento:
  ✅ preprocess_audio()    - Conversión completa a formato estándar
  ✅ detect_sample_rate()  - Detectar frecuencia de muestreo
  ✅ is_audio_valid()      - Validar duración y contenido
  ✅ normalize_audio()     - Normalizar volumen
  ✅ convert_to_pcm16()    - Convertir a bytes PCM 16-bit

Configuración estándar para STT/VAD:
  - Frecuencia: 16,000 Hz (16 kHz)
  - Canales: Mono (1 canal)
  - Formato: PCM sin comprimir
  - Tipo: float32 (VAD) o int16 (STT)
  - Profundidad: 16 bits

Instalación de dependencias opcionales:
  pip install librosa      # Soporte completo (MP3, M4A, resample)
  pip install soundfile    # Básico (WAV, OGG, FLAC)
""")
    
    print("=" * 70)
    print("🎉 EJEMPLO COMPLETADO")
    print("=" * 70)

except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("\nDependencias requeridas:")
    print("  pip install soundfile librosa")
    sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
