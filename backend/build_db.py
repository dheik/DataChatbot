"""
build_db.py — Monta o banco SQLite `data/pokemon.db` a partir dos dados oficiais da PokéAPI.

A PokéAPI (https://pokeapi.co) publica todo o seu banco como CSVs no GitHub
(https://github.com/PokeAPI/pokeapi/tree/master/data/v2/csv). Este script baixa esses
arquivos (se ainda não existirem em data/raw/), normaliza os dados e gera uma tabela
única e "amigável para IA", que é a fonte de verdade das respostas do chatbot.

Uso:
    python build_db.py            # baixa (se preciso) e gera data/pokemon.db
    python build_db.py --refresh  # força novo download dos CSVs
"""
import csv
import os
import sqlite3
import sys
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv"
SPRITE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{id}.png"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw")
DB_PATH = os.path.join(HERE, "data", "pokemon.db")

FILES = [
    "pokemon", "pokemon_stats", "pokemon_types", "types", "pokemon_species",
    "pokemon_forms", "pokemon_form_names", "pokemon_species_names",
    "generations", "regions", "pokemon_abilities", "ability_names",
]
ENGLISH = "9"

# Região "nativa" de cada geração
GENERATION_REGION = {
    1: "kanto", 2: "johto", 3: "hoenn", 4: "sinnoh", 5: "unova",
    6: "kalos", 7: "alola", 8: "galar", 9: "paldea",
}
# Espécies da Geração 8 que, na verdade, foram introduzidas em Hisui (Legends: Arceus)
HISUI_SPECIES = {"wyrdeer", "kleavor", "ursaluna", "basculegion", "sneasler", "overqwil", "enamorus"}
REGIONAL_TAGS = ("alola", "galar", "hisui", "paldea")

# Formas puramente cosméticas/duplicadas que só poluiriam os resultados
def is_noise(identifier: str) -> bool:
    if "totem" in identifier or identifier.endswith("-starter"):
        return True
    # Pikachu de boné / cosplay: mesmos status do Pikachu normal
    return identifier.startswith("pikachu-") and identifier != "pikachu-gmax"


def download(refresh: bool = False) -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    for name in FILES:
        path = os.path.join(RAW_DIR, f"{name}.csv")
        if os.path.exists(path) and not refresh:
            continue
        print(f"  baixando {name}.csv ...")
        urllib.request.urlretrieve(f"{BASE_URL}/{name}.csv", path)


