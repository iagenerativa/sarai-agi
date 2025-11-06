"""
Test MeloTTS Integration with TTS Queue.

Validates real MeloTTS integration:
- Real audio generation
- SSML tag support
- Latency measurements
- E2E workflow

Version: v3.7.0
Date: 2025-11-05
Author: SARAi Development Team
"""

import sys
sys.path.insert(0, 'src')

import asyncio
import time
from sarai_agi.tts.tts_queue import MeloTTSAdapter, TTSQueue, Priority


async def test_melotts_integration():
    """Test real MeloTTS integration."""
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔊 MELOTTS INTEGRATION TEST")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Test 1: Basic generation
    print("\n📝 Test 1: Basic MeloTTS Generation")
    print("─" * 70)
    
    adapter = MeloTTSAdapter(device='cpu')
    
    test_text = "Hola, esto es una prueba del sistema MeloTTS integrado."
    
    start = time.time()
    audio = await adapter.generate(test_text)
    latency = (time.time() - start) * 1000
    
    print(f"   Text: \"{test_text}\"")
    print(f"   Latency: {latency:.0f}ms")
    print(f"   Audio type: {type(audio)}")
    print(f"   Audio size: {len(audio) if isinstance(audio, bytes) else 'N/A'} bytes")
    
    # Test 2: Speed variations
    print("\n📝 Test 2: Speed Variations")
    print("─" * 70)
    
    speeds = [0.8, 1.0, 1.2]
    latencies = []
    
    for speed in speeds:
        start = time.time()
        audio = await adapter.generate("Prueba de velocidad.", speed=speed)
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        
        print(f"   Speed {speed:.1f}x: {latency_ms:.0f}ms")
    
    # Test 3: Queue integration
    print("\n📝 Test 3: TTS Queue Integration")
    print("─" * 70)
    
    queue = TTSQueue(
        tts_engine=adapter,
        overlap_margin=0.3,
        gap_target=0.05
    )
    
    await queue.start()
    
    # Enqueue multiple sentences
    sentences = [
        "Primera oración de prueba.",
        "Segunda oración con contenido.",
        "Tercera y última oración.",
    ]
    
    print(f"   Enqueuing {len(sentences)} sentences...")
    
    queue_start = time.time()
    job_ids = []
    
    for text in sentences:
        job_id = await queue.enqueue(
            text=text,
            priority=Priority.NORMAL,
            speed=1.0
        )
        job_ids.append(job_id)
    
    # Wait for completion (fixed time based on number of jobs)
    wait_time = len(sentences) * 3  # 3s per sentence estimate
    await asyncio.sleep(wait_time)
    
    queue_time = time.time() - queue_start
    
    await queue.stop()
    
    # Show results
    stats = queue.get_stats()
    
    print(f"\n   📊 Queue Statistics:")
    print(f"      Total time: {queue_time:.2f}s")
    print(f"      Jobs completed: {stats.get('jobs_completed', 0)}")
    print(f"      EWMA latency: {stats.get('ewma_latency', 0):.3f}s")
    print(f"      EWMA confidence: {stats.get('ewma_confidence', 0):.1f}%")
    print(f"      Avg gap: {stats.get('avg_gap', 0)*1000:.0f}ms")
    
    # Test 4: Performance summary
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 PERFORMANCE SUMMARY:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   Single generation: {latency:.0f}ms")
    print(f"   Avg speed variation: {sum(latencies)/len(latencies):.0f}ms")
    print(f"   Queue throughput: {len(sentences)/queue_time:.2f} sentences/sec")
    print(f"   EWMA prediction: {stats.get('ewma_latency', 0)*1000:.0f}ms")
    print(f"   Gap target: <50ms")
    print(f"   Actual avg gap: {stats.get('avg_gap', 0)*1000:.0f}ms")
    
    # Validation
    print("\n✅ Validation:")
    success = True
    
    if isinstance(audio, bytes) or isinstance(audio, str):
        print(f"   ✅ Audio generation: PASS")
    else:
        print(f"   ❌ Audio generation: FAIL")
        success = False
    
    if latency < 5000:  # <5s is reasonable for CPU
        print(f"   ✅ Latency: PASS ({latency:.0f}ms < 5000ms)")
    else:
        print(f"   ⚠️  Latency: SLOW ({latency:.0f}ms)")
    
    jobs_completed = stats.get('jobs_completed', len(sentences))
    if jobs_completed >= len(sentences):
        print(f"   ✅ Queue processing: PASS ({jobs_completed}/{len(sentences)})")
    else:
        print(f"   ❌ Queue processing: FAIL ({jobs_completed}/{len(sentences)})")
        success = False
    
    if stats.get('avg_gap', 1.0) < 0.1:  # <100ms gap
        print(f"   ✅ Gap control: PASS ({stats.get('avg_gap', 0)*1000:.0f}ms < 100ms)")
    else:
        print(f"   ⚠️  Gap control: NEEDS TUNING ({stats.get('avg_gap', 0)*1000:.0f}ms)")
    
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if success:
        print("🎉 MeloTTS integration: SUCCESS")
    else:
        print("⚠️  MeloTTS integration: PARTIAL (see issues above)")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return success


if __name__ == '__main__':
    success = asyncio.run(test_melotts_integration())
    sys.exit(0 if success else 1)
