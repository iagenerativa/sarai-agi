"""Tests para MCP (Meta Control Plane)."""

import pytest

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from sarai_agi.mcp import (
    MCP,
    MCPRules,
    create_mcp,
    route_to_skills,
)


class TestMCPRules:
    """Tests para MCP basado en reglas."""
    
    def test_technical_pure_routing(self):
        """Query técnico puro detectado correctamente (α dominante)."""
        mcp = MCPRules()
        alpha, beta = mcp.compute_weights(hard=0.9, soft=0.2)
        
        assert alpha > 0.9
        assert beta < 0.1
        assert abs(alpha + beta - 1.0) < 0.01
    
    def test_emotional_pure_routing(self):
        """Query emocional puro detectado correctamente (β dominante)."""
        mcp = MCPRules()
        alpha, beta = mcp.compute_weights(hard=0.2, soft=0.8)
        
        assert beta > 0.7
        assert alpha < 0.3
        assert abs(alpha + beta - 1.0) < 0.01
    
    def test_hybrid_balanced_routing(self):
        """Query híbrido detectado correctamente (α ≈ β)."""
        mcp = MCPRules()
        alpha, beta = mcp.compute_weights(hard=0.5, soft=0.5)
        
        assert 0.4 < alpha < 0.6
        assert 0.4 < beta < 0.6
        assert abs(alpha + beta - 1.0) < 0.01
    
    def test_feedback_adjustment(self):
        """Ajuste con feedback histórico funciona."""
        mcp = MCPRules()
        
        # Feedback indicando que hard-agent falla
        feedback = [
            {"alpha": 0.9, "beta": 0.1, "feedback": -1},  # Hard falló
            {"alpha": 0.85, "beta": 0.15, "feedback": -1},
            {"alpha": 0.8, "beta": 0.2, "feedback": -1},
        ] * 4  # 12 interacciones
        
        alpha, beta = mcp.compute_weights(hard=0.8, soft=0.3, feedback_buffer=feedback)
        
        # Debería aumentar beta por bajo éxito de hard
        assert beta > 0.2  # Mayor que sin ajuste


class TestSkillsRouting:
    """Tests para routing de skills MoE."""
    
    def test_filters_base_skills(self):
        """Excluye hard/soft/web_query del routing."""
        scores = {
            "hard": 0.9,
            "soft": 0.8,
            "web_query": 0.7,
            "sql": 0.6,
            "code": 0.5,
        }
        
        skills = route_to_skills(scores, threshold=0.3)
        
        assert "hard" not in skills
        assert "soft" not in skills
        assert "web_query" not in skills
        assert "sql" in skills
        assert "code" in skills
    
    def test_applies_threshold(self):
        """Aplica threshold correctamente."""
        scores = {
            "sql": 0.8,
            "code": 0.6,
            "math": 0.2,  # Bajo threshold
        }
        
        skills = route_to_skills(scores, threshold=0.5)
        
        assert "sql" in skills
        assert "code" in skills
        assert "math" not in skills
    
    def test_limits_top_k(self):
        """Respeta límite top_k."""
        scores = {
            "sql": 0.9,
            "code": 0.8,
            "math": 0.7,
            "reasoning": 0.6,
        }
        
        skills = route_to_skills(scores, threshold=0.3, top_k=2)
        
        assert len(skills) == 2
        assert skills == ["sql", "code"]  # Top-2 por score
    
    def test_sorts_by_score_descending(self):
        """Ordena por score descendente."""
        scores = {
            "code": 0.6,
            "sql": 0.9,
            "math": 0.7,
        }
        
        skills = route_to_skills(scores, threshold=0.3)
        
        assert skills[0] == "sql"  # Mayor score primero
        assert skills[1] == "math"
        assert skills[2] == "code"


@pytest.mark.skipif(not HAS_TORCH, reason="PyTorch no disponible")
class TestMCPLearned:
    """Tests para MCP neural."""
    
    def test_mcp_creation_default(self):
        """MCP se crea en modo rules por defecto."""
        mcp = create_mcp()
        
        assert mcp.mode == "rules"
        assert mcp.rules_mcp is not None
    
    def test_compute_weights_dict_format(self):
        """compute_weights acepta dict de scores."""
        mcp = create_mcp()
        
        scores = {"hard": 0.8, "soft": 0.3}
        alpha, beta = mcp.compute_weights(scores)
        
        assert alpha > 0.7
        assert abs(alpha + beta - 1.0) < 0.01
    
    def test_compute_weights_positional_format(self):
        """compute_weights acepta argumentos posicionales."""
        mcp = create_mcp()
        
        alpha, beta = mcp.compute_weights(0.8, 0.3)
        
        assert alpha > 0.7
        assert abs(alpha + beta - 1.0) < 0.01
    
    def test_feedback_accumulation(self):
        """Feedback se acumula en buffer."""
        mcp = create_mcp()
        
        mcp.add_feedback({"hard": 0.8, "soft": 0.2, "feedback": 1})
        mcp.add_feedback({"hard": 0.7, "soft": 0.3, "feedback": -1})
        
        assert len(mcp.feedback_buffer) == 2
    
    def test_feedback_buffer_size_limit(self):
        """Buffer de feedback respeta tamaño máximo."""
        mcp = MCP(config={"feedback_buffer_size": 10})
        
        for i in range(20):
            mcp.add_feedback({"hard": 0.5, "soft": 0.5, "feedback": 1})
        
        assert len(mcp.feedback_buffer) == 10
