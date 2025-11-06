#!/usr/bin/env python3.13
"""
Descargador de voces Piper TTS
Descarga automática desde HuggingFace
"""
import urllib.request
import json
from pathlib import Path

def download_voice(voice_name="es_ES-mls_9972-low"):
    """Descarga una voz de Piper desde HuggingFace"""
    
    output_dir = Path("models/piper")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # URL base HuggingFace
    base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/mls_9972/low"
    
    files = {
        "onnx": f"{voice_name}.onnx",
        "json": f"{voice_name}.onnx.json"
    }
    
    print(f"📥 Descargando voz: {voice_name}")
    print(f"   Destino: {output_dir}")
    
    for file_type, filename in files.items():
        url = f"{base_url}/{filename}"
        output_path = output_dir / filename
        
        print(f"\n🔄 Descargando {filename}...")
        print(f"   URL: {url}")
        
        try:
            urllib.request.urlretrieve(url, output_path)
            size = output_path.stat().st_size / (1024*1024)
            print(f"   ✅ Descargado: {size:.1f} MB")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    print(f"\n✅ Voz {voice_name} descargada correctamente")
    return True

if __name__ == "__main__":
    success = download_voice()
    if not success:
        print("\n⚠️  Método alternativo: Descarga manual")
        print("   1. Ve a: https://github.com/rhasspy/piper/blob/master/VOICES.md")
        print("   2. Busca una voz español (es_ES)")
        print("   3. Descarga .onnx y .onnx.json")
        print("   4. Guárdalos en models/piper/")
