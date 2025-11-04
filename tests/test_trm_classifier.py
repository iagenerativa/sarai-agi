"""Tests para TRM Classifier."""

import pytest

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from sarai_agi.classifier import (
    TRMClassifier,
    TRMClassifierSimulated,
    create_trm_classifier,
)


class TestTRMClassifierSimulated:
    """Tests para clasificador simulado (sin torch)."""
    
    def test_hard_query_detection(self):
        """Query técnico detectado correctamente."""
        classifier = TRMClassifierSimulated()
        scores = classifier("Necesito configurar SSH en mi servidor Linux")
        
        assert scores["hard"] > 0.5
        assert scores["hard"] > scores["soft"]
    
    def test_soft_query_detection(self):
        """Query emocional detectado correctamente."""
        classifier = TRMClassifierSimulated()
        scores = classifier("Me siento muy frustrado con este problema")
        
        assert scores["soft"] > 0.5
        assert scores["soft"] > scores["hard"]
    
    def test_web_query_detection(self):
        """Búsqueda web detectada correctamente."""
        classifier = TRMClassifierSimulated()
        scores = classifier("¿Quién ganó el Oscar 2025?")
        
        assert scores["web_query"] > 0.5
    
    def test_neutral_query_baseline(self):
        """Query neutral retorna scores bajos."""
        classifier = TRMClassifierSimulated()
        scores = classifier("Hola, ¿cómo estás?")
        
        assert scores["hard"] < 0.3
        assert scores["soft"] < 0.3
        assert scores["web_query"] < 0.3
    
    def test_combined_hard_soft(self):
        """Query mixto detecta ambas dimensiones."""
        classifier = TRMClassifierSimulated()
        scores = classifier("Estoy perdido con este código Python, ¿me ayudas?")
        
        # Debe detectar ambos
        assert scores["hard"] > 0.3  # "código Python"
        assert scores["soft"] > 0.3  # "perdido", "ayudas"


@pytest.mark.skipif(not HAS_TORCH, reason="PyTorch no disponible")
class TestTRMClassifierNeural:
    """Tests para clasificador neural (requiere torch)."""
    
    def test_classifier_creation(self):
        """Clasificador se crea con parámetros correctos."""
        classifier = TRMClassifier(
            d_model=128,
            d_latent=64,
            h_cycles=2,
            l_cycles=3,
            embedding_dim=384,
        )
        
        assert classifier.d_model == 128
        assert classifier.d_latent == 64
        assert classifier.h_cycles == 2
        assert classifier.l_cycles == 3
    
    def test_forward_pass_shape(self):
        """Forward pass retorna scores válidos."""
        classifier = TRMClassifier(
            d_model=128,
            d_latent=64,
            h_cycles=2,
            l_cycles=2,
            embedding_dim=384,
        )
        
        # Input simulado (batch_size=1, embedding_dim=384)
        x = torch.randn(1, 384)
        
        scores = classifier(x)
        
        assert "hard" in scores
        assert "soft" in scores
        assert "web_query" in scores
        assert 0 <= scores["hard"] <= 1
        assert 0 <= scores["soft"] <= 1
        assert 0 <= scores["web_query"] <= 1
    
    def test_batch_processing(self):
        """Procesa batch correctamente."""
        classifier = TRMClassifier(d_model=128, d_latent=64, embedding_dim=384)
        classifier.eval()  # Poner en modo evaluación
        
        # Batch de 4 queries
        x = torch.randn(4, 384)
        
        scores = classifier(x)
        
        assert isinstance(scores["hard"], list)
        assert len(scores["hard"]) == 4
    
    def test_checkpoint_save_load(self, tmp_path):
        """Checkpoint guarda y carga correctamente."""
        classifier = TRMClassifier(d_model=128, d_latent=64, embedding_dim=384)
        
        checkpoint_path = tmp_path / "test_checkpoint.pt"
        classifier.save_checkpoint(checkpoint_path)
        
        assert checkpoint_path.exists()
        
        # Cargar en nuevo clasificador
        classifier_new = TRMClassifier(d_model=128, d_latent=64, embedding_dim=384)
        success = classifier_new.load_checkpoint(checkpoint_path)
        
        assert success


class TestTRMFactory:
    """Tests para factory create_trm_classifier."""
    
    def test_factory_simulated_fallback(self):
        """Factory retorna simulado si torch no disponible."""
        classifier = create_trm_classifier(use_simulated=True)
        assert isinstance(classifier, TRMClassifierSimulated)
    
    @pytest.mark.skipif(not HAS_TORCH, reason="PyTorch no disponible")
    def test_factory_neural(self):
        """Factory retorna neural si torch disponible."""
        # Sin checkpoint válido debería fallar gracefully
        classifier = create_trm_classifier(
            checkpoint_path="/tmp/nonexistent.pt",
        )
        
        # Debería crear el clasificador aunque el checkpoint no exista
        assert isinstance(classifier, TRMClassifier)