def read(name: str) -> list:
    with open(os.path.join(RAW_DIR, f"{name}.csv"), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build() -> int:
    pokemon = read("pokemon")
    species = {r["id"]: r for r in read("pokemon_species")}
    types = {r["id"]: r["identifier"] for r in read("types")}

    species_name = {r["pokemon_species_id"]: r["name"]
                    for r in read("pokemon_species_names") if r["local_language_id"] == ENGLISH}

    # forma padrão de cada "pokemon" (uma linha de pokemon.csv pode ter várias formas cosméticas)
    forms = {}
    for r in read("pokemon_forms"):
        if r["is_default"] == "1":
            forms[r["pokemon_id"]] = r
    form_display = {r["pokemon_form_id"]: (r["form_name"], r["pokemon_name"])
                    for r in read("pokemon_form_names") if r["local_language_id"] == ENGLISH}

    stat_cols = {"1": "hp", "2": "attack", "3": "defense", "4": "sp_attack", "5": "sp_defense", "6": "speed"}
    stats = {}
    for r in read("pokemon_stats"):
        if r["stat_id"] in stat_cols:
            stats.setdefault(r["pokemon_id"], {})[stat_cols[r["stat_id"]]] = int(r["base_stat"])

    ptypes = {}
    for r in read("pokemon_types"):
        ptypes.setdefault(r["pokemon_id"], {})[int(r["slot"])] = types[r["type_id"]]

    ability_name = {r["ability_id"]: r["name"] for r in read("ability_names") if r["local_language_id"] == ENGLISH}
    abilities = {}
    for r in read("pokemon_abilities"):
        abilities.setdefault(r["pokemon_id"], []).append(
            (ability_name.get(r["ability_id"], r["ability_id"]), r["is_hidden"] == "1", int(r["slot"])))

    rows, ability_rows = [], []
    for p in pokemon:
        ident, pid = p["identifier"], p["id"]
        if is_noise(ident) or pid not in stats:
            continue
        sp = species[p["species_id"]]
        gen = int(sp["generation_id"])
        form = forms.get(pid, {})
        form_id = form.get("form_identifier", "") or ""

        regional = next((t for t in REGIONAL_TAGS if t in ident.split("-")), None)
        if "-mega" in ident or ident.endswith("-primal"):
            category = "mega"
        elif ident.endswith("-gmax"):
            category = "gigantamax"
        elif regional:
            category = "regional"
        elif p["is_default"] == "1":
            category = "base"
        else:
            category = "alternate"

        region = regional or ("hisui" if sp["identifier"] in HISUI_SPECIES else GENERATION_REGION[gen])

        base = species_name.get(p["species_id"], sp["identifier"].title())
        fname, pname = form_display.get(form.get("id", ""), ("", ""))
        display = pname or (f"{base} ({fname})" if fname else base)

        s = stats[pid]
        t = ptypes.get(pid, {})
        rows.append({
            "id": int(pid),
            "pokedex_number": int(p["species_id"]),
            "name": display,
            "species": base,
            "form": form_id or None,
            "form_category": category,
            "type1": t.get(1),
            "type2": t.get(2),
            **s,
            "total": sum(s.values()),
            "generation": gen,
            "region": region,
            "height_m": int(p["height"]) / 10,
            "weight_kg": int(p["weight"]) / 10,
            "is_legendary": int(sp["is_legendary"]),
            "is_mythical": int(sp["is_mythical"]),
            "is_baby": int(sp["is_baby"]),
            "capture_rate": int(sp["capture_rate"]) if sp["capture_rate"] else None,
            "evolves_from_species_id": int(sp["evolves_from_species_id"]) if sp["evolves_from_species_id"] else None,
            "sprite_url": SPRITE_URL.format(id=pid),
        })
        for name, hidden, slot in sorted(abilities.get(pid, []), key=lambda a: a[2]):
            ability_rows.append((int(pid), name, int(hidden)))

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
    CREATE TABLE pokemon (
        id INTEGER PRIMARY KEY,
        pokedex_number INTEGER NOT NULL,
        name TEXT NOT NULL,
        species TEXT NOT NULL,
        form TEXT,
        form_category TEXT NOT NULL CHECK (form_category IN ('base','regional','mega','gigantamax','alternate')),
        type1 TEXT NOT NULL,
        type2 TEXT,
        hp INTEGER, attack INTEGER, defense INTEGER,
        sp_attack INTEGER, sp_defense INTEGER, speed INTEGER,
        total INTEGER,
        generation INTEGER,
        region TEXT,
        height_m REAL, weight_kg REAL,
        is_legendary INTEGER, is_mythical INTEGER, is_baby INTEGER,
        capture_rate INTEGER,
        evolves_from_species_id INTEGER,
        sprite_url TEXT
    );
    CREATE TABLE pokemon_abilities (
        pokemon_id INTEGER NOT NULL REFERENCES pokemon(id),
        ability TEXT NOT NULL,
        is_hidden INTEGER NOT NULL
    );
    CREATE INDEX idx_type ON pokemon(type1, type2);
    CREATE INDEX idx_region ON pokemon(region);
    CREATE INDEX idx_ab ON pokemon_abilities(pokemon_id);
    """)
    cols = list(rows[0].keys())
    con.executemany(f"INSERT INTO pokemon ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    [tuple(r[c] for c in cols) for r in rows])
    con.executemany("INSERT INTO pokemon_abilities VALUES (?,?,?)", ability_rows)
    con.commit()
    con.close()
    return len(rows)


if __name__ == "__main__":
    print("Baixando dados da PokéAPI...")
    download(refresh="--refresh" in sys.argv)
    print("Gerando banco SQLite...")
    n = build()
    print(f"OK: {n} Pokémon gravados em {DB_PATH}")
