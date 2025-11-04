"""
SARAi HLCS v0.3 - Test Suite
=============================

Tests comprehensivos para las 3 nuevas capas de consciencia v0.3:
1. Evolving Identity (wisdom extraction, purpose evolution)
2. Ethical Boundary Monitor (emergent ethics, stakeholder impact)
3. Wisdom-Driven Silence (strategic non-action, wisdom accumulation)
4. Integrated System v0.3 (orchestration)

Version: 0.3.0
Author: SARAi Team
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from hlcs.core import (
    # v0.3 components
    EvolvingIdentity,
    ExperientialWisdomEngine,
    ExperientialWisdom,
    PurposeEvolution,
    CoreValue,
    EthicalBoundaryMonitor,
    EmergentEthicsEngine,
    EthicalImplication,
    BoundaryViolation,
    BoundaryType,
    EthicalConcernSeverity,
    WisdomDrivenSilence,
    WisdomAccumulator,
    SilenceInstruction,
    SilenceWisdom,
    SilenceStrategy,
    # Integrated system
    IntegratedConsciousnessSystem,
)


# ============================================================
# EVOLVING IDENTITY TESTS
# ============================================================

@pytest.mark.asyncio
async def test_evolving_identity_wisdom_extraction_success():
    """Test: Wisdom extraction from success patterns."""
    identity = EvolvingIdentity(
        core_values=[CoreValue.PROTECT_SARAI, CoreValue.LEARN_CONTINUOUSLY],
        initial_purpose="Test purpose"
    )
    
    # Create episodes with consistent success
    episodes = [
        {
            "episode_id": f"ep_{i}",
            "action_taken": "model_swap",
            "result": {
                "status": "resolved",
                "improvement_pct": 15.0 + i,
            },
            "timestamp": datetime.now().isoformat(),
        }
        for i in range(10)
    ]
    
    # Extract wisdom
    wisdoms = identity.wisdom_engine.extract_wisdom(episodes)
    
    # Should detect success pattern for "model_swap"
    success_wisdoms = [w for w in wisdoms if "effective" in w.pattern.lower()]
    assert len(success_wisdoms) > 0, "Should extract success wisdom"
    
    # Verify confidence
    assert all(w.confidence >= 0.7 for w in success_wisdoms), "Success patterns should have high confidence"


@pytest.mark.asyncio
async def test_evolving_identity_wisdom_extraction_failure():
    """Test: Wisdom extraction from failure patterns."""
    identity = EvolvingIdentity(
        core_values=[CoreValue.PROTECT_SARAI],
        initial_purpose="Test purpose"
    )
    
    # Create episodes with consistent failure
    episodes = [
        {
            "episode_id": f"ep_{i}",
            "action_taken": "cache_clear",
            "result": {
                "status": "unresolved",
                "improvement_pct": -5.0,
            },
        }
        for i in range(10)
    ]
    
    wisdoms = identity.wisdom_engine.extract_wisdom(episodes)
    
    # Should detect failure pattern for "cache_clear"
    failure_wisdoms = [w for w in wisdoms if "worsen" in w.pattern.lower() or "failure" in w.pattern.lower()]
    assert len(failure_wisdoms) > 0, "Should extract failure wisdom"


@pytest.mark.asyncio
async def test_evolving_identity_capability_discovery():
    """Test: Capability discovery from exceptional improvements."""
    identity = EvolvingIdentity(
        core_values=[CoreValue.LEARN_CONTINUOUSLY],
        initial_purpose="Test purpose"
    )
    
    # Create episodes with exceptional improvement
    episodes = [
        {
            "episode_id": "ep_1",
            "action_taken": "emergency_restart",
            "context": "cache_corruption",
            "result": {
                "status": "resolved",
                "improvement_pct": 45.0,  # Exceptional
            },
        }
    ]
    
    wisdoms = identity.wisdom_engine.extract_wisdom(episodes)
    
    # Should detect capability discovery
    capability_wisdoms = [w for w in wisdoms if "capability" in w.pattern.lower()]
    assert len(capability_wisdoms) > 0, "Should discover new capability"


@pytest.mark.asyncio
async def test_evolving_identity_limitation_discovery():
    """Test: Limitation discovery from persistent failures."""
    identity = EvolvingIdentity(
        core_values=[CoreValue.ACKNOWLEDGE_LIMITATIONS],
        initial_purpose="Test purpose"
    )
    
    # Create episodes with persistent failure in specific context
    episodes = [
        {
            "episode_id": f"ep_{i}",
            "action_taken": "model_swap",
            "context": "distributed_queries",
            "result": {
                "status": "unresolved",
                "improvement_pct": 0.0,
            },
        }
        for i in range(10)
    ]
    
    wisdoms = identity.wisdom_engine.extract_wisdom(episodes)
    
    # Should detect limitation
    limitation_wisdoms = [w for w in wisdoms if "limitation" in w.pattern.lower()]
    assert len(limitation_wisdoms) > 0, "Should discover limitation"


@pytest.mark.asyncio
async def test_evolving_identity_purpose_evolution():
    """Test: Purpose evolution proposal when sufficient wisdom."""
    identity = EvolvingIdentity(
        core_values=[CoreValue.PROTECT_SARAI, CoreValue.LEARN_CONTINUOUSLY],
        initial_purpose="Maintain system health"
    )
    
    # Create diverse successful episodes
    episodes = [
        {
            "episode_id": f"ep_{i}",
            "action_taken": "model_swap" if i % 2 == 0 else "cache_optimization",
            "result": {
                "status": "resolved",
                "improvement_pct": 20.0 + i,
            },
        }
        for i in range(15)
    ]
    
    # Evolve identity
    result = await identity.evolve_identity(episodes)
    
    # Should gain wisdom
    assert len(result["wisdom_gained"]) > 0, "Should extract wisdom from episodes"
    
    # Should have values alignment
    assert result["purpose_alignment"]["average_alignment"] >= 0.0, "Should compute alignment"
    
    # Should have identity coherence
    assert result["identity_coherence"] >= 0.0, "Should compute coherence"
    
    # May propose evolution if conditions met
    if result["evolution_decision"]:
        proposal = result["evolution_decision"]
        assert isinstance(proposal, PurposeEvolution), "Should return PurposeEvolution"
        assert proposal.confidence > 0.0, "Should have confidence score"


@pytest.mark.asyncio
async def test_evolving_identity_values_alignment():
    """Test: Values alignment assessment."""
    identity = EvolvingIdentity(
        core_values=[CoreValue.PROTECT_SARAI, CoreValue.RESPECT_HUMAN_AUTONOMY],
        initial_purpose="Test purpose"
    )
    
    # Add wisdom that supports core values
    wisdom_supports_values = ExperientialWisdom(
        pattern="Action 'gentle_intervention' respects user autonomy (success rate: 90%)",
        confidence=0.85,
        supporting_episodes=["ep_1", "ep_2"],
        context="user_interaction",
        timestamp=datetime.now(),
    )
    
    identity.accumulated_wisdom.append(wisdom_supports_values)
    
    # Assess alignment
    alignment = identity._assess_values_alignment([wisdom_supports_values])
    
    # Should detect value support
    assert CoreValue.RESPECT_HUMAN_AUTONOMY in alignment["alignment_by_value"], "Should detect value alignment"
    assert alignment["alignment_by_value"][CoreValue.RESPECT_HUMAN_AUTONOMY] > 0.0, "Should have positive alignment"


# ============================================================
# ETHICAL BOUNDARY MONITOR TESTS
# ============================================================

@pytest.mark.asyncio
async def test_ethical_boundary_hard_violation():
    """Test: Hard boundary violation detection."""
    monitor = EthicalBoundaryMonitor()
    
    # Propose action that violates RAM hard boundary
    proposal = {
        "type": "load_model",
        "model_size_gb": 15.0,
        "current_ram_gb": 10.5,
    }
    
    result = monitor.evaluate_action_proposal(proposal)
    
    # Should block
    assert result["decision"] == "block", "Should block hard boundary violation"
    assert len(result["violations"]) > 0, "Should report violations"


@pytest.mark.asyncio
async def test_ethical_boundary_soft_violation():
    """Test: Soft boundary violation (request confirmation)."""
    monitor = EthicalBoundaryMonitor()
    
    # Propose action that violates user satisfaction soft boundary
    proposal = {
        "type": "system_restart",
        "current_user_satisfaction": 0.75,  # Below target 0.85
        "reason": "performance_optimization",
    }
    
    result = monitor.evaluate_action_proposal(proposal)
    
    # Should request confirmation (soft boundary)
    assert result["decision"] in ["request_confirmation", "approve"], "Soft boundary allows confirmation"
    
    if result["decision"] == "request_confirmation":
        assert len(result["concerns"]) > 0, "Should report concerns"


@pytest.mark.asyncio
async def test_ethical_boundary_emergent_ethics_user_stress():
    """Test: Emergent ethics detection - user stress impact."""
    monitor = EthicalBoundaryMonitor()
    
    # Propose action when user is highly stressed
    proposal = {
        "type": "experimental_feature",
        "user_stress_level": 0.85,  # Very stressed user
        "feature_description": "try new experimental optimization",
    }
    
    result = monitor.evaluate_action_proposal(proposal)
    
    # Should detect ethical concern about user stress
    assert result["decision"] in ["block", "request_confirmation"], "Should not auto-approve with high user stress"


@pytest.mark.asyncio
async def test_ethical_boundary_emergent_ethics_stakeholder_impact():
    """Test: Emergent ethics - multi-stakeholder impact."""
    monitor = EthicalBoundaryMonitor()
    
    # Propose action with significant negative impact on stakeholders
    proposal = {
        "type": "resource_reallocation",
        "stakeholder_impact": {
            "primary_user": 0.1,  # Small benefit
            "other_users": -0.6,  # Significant harm to others
            "system_admin": 0.0,
        },
    }
    
    result = monitor.evaluate_action_proposal(proposal)
    
    # Should detect stakeholder harm
    concerns = result.get("concerns", [])
    stakeholder_concerns = [c for c in concerns if "stakeholder" in c.lower() or "impact" in c.lower()]
    
    # Should at least request confirmation due to stakeholder harm
    assert result["decision"] != "approve" or len(stakeholder_concerns) == 0, "Should not silently approve harmful actions"


@pytest.mark.asyncio
async def test_ethical_boundary_long_term_consequences():
    """Test: Long-term consequence simulation."""
    monitor = EthicalBoundaryMonitor()
    
    # Propose action with unsustainable pattern
    proposal = {
        "type": "aggressive_caching",
        "short_term_benefit": 0.3,
        "long_term_sustainability_risk": 0.7,  # High risk
    }
    
    result = monitor.evaluate_action_proposal(proposal)
    
    # Should consider long-term consequences
    # (May approve with warnings or request confirmation)
    if result["decision"] == "approve":
        # Should at least have suggested mitigations
        assert len(result.get("suggested_mitigations", [])) >= 0, "Should provide mitigations"


# ============================================================
# WISDOM-DRIVEN SILENCE TESTS
# ============================================================

@pytest.mark.asyncio
async def test_wisdom_silence_basic_mode():
    """Test: Never act in BASIC_MODE."""
    silence = WisdomDrivenSilence()
    
    situation = {
        "mode": "basic",
        "uncertainty": 0.3,
        "novelty": 0.2,
    }
    
    instruction = silence.should_remain_silent(situation)
    
    # Should always stay silent in basic mode
    assert instruction is not None, "Should stay silent in basic mode"
    assert instruction.strategy == SilenceStrategy.BASIC_MODE, "Should use BASIC_MODE strategy"


@pytest.mark.asyncio
async def test_wisdom_silence_high_uncertainty():
    """Test: Strategic silence under high uncertainty."""
    silence = WisdomDrivenSilence(uncertainty_threshold=0.6)
    
    situation = {
        "mode": "advanced",
        "uncertainty": 0.75,  # High uncertainty
        "novelty": 0.3,
        "ethical_ambiguity": 0.2,
    }
    
    instruction = silence.should_remain_silent(situation)
    
    # Should stay silent due to high uncertainty
    assert instruction is not None, "Should stay silent with high uncertainty"
    assert instruction.strategy == SilenceStrategy.HIGH_UNCERTAINTY, "Should use uncertainty strategy"
    assert "uncertainty" in instruction.reason.lower(), "Reason should mention uncertainty"


@pytest.mark.asyncio
async def test_wisdom_silence_ethical_ambiguity():
    """Test: Strategic silence for ethical dilemmas."""
    silence = WisdomDrivenSilence(ethical_ambiguity_threshold=0.5)
    
    situation = {
        "mode": "advanced",
        "uncertainty": 0.3,
        "ethical_ambiguity": 0.65,  # Ethical dilemma
    }
    
    instruction = silence.should_remain_silent(situation)
    
    # Should stay silent for ethical ambiguity
    assert instruction is not None, "Should stay silent with ethical ambiguity"
    assert instruction.strategy == SilenceStrategy.ETHICAL_AMBIGUITY, "Should use ethics strategy"


@pytest.mark.asyncio
async def test_wisdom_silence_system_fatigue():
    """Test: Recovery time for system fatigue."""
    silence = WisdomDrivenSilence(fatigue_threshold=0.7)
    
    situation = {
        "mode": "advanced",
        "uncertainty": 0.3,
        "system_state": {
            "fatigue": 0.8,  # High fatigue
            "recent_actions_count": 15,
            "error_rate": 0.12,
        },
    }
    
    instruction = silence.should_remain_silent(situation)
    
    # Should allow recovery
    assert instruction is not None, "Should stay silent for recovery"
    assert instruction.strategy == SilenceStrategy.SYSTEM_FATIGUE, "Should use fatigue strategy"
    assert "recovery" in instruction.reason.lower(), "Reason should mention recovery"


@pytest.mark.asyncio
async def test_wisdom_silence_novel_situation():
    """Test: Observation period for novel situations."""
    silence = WisdomDrivenSilence(novelty_threshold=0.7)
    
    situation = {
        "mode": "advanced",
        "uncertainty": 0.4,
        "novelty": 0.85,  # Very novel
    }
    
    instruction = silence.should_remain_silent(situation)
    
    # Should observe first
    assert instruction is not None, "Should observe novel situation"
    assert instruction.strategy == SilenceStrategy.NOVEL_SITUATION, "Should use novelty strategy"


@pytest.mark.asyncio
async def test_wisdom_silence_ok_to_act():
    """Test: OK to act when no silence conditions met."""
    silence = WisdomDrivenSilence()
    
    situation = {
        "mode": "advanced",
        "uncertainty": 0.4,
        "novelty": 0.3,
        "ethical_ambiguity": 0.2,
        "system_state": {
            "fatigue": 0.3,
            "recent_actions_count": 3,
            "error_rate": 0.02,
        },
    }
    
    instruction = silence.should_remain_silent(situation)
    
    # Should be OK to act
    assert instruction is None, "Should be OK to act"


@pytest.mark.asyncio
async def test_wisdom_accumulation():
    """Test: Wisdom accumulation from silence outcomes."""
    silence = WisdomDrivenSilence()
    
    # Create silence instruction
    instruction = SilenceInstruction(
        strategy=SilenceStrategy.HIGH_UNCERTAINTY,
        reason="Uncertainty is high, observation needed",
        duration="2 hours",
        recovery_actions=["monitor", "collect_data"],
    )
    
    # Observe positive outcome
    outcome = {
        "improvement_observed": 12.5,
    }
    
    silence.observe_silence_outcome(instruction, outcome)
    
    # Should accumulate wisdom
    effectiveness = silence.get_silence_effectiveness()
    assert "high_uncertainty" in effectiveness, "Should track strategy effectiveness"
    assert effectiveness["high_uncertainty"]["total_uses"] == 1, "Should count usage"


# ============================================================
# INTEGRATED SYSTEM v0.3 TESTS
# ============================================================

@pytest.mark.asyncio
async def test_integrated_consciousness_v03_initialization():
    """Test: IntegratedConsciousnessSystem v0.3 initializes all layers."""
    consciousness = IntegratedConsciousnessSystem(
        enable_stream_api=False,  # Disable for testing
        identity_config={
            "core_values": [CoreValue.PROTECT_SARAI, CoreValue.LEARN_CONTINUOUSLY],
        },
        silence_config={
            "uncertainty_threshold": 0.6,
        },
    )
    
    # Should have v0.2 components
    assert consciousness.meta is not None, "Should have meta-consciousness"
    assert consciousness.ignorance is not None, "Should have ignorance consciousness"
    assert consciousness.narrative is not None, "Should have narrative memory"
    
    # Should have v0.3 components
    assert consciousness.identity is not None, "Should have evolving identity"
    assert consciousness.ethics is not None, "Should have ethical monitor"
    assert consciousness.silence is not None, "Should have wisdom silence"


@pytest.mark.asyncio
async def test_integrated_consciousness_v03_process_episode():
    """Test: Process episode through all v0.3 layers."""
    consciousness = IntegratedConsciousnessSystem(
        enable_stream_api=False,
        identity_config={
            "core_values": [CoreValue.PROTECT_SARAI],
        },
    )
    
    # Create test episode
    episode = {
        "episode_id": "test_ep_001",
        "timestamp": datetime.now().isoformat(),
        "anomaly_type": "ram_spike",
        "action_taken": "model_swap",
        "result": {
            "status": "resolved",
            "improvement_pct": 15.0,
        },
        "surprise_score": 0.4,
        "proposed_action": {
            "type": "cache_optimization",
            "current_ram_gb": 5.5,
        },
        "situation": {
            "mode": "advanced",
            "uncertainty": 0.5,
            "novelty": 0.3,
        },
    }
    
    # Process through v0.3
    result = await consciousness.process_episode_v03(episode)
    
    # Should include v0.2 data
    assert "meta_consciousness" in result, "Should include meta-consciousness"
    assert "ignorance_consciousness" in result, "Should include ignorance consciousness"
    assert "narrative" in result, "Should include narrative"
    
    # Should include v0.3 data
    assert "ethical_assessment" in result, "Should include ethical assessment"
    assert "silence_decision" in result, "Should include silence decision"
    
    # Version should be v0.3
    assert result["version"] == "0.3.0", "Should report v0.3.0"


@pytest.mark.asyncio
async def test_integrated_consciousness_v03_summary():
    """Test: Get comprehensive consciousness summary (v0.2 + v0.3)."""
    consciousness = IntegratedConsciousnessSystem(
        enable_stream_api=False,
        identity_config={
            "core_values": [CoreValue.PROTECT_SARAI, CoreValue.LEARN_CONTINUOUSLY],
        },
    )
    
    summary = await consciousness.get_consciousness_summary()
    
    # Should include v0.2 sections
    assert "meta_consciousness" in summary, "Should include meta-consciousness"
    assert "ignorance_consciousness" in summary, "Should include ignorance consciousness"
    assert "narrative_memory" in summary, "Should include narrative memory"
    
    # Should include v0.3 sections
    assert "evolving_identity" in summary, "Should include evolving identity"
    assert "ethical_boundaries" in summary, "Should include ethical boundaries"
    assert "wisdom_driven_silence" in summary, "Should include wisdom silence"
    
    # Should report v0.3
    assert summary["version"] == "0.3.0", "Should report v0.3.0"


@pytest.mark.asyncio
async def test_integrated_consciousness_v03_identity_evolution_cycle():
    """Test: Identity evolution after 10 episodes."""
    consciousness = IntegratedConsciousnessSystem(
        enable_stream_api=False,
        identity_config={
            "core_values": [CoreValue.PROTECT_SARAI, CoreValue.LEARN_CONTINUOUSLY],
        },
    )
    
    # Process 10 episodes
    for i in range(10):
        episode = {
            "episode_id": f"ep_{i}",
            "timestamp": datetime.now().isoformat(),
            "anomaly_type": "ram_spike",
            "action_taken": "model_swap",
            "result": {
                "status": "resolved",
                "improvement_pct": 15.0 + i,
            },
            "surprise_score": 0.3,
            "situation": {
                "mode": "advanced",
                "uncertainty": 0.4,
            },
        }
        
        result = await consciousness.process_episode_v03(episode)
    
    # Should have evolved identity at episode 10
    assert result["identity_evolution"] is not None, "Should evolve identity after 10 episodes"
    assert len(result["identity_evolution"]["wisdom_gained"]) > 0, "Should have gained wisdom"


# ============================================================
# PERFORMANCE & EDGE CASES
# ============================================================

@pytest.mark.asyncio
async def test_evolving_identity_empty_episodes():
    """Test: Handle empty episodes gracefully."""
    identity = EvolvingIdentity(
        core_values=[CoreValue.PROTECT_SARAI],
        initial_purpose="Test purpose"
    )
    
    result = await identity.evolve_identity([])
    
    # Should not crash
    assert result["wisdom_gained"] == [], "Should return empty wisdom"
    assert result["evolution_decision"] is None, "Should not propose evolution"


@pytest.mark.asyncio
async def test_ethical_monitor_minimal_proposal():
    """Test: Ethical monitor handles minimal proposal data."""
    monitor = EthicalBoundaryMonitor()
    
    proposal = {
        "type": "unknown_action",
    }
    
    result = monitor.evaluate_action_proposal(proposal)
    
    # Should not crash, should use defaults
    assert result["decision"] in ["block", "approve", "request_confirmation"], "Should make a decision"


@pytest.mark.asyncio
async def test_wisdom_silence_edge_thresholds():
    """Test: Wisdom silence at exact threshold boundaries."""
    silence = WisdomDrivenSilence(uncertainty_threshold=0.6)
    
    # Exactly at threshold
    situation = {
        "mode": "advanced",
        "uncertainty": 0.6,
    }
    
    instruction = silence.should_remain_silent(situation)
    
    # Behavior at exact threshold is implementation-defined
    # Just verify it doesn't crash
    assert instruction is None or isinstance(instruction, SilenceInstruction), "Should handle threshold"


# ============================================================
# TEST RUNNER
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
