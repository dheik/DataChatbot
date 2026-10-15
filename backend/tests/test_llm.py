from types import SimpleNamespace

from google import genai
from google.genai import types

from app.config import Settings
from app.llm import GeminiClient


def test_default_models_use_documented_flash_models(monkeypatch):
    monkeypatch.delenv("GEMINI_MODELS", raising=False)

    assert Settings().gemini_models == ["gemini-3.8-flash", "gemini-3.6-flash"]


def test_gemini_uses_fallback_model_when_primary_is_unavailable(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            calls.append(model)
            if model == "gemini-3.8-flash":
                raise RuntimeError("503 UNAVAILABLE")
            return SimpleNamespace(text="resposta")

    fake_client = SimpleNamespace(models=FakeModels())
    monkeypatch.setattr(genai, "Client", lambda api_key: fake_client)
    monkeypatch.setattr(types, "GenerateContentConfig", lambda **kwargs: kwargs)

    client = GeminiClient(
        api_key="test-key",
        models=["gemini-3.8-flash", "gemini-3.6-flash"],
    )

    assert client.generate("prompt") == "resposta"
    assert calls == ["gemini-3.8-flash", "gemini-3.6-flash"]
    assert client.last_model == "gemini-3.6-flash"
