#!/usr/bin/env python3.13
"""
Test rápido de Piper TTS (Python 3.13)
Mide latencia y calidad de síntesis
Requiere: Python 3.13 con no-GIL para SARAi
"""
import time
import wave
import os
from pathlib import Path

def test_piper_basic():
    """Test básico de Piper TTS"""
    print("🔧 Probando Piper TTS...")
    print(f"   Python: {os.sys.version}")
    
    try:
        from piper import PiperVoice
        print("✅ Piper importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando Piper: {e}")
        return False
    
    # Buscar modelos disponibles
    models_dir = Path("models/piper")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    onnx_files = list(models_dir.glob("*.onnx"))
    
    if not onnx_files:
        print(f"\n⚠️  No hay modelos descargados en {models_dir}")
        print("\n📥 Para descargar un modelo español:")
        print("   1. Visita: https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_ES")
        print("   2. Descarga un modelo (recomendado: carlfm/medium)")
        print("\n   Ejemplo con wget:")
        print("   cd models/piper")
        print("   wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/medium/es_ES-carlfm-medium.onnx")
        print("   wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/medium/es_ES-carlfm-medium.onnx.json")
        print("\n   O descarga directa (más rápido):")
        print("   wget -O models/piper/es_ES-carlfm-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/medium/es_ES-carlfm-medium.onnx")
        print("   wget -O models/piper/es_ES-carlfm-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/medium/es_ES-carlfm-medium.onnx.json")
        return False
    
    model_path = onnx_files[0]
    print(f"✅ Modelo encontrado: {model_path.name}")
    
    # Cargar voz
    print("\n🔄 Cargando modelo...")
    start = time.time()
    try:
        voice = PiperVoice.load(str(model_path))
        load_time = time.time() - start
        print(f"✅ Modelo cargado en {load_time*1000:.0f}ms")
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return False
    
    # Test de síntesis
    test_texts = [
        "Hola. ¿En qué puedo ayudarte?",
        "Esta es una prueba de Piper TTS.",
        "SARAi está lista para conversar contigo."
    ]
    
    print("\n🎤 Probando síntesis de voz...")
    print("─" * 60)
    
    total_latency = 0
    total_audio_duration = 0
    
    for i, text in enumerate(test_texts, 1):
        output_file = f"test_piper_{i}.wav"
        
        print(f"\n{i}. Texto: '{text}'")
        print(f"   Longitud: {len(text)} chars")
        
        # Síntesis
        start = time.time()
        try:
            # Generar audio en memoria (stream de AudioChunks)
            audio_bytes = b''
            sample_rate = None
            for audio_chunk in voice.synthesize(text):
                audio_bytes += audio_chunk.audio_int16_bytes  # bytes del audio 16-bit
                if sample_rate is None:
                    sample_rate = audio_chunk.sample_rate
            
            latency = time.time() - start
            
            # Guardar a archivo WAV
            with wave.open(output_file, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate or 16000)
                wav_file.writeframes(audio_bytes)
            
            # Leer duración del audio
            with wave.open(output_file, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
            
            ratio = latency / duration if duration > 0 else 0
            
            print(f"   ⏱️  Latencia: {latency*1000:.0f}ms")
            print(f"   🎵 Duración audio: {duration:.2f}s")
            print(f"   📊 Ratio: {ratio:.2f}x real-time")
            
            if latency < 0.5:
                print(f"   ✅ MUY RÁPIDO (< 500ms)")
            elif latency < 1.0:
                print(f"   ✅ RÁPIDO (< 1s)")
            else:
                print(f"   ⚠️  Lento (> 1s)")
            
            total_latency += latency
            total_audio_duration += duration
            
            # Limpiar archivo
            os.remove(output_file)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    # Resumen
    print("\n" + "═" * 60)
    print("📊 RESUMEN DE RENDIMIENTO")
    print("═" * 60)
    
    avg_latency = total_latency / len(test_texts)
    avg_ratio = total_latency / total_audio_duration if total_audio_duration > 0 else 0
    
    print(f"Tests ejecutados: {len(test_texts)}")
    print(f"Latencia promedio: {avg_latency*1000:.0f}ms")
    print(f"Ratio promedio: {avg_ratio:.2f}x real-time")
    print(f"Audio total: {total_audio_duration:.2f}s")
    print(f"Tiempo total: {total_latency:.2f}s")
    
    print("\n🎯 OBJETIVO vs RESULTADO:")
    print(f"   Target latencia: < 300ms")
    print(f"   Actual: {avg_latency*1000:.0f}ms", end="")
    
    if avg_latency < 0.3:
        print(" ✅ OBJETIVO CUMPLIDO")
    elif avg_latency < 0.5:
        print(" ✅ MUY BUENO (< 500ms)")
    elif avg_latency < 1.0:
        print(" ⚠️  ACEPTABLE (< 1s)")
    else:
        print(" ❌ NECESITA OPTIMIZACIÓN")
    
    print(f"\n   Comparado con MeloTTS (1,900ms):")
    improvement = ((1.9 - avg_latency) / 1.9) * 100
    print(f"   Mejora: {improvement:.1f}% más rápido 🚀")
    
    return True

if __name__ == "__main__":
    success = test_piper_basic()
    if success:
        print("\n✅ Test completado exitosamente")
    else:
        print("\n⚠️  Test incompleto - revisar instrucciones arriba")
