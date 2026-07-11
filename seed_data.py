"""
Importa dados públicos de CEP, cidades, estados e países para a 360ti API.

Uso:
    python seed_data.py

Os arquivos de dados (JSON/NDJSON) devem estar no diretório apontado pela
variável DATA_DIR (padrão: ./data). Veja README.md para instruções de
download dos dados públicos.
"""

import gzip
import json
import os

import psycopg2
from psycopg2.extras import execute_values

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "360tiapi"),
    "user": os.environ.get("DB_USER", "360tiapi"),
    "password": os.environ.get("DB_PASS", "changeme"),
}

BATCH_SIZE = 500


def log(msg: str):
    print(f"[seed] {msg}")


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        log(f"WARNING: {path} not found, skipping")
        return []
    with open(path, "r") as f:
        return json.load(f)


def load_ndjson(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        log(f"WARNING: {path} not found, skipping")
        return []
    data = []
    errors = 0
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if item and "codigo" in item:
                    data.append(item)
                else:
                    errors += 1
            except json.JSONDecodeError:
                errors += 1
    if errors:
        log(f"  {errors} malformed lines skipped")
    return data


def load_ndjson_gz(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        log(f"WARNING: {path} not found, skipping")
        return []
    data = []
    errors = 0
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if item and "cep" in item:
                    data.append(item)
                else:
                    errors += 1
            except json.JSONDecodeError:
                errors += 1
    if errors:
        log(f"  {errors} malformed lines skipped")
    return data


def seed_paises(conn):
    log("Importing paises...")
    paises = load_json("paises.json")
    if not paises:
        return
    rows = [(p.get("codigo"), p.get("nome"), p.get("sigla"), p.get("origem")) for p in paises]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ibge_paises RESTART IDENTITY CASCADE")
        execute_values(
            cur,
            "INSERT INTO ibge_paises (codigo, nome, sigla, origem) VALUES %s",
            rows,
            template="(%s, %s, %s, %s)",
        )
    conn.commit()
    log(f"  {len(rows)} paises imported")


def seed_estados(conn):
    log("Importing estados...")
    estados = load_json("estados.json")
    if not estados:
        return
    rows = [(e.get("codigo"), e.get("nome"), e.get("sigla"), e.get("pais_codigo")) for e in estados]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ibge_estados RESTART IDENTITY CASCADE")
        execute_values(
            cur,
            "INSERT INTO ibge_estados (codigo, nome, sigla, pais_codigo) VALUES %s",
            rows,
            template="(%s, %s, %s, %s)",
        )
    conn.commit()
    log(f"  {len(rows)} estados imported")


def seed_cidades(conn):
    log("Importing cidades...")
    cidades = load_json("cidades.json")
    if not cidades:
        return
    rows = [
        (c.get("codigo"), c.get("nome"), c.get("estado_codigo"), c.get("codigocorreios"))
        for c in cidades
    ]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ibge_cidades RESTART IDENTITY CASCADE")
        execute_values(
            cur,
            "INSERT INTO ibge_cidades (codigo, nome, estado_codigo, codigocorreios) VALUES %s",
            rows,
            template="(%s, %s, %s, %s)",
        )
    conn.commit()
    log(f"  {len(rows)} cidades imported")


def seed_tipos_logradouros(conn):
    log("Importing tipos_logradouros...")
    tipos = load_ndjson("tipos_logradouros.ndjson")
    if not tipos:
        return
    rows = [(t.get("codigo"), t.get("nome"), t.get("sigla")) for t in tipos]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE tipos_logradouros RESTART IDENTITY CASCADE")
        execute_values(
            cur,
            "INSERT INTO tipos_logradouros (codigo, nome, sigla) VALUES %s",
            rows,
            template="(%s, %s, %s)",
        )
    conn.commit()
    log(f"  {len(rows)} tipos_logradouros imported")


def seed_ceps(conn):
    log("Importing correios_ceps (this may take a while)...")
    ceps = load_ndjson_gz("correios_ceps.ndjson.gz")
    if not ceps:
        return
    with conn.cursor() as cur:
        cur.execute("DELETE FROM correios_ceps")
        batch = []
        for c in ceps:
            batch.append((
                c.get("cep"),
                c.get("tipologradouro"),
                c.get("logradouro"),
                c.get("numero"),
                c.get("complemento"),
                c.get("bairro"),
                c.get("cidade"),
                c.get("uf"),
                c.get("pais"),
            ))
            if len(batch) >= BATCH_SIZE:
                execute_values(
                    cur,
                    """INSERT INTO correios_ceps
                    (cep, tipo_logradouro_codigo, logradouro, numero, complemento,
                     bairro, cidade_codigo, uf_codigo, pais_codigo)
                    VALUES %s""",
                    batch,
                    template="(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                )
                batch = []
        if batch:
            execute_values(
                cur,
                """INSERT INTO correios_ceps
                (cep, tipo_logradouro_codigo, logradouro, numero, complemento,
                 bairro, cidade_codigo, uf_codigo, pais_codigo)
                VALUES %s""",
                batch,
                template="(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            )
    conn.commit()
    log(f"  {len(ceps)} CEPs imported")


def main():
    log(f"Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        seed_paises(conn)
        seed_estados(conn)
        seed_cidades(conn)
        seed_tipos_logradouros(conn)
        seed_ceps(conn)
        log("Done!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
