import pytest

from src import __version__
from src.sarai_agi.pipeline import PipelineDependencies, create_parallel_pipeline


def test_version_no_vacia():
    """La versión declarada no debe estar vacía."""
    assert __version__, "La versión debe declararse en el archivo VERSION"

@pytest.mark.parametrize(
    "campo",
    ["pipeline", "quantizacion", "telemetria", "seguridad"],
)
def test_campos_configuracion_existentes(campo):
    """La configuración por defecto debe contener los campos principales."""
    from pathlib import Path

    import yaml

    config_path = Path(__file__).resolve().parents[1] / "config" / "default_settings.yaml"
    config = yaml.safe_load(config_path.read_text())
    assert campo in config, f"El campo '{campo}' debe existir en la configuración"


def _build_dependencies():
    def classifier(state):
        text = state.get("input", "").lower()
        if "tecnic" in text:
            return {"hard": 0.9, "soft": 0.1}
        if "emocion" in text:
            return {"hard": 0.2, "soft": 0.8}
        return {"hard": 0.6, "soft": 0.4}

    def weighter(state):
        hard = state.get("hard", 0.5)
        soft = state.get("soft", 0.5)
        total = hard + soft or 1.0
        return {"alpha": hard / total, "beta": soft / total}

    def generator(state, agent_key):
        return f"respuesta::{agent_key}::{state.get('input')}"

    def router(state):
        if state.get("alpha", 0.0) >= 0.7:
            return "expert"
        if state.get("beta", 0.0) >= 0.7:
            return "empathy"
        return "balanced"

    return PipelineDependencies(
        trm_classifier=classifier,
        mcp_weighter=weighter,
        response_generator=generator,
        router=router,
    )


@pytest.mark.asyncio
async def test_pipeline_enruta_experto():
    deps = _build_dependencies()
    pipeline = create_parallel_pipeline(dependencies=deps, config={"enable_parallelization": False})

    resultado = await pipeline.run({"input": "consulta tecnica"})
    await pipeline.shutdown()

    assert resultado["response"].startswith("respuesta::expert"), resultado
    assert resultado["metadata"]["agent"] == "expert"
    assert "pipeline_metrics" in resultado["metadata"]


@pytest.mark.asyncio
async def test_pipeline_enruta_empatia():
    deps = _build_dependencies()
    pipeline = create_parallel_pipeline(dependencies=deps, config={"enable_parallelization": False})

    resultado = await pipeline.run({"input": "situacion emocional"})
    await pipeline.shutdown()

    assert resultado["metadata"]["agent"] == "empathy"
    assert "response" in resultado


@pytest.mark.asyncio
async def test_pipeline_prefetch_por_longitud():
    deps = _build_dependencies()
    pipeline = create_parallel_pipeline(dependencies=deps, config={"enable_parallelization": True, "min_input_length": 5})

    texto_largo = "x" * 600
    resultado = await pipeline.run({"input": texto_largo})
    await pipeline.shutdown()

    metrics = resultado["metadata"]["pipeline_metrics"]
    assert metrics["prefetch_target"] in {"expert_long", "expert_short", "tiny"}

