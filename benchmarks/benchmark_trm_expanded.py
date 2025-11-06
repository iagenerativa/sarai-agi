"""
Benchmark for expanded TRM templates (v3.7.0).

Tests accuracy with 51 templates across 6 categories.

Target: 95%+ accuracy on closed simple queries
Current: 15 templates → 84.2% accuracy (benchmark_trm.py)
Expected: 51 templates → 95%+ accuracy

Version: v3.7.0
Date: 2025-11-05
Author: SARAi Development Team
"""

import sys
sys.path.insert(0, 'src')

from sarai_agi.trm.template_manager import TemplateResponseManager
import time


def run_accuracy_benchmark():
    """Test TRM accuracy with comprehensive test set."""
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎯 TRM ACCURACY BENCHMARK (Expanded Templates)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    trm = TemplateResponseManager(lang='es')
    
    # Comprehensive test set covering all categories + variations
    test_cases = {
        # GREETINGS (15 variations)
        'hola': True,
        'buenos días': True,
        'buenas tardes': True,
        'buenas noches': True,
        'hey': True,
        'qué tal': True,
        'qué onda': True,
        'buenas': True,
        'hola de nuevo': True,
        'cómo va todo': True,
        'me alegro de verte': True,
        'encantado': True,
        'saludos': True,
        'buen día': True,
        'qué pasa': True,
        
        # CONFIRMATIONS (15 variations)
        'sí': True,
        'no': True,
        'vale': True,
        'ok': True,
        'claro': True,
        'correcto': True,
        'entiendo': True,
        'de acuerdo': True,
        'puede ser': True,
        'está bien': True,
        'eso mismo': True,
        'afirmativo': True,
        'exacto': True,
        'obvio': True,
        'dale': True,
        
        # THANKS (10 variations)
        'gracias': True,
        'muchas gracias': True,
        'te lo agradezco': True,
        'perfecto gracias': True,
        'eso es todo gracias': True,
        'aprecio tu ayuda': True,
        'gracias por todo': True,
        'muy amable': True,
        'mil gracias': True,
        'valoro tu ayuda': True,
        
        # FAREWELLS (12 variations)
        'adiós': True,
        'chau': True,
        'hasta luego': True,
        'nos vemos': True,
        'hasta pronto': True,
        'me voy': True,
        'bye': True,
        'buenas noches adiós': True,
        'hasta aquí': True,
        'nos vemos luego': True,
        'cuídate': True,
        'hasta mañana': True,
        
        # HELP (10 variations)
        'ayuda': True,
        'qué puedes hacer': True,
        'cómo funciona': True,
        'instrucciones': True,
        'no entiendo': True,
        'quién eres': True,
        'ejemplos': True,
        'cómo te llamas': True,
        'qué sabes hacer': True,
        'necesito ayuda': True,
        
        # STATUS (12 variations)
        'estás ahí': True,
        'me escuchas': True,
        'funciona': True,
        'cómo estás': True,
        'listo': True,
        'ocupado': True,
        'prueba': True,
        'puedes responder': True,
        'sigues ahí': True,
        'me oyes': True,
        'estás funcionando': True,
        'estás disponible': True,
        
        # NEGATIVE CASES (should NOT match - complex queries)
        'explícame la relatividad': False,
        'cuánto es 2 + 2': False,
        'busca información sobre python': False,
        'traduce hello al español': False,
        'cuál es la capital de Francia': False,
        'qué tiempo hace hoy': False,
        'resuelve esta ecuación': False,
        'genera código python': False,
    }
    
    print(f"\n📊 Testing {len(test_cases)} queries...")
    print(f"   ├─ Expected matches (closed simple): {sum(test_cases.values())}")
    print(f"   └─ Expected no-match (complex): {len(test_cases) - sum(test_cases.values())}\n")
    
    correct = 0
    total = len(test_cases)
    
    category_stats = {}
    latencies = []
    
    for query, should_match in test_cases.items():
        start = time.perf_counter()
        result = trm.match(query)
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)
        
        matched = result is not None
        is_correct = matched == should_match
        
        if is_correct:
            correct += 1
        
        # Track by category
        if matched and result:
            cat = result.get('category', 'unknown')
            if cat not in category_stats:
                category_stats[cat] = {'correct': 0, 'total': 0}
            category_stats[cat]['total'] += 1
            if is_correct:
                category_stats[cat]['correct'] += 1
        
        # Show failures
        if not is_correct:
            expected = "MATCH" if should_match else "NO MATCH"
            actual = "MATCH" if matched else "NO MATCH"
            print(f"   ❌ FAIL: \"{query}\" (expected {expected}, got {actual})")
    
    accuracy = (correct / total) * 100
    
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 RESULTS:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   Total queries:        {total}")
    print(f"   Correct:              {correct}")
    print(f"   Accuracy:             {accuracy:.1f}%")
    print(f"   Target:               95.0%")
    print(f"   Status:               {'✅ PASS' if accuracy >= 95.0 else '⚠️ NEEDS IMPROVEMENT'}")
    
    print("\n📋 Category Breakdown:")
    for cat in sorted(category_stats.keys()):
        stats = category_stats[cat]
        cat_acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"   {cat:15s}: {stats['correct']:2d}/{stats['total']:2d} ({cat_acc:5.1f}%)")
    
    print(f"\n⚡ Performance:")
    print(f"   Avg latency:          {sum(latencies)/len(latencies):.4f}ms")
    print(f"   P50 latency:          {sorted(latencies)[len(latencies)//2]:.4f}ms")
    print(f"   P95 latency:          {sorted(latencies)[int(len(latencies)*0.95)]:.4f}ms")
    print(f"   P99 latency:          {sorted(latencies)[int(len(latencies)*0.99)]:.4f}ms")
    print(f"   Max latency:          {max(latencies):.4f}ms")
    print(f"   Target:               <50ms")
    print(f"   Status:               {'✅ PASS' if max(latencies) < 50 else '❌ FAIL'}")
    
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return accuracy >= 95.0


if __name__ == '__main__':
    success = run_accuracy_benchmark()
    sys.exit(0 if success else 1)
