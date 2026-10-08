"""
Acesso ao banco SQLite com execução SEGURA de SQL gerado pela IA.

Camadas de proteção (defesa em profundidade):
1. Validação textual: apenas UMA instrução, começando com SELECT ou WITH.
2. Conexão aberta em modo somente leitura (mode=ro).
3. Authorizer do SQLite: bloqueia qualquer operação que não seja leitura/funções.
4. Progress handler: aborta consultas que passam do tempo limite.
5. Limite de linhas: o resultado nunca passa de MAX_ROWS.
"""
import re
import sqlite3
import time
from typing import Any

from .config import settings


class UnsafeQueryError(ValueError):
    """A consulta gerada viola as regras de segurança."""


class QueryExecutionError(RuntimeError):
    """A consulta é válida, mas falhou ao executar (erro de sintaxe, coluna inexistente...)."""


_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum|reindex|analyze|begin|commit|rollback|savepoint|release)\b",
    re.IGNORECASE,
)
_ALLOWED_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
_ALLOWED_TABLES = {"pokemon", "pokemon_abilities"}


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", " ", sql)
    return re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)


def validate_sql(sql: str) -> str:
    """Retorna o SQL normalizado ou lança UnsafeQueryError."""
    if not sql or not sql.strip():
        raise UnsafeQueryError("A IA não gerou nenhuma consulta.")
    clean = _strip_comments(sql).strip().rstrip(";").strip()
    if ";" in clean:
        raise UnsafeQueryError("Apenas uma instrução SQL é permitida.")
    if not re.match(r"^(select|with)\b", clean, re.IGNORECASE):
        raise UnsafeQueryError("Apenas consultas de leitura (SELECT) são permitidas.")
    if _FORBIDDEN.search(clean):
        raise UnsafeQueryError("A consulta contém comandos não permitidos.")
    return clean


def _authorizer(action, arg1, arg2, db_name, trigger):
    if action not in _ALLOWED_ACTIONS:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_READ and arg1 not in _ALLOWED_TABLES:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{settings.database_path}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def run_safe_query(sql: str) -> dict:
    """Executa uma consulta gerada pela IA com todas as proteções. Retorna colunas e linhas."""
    clean = validate_sql(sql)
    # Regra de negócio: nunca devolver mais que MAX_ROWS (envolve a consulta original)
    wrapped = f"SELECT * FROM ({clean}) LIMIT {settings.max_rows + 1}"

    con = _connect()
    deadline = time.monotonic() + settings.query_timeout_ms / 1000
    con.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10_000)
    con.set_authorizer(_authorizer)
    try:
        cur = con.execute(wrapped)
        rows = [dict(r) for r in cur.fetchall()]
        columns = [d[0] for d in cur.description] if cur.description else []
    except sqlite3.DatabaseError as exc:
        msg = str(exc)
        if "interrupted" in msg:
            raise QueryExecutionError("A consulta demorou demais e foi cancelada.") from exc
        if "not authorized" in msg or "prohibited" in msg:
            raise UnsafeQueryError("A consulta tentou acessar algo não permitido.") from exc
        raise QueryExecutionError(msg) from exc
    finally:
        con.close()

    truncated = len(rows) > settings.max_rows
    return {"sql": clean, "columns": columns, "rows": rows[: settings.max_rows], "truncated": truncated}


def fetch_pokemon_by_ids(ids: list) -> list:
    """Busca as fichas completas (com habilidades) preservando a ordem recebida."""
    if not ids:
        return []
    con = _connect()
    try:
        marks = ",".join("?" * len(ids))
        found = {r["id"]: dict(r) for r in con.execute(f"SELECT * FROM pokemon WHERE id IN ({marks})", ids)}
        abilities: dict = {}
        for r in con.execute(
                f"SELECT pokemon_id, ability, is_hidden FROM pokemon_abilities WHERE pokemon_id IN ({marks})", ids):
            abilities.setdefault(r["pokemon_id"], []).append({"name": r["ability"], "hidden": bool(r["is_hidden"])})
    finally:
        con.close()
    result = []
    for i in ids:
        if i in found:
            p = found[i]
            p["types"] = [t for t in (p.pop("type1"), p.pop("type2")) if t]
            p["abilities"] = abilities.get(i, [])
            for flag in ("is_legendary", "is_mythical", "is_baby"):
                p[flag] = bool(p[flag])
            result.append(p)
    return result


def get_schema_description() -> str:
    """Esquema real do banco + valores possíveis das colunas categóricas (vai para o prompt)."""
    con = _connect()
    try:
        ddl = "\n".join(r[0] for r in con.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name") if r[0])

        def distinct(col: str) -> str:
            return ", ".join(r[0] for r in con.execute(
                f"SELECT DISTINCT {col} FROM pokemon WHERE {col} IS NOT NULL ORDER BY 1"))

        types = distinct("type1")
        regions = distinct("region")
        categories = distinct("form_category")
        count = con.execute("SELECT COUNT(*) FROM pokemon").fetchone()[0]
    finally:
        con.close()
    return (f"{ddl}\n\n-- {count} linhas na tabela pokemon\n"
            f"-- valores de type1/type2: {types}\n"
            f"-- valores de region: {regions}\n"
            f"-- valores de form_category: {categories}")


def stats() -> dict[str, Any]:
    con = _connect()
    try:
        return {"pokemon": con.execute("SELECT COUNT(*) FROM pokemon").fetchone()[0]}
    finally:
        con.close()
