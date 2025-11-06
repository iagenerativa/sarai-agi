"""
E2E Latency Benchmark - End-to-end TRM pipeline latency validation.

Validates complete pipeline latency:
- TRM path: <50ms
- LLM path: varies by complexity
- Overall P95 latency targets

Version: v3.7.0
Author: SARAi Development Team
Date: 2025-11-05
"""

import sys
import asyncio
import time
import statistics
from typing import List, Dict

sys.path.insert(0, '/home/noel/sarai-agi/src')

from sarai_agi.pipeline.trm_integration import TRMPipelineIntegration


async def mock_llm_generator(text: str, context):
    """Mock LLM with realistic latency."""
    import random
    
    # Simulate latency based on complexity
    word_count = len(text.split())
    
    if word_count < 10:
        base_latency = 1.5  # Fast queries
    elif word_count < 20:
        base_latency = 3.0  # Medium
    else:
        base_latency = 5.0  # Long
    
    # Add variance
    latency = base_latency + random.uniform(-0.5, 0.5)
    await asyncio.sleep(latency)
    
    return f"Generated response for: {text[:50]}..."


async def benchmark_e2e_latency(iterations: int = 100) -> Dict:
    """
    Benchmark end-to-end pipeline latency.
    
    Args:
        iterations: Number of test queries
    
    Returns:
        Dict with benchmark results
    """
    print("=" * 70)
    print(f"E2E Latency Benchmark - {iterations} queries")
    print("=" * 70)
    
    # Create pipeline
    trm = TRMPipelineIntegration(lang='es', enable_feedback=False)
    
    # Test queries (mix of TRM hits and LLM calls)
    test_queries = [
        # TRM hits (should be <50ms)
        "hola",
        "gracias",
        "adiós",
        "ok",
        "ayuda",
        
        # LLM calls - closed complex (1.5-2s target)
        "¿Cuál es la capital de Francia?",
        "¿Cuántos habitantes tiene Madrid?",
        "¿Qué es Python?",
        
        # LLM calls - open (3-5s target)
        "Explícame la teoría de la relatividad",
        "Cuéntame sobre la historia de Roma",
    ]
    
    latencies_trm = []
    latencies_llm_complex = []
    latencies_llm_open = []
    
    print(f"\n🚀 Running {iterations} queries...")
    
    for i in range(iterations):
        query = test_queries[i % len(test_queries)]
        
        result = await trm.process(query, llm_generator=mock_llm_generator)
        
        latency_ms = result['latency_ms']
        route = result['route']
        
        # Categorize
        if route == 'TRM':
            latencies_trm.append(latency_ms)
        elif result['query_type'] == 'closed_complex':
            latencies_llm_complex.append(latency_ms)
        elif result['query_type'] == 'open':
            latencies_llm_open.append(latency_ms)
        
        # Progress
        if (i + 1) % 20 == 0:
            print(f"   Processed {i+1}/{iterations}...")
    
    # Calculate stats
    all_latencies = latencies_trm + latencies_llm_complex + latencies_llm_open
    
    results = {
        'total_queries': iterations,
        
        # Overall
        'latency_p50_ms': statistics.median(all_latencies),
        'latency_p95_ms': statistics.quantiles(all_latencies, n=20)[18],
        'latency_p99_ms': statistics.quantiles(all_latencies, n=100)[98] if len(all_latencies) >= 100 else max(all_latencies),
        'latency_mean_ms': statistics.mean(all_latencies),
        
        # By route
        'trm_count': len(latencies_trm),
        'trm_p50_ms': statistics.median(latencies_trm) if latencies_trm else 0,
        'trm_p95_ms': statistics.quantiles(latencies_trm, n=20)[18] if len(latencies_trm) >= 20 else max(latencies_trm) if latencies_trm else 0,
        'trm_target_50ms': max(latencies_trm) < 50.0 if latencies_trm else True,
        
        'llm_complex_count': len(latencies_llm_complex),
        'llm_complex_p50_ms': statistics.median(latencies_llm_complex) if latencies_llm_complex else 0,
        'llm_complex_target_2s': statistics.median(latencies_llm_complex) < 2000 if latencies_llm_complex else True,
        
        'llm_open_count': len(latencies_llm_open),
        'llm_open_p50_ms': statistics.median(latencies_llm_open) if latencies_llm_open else 0,
        'llm_open_target_5s': statistics.median(latencies_llm_open) < 5000 if latencies_llm_open else True,
    }
    
    # Get TRM stats
    trm_stats = trm.get_stats()
    results['trm_hit_rate'] = trm_stats['trm_hit_rate']
    results['unknown_detected'] = trm_stats['unknown_detected']
    
    return results


def print_results(results: Dict):
    """Print benchmark results."""
    
    print("\n" + "=" * 70)
    print("📊 BENCHMARK RESULTS")
    print("=" * 70)
    
    print(f"\n🚀 OVERALL METRICS:")
    print(f"   Total queries: {results['total_queries']}")
    print(f"   Latency P50: {results['latency_p50_ms']:.2f}ms")
    print(f"   Latency P95: {results['latency_p95_ms']:.2f}ms")
    print(f"   Latency P99: {results['latency_p99_ms']:.2f}ms")
    print(f"   Latency Mean: {results['latency_mean_ms']:.2f}ms")
    
    print(f"\n🎯 TRM PATH ({results['trm_count']} queries):")
    print(f"   P50: {results['trm_p50_ms']:.2f}ms")
    print(f"   P95: {results['trm_p95_ms']:.2f}ms")
    print(f"   ✅ Target <50ms: {'PASS' if results['trm_target_50ms'] else 'FAIL'}")
    
    print(f"\n📈 LLM COMPLEX PATH ({results['llm_complex_count']} queries):")
    print(f"   P50: {results['llm_complex_p50_ms']:.0f}ms")
    print(f"   ✅ Target <2s: {'PASS' if results['llm_complex_target_2s'] else 'FAIL'}")
    
    print(f"\n📊 LLM OPEN PATH ({results['llm_open_count']} queries):")
    print(f"   P50: {results['llm_open_p50_ms']:.0f}ms")
    print(f"   ✅ Target <5s: {'PASS' if results['llm_open_target_5s'] else 'FAIL'}")
    
    print(f"\n💡 PIPELINE STATS:")
    print(f"   TRM hit rate: {results['trm_hit_rate']:.1%}")
    print(f"   Unknown detected: {results['unknown_detected']}")
    
    # Overall verdict
    all_pass = (
        results['trm_target_50ms'] and
        results['llm_complex_target_2s'] and
        results['llm_open_target_5s']
    )
    
    print("\n" + "=" * 70)
    if all_pass:
        print("✅ ALL LATENCY TARGETS MET! 🎉")
    else:
        print("❌ SOME LATENCY TARGETS NOT MET")
    print("=" * 70)


async def main():
    print("=" * 70)
    print("E2E Latency Benchmark Suite - v3.7.0")
    print("=" * 70)
    
    # Run benchmark
    results = await benchmark_e2e_latency(iterations=100)
    
    # Print results
    print_results(results)


if __name__ == "__main__":
    asyncio.run(main())
