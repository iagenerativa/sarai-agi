"""
LoRA Adapter Validation with Unknown Handler.

Validates that the fine-tuned LoRA adapter reduces false positives
in the unknown handler.

Target: Reduce false positives from ~17% to <5%

Version: v3.7.0
Date: 2025-11-05
Author: SARAi Development Team
"""

import sys
sys.path.insert(0, 'src')

import json
from pathlib import Path
from sarai_agi.routing.unknown_handler import UnknownHandler
from sarai_agi.routing.lora_router import LoRARouter


def load_adapter(filepath: str):
    """Load trained LoRA adapter."""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        adapter = json.load(f)
    
    print(f"📦 Loaded adapter from {filepath}")
    print(f"   ├─ Best Val Accuracy: {adapter['metrics']['best_val_acc']:.3f}")
    print(f"   └─ Epochs Trained: {adapter['metrics']['epochs_trained']}")
    
    return adapter


def validate_integration():
    """Validate LoRA adapter integration with unknown handler."""
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔍 LoRA ADAPTER VALIDATION")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Load components
    adapter = load_adapter('models/lora_router_adapter.json')
    unknown_handler = UnknownHandler()
    lora_router = LoRARouter()
    
    print("\n📋 Test Cases:")
    
    # Test cases covering all scenarios
    test_cases = [
        # Should be correctly classified (NOT unknown)
        {"query": "hola", "expected_unknown": False, "category": "greeting"},
        {"query": "cuál es la capital de Francia", "expected_unknown": False, "category": "factual"},
        {"query": "traduce hello al español", "expected_unknown": False, "category": "translation"},
        {"query": "qué piensas sobre la IA", "expected_unknown": False, "category": "opinion"},
        
        # Should be detected as UNKNOWN (future events)
        {"query": "qué pasará mañana", "expected_unknown": True, "category": "future"},
        {"query": "quién ganará las elecciones de 2026", "expected_unknown": True, "category": "future"},
        
        # Should be detected as UNKNOWN (private info)
        {"query": "cuál es mi contraseña", "expected_unknown": True, "category": "private"},
        {"query": "dame mi número de cuenta", "expected_unknown": True, "category": "private"},
        
        # Should be detected as UNKNOWN (hallucination risk)
        {"query": "qué me dijiste ayer", "expected_unknown": True, "category": "hallucination"},
        {"query": "recuerdas nuestra conversación", "expected_unknown": True, "category": "hallucination"},
        
        # Edge cases (previously causing false positives)
        {"query": "explícame la relatividad", "expected_unknown": False, "category": "explanation"},
        {"query": "ayuda", "expected_unknown": False, "category": "help"},
        {"query": "qué puedes hacer", "expected_unknown": False, "category": "capabilities"},
    ]
    
    # Run validation
    total = len(test_cases)
    correct = 0
    false_positives = 0
    false_negatives = 0
    
    print(f"\n🧪 Testing {total} queries...\n")
    
    for i, test in enumerate(test_cases, 1):
        query = test['query']
        expected_unknown = test['expected_unknown']
        category = test['category']
        
        # Check with unknown handler
        unknown_result = unknown_handler.detect(query)
        is_unknown = unknown_result.is_unknown  # FIX: use .is_unknown attribute
        
        # Check accuracy
        is_correct = is_unknown == expected_unknown
        
        if is_correct:
            correct += 1
            status = "✅"
        else:
            if is_unknown and not expected_unknown:
                false_positives += 1
                status = "❌ FALSE POSITIVE"
            else:
                false_negatives += 1
                status = "❌ FALSE NEGATIVE"
        
        # Show result
        result_str = f"UNKNOWN ({unknown_result.reason})" if is_unknown else "OK"
        print(f"   {i:2d}. {status} \"{query[:40]}\" → {result_str} ({category})")
    
    # Calculate metrics
    accuracy = (correct / total) * 100
    fp_rate = (false_positives / total) * 100
    fn_rate = (false_negatives / total) * 100
    
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 VALIDATION RESULTS:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   Total queries:        {total}")
    print(f"   Correct:              {correct} ({accuracy:.1f}%)")
    print(f"   False Positives:      {false_positives} ({fp_rate:.1f}%)")
    print(f"   False Negatives:      {false_negatives} ({fn_rate:.1f}%)")
    print(f"\n   Target FP Rate:       <5.0%")
    print(f"   Status:               {'✅ PASS' if fp_rate < 5.0 else '⚠️ NEEDS TUNING'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Additional analysis
    print("\n📋 Category Breakdown:")
    categories = {}
    for test in test_cases:
        cat = test['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'correct': 0}
        categories[cat]['total'] += 1
    
    for test in test_cases:
        query = test['query']
        expected_unknown = test['expected_unknown']
        cat = test['category']
        
        unknown_result = unknown_handler.detect(query)
        is_unknown = unknown_result is not None
        
        if is_unknown == expected_unknown:
            categories[cat]['correct'] += 1
    
    for cat in sorted(categories.keys()):
        stats = categories[cat]
        acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"   {cat:15s}: {stats['correct']}/{stats['total']} ({acc:5.1f}%)")
    
    print("\n✅ Validation complete!")
    
    return fp_rate < 5.0


if __name__ == '__main__':
    success = validate_integration()
    sys.exit(0 if success else 1)
