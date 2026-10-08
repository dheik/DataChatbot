"""
Regras de negócio do DataDex.

Fluxo de uma pergunta:
  validar pergunta -> (cache?) -> Gemini gera SQL -> validar/executar SQL com segurança
  -> (se falhar, Gemini corrige 1x) -> montar cards a partir do banco -> Gemini resume
  SOMENTE os dados retornados -> registrar histórico.
"""
import json
import re
import time
import unicodedata
import uuid
from collections import OrderedDict, deque
from datetime import datetime, timezone
from typing import Optional

from . import database
from .config import settings
from .database import QueryExecutionError
from .llm import LLMClient, LLMError, parse_json
from .prompts import ANSWER_PROMPT, FIX_PROMPT, SQL_PROMPT


class ValidationError(ValueError):
    """Pergunta inválida (regra de negócio)."""


class NotAnswerableError(ValueError):
    """A pergunta não pode ser respondida com o banco de Pokémon."""


def normalize_question(question: Optional[str]) -> str:
    if question is None:
        raise ValidationError("Envie uma pergunta.")
    q = unicodedata.normalize("NFC", re.sub(r"\s+", " ", str(question))).strip()
    if len(q) < 3:
        raise ValidationError("A pergunta é muito curta. Ex.: 'Qual o Pokémon mais rápido?'")
    if len(q) > settings.max_question_length:
        raise ValidationError(f"A pergunta deve ter no máximo {settings.max_question_length} caracteres.")
    if not re.search(r"[A-Za-zÀ-ÿ]", q):
        raise ValidationError("A pergunta precisa conter texto.")
    return q


class DataDexService:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.schema = database.get_schema_description()
        self._cache: "OrderedDict[str, dict]" = OrderedDict()
        self._sessions: dict = {}
        self.history: deque = deque(maxlen=50)

    # ---------- auxiliares ----------
    def _session_context(self, session_id: Optional[str]) -> str:
        turns = self._sessions.get(session_id) or []
        if not turns:
            return "(nenhum)"
        return "\n".join(f"- Pergunta: {t['question']}\n  SQL: {t['sql']}" for t in turns)

    def _remember(self, session_id: Optional[str], question: str, sql: str) -> None:
        if not session_id:
            return
        turns = self._sessions.setdefault(session_id, deque(maxlen=3))
        turns.append({"question": question, "sql": sql})

    def _ask_for_sql(self, question: str, history: str) -> dict:
        raw = self.llm.generate(SQL_PROMPT.format(schema=self.schema, history=history, question=question),
                                json_mode=True)
        data = parse_json(raw)
        if not data.get("answerable", True) or not (data.get("sql") or "").strip():
            raise NotAnswerableError(data.get("explanation")
                                     or "Só consigo responder perguntas sobre os dados de Pokémon.")
        return data

    def _execute_with_retry(self, question: str, plan: dict) -> tuple:
        """Executa o SQL; se der erro de execução, pede ao Gemini para corrigir uma única vez.
        Consultas bloqueadas por segurança (UnsafeQueryError) NÃO são reenviadas: falham na hora."""
        try:
            return database.run_safe_query(plan["sql"]), plan, False
        except QueryExecutionError as exc:
            fixed = parse_json(self.llm.generate(
                FIX_PROMPT.format(question=question, error=str(exc), sql=plan["sql"]), json_mode=True))
            if not (fixed.get("sql") or "").strip():
                raise
            plan = {**plan, **fixed}
            return database.run_safe_query(plan["sql"]), plan, True

    def _summarize(self, question: str, explanation: str, result: dict, pokemon: list) -> str:
        rows = result["rows"]
        if not rows:
            return "Nenhum Pokémon no banco atende a esses critérios."
        compact = rows[:15]
        try:
            text = self.llm.generate(ANSWER_PROMPT.format(
                question=question, explanation=explanation, count=len(rows),
                truncated=", lista truncada" if result["truncated"] else "",
                data=json.dumps(compact, ensure_ascii=False, default=str)))
            text = text.strip()
            if text:
                return text
        except LLMError:
            pass
        # Fallback determinístico: também 100% baseado nos dados
        if pokemon:
            names = ", ".join(p["name"] for p in pokemon[:5])
            more = f" e mais {len(pokemon) - 5}" if len(pokemon) > 5 else ""
            return f"Encontrei {len(pokemon)} Pokémon: {names}{more}."
        return f"A consulta retornou {len(rows)} linha(s)."

    # ---------- caso de uso principal ----------
    def ask(self, question: str, session_id: Optional[str] = None) -> dict:
        started = time.perf_counter()
        q = normalize_question(question)
        history = self._session_context(session_id)

        cache_key = q.lower()
        if history == "(nenhum)" and cache_key in self._cache:
            cached = {**self._cache[cache_key], "cached": True}
            self._remember(session_id, q, cached["sql"])
            self._log(q, cached)
            return cached

        plan = self._ask_for_sql(q, history)
        result, plan, corrected = self._execute_with_retry(q, plan)

        pokemon = []
        if "id" in result["columns"]:
            ids = list(dict.fromkeys(r["id"] for r in result["rows"] if isinstance(r.get("id"), int)))
            pokemon = database.fetch_pokemon_by_ids(ids)
            # colunas extras calculadas pela consulta (ex.: média, diferença) viram destaque no card
            extras = {r["id"]: {k: v for k, v in r.items() if k != "id"} for r in result["rows"] if "id" in r}
            for p in pokemon:
                p["query_values"] = extras.get(p["id"], {})

        response = {
            "id": str(uuid.uuid4()),
            "question": q,
            "answer": self._summarize(q, plan.get("explanation", ""), result, pokemon),
            "explanation": plan.get("explanation", ""),
            "sql": result["sql"],
            "result_type": "pokemon" if pokemon else "table",
            "pokemon": pokemon,
            "table": {"columns": result["columns"], "rows": result["rows"]} if not pokemon else None,
            "row_count": len(result["rows"]),
            "truncated": result["truncated"],
            "self_corrected": corrected,
            "model": getattr(self.llm, "last_model", None),
            "cached": False,
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        }
        self._cache[cache_key] = response
        if len(self._cache) > 100:
            self._cache.popitem(last=False)
        self._remember(session_id, q, result["sql"])
        self._log(q, response)
        return response

    def _log(self, question: str, response: dict) -> None:
        self.history.appendleft({
            "question": question,
            "sql": response["sql"],
            "row_count": response["row_count"],
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
