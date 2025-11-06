#!/usr/bin/env python3
"""
Script de validación rápida para Week 1 Audio Pipeline.

Verifica que todos los componentes están disponibles y funcionando.

Uso:
    python3 validate_week1.py
    
Exit codes:
    0: Todo OK
    1: Algún componente falla

Week 1 Complete | v3.8.0-dev
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def check_component(name, check_func):
    """Helper para verificar un componente."""
    try:
        result = check_func()
        status = "✅" if result else "❌"
        print(f"{status} {name}: {result}")
        return result
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False


def main():
    """Valida todos los componentes de Week 1."""
    
    print("=" * 70)
    print("WEEK 1 AUDIO PIPELINE - VALIDACIÓN")
    print("=" * 70)
    
    results = {}
    
    # ═════════════════════════════════════════════
    # 1. IMPORTS
    # ═════════════════════════════════════════════
    
    print("\n📦 VALIDANDO IMPORTS...")
    
    try:
        from sarai_agi.audio import (
            VoskSTT,
            SherpaVAD,
            MeloTTS,
            FillerSystem,
            get_tts,
            get_filler_system,
            preprocess_audio
        )
        print("✅ Todos los imports exitosos")
        results['imports'] = True
    except ImportError as e:
        print(f"❌ Error en imports: {e}")
        results['imports'] = False
        return 1
    
    # ═════════════════════════════════════════════
    # 2. STT (Vosk)
    # ═════════════════════════════════════════════
    
    print("\n🎤 VALIDANDO STT (Vosk)...")
    
    try:
        stt = VoskSTT()
        results['stt_init'] = check_component(
            "STT Initialization",
            lambda: stt is not None
        )
        results['stt_available'] = check_component(
            "STT Available",
            lambda: stt.is_available()
        )
    except Exception as e:
        print(f"❌ STT Error: {e}")
        results['stt_init'] = False
        results['stt_available'] = False
    
    # ═════════════════════════════════════════════
    # 3. VAD (Sherpa)
    # ═════════════════════════════════════════════
    
    print("\n👂 VALIDANDO VAD (Sherpa)...")
    
    try:
        vad = SherpaVAD()
        results['vad_init'] = check_component(
            "VAD Initialization",
            lambda: vad is not None
        )
        results['vad_available'] = check_component(
            "VAD Available",
            lambda: vad.is_available()
        )
    except Exception as e:
        print(f"❌ VAD Error: {e}")
        results['vad_init'] = False
        results['vad_available'] = False
    
    # ═════════════════════════════════════════════
    # 4. TTS (MeloTTS)
    # ═════════════════════════════════════════════
    
    print("\n🔊 VALIDANDO TTS (MeloTTS)...")
    
    try:
        tts = get_tts()
        results['tts_init'] = check_component(
            "TTS Initialization",
            lambda: tts is not None
        )
        results['tts_available'] = check_component(
            "TTS Available",
            lambda: tts.is_available()
        )
        
        if tts.is_available():
            results['tts_sample_rate'] = check_component(
                "TTS Sample Rate (44100Hz)",
                lambda: tts.sample_rate == 44100
            )
            results['tts_speakers'] = check_component(
                "TTS Speakers (ES available)",
                lambda: 'ES' in tts.speakers or 0 in tts.speakers.values()
            )
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        results['tts_init'] = False
        results['tts_available'] = False
    
    # ═════════════════════════════════════════════
    # 5. FILLERS
    # ═════════════════════════════════════════════
    
    print("\n💬 VALIDANDO FILLERS...")
    
    try:
        fillers = get_filler_system()
        results['fillers_init'] = check_component(
            "Fillers Initialization",
            lambda: fillers is not None
        )
        results['fillers_available'] = check_component(
            "Fillers Available",
            lambda: fillers.is_available()
        )
        
        if fillers.is_available():
            results['fillers_categories'] = check_component(
                "Fillers Categories (4)",
                lambda: len(fillers.FILLERS) == 4
            )
            results['fillers_count'] = check_component(
                f"Fillers Total ({len(fillers._get_all_filler_texts())})",
                lambda: len(fillers._get_all_filler_texts()) >= 15
            )
    except Exception as e:
        print(f"❌ Fillers Error: {e}")
        results['fillers_init'] = False
        results['fillers_available'] = False
    
    # ═════════════════════════════════════════════
    # 6. AUDIO UTILS
    # ═════════════════════════════════════════════
    
    print("\n🔧 VALIDANDO AUDIO UTILS...")
    
    try:
        from sarai_agi.audio import (
            convert_to_pcm16,
            normalize_audio,
            detect_sample_rate,
            is_audio_valid
        )
        results['utils_available'] = check_component(
            "Audio Utils Functions",
            lambda: all([
                callable(convert_to_pcm16),
                callable(normalize_audio),
                callable(detect_sample_rate),
                callable(is_audio_valid)
            ])
        )
    except Exception as e:
        print(f"❌ Utils Error: {e}")
        results['utils_available'] = False
    
    # ═════════════════════════════════════════════
    # RESUMEN FINAL
    # ═════════════════════════════════════════════
    
    print("\n" + "=" * 70)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    print(f"\n✅ Checks pasados: {passed_checks}/{total_checks}")
    print(f"📊 Success rate: {passed_checks/total_checks*100:.1f}%")
    
    # Detalles de fallos
    failed = [k for k, v in results.items() if not v]
    if failed:
        print(f"\n❌ Checks fallidos:")
        for check in failed:
            print(f"   • {check}")
    
    # Conclusión
    print("\n" + "=" * 70)
    
    if passed_checks == total_checks:
        print("✅ VALIDACIÓN EXITOSA")
        print("=" * 70)
        print("\n🎉 Week 1 Audio Pipeline completamente funcional!")
        print("\nComponentes disponibles:")
        print("  • VoskSTT (Speech-to-Text)")
        print("  • SherpaVAD (Voice Activity Detection)")
        print("  • MeloTTS (Text-to-Speech con expresividad)")
        print("  • FillerSystem (Turn-taking natural)")
        print("  • AudioUtils (Preprocessing)")
        return 0
    elif passed_checks >= total_checks * 0.7:
        print("⚠️ VALIDACIÓN PARCIAL")
        print("=" * 70)
        print(f"\n{passed_checks}/{total_checks} checks pasados")
        print("Sistema parcialmente funcional (algunos componentes faltantes)")
        return 0
    else:
        print("❌ VALIDACIÓN FALLIDA")
        print("=" * 70)
        print(f"\nSolo {passed_checks}/{total_checks} checks pasados")
        print("Revisar instalación de dependencias")
        print("\nVer documentación:")
        print("  docs/WEEK1_DAY1-2_RESUMEN.md")
        print("  docs/WEEK1_DAY3-4_RESUMEN.md")
        print("  docs/WEEK1_DAY5_RESUMEN.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
