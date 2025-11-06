#!/usr/bin/env python3
"""
Interactive Chat con SARAi - Análisis de Performance en Tiempo Real

Permite conversación natural con SARAi midiendo:
- Latencia de cada componente
- Cuellos de botella
- Uso de recursos
- Métricas de calidad

Usage:
    python3 interactive_chat.py
"""

import sys
sys.path.insert(0, 'src')

import time
import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from collections import deque
import psutil
import os

# SARAi Components
from sarai_agi.trm.template_manager import TemplateResponseManager
from sarai_agi.routing.unknown_handler import UnknownHandler

# TTS Engine - Piper (10x más rápido que MeloTTS)
try:
    from sarai_agi.audio.pipertts import PiperTTSAdapter as TTSEngine
    TTS_ENGINE_NAME = "Piper TTS"
except ImportError:
    print("⚠️  Piper TTS no disponible, usando MeloTTS como fallback")
    from sarai_agi.audio.melotts import MeloTTS as TTSEngine
    TTS_ENGINE_NAME = "MeloTTS (fallback)"


@dataclass
class PerformanceMetrics:
    """Métricas de performance de una respuesta."""
    query: str
    total_time: float = 0.0
    
    # Component timings
    trm_time: float = 0.0
    unknown_check_time: float = 0.0
    response_gen_time: float = 0.0
    tts_time: float = 0.0
    
    # Resource usage
    ram_before_mb: float = 0.0
    ram_after_mb: float = 0.0
    ram_delta_mb: float = 0.0
    
    # Response info
    response_text: str = ""
    response_length: int = 0
    audio_duration: float = 0.0
    audio_samples: int = 0
    
    # Classification
    is_template: bool = False
    is_unknown: bool = False
    route_taken: str = ""
    
    def get_bottleneck(self) -> str:
        """Identifica el cuello de botella principal."""
        timings = {
            'TRM': self.trm_time,
            'Unknown Check': self.unknown_check_time,
            'Response Gen': self.response_gen_time,
            'TTS': self.tts_time
        }
        
        max_component = max(timings.items(), key=lambda x: x[1])
        return f"{max_component[0]} ({max_component[1]:.3f}s)"
    
    def get_summary(self) -> str:
        """Resumen de métricas."""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ MÉTRICAS DE PERFORMANCE                                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Query: {self.query[:70]:<70} ║
║ Route: {self.route_taken:<70} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ TIMINGS (ms):                                                                ║
║   • TRM Classification:    {self.trm_time*1000:>8.2f} ms                                  ║
║   • Unknown Detection:     {self.unknown_check_time*1000:>8.2f} ms                                  ║
║   • Response Generation:   {self.response_gen_time*1000:>8.2f} ms                                  ║
║   • TTS Synthesis:         {self.tts_time*1000:>8.2f} ms                                  ║
║   ─────────────────────────────────────────────────────────────────────────  ║
║   • TOTAL:                 {self.total_time*1000:>8.2f} ms                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ BOTTLENECK: {self.get_bottleneck():<65} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ RECURSOS:                                                                    ║
║   • RAM Delta:             {self.ram_delta_mb:>8.2f} MB                                  ║
║   • Response Length:       {self.response_length:>8} chars                               ║
║   • Audio Duration:        {self.audio_duration:>8.2f} s                                    ║
║   • Audio Samples:         {self.audio_samples:>8} samples                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


