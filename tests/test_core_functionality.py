"""
Tests para funcionalidad core de SARAi AGI sin dependencias opcionales

Estos tests validan que la funcionalidad básica del sistema funciona
sin necesidad de instalar dependencias pesadas como llama-cpp-python,
chromadb, transformers, etc.

Author: SARAi v3.5.1  
Date: November 4, 2025
"""

import pytest
from unittest.mock import Mock, patch

@pytest.mark.core
class TestCoreImports:
    """Test que los imports core funcionen sin dependencias opcionales"""
    
    def test_configuration_import(self):
        """Test que configuration.py se importa sin problemas"""
        from sarai_agi.configuration import get_config
        config = get_config()
        assert isinstance(config, dict)
        
    def test_cascade_imports(self):
        """Test que los módulos CASCADE se importan correctamente"""
        from sarai_agi.cascade import (
            ConfidenceRouter,
            ThinkModeClassifier,
            get_confidence_router,
            get_think_mode_classifier,
        )
        
        # Test singleton factories
        router = get_confidence_router()
        classifier = get_think_mode_classifier()
        
        assert isinstance(router, ConfidenceRouter)
        assert isinstance(classifier, ThinkModeClassifier)
        
    def test_mcp_imports(self):
        """Test que MCP se importa sin problemas (sin torch)"""
        from sarai_agi.mcp import MCP, MCPRules, create_mcp
        
        # Test factory function
        mcp = create_mcp()
        assert mcp is not None
        
    def test_emotion_imports(self):
        """Test que emotion context se importa correctamente"""  
        from sarai_agi.emotion import (
            EmotionalContextEngine,
            get_emotional_context_engine
        )
        
        engine = get_emotional_context_engine()
        assert isinstance(engine, EmotionalContextEngine)

@pytest.mark.core        
class TestCoreConfiguration:
    """Test configuración básica del sistema"""
    
    def test_default_config_loads(self):
        """Test que la configuración por defecto carga sin errores"""
        from sarai_agi.configuration import load_config, get_config
        
        # Test load function
        config = load_config()
        assert isinstance(config, dict)
        assert "version_base" in config
        
        # Test cached getter
        cached_config = get_config()
        assert cached_config is config  # Same instance (cached)
        
    def test_config_has_required_sections(self):
        """Test que la config tiene las secciones principales"""
        from sarai_agi.configuration import get_config
        
        config = get_config()
        
        # Verificar secciones principales (pueden estar vacías)
        expected_sections = ["pipeline", "model", "cascade", "emotion"]
        
        # Al menos una de estas secciones debe existir
        found_sections = [section for section in expected_sections if section in config]
        assert len(found_sections) > 0, f"Al menos una sección requerida debe existir: {expected_sections}"

@pytest.mark.core
class TestMockingCapability:
    """Test que el sistema puede funcionar con mocks para dependencias opcionales"""
    
    @patch('sarai_agi.model.wrapper.torch', None)
    def test_model_wrapper_without_torch(self):
        """Test que model wrapper funciona sin torch"""
        from sarai_agi.model.wrapper import UnifiedModelWrapper
        
        # Should not crash on import
        assert UnifiedModelWrapper is not None
        
    @patch('sarai_agi.memory.vector_db.qdrant_client', None)  
    @patch('sarai_agi.memory.vector_db.chromadb', None)
    def test_vector_db_graceful_degradation(self):
        """Test que vector_db degrada elegantemente sin backends"""
        from sarai_agi.memory.vector_db import VectorDB
        
        # Should not crash on import, even without backends
        assert VectorDB is not None
        
        # Constructor should handle missing backends gracefully
        try:
            # This should raise a clear error, not crash
            db = VectorDB(backend="qdrant")
        except Exception as e:
            # Should be a clear dependency error, not import error
            assert "qdrant-client no disponible" in str(e)

@pytest.mark.core
class TestSystemHealthChecks:
    """Tests básicos de salud del sistema"""
    
    def test_python_version_compatibility(self):
        """Test que estamos ejecutando en Python compatible"""
        import sys
        
        version = sys.version_info
        assert version.major == 3
        assert version.minor >= 10, f"SARAi requiere Python 3.10+, encontrado {version.major}.{version.minor}"
        
    def test_required_stdlib_available(self):
        """Test que módulos estándar requeridos están disponibles"""
        import json
        import os
        import pathlib
        import logging
        import asyncio
        import dataclasses
        import typing
        
        # Si llegamos aquí, los imports básicos funcionan
        assert True
        
    def test_numpy_available(self):
        """Test que numpy (dependencia core) está disponible"""
        import numpy as np
        
        # Test básico de funcionalidad
        arr = np.array([1, 2, 3])
        assert arr.sum() == 6
        
    def test_yaml_available(self):
        """Test que PyYAML (dependencia core) está disponible"""
        import yaml
        
        # Test básico de funcionalidad
        test_data = {"test": "value"}
        yaml_str = yaml.dump(test_data)
        loaded = yaml.safe_load(yaml_str)
        assert loaded == test_data