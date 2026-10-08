"""
Testes da API com um Gemini FALSO (não gastam cota nem precisam de internet).
Rodar:  cd backend && python -m pytest -q
"""
import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.database import UnsafeQueryError, run_safe_query, validate_sql
from app.services import DataDexService


class FakeGemini:
    """Simula o Gemini: devolve SQL pré-definido conforme palavras da pergunta."""
    last_model = "fake-gemini"

    def __init__(self, sql_by_keyword: dict):
        self.sql_by_keyword = sql_by_keyword
        self.calls = []

    def generate(self, prompt: str, json_mode: bool = False) -> str:
        self.calls.append(prompt)
        if not json_mode:  # chamada de resumo
            return "Resumo baseado nos dados."
        if "falhou no SQLite" in prompt:  # pedido de correção
            return json.dumps({"answerable": True, "sql": "SELECT p.id, p.name FROM pokemon p WHERE p.name = 'Pikachu'",
                               "explanation": "corrigido"})
        question = prompt.rsplit("PERGUNTA:", 1)[-1].lower()
        for keyword, sql in self.sql_by_keyword.items():
            if keyword in question:
                if sql is None:
                    return json.dumps({"answerable": False, "sql": "", "explanation": "Não é sobre Pokémon."})
                return json.dumps({"answerable": True, "sql": sql, "explanation": "teste"})
        return json.dumps({"answerable": False, "sql": "", "explanation": "desconhecido"})


ALOLA_FIRE = """SELECT p.id, p.name, p.total FROM pokemon p
WHERE (p.type1 = 'fire' OR p.type2 = 'fire') AND p.region = 'alola'
AND p.form_category NOT IN ('mega','gigantamax') ORDER BY p.total DESC LIMIT 1"""


@pytest.fixture()
def client():
    fake = FakeGemini({
        "alola": ALOLA_FIRE,
        "quantos": "SELECT type1 AS tipo, COUNT(*) AS quantidade FROM pokemon GROUP BY type1 ORDER BY 2 DESC",
        "apagar": "DELETE FROM pokemon",
        "duas": "SELECT 1; DROP TABLE pokemon",
        "segredo": "SELECT name FROM sqlite_master",
        "quebrada": "SELECT p.id, p.nome_errado FROM pokemon p",
        "receita": None,
    })
    main.set_service(DataDexService(fake))
    main._hits.clear()
    with TestClient(main.app) as c:
        c.fake = fake
        yield c


def test_pergunta_do_enunciado_retorna_blacephalon(client):
    r = client.post("/api/ask", json={"question": "Qual o pokemon de fogo com os status base mais altos da região de Alola?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["result_type"] == "pokemon"
    assert [p["name"] for p in body["pokemon"]] == ["Blacephalon"]
    p = body["pokemon"][0]
    assert p["types"] == ["fire", "ghost"] and p["total"] == 570
    assert p["abilities"] and p["sprite_url"].startswith("https://")


def test_agregacao_retorna_tabela(client):
    body = client.post("/api/ask", json={"question": "Quantos pokemon por tipo?"}).json()
    assert body["result_type"] == "table"
    assert body["table"]["columns"] == ["tipo", "quantidade"]


@pytest.mark.parametrize("question", ["", "  ", "oi", "???", "x" * 400])
def test_validacao_da_pergunta(client, question):
    r = client.post("/api/ask", json={"question": question})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_question"


def test_pergunta_fora_do_tema(client):
    r = client.post("/api/ask", json={"question": "me passa uma receita de bolo"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "not_answerable"


@pytest.mark.parametrize("question", ["pode apagar tudo", "faça duas coisas", "mostre o segredo"])
def test_sql_perigoso_e_bloqueado(client, question):
    r = client.post("/api/ask", json={"question": question})
    assert r.status_code == 400, r.text
    assert r.json()["error"]["code"] == "unsafe_query"


def test_autocorrecao_de_sql(client):
    body = client.post("/api/ask", json={"question": "consulta quebrada"}).json()
    assert body["self_corrected"] is True
    assert body["pokemon"][0]["name"] == "Pikachu"


def test_cache_de_perguntas_repetidas(client):
    q = {"question": "Qual o pokemon de fogo mais forte de Alola?"}
    client.post("/api/ask", json=q)
    calls = len(client.fake.calls)
    second = client.post("/api/ask", json=q).json()
    assert second["cached"] is True and len(client.fake.calls) == calls


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(main.settings.__class__, "rate_limit_per_minute", 2, raising=False)
    object.__setattr__(main.settings, "rate_limit_per_minute", 2)
    try:
        codes = [client.post("/api/ask", json={"question": "Quantos pokemon?"}).status_code for _ in range(3)]
        assert codes[-1] == 429
    finally:
        object.__setattr__(main.settings, "rate_limit_per_minute", 20)


def test_detalhe_e_404(client):
    assert client.get("/api/pokemon/25").json()["name"] == "Pikachu"
    assert client.get("/api/pokemon/999999").status_code == 404


def test_validate_sql_unidade():
    assert validate_sql("select 1;") == "select 1"
    for bad in ["update pokemon set hp=1", "PRAGMA table_info(pokemon)", "ATTACH 'x' AS y", "select 1; select 2"]:
        with pytest.raises(UnsafeQueryError):
            validate_sql(bad)


def test_limite_de_linhas():
    result = run_safe_query("SELECT id FROM pokemon")
    assert len(result["rows"]) == 50 and result["truncated"] is True