@dataclass
class SessionStats:
    """Estadísticas acumuladas de la sesión."""
    queries: List[PerformanceMetrics] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    
    def add_query(self, metrics: PerformanceMetrics):
        """Agrega métricas de una query."""
        self.queries.append(metrics)
    
    def get_avg_timing(self, component: str) -> float:
        """Obtiene tiempo promedio de un componente."""
        if not self.queries:
            return 0.0
        
        timings = {
            'trm': [q.trm_time for q in self.queries],
            'unknown': [q.unknown_check_time for q in self.queries],
            'response': [q.response_gen_time for q in self.queries],
            'tts': [q.tts_time for q in self.queries],
            'total': [q.total_time for q in self.queries]
        }
        
        return sum(timings.get(component, [])) / len(self.queries) if self.queries else 0.0
    
    def get_bottleneck_summary(self) -> Dict[str, int]:
        """Cuenta cuántas veces cada componente fue el cuello de botella."""
        bottlenecks = {}
        for q in self.queries:
            component = q.get_bottleneck().split(' ')[0]
            bottlenecks[component] = bottlenecks.get(component, 0) + 1
        return bottlenecks
    
    def get_summary(self) -> str:
        """Resumen de la sesión completa."""
        if not self.queries:
            return "No hay queries registradas."
        
        session_duration = time.time() - self.start_time
        bottlenecks = self.get_bottleneck_summary()
        
        template_count = sum(1 for q in self.queries if q.is_template)
        unknown_count = sum(1 for q in self.queries if q.is_unknown)
        
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ RESUMEN DE SESIÓN                                                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Duración: {session_duration:>8.2f} segundos                                            ║
║ Queries:  {len(self.queries):>8} totales                                                 ║
║   • Templates:  {template_count:>5}                                                      ║
║   • Unknown:    {unknown_count:>5}                                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ TIEMPOS PROMEDIO (ms):                                                       ║
║   • TRM:              {self.get_avg_timing('trm')*1000:>8.2f} ms                                  ║
║   • Unknown Check:    {self.get_avg_timing('unknown')*1000:>8.2f} ms                                  ║
║   • Response Gen:     {self.get_avg_timing('response')*1000:>8.2f} ms                                  ║
║   • TTS:              {self.get_avg_timing('tts')*1000:>8.2f} ms                                  ║
║   • TOTAL:            {self.get_avg_timing('total')*1000:>8.2f} ms                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ CUELLOS DE BOTELLA (frecuencia):                                            ║
"""
        
        for component, count in sorted(bottlenecks.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.queries)) * 100
            summary += f"║   • {component:<15} {count:>3} veces ({percentage:>5.1f}%)                           ║\n"
        
        summary += "╚══════════════════════════════════════════════════════════════════════════════╝"
        
        return summary


class InteractiveSARAi:
    """Chat interactivo con SARAi con medición de performance."""
    
    def __init__(self, enable_tts: bool = True):
        """
        Inicializa el sistema interactivo.
        
        Args:
            enable_tts: Si True, genera audio (más lento). Si False, solo texto.
        """
        print("🚀 Inicializando SARAi Interactive Chat...")
        print("=" * 80)
        
        # Components
        self.trm = TemplateResponseManager()
        self.unknown_handler = UnknownHandler()
        self.tts = TTSEngine() if enable_tts else None
        self.enable_tts = enable_tts and (self.tts is not None)
        
        # Stats
        self.session_stats = SessionStats()
        
        # Info
        print(f"✅ TTS Engine: {TTS_ENGINE_NAME}")
        
        # Process info
        self.process = psutil.Process(os.getpid())
        
        print(f"✅ TRM: {self.trm} cargado")
        print(f"✅ Unknown Handler: Activo")
        print(f"{'✅' if self.enable_tts else '⚠️ '} TTS: {'Habilitado' if self.enable_tts else 'Deshabilitado (modo texto)'}")
        print("=" * 80)
    
    def get_ram_usage_mb(self) -> float:
        """Obtiene uso de RAM en MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def process_query(self, query: str, verbose: bool = True) -> PerformanceMetrics:
        """
        Procesa una query y mide performance.
        
        Args:
            query: Query del usuario
            verbose: Si True, muestra detalles en consola
            
        Returns:
            Métricas de performance
        """
        metrics = PerformanceMetrics(query=query)
        start_total = time.time()
        metrics.ram_before_mb = self.get_ram_usage_mb()
        
        # 1. TRM Classification
        start = time.time()
        template_result = self.trm.match(query)
        metrics.trm_time = time.time() - start
        metrics.is_template = template_result is not None
        
        if verbose:
            print(f"\n⏱️  TRM: {metrics.trm_time*1000:.2f}ms → {'✓ Template' if metrics.is_template else '✗ No template'}")
        
        # 2. Unknown Detection
        start = time.time()
        unknown_result = self.unknown_handler.detect(query)
        metrics.unknown_check_time = time.time() - start
        metrics.is_unknown = unknown_result.is_unknown if hasattr(unknown_result, 'is_unknown') else False
        
        if verbose:
            print(f"⏱️  Unknown: {metrics.unknown_check_time*1000:.2f}ms → {'⚠️  Unknown' if metrics.is_unknown else '✓ Known'}")
        
        # 3. Response Generation
        start = time.time()
        
        if metrics.is_template:
            response = template_result.get('response', template_result.get('text', 'Template response'))
            metrics.route_taken = f"Template ({template_result.get('category', 'unknown')})"
        elif metrics.is_unknown:
            response = "Lo siento, no puedo ayudarte con eso por razones de privacidad."
            metrics.route_taken = "Unknown (Privacy)"
        else:
            # Aquí iría el modelo LLM real
            response = f"Respuesta simulada para: {query}"
            metrics.route_taken = "LLM (Simulated)"
        
        metrics.response_gen_time = time.time() - start
        metrics.response_text = response
        metrics.response_length = len(response)
        
        if verbose:
            print(f"⏱️  Response: {metrics.response_gen_time*1000:.2f}ms → {len(response)} chars")
            print(f"💬 Respuesta: {response}")
        
        # 4. TTS Synthesis (opcional)
        if self.enable_tts:
            start = time.time()
            audio = self.tts.synthesize(response, speaker="ES", speed=1.0)
            metrics.tts_time = time.time() - start
            
            if audio is not None:
                metrics.audio_samples = len(audio)
                metrics.audio_duration = len(audio) / self.tts.get_sample_rate()
                
                if verbose:
                    print(f"⏱️  TTS: {metrics.tts_time*1000:.2f}ms → {metrics.audio_duration:.2f}s audio")
            else:
                if verbose:
                    print(f"⚠️  TTS: Falló la síntesis")
        else:
            if verbose:
                print(f"⏭️  TTS: Deshabilitado")
        
        # Final metrics
        metrics.total_time = time.time() - start_total
        metrics.ram_after_mb = self.get_ram_usage_mb()
        metrics.ram_delta_mb = metrics.ram_after_mb - metrics.ram_before_mb
        
        if verbose:
            print(f"\n⏱️  TOTAL: {metrics.total_time*1000:.2f}ms")
            print(f"🧠 RAM: {metrics.ram_delta_mb:+.2f}MB (now {metrics.ram_after_mb:.1f}MB)")
        
        return metrics
    
    def run(self):
        """Ejecuta el chat interactivo."""
        print("\n" + "=" * 80)
        print("🎯 SARAi Interactive Chat - Análisis de Performance")
        print("=" * 80)
        print("\nComandos:")
        print("  • Escribe tu mensaje para chatear")
        print("  • 'stats' - Ver estadísticas de la sesión")
        print("  • 'clear' - Limpiar estadísticas")
        print("  • 'tts on/off' - Habilitar/deshabilitar audio")
        print("  • 'quit' / 'exit' / 'q' - Salir")
        print("\n" + "=" * 80)
        
        query_count = 0
        
        while True:
            try:
                # Input
                query = input(f"\n🧑 Tú [{query_count}]: ").strip()
                
                if not query:
                    continue
                
                # Commands
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 ¡Hasta luego!")
                    break
                
                if query.lower() == 'stats':
                    print(self.session_stats.get_summary())
                    continue
                
                if query.lower() == 'clear':
                    self.session_stats = SessionStats()
                    query_count = 0
                    print("✅ Estadísticas limpiadas")
                    continue
                
                if query.lower() == 'tts on':
                    if self.tts and self.tts.is_available():
                        self.enable_tts = True
                        print("✅ TTS habilitado")
                    else:
                        print("⚠️  TTS no disponible")
                    continue
                
                if query.lower() == 'tts off':
                    self.enable_tts = False
                    print("✅ TTS deshabilitado")
                    continue
                
                # Process query
                print("\n" + "-" * 80)
                print(f"⚙️  Procesando...")
                
                metrics = self.process_query(query, verbose=True)
                self.session_stats.add_query(metrics)
                query_count += 1
                
                # Show bottleneck
                print(f"\n🔍 Cuello de botella: {metrics.get_bottleneck()}")
                print("-" * 80)
                
            except KeyboardInterrupt:
                print("\n\n👋 Sesión interrumpida")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        # Final summary
        if self.session_stats.queries:
            print("\n" + "=" * 80)
            print("📊 RESUMEN FINAL DE LA SESIÓN")
            print("=" * 80)
            print(self.session_stats.get_summary())


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Interactive chat con SARAi')
    parser.add_argument('--no-tts', action='store_true', help='Deshabilitar TTS (más rápido)')
    parser.add_argument('--benchmark', type=str, help='Ejecutar benchmark con queries de archivo')
    
    args = parser.parse_args()
    
    if args.benchmark:
        # Benchmark mode
        print(f"📊 Modo Benchmark: {args.benchmark}")
        chat = InteractiveSARAi(enable_tts=not args.no_tts)
        
        with open(args.benchmark, 'r') as f:
            queries = [line.strip() for line in f if line.strip()]
        
        print(f"Ejecutando {len(queries)} queries...")
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*80}\nQuery {i}/{len(queries)}: {query}")
            metrics = chat.process_query(query, verbose=True)
            chat.session_stats.add_query(metrics)
        
        print(chat.session_stats.get_summary())
    else:
        # Interactive mode
        chat = InteractiveSARAi(enable_tts=not args.no_tts)
        chat.run()


if __name__ == '__main__':
    main()
