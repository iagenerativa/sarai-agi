"""
TRM Pipeline Integration - v3.7.0

Integrates TRM system components into SARAi pipeline:
- LoRA Router: Query type classification
- Template Manager: Instant responses
- Latency Predictor: Adaptive filler selection
- Expressive Modulator: SSML prosody
- Mirror Feedback: Real-time updates
- Unknown Handler: Out-of-domain detection

Version: v3.7.0
LOC: ~150
Author: SARAi Development Team
Date: 2025-11-05
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

from ..routing.lora_router import LoRARouter, QueryType, Route
from ..routing.latency_predictor import EWMALatencyPredictor
from ..routing.unknown_handler import UnknownHandler
from ..trm.template_manager import TemplateResponseManager
from ..tts.expressive_modulator import ExpressiveModulator
from ..feedback.mirror_feedback import MirrorFeedbackSystem

logger = logging.getLogger(__name__)


class TRMPipelineIntegration:
    """
    TRM system integration into SARAi pipeline.
    
    Workflow:
    1. Unknown detection → Handle or proceed
    2. LoRA routing → TRM or LLM
    3. If TRM: instant template response
    4. If LLM: predict latency → select filler → generate
    5. Add SSML prosody
    6. Stream feedback during generation
    
    Features:
    - 40ms response for closed_simple queries (TRM)
    - 1.5-4s response for closed_complex (LLM HIGH)
    - 3-5s response for open queries (LLM NORMAL)
    - Real-time feedback (progress, confidence)
    
    Usage:
        >>> trm = TRMPipelineIntegration()
        >>> result = await trm.process("hola")
        >>> print(result['response'])  # "Hola. ¿En qué puedo ayudarte?"
        >>> print(result['latency_ms'])  # ~40ms
    """
    
    def __init__(
        self,
        lang: str = 'es',
        knowledge_cutoff_year: int = 2023,
        enable_rag_fallback: bool = True,
        enable_feedback: bool = True
    ):
        """
        Initialize TRM pipeline integration.
        
        Args:
            lang: Language code
            knowledge_cutoff_year: Knowledge cutoff year
            enable_rag_fallback: Enable RAG for unknown queries
            enable_feedback: Enable mirror feedback
        """
        # Components
        self.router = LoRARouter(lang=lang)
        self.template_manager = TemplateResponseManager(lang=lang)
        self.latency_predictor = EWMALatencyPredictor()
        self.unknown_handler = UnknownHandler(
            knowledge_cutoff_year=knowledge_cutoff_year,
            enable_rag_fallback=enable_rag_fallback
        )
        self.expressive_modulator = ExpressiveModulator()
        
        # Feedback system (optional)
        self.feedback_system = MirrorFeedbackSystem() if enable_feedback else None
        
        # Stats
        self.total_requests = 0
        self.trm_hits = 0
        self.llm_calls = 0
        self.unknown_detected = 0
    
    async def process(
        self,
        text: str,
        context: Optional[list] = None,
        llm_generator: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Process query through TRM pipeline.
        
        Args:
            text: User query
            context: Conversation context
            llm_generator: LLM generator function (if None, returns template only)
        
        Returns:
            Dict with response, latency, metadata
        """
        start_time = time.time()
        self.total_requests += 1
        
        result = {
            'response': '',
            'latency_ms': 0,
            'route': '',
            'query_type': '',
            'filler_type': None,
            'ssml': '',
            'metadata': {}
        }
        
        # Step 1: Unknown detection
        unknown_detection = self.unknown_handler.detect(text, context)
        
        if unknown_detection.is_unknown and unknown_detection.suggested_action == 'refuse':
            # Refuse private info
            self.unknown_detected += 1
            result['response'] = self.unknown_handler.format_response(unknown_detection, include_rag_link=False)
            result['route'] = 'REFUSED'
            result['latency_ms'] = (time.time() - start_time) * 1000
            return result
        
        # Step 2: LoRA routing
        routing_decision = self.router.route(text, context)
        result['route'] = routing_decision.route.value
        result['query_type'] = routing_decision.query_type.value
        
        # Step 3A: TRM path (closed_simple)
        if routing_decision.route == Route.TRM:
            self.trm_hits += 1
            
            # Try template match
            template_result = self.template_manager.match(text)
            
            if template_result:
                result['response'] = template_result['text']
                result['latency_ms'] = template_result['latency_ms']
                result['metadata']['template_id'] = template_result['template_id']
                
                # Add SSML
                result['ssml'] = self.expressive_modulator.add_prosody(
                    template_result['text'],
                    context='neutral'
                )
                
                return result
            
            else:
                # No template match, fallback to LLM
                logger.warning(f"TRM miss for: {text[:50]}")
                routing_decision.route = Route.LLM
        
        # Step 3B: LLM path (closed_complex or open)
        if routing_decision.route == Route.LLM:
            self.llm_calls += 1
            
            # Extract features
            features = self.latency_predictor.extract_features(text, context)
            
            # Predict latency
            prediction = self.latency_predictor.predict(features)
            result['filler_type'] = prediction.filler_type.value
            result['metadata']['predicted_latency'] = prediction.predicted_latency
            
            # Send initial feedback
            if self.feedback_system:
                self.feedback_system.send_status('thinking', force=True)
                self.feedback_system.send_progress(0, force=True)
                self.feedback_system.send_confidence(prediction.confidence)
            
            # Generate response (if LLM available)
            if llm_generator:
                generation_start = time.time()
                
                # Call LLM
                llm_response = await llm_generator(text, context) if asyncio.iscoroutinefunction(llm_generator) else llm_generator(text, context)
                
                generation_time = time.time() - generation_start
                
                # Update latency predictor
                self.latency_predictor.update(features, generation_time)
                
                result['response'] = llm_response
                result['metadata']['generation_ms'] = generation_time * 1000
                
                # Send completion feedback
                if self.feedback_system:
                    self.feedback_system.send_progress(100, force=True)
                    self.feedback_system.send_status('done', force=True)
            
            else:
                # No LLM, return placeholder
                result['response'] = f"[LLM would generate response for: {text[:50]}...]"
            
            # Add SSML
            if result['response']:
                context_emotion = 'neutral'
                if routing_decision.query_type == QueryType.OPEN:
                    context_emotion = 'neutral'
                
                result['ssml'] = self.expressive_modulator.add_prosody(
                    result['response'],
                    context=context_emotion
                )
        
        # Final latency
        result['latency_ms'] = (time.time() - start_time) * 1000
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            'total_requests': self.total_requests,
            'trm_hits': self.trm_hits,
            'trm_hit_rate': self.trm_hits / max(self.total_requests, 1),
            'llm_calls': self.llm_calls,
            'unknown_detected': self.unknown_detected,
            'latency_predictor': self.latency_predictor.get_stats(),
        }


