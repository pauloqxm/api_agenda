import os
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2

SCHEMA = os.getenv("DB_SCHEMA", "bd_agenda")

def _get_db_url() -> str:
    candidates = [
        "DATABASE_PUBLIC_URL",
        "DATABASE_URL",
        "DATABASE_PRIVATE_URL",
        "DATABASE_URL_PUBLIC",
        "DATABASE_URL_PRIVATE",
        "POSTGRES_URL",
        "POSTGRES_PUBLIC_URL",
        "POSTGRES_PRIVATE_URL",
    ]
    for k in candidates:
        v = os.getenv(k)
        if v:
            return v
    raise RuntimeError("Nenhuma URL do banco encontrada nas variáveis do ambiente.")

def _get_db_config() -> dict:
    u = urlparse(_get_db_url())
    return {
        "host": u.hostname,
        "dbname": u.path.lstrip("/"),
        "user": u.username,
        "password": u.password,
        "port": int(u.port or 5432),
        "sslmode": os.getenv("PGSSLMODE", "require"),
        "connect_timeout": int(os.getenv("PG_CONNECT_TIMEOUT", "10")),
    }

@contextmanager
def get_db_connection():
    cfg = _get_db_config()
    conn = None
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            port=cfg["port"],
            sslmode=cfg["sslmode"],
            connect_timeout=cfg["connect_timeout"],
        )
        conn.autocommit = False

        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")
            cur.execute(f"SET search_path TO {SCHEMA}, public;")
        conn.commit()

        yield conn
    finally:
        if conn:
            conn.close()

def test_db_connection():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user;")
                db, user = cur.fetchone()
                cur.execute("SHOW search_path;")
                sp = cur.fetchone()[0]
        return True, f"Banco OK. DB={db} USER={user} search_path={sp}"
    except Exception as e:
        return False, f"Erro no banco: {e}"
