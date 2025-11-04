import pytest

from src.sarai_agi.model import (
    QuantizationLevel,
    create_dynamic_quantization_selector,
)


def test_selector_respeta_override_de_calidad():
    selector = create_dynamic_quantization_selector(min_ram_free_gb=1.0, force_quality_threshold=0.85)

    decision = selector.select_quantization(
        prompt="Explicación extensa",
        task_complexity=0.95,
        quality_request=0.9,
        ram_available_gb=2.0,
    )

    assert decision.level == QuantizationLevel.Q5_K_M
    assert "force_quality" in decision.metadata.rationale


def test_selector_reduce_cuando_prompt_corto():
    selector = create_dynamic_quantization_selector(min_ram_free_gb=1.0)

    decision = selector.select_quantization(
        prompt="hola",
        task_complexity=0.1,
        ram_available_gb=4.0,
    )

    assert decision.level in {QuantizationLevel.IQ3_XXS, QuantizationLevel.Q4_K_M}


def test_update_historial_incrementa_conteos():
    selector = create_dynamic_quantization_selector()

    selector.update_usage_history(QuantizationLevel.Q4_K_M, success=True, latency_ms=2100)
    selector.update_usage_history(QuantizationLevel.Q4_K_M, success=False, latency_ms=2200)

    stats = selector.get_usage_stats()[QuantizationLevel.Q4_K_M.value]
    assert stats["count"] == pytest.approx(2.0)
    assert 0.0 <= stats["success_rate"] <= 1.0