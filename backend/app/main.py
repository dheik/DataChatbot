"""API REST do DataDex (FastAPI)."""
import logging
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import database
from .config import settings
from .database import QueryExecutionError, UnsafeQueryError
from .llm import GeminiClient, LLMError
from .services import NotAnswerableError, DataDexService, ValidationError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="DataDex API",
    description="Pergunte sobre Pokémon em português: o Gemini gera SQL e a resposta vem do banco.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])

_service: Optional[DataDexService] = None


def get_service() -> DataDexService:
    global _service
    if _service is None:
        try:
            _service = DataDexService(GeminiClient())
        except LLMError as exc:
            raise HTTPException(503, str(exc))
    return _service


def set_service(service: DataDexService) -> None:
    """Permite injetar um serviço (usado nos testes com um Gemini falso)."""
    global _service
    _service = service


# ---------- rate limit simples por IP ----------
_hits: dict = defaultdict(deque)


def check_rate_limit(ip: str) -> None:
    now = time.monotonic()
    window = _hits[ip]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(429, "Muitas perguntas em pouco tempo. Aguarde um minuto.")
    window.append(now)


# ---------- modelos de entrada ----------
class AskRequest(BaseModel):
    question: str = Field(..., examples=["Qual o Pokémon de fogo com os status base mais altos da região de Alola?"])
    session_id: Optional[str] = Field(None, max_length=64)


# ---------- tratamento de erros padronizado ----------
def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(ValidationError)
async def _validation(_, exc):
    return _error(422, "invalid_question", str(exc))


@app.exception_handler(NotAnswerableError)
async def _not_answerable(_, exc):
    return _error(422, "not_answerable", str(exc))


@app.exception_handler(UnsafeQueryError)
async def _unsafe(_, exc):
    return _error(400, "unsafe_query", f"A consulta gerada foi bloqueada por segurança: {exc}")


@app.exception_handler(QueryExecutionError)
async def _query_failed(_, exc):
    return _error(500, "query_failed", f"Não consegui montar uma consulta válida: {exc}")


@app.exception_handler(LLMError)
async def _llm(_, exc):
    return _error(502, "gemini_unavailable", str(exc))


@app.exception_handler(HTTPException)
async def _http(_, exc):
    return _error(exc.status_code, "http_error", str(exc.detail))


# ---------- rotas ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "database": database.stats(), "gemini_configured": bool(settings.gemini_api_key)}


@app.post("/api/ask")
def ask(body: AskRequest, request: Request):
    check_rate_limit(request.client.host if request.client else "anon")
    return get_service().ask(body.question, body.session_id)


@app.get("/api/pokemon/{pokemon_id}")
def pokemon_detail(pokemon_id: int):
    found = database.fetch_pokemon_by_ids([pokemon_id])
    if not found:
        raise HTTPException(404, "Pokémon não encontrado.")
    return found[0]


@app.get("/api/history")
def history():
    return list(get_service().history) if _service else []


@app.get("/api/examples")
def examples():
    return [
        "Qual o Pokémon de fogo com os status base mais altos da região de Alola?",
        "Quais os 5 Pokémon mais rápidos que não são lendários?",
        "Quais Pokémon de Paldea têm a habilidade Intimidate?",
        "Quantos Pokémon de cada tipo primário existem?",
        "Qual o Pokémon de água com mais ataque especial de Kanto?",
        "Quais formas regionais de Hisui existem?",
    ]