if __name__ == "__main__":
    print("=" * 70)
    print("TRM Pipeline Integration Demo - v3.7.0")
    print("=" * 70)
    
    async def demo():
        # Create pipeline
        trm = TRMPipelineIntegration(lang='es', enable_feedback=False)
        
        # Mock LLM generator
        async def mock_llm(text, context):
            await asyncio.sleep(0.2)  # Simulate LLM latency
            return f"Respuesta generada para: {text}"
        
        # Test queries
        test_queries = [
            "hola",
            "gracias",
            "¿Cuál es la capital de Francia?",
            "Explícame la teoría de la relatividad",
            "¿Cuál es mi contraseña?",
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} queries:")
        print("=" * 70)
        
        for query in test_queries:
            result = await trm.process(query, llm_generator=mock_llm)
            
            print(f"\n📝 '{query}'")
            print(f"   Route: {result['route']}")
            print(f"   Type: {result['query_type']}")
            print(f"   Latency: {result['latency_ms']:.2f}ms")
            print(f"   Filler: {result['filler_type'] or 'N/A'}")
            print(f"   Response: {result['response'][:60]}...")
        
        print("\n" + "=" * 70)
        print("📊 Pipeline statistics:")
        stats = trm.get_stats()
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"      {k}: {v:.2f}" if isinstance(v, float) else f"      {k}: {v}")
            else:
                print(f"   {key}: {value:.2f}" if isinstance(value, float) else f"   {key}: {value}")
        
        print("\n" + "=" * 70)
        print("✅ Demo completed!")
        print("=" * 70)
    
    # Run demo
    asyncio.run(demo())
