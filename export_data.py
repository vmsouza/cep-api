"""
Exporta dados do PostgreSQL para arquivos JSON/NDJSON.
Uso: python export_data.py

Os arquivos gerados podem ser usados com seed_data.py em outro banco.
"""

import gzip
import json
import os

import psycopg2

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "cep-api"),
    "user": os.environ.get("DB_USER", "cep-api"),
    "password": os.environ.get("DB_PASS", "changeme"),
}


def log(msg: str):
    print(f"[export] {msg}")


def export_json(conn, query, filename, orient="records"):
    path = os.path.join(DATA_DIR, filename)
    log(f"Exportando {filename}...")
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    with open(path, "w") as f:
        json.dump(rows, f, ensure_ascii=False, default=str)
    log(f"  {len(rows)} registros salvos em {filename}")


def export_ndjson(conn, query, filename, chunk_size=500):
    path = os.path.join(DATA_DIR, filename)
    log(f"Exportando {filename}...")
    count = 0
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        with open(path, "w") as f:
            while True:
                rows = cur.fetchmany(chunk_size)
                if not rows:
                    break
                for row in rows:
                    item = dict(zip(columns, row))
                    f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
                    count += 1
    log(f"  {count} registros salvos em {filename}")


def export_ndjson_gz(conn, query, filename, chunk_size=500):
    path = os.path.join(DATA_DIR, filename)
    log(f"Exportando {filename}...")
    count = 0
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        with gzip.open(path, "wt", encoding="utf-8") as f:
            while True:
                rows = cur.fetchmany(chunk_size)
                if not rows:
                    break
                for row in rows:
                    item = dict(zip(columns, row))
                    f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
                    count += 1
    log(f"  {count} registros salvos em {filename}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    log(f"Conectando a {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        export_json(conn, "SELECT codigo, nome, sigla, origem FROM ibge_paises ORDER BY codigo", "paises.json")
        export_json(conn, "SELECT codigo, nome, sigla, pais_codigo FROM ibge_estados ORDER BY codigo", "estados.json")
        export_json(conn, "SELECT codigo, nome, estado_codigo, codigocorreios FROM ibge_cidades ORDER BY codigo", "cidades.json")
        export_ndjson(conn, "SELECT codigo, nome, sigla FROM tipos_logradouros ORDER BY codigo", "tipos_logradouros.ndjson")
        export_ndjson_gz(
            conn,
            """SELECT cep, tipo_logradouro_codigo AS tipologradouro,
                      logradouro, numero, complemento, bairro,
                      cidade_codigo AS cidade, uf_codigo AS uf, pais_codigo AS pais
               FROM correios_ceps ORDER BY cep""",
            "correios_ceps.ndjson.gz",
        )
        log("Pronto! Dados exportados para " + DATA_DIR)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
