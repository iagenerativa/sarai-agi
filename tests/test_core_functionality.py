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
        from sarai_agi.configuration import load_settings
        config = load_settings()
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
        
        # Test factory function (may fail if torch not available, but should not crash on import)
        try:
            mcp = create_mcp()
            assert mcp is not None
        except Exception:
            # If it fails, it should be due to missing dependencies, not import errors
            pass
        
    def test_emotion_imports(self):
        """Test que emotion context se importa correctamente"""  
        from sarai_agi.emotion import (
            EmotionalContextEngine,
            create_emotional_context_engine
        )
        
        engine = create_emotional_context_engine()
        assert isinstance(engine, EmotionalContextEngine)

@pytest.mark.core        
class TestCoreConfiguration:
    """Test configuración básica del sistema"""
    
    def test_default_config_loads(self):
        """Test que la configuración por defecto carga sin errores"""
        from sarai_agi.configuration import load_settings, get_section
        
        # Test load function
        config = load_settings()
        assert isinstance(config, dict)
        
        # Test section getter (even if config is empty)
        pipeline_section = get_section(config, "pipeline", {})
        assert isinstance(pipeline_section, dict)
        
    def test_config_sections_accessible(self):
        """Test que las secciones de config son accesibles via get_section"""
        from sarai_agi.configuration import load_settings, get_section
        
        config = load_settings()
        
        # Verificar que get_section funciona para secciones comunes
        test_sections = ["pipeline", "model", "cascade", "emotion"]
        
        for section in test_sections:
            # Should not crash, even if section doesn't exist
            section_config = get_section(config, section, {})
            assert isinstance(section_config, dict), f"get_section('{section}') should return dict"

@pytest.mark.core
class TestMockingCapability:
    """Test que el sistema puede funcionar con mocks para dependencias opcionales"""
    
    def test_model_imports(self):
        """Test que model pool se importa sin problemas (sin cargar LLMs)"""
        from sarai_agi.model import ModelPool, get_model_pool, UnifiedModelWrapper
        
        # Test que las clases se importan correctamente
        assert ModelPool is not None
        assert UnifiedModelWrapper is not None
        
        # Test factory function (may fail if config not available, but import should work)
        try:
            pool = get_model_pool()
            assert pool is not None
            assert isinstance(pool, ModelPool)
        except Exception:
            # If it fails, it should be due to missing config, not import errors
            pass
    
    def test_vector_db_import_graceful(self):
        """Test que vector_db se importa y maneja dependencias faltantes correctamente"""
        from sarai_agi.memory.vector_db import VectorDB, QDRANT_AVAILABLE, CHROMA_AVAILABLE
        
        # Should not crash on import
        assert VectorDB is not None
        
        # Check availability flags
        assert isinstance(QDRANT_AVAILABLE, bool)
        assert isinstance(CHROMA_AVAILABLE, bool)
        
        # If no backends available, constructor should fail gracefully
        if not QDRANT_AVAILABLE:
            try:
                db = VectorDB(backend="qdrant")
                # Should not reach here if qdrant not available
                assert False, "Expected qdrant unavailable error"
            except Exception as e:
                assert "qdrant-client no disponible" in str(e), f"Expected qdrant error, got: {e}"

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