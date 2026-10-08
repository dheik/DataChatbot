"""Integração com a API do Gemini (SDK oficial google-genai)."""
import json
import logging
import re
from typing import Optional, Protocol

from .config import settings

log = logging.getLogger("pokedex.llm")


class LLMError(RuntimeError):
    """Falha ao se comunicar com o Gemini."""


class LLMClient(Protocol):
    def generate(self, prompt: str, json_mode: bool = False) -> str: ...


class GeminiClient:
    """Cliente do Gemini com saída em JSON e troca automática de modelo em caso de falha."""

    def __init__(self, api_key: Optional[str] = None, models: Optional[list] = None):
        from google import genai  # import tardio: os testes não precisam do SDK
        from google.genai import types

        key = api_key or settings.gemini_api_key
        if not key:
            raise LLMError("GEMINI_API_KEY não configurada no arquivo .env")
        self._types = types
        self._client = genai.Client(api_key=key)
        self.models = models or settings.gemini_models
        self.last_model: Optional[str] = None

    def generate(self, prompt: str, json_mode: bool = False) -> str:
        config = self._types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
        errors = []
        for model in self.models:
            try:
                response = self._client.models.generate_content(model=model, contents=prompt, config=config)
                self.last_model = model
                if not response.text:
                    raise LLMError("O Gemini retornou uma resposta vazia.")
                return response.text
            except Exception as exc:  # tenta o próximo modelo da lista
                log.warning("Falha no modelo %s: %s", model, exc)
                errors.append(f"{model}: {exc}")
        raise LLMError("Não foi possível obter resposta do Gemini. " + " | ".join(errors))


def parse_json(text: str) -> dict:
    """Extrai o JSON da resposta (tolera ```json ... ``` em volta)."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise LLMError("A IA não retornou um JSON válido.")
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise LLMError("A IA retornou um formato inesperado.")
    return data
