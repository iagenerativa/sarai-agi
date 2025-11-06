"""
Ejemplo de uso de MeloTTS con diferentes niveles de expresividad.

Demuestra:
- Síntesis normal (expresiva y acelerada)
- Síntesis muy expresiva (emocional)
- Síntesis monótona (robot-like)
- Diferentes velocidades

Week 1 Day 3-4 | v3.8.0-dev
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sarai_agi.audio.melotts import MeloTTS


def main():
    """Ejemplo completo de MeloTTS con expresividad."""
    
    print("=" * 70)
    print("MeloTTS - Ejemplo de Expresividad y Velocidad")
    print("=" * 70)
    
    # Inicializar TTS (ya viene con configuración expresiva por defecto)
    print("\n1️⃣ Inicializando MeloTTS con configuración expresiva...")
    tts = MeloTTS()
    
    if not tts.is_available():
        print("❌ ERROR: MeloTTS no está disponible")
        print("Instalar: cd models && git clone https://github.com/myshell-ai/MeloTTS.git")
        print("         cd MeloTTS && pip install -e .")
        return
    
    print(f"✅ MeloTTS cargado: {tts.sample_rate}Hz, speakers: {tts.speakers}")
    
    # Textos de prueba
    textos = {
        "normal": "Hola, soy SARAi. ¿En qué puedo ayudarte hoy?",
        "emocional": "¡Hola! ¡Qué alegría verte! ¿Cómo estás? ¿Necesitas ayuda?",
        "técnico": "El sistema está funcionando correctamente. Todos los parámetros están dentro del rango esperado.",
        "pregunta": "¿Estás seguro de que quieres continuar con esta operación?",
    }
    
    output_dir = Path("/tmp/melotts_examples")
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "=" * 70)
    print("2️⃣ Síntesis NORMAL (configuración por defecto expresiva)")
    print("   speed=1.2x, sdp=0.2, noise=0.6, noise_w=0.8")
    print("=" * 70)
    
    for nombre, texto in textos.items():
        output_file = output_dir / f"{nombre}_normal.wav"
        print(f"\n📝 {nombre.upper()}: {texto}")
        
        success = tts.synthesize_to_file(texto, output_file)
        
        if success:
            print(f"✅ Generado: {output_file}")
        else:
            print(f"❌ Error generando {nombre}")
    
    print("\n" + "=" * 70)
    print("3️⃣ Síntesis MUY EXPRESIVA (emocional, variable)")
    print("   speed=1.3x, sdp=0.3, noise=0.8, noise_w=0.9")
    print("=" * 70)
    
    for nombre, texto in textos.items():
        output_file = output_dir / f"{nombre}_expresivo.wav"
        print(f"\n📝 {nombre.upper()}: {texto}")
        
        success = tts.synthesize_to_file(
            texto,
            output_file,
            speed=1.3,
            sdp_ratio=0.3,      # Más variabilidad prosódica
            noise_scale=0.8,    # Más variación de tono
            noise_scale_w=0.9   # Más variación de ritmo
        )
        
        if success:
            print(f"✅ Generado: {output_file}")
        else:
            print(f"❌ Error generando {nombre}")
    
    print("\n" + "=" * 70)
    print("4️⃣ Síntesis MONÓTONA (robot-like, uniforme)")
    print("   speed=1.0x, sdp=0.1, noise=0.2, noise_w=0.3")
    print("=" * 70)
    
    for nombre, texto in textos.items():
        output_file = output_dir / f"{nombre}_monotono.wav"
        print(f"\n📝 {nombre.upper()}: {texto}")
        
        success = tts.synthesize_to_file(
            texto,
            output_file,
            speed=1.0,
            sdp_ratio=0.1,      # Menos variabilidad
            noise_scale=0.2,    # Menos variación de tono
            noise_scale_w=0.3   # Menos variación de ritmo
        )
        
        if success:
            print(f"✅ Generado: {output_file}")
        else:
            print(f"❌ Error generando {nombre}")
    
    print("\n" + "=" * 70)
    print("5️⃣ Síntesis RÁPIDA (urgente, apresurada)")
    print("   speed=1.5x, sdp=0.2, noise=0.7, noise_w=0.7")
    print("=" * 70)
    
    texto_urgente = "¡Atención! Necesito que revises esto inmediatamente."
    output_file = output_dir / "urgente_rapido.wav"
    print(f"\n📝 URGENTE: {texto_urgente}")
    
    success = tts.synthesize_to_file(
        texto_urgente,
        output_file,
        speed=1.5,
        noise_scale=0.7,
        noise_scale_w=0.7
    )
    
    if success:
        print(f"✅ Generado: {output_file}")
    
    print("\n" + "=" * 70)
    print("6️⃣ Síntesis LENTA (calmada, reflexiva)")
    print("   speed=0.9x, sdp=0.2, noise=0.5, noise_w=0.6")
    print("=" * 70)
    
    texto_calmado = "Tómate tu tiempo. Piénsalo bien antes de decidir."
    output_file = output_dir / "calmado_lento.wav"
    print(f"\n📝 CALMADO: {texto_calmado}")
    
    success = tts.synthesize_to_file(
        texto_calmado,
        output_file,
        speed=0.9,
        noise_scale=0.5,
        noise_scale_w=0.6
    )
    
    if success:
        print(f"✅ Generado: {output_file}")
    
    print("\n" + "=" * 70)
    print("✅ TODOS LOS EJEMPLOS GENERADOS")
    print("=" * 70)
    print(f"\n📁 Archivos generados en: {output_dir}")
    print("\nComparación de estilos:")
    print("  • normal      → Expresiva y acelerada (default SARAi)")
    print("  • expresivo   → Muy emocional y variable")
    print("  • monotono    → Robot-like, uniforme")
    print("  • rapido      → Urgente, apresurado")
    print("  • lento       → Calmado, reflexivo")
    
    print("\n🎧 Reproduce los archivos para escuchar las diferencias:")
    print(f"   aplay {output_dir}/*.wav")
    print(f"   # o")
    print(f"   vlc {output_dir}/*.wav")


if __name__ == "__main__":
    main()
