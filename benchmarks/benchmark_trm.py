"""
TRM Benchmark - Performance validation for Template Response Manager.

Validates:
- Response time <50ms
- Template match accuracy >95%
- Latency consistency

Version: v3.7.0
Author: SARAi Development Team
Date: 2025-11-05
"""

import sys
import time
import statistics
from typing import List, Dict

# Add src to path
sys.path.insert(0, '/home/noel/sarai-agi/src')

from sarai_agi.trm.template_manager import TemplateResponseManager


def benchmark_trm_latency(iterations: int = 1000) -> Dict:
    """
    Benchmark TRM response latency.
    
    Args:
        iterations: Number of test iterations
    
    Returns:
        Dict with benchmark results
    """
    print("=" * 70)
    print(f"TRM Latency Benchmark - {iterations} iterations")
    print("=" * 70)
    
    # Initialize TRM
    trm = TemplateResponseManager(lang='es')
    
    # Test queries (mix of matches and misses)
    test_queries = [
        "hola",
        "gracias",
        "¿cómo estás?",
        "adiós",
        "ayuda",
        "estado",
        "this should not match",
        "query muy larga que no va a matchear con nada",
    ]
    
    # Warmup
    for query in test_queries:
        trm.match(query)
    
    # Benchmark
    latencies_match = []
    latencies_miss = []
    
    print(f"\n🔥 Running {iterations} iterations...")
    
    start_total = time.time()
    
    for i in range(iterations):
        query = test_queries[i % len(test_queries)]
        
        start = time.time()
        result = trm.match(query)
        latency = (time.time() - start) * 1000  # ms
        
        if result:
            latencies_match.append(latency)
        else:
            latencies_miss.append(latency)
    
    total_time = time.time() - start_total
    
    # Calculate stats
    all_latencies = latencies_match + latencies_miss
    
    results = {
        'total_iterations': iterations,
        'total_time_sec': total_time,
        'throughput_qps': iterations / total_time,
        
        # Latency stats (all)
        'latency_p50_ms': statistics.median(all_latencies),
        'latency_p95_ms': statistics.quantiles(all_latencies, n=20)[18],  # 95th percentile
        'latency_p99_ms': statistics.quantiles(all_latencies, n=100)[98],  # 99th percentile
        'latency_mean_ms': statistics.mean(all_latencies),
        'latency_max_ms': max(all_latencies),
        
        # Match vs miss
        'matches': len(latencies_match),
        'misses': len(latencies_miss),
        'match_rate': len(latencies_match) / iterations,
        
        # Latency by type
        'match_p50_ms': statistics.median(latencies_match) if latencies_match else 0,
        'miss_p50_ms': statistics.median(latencies_miss) if latencies_miss else 0,
        
        # Target validation
        'target_50ms': max(all_latencies) < 50.0,
        'p99_under_10ms': statistics.quantiles(all_latencies, n=100)[98] < 10.0,
    }
    
    return results


def benchmark_template_accuracy() -> Dict:
    """
    Benchmark template match accuracy.
    
    Returns:
        Dict with accuracy results
    """
    print("\n" + "=" * 70)
    print("TRM Accuracy Benchmark")
    print("=" * 70)
    
    trm = TemplateResponseManager(lang='es')
    
    # Test cases (query, should_match, expected_category)
    test_cases = [
        ("hola", True, "greetings"),
        ("HOLA", True, "greetings"),
        ("  hola  ", True, "greetings"),
        ("buenos días", True, "greetings"),
        ("hey qué tal", True, "greetings"),
        
        ("gracias", True, "confirmations"),
        ("muchas gracias", True, "confirmations"),
        ("ok", True, "confirmations"),
        ("vale", True, "confirmations"),
        ("adiós", True, "confirmations"),
        
        ("ayuda", True, "help"),
        ("help", True, "help"),
        ("ayúdame", True, "help"),
        
        ("estado", True, "status"),
        ("status", True, "status"),
        
        # Should NOT match
        ("esto no debería matchear", False, None),
        ("query aleatoria sin sentido", False, None),
        ("12345", False, None),
        ("¿cuál es la capital de francia?", False, None),
    ]
    
    correct = 0
    total = len(test_cases)
    
    print(f"\n🔍 Testing {total} cases...")
    
    for query, should_match, expected_category in test_cases:
        result = trm.match(query)
        
        if should_match:
            # Should match
            if result and (expected_category is None or result['category'] == expected_category):
                correct += 1
            else:
                print(f"   ❌ MISS: '{query}' (expected {expected_category}, got {result['category'] if result else 'None'})")
        else:
            # Should NOT match
            if not result:
                correct += 1
            else:
                print(f"   ❌ FALSE POSITIVE: '{query}' matched {result['category']}")
    
    accuracy = correct / total
    
    results = {
        'total_cases': total,
        'correct': correct,
        'accuracy': accuracy,
        'target_95_percent': accuracy >= 0.95,
    }
    
    return results


def print_results(latency_results: Dict, accuracy_results: Dict):
    """Print benchmark results."""
    
    print("\n" + "=" * 70)
    print("📊 BENCHMARK RESULTS")
    print("=" * 70)
    
    print("\n🚀 LATENCY METRICS:")
    print(f"   Total iterations: {latency_results['total_iterations']}")
    print(f"   Total time: {latency_results['total_time_sec']:.2f}s")
    print(f"   Throughput: {latency_results['throughput_qps']:.0f} queries/sec")
    print(f"\n   Latency P50: {latency_results['latency_p50_ms']:.4f}ms")
    print(f"   Latency P95: {latency_results['latency_p95_ms']:.4f}ms")
    print(f"   Latency P99: {latency_results['latency_p99_ms']:.4f}ms")
    print(f"   Latency Mean: {latency_results['latency_mean_ms']:.4f}ms")
    print(f"   Latency Max: {latency_results['latency_max_ms']:.4f}ms")
    
    print(f"\n   Matches: {latency_results['matches']} ({latency_results['match_rate']*100:.1f}%)")
    print(f"   Misses: {latency_results['misses']}")
    print(f"   Match P50: {latency_results['match_p50_ms']:.4f}ms")
    print(f"   Miss P50: {latency_results['miss_p50_ms']:.4f}ms")
    
    # Validation
    print(f"\n   ✅ Target <50ms: {'PASS' if latency_results['target_50ms'] else 'FAIL'}")
    print(f"   ✅ P99 <10ms: {'PASS' if latency_results['p99_under_10ms'] else 'FAIL'}")
    
    print("\n🎯 ACCURACY METRICS:")
    print(f"   Total cases: {accuracy_results['total_cases']}")
    print(f"   Correct: {accuracy_results['correct']}")
    print(f"   Accuracy: {accuracy_results['accuracy']*100:.1f}%")
    print(f"   ✅ Target ≥95%: {'PASS' if accuracy_results['target_95_percent'] else 'FAIL'}")
    
    # Overall verdict
    all_pass = (
        latency_results['target_50ms'] and
        latency_results['p99_under_10ms'] and
        accuracy_results['target_95_percent']
    )
    
    print("\n" + "=" * 70)
    if all_pass:
        print("✅ ALL BENCHMARKS PASSED! 🎉")
    else:
        print("❌ SOME BENCHMARKS FAILED")
    print("=" * 70)


if __name__ == "__main__":
    print("=" * 70)
    print("TRM Performance Benchmark Suite - v3.7.0")
    print("=" * 70)
    
    # Run benchmarks
    latency_results = benchmark_trm_latency(iterations=1000)
    accuracy_results = benchmark_template_accuracy()
    
    # Print results
    print_results(latency_results, accuracy_results)
