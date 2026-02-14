import os
from datetime import date, datetime, time
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from db import get_db_connection, SCHEMA, test_db_connection

TABLE = os.getenv("DB_TABLE", "eventos")

app = FastAPI(title="Agenda API")

# API aberta
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

def _parse_horario(h: str | None) -> time | None:
    if not h:
        return None
    h = str(h).strip()
    if not h:
        return None

    try:
        if ":" in h:
            parts = h.split(":")
            hh = int(parts[0])
            mm = int(parts[1]) if len(parts) > 1 else 0
            return time(hour=hh, minute=mm)
        if len(h) == 4 and h.isdigit():
            return time(hour=int(h[:2]), minute=int(h[2:]))
    except:
        return None

    return None

def _to_iso_start(d: date, h: str | None) -> str:
    t = _parse_horario(h) or time(0, 0)
    return datetime.combine(d, t).isoformat()

@app.get("/health")
def health():
    ok, msg = test_db_connection()
    return {"ok": ok, "msg": msg, "schema": SCHEMA, "table": f"{SCHEMA}.{TABLE}"}

@app.get("/congregacoes")
def congregacoes():
    sql = f"""
    SELECT DISTINCT congregacao
    FROM {SCHEMA}.{TABLE}
    WHERE congregacao IS NOT NULL AND TRIM(congregacao) <> ''
    ORDER BY congregacao ASC
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return {"congregacoes": [r[0] for r in rows]}

@app.get("/calendario")
def calendario(
    start: date = Query(..., description="YYYY-MM-DD"),
    end: date = Query(..., description="YYYY-MM-DD"),
    congregacao: str | None = Query(None, description="Filtro"),
):
    where = ["data >= %(start)s", "data < %(end)s"]
    params = {"start": start, "end": end}

    if congregacao:
        where.append("congregacao = %(congregacao)s")
        params["congregacao"] = congregacao

    where_sql = " AND ".join(where)

    sql = f"""
    SELECT
      id, congregacao, tipo, subtipo, turma_ebd, data, horario,
      dirigente1, dirigente2, dirigente3, observacoes
    FROM {SCHEMA}.{TABLE}
    WHERE {where_sql}
    ORDER BY data ASC, horario ASC, id ASC
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

    eventos = []
    for r in rows:
        d = dict(zip(cols, r))
        if not d.get("data"):
            continue

        title_parts = []
        if d.get("tipo"):
            title_parts.append(str(d["tipo"]))
        if d.get("subtipo"):
            title_parts.append(str(d["subtipo"]))
        if d.get("turma_ebd"):
            title_parts.append(f"EBD {d['turma_ebd']}")
        if d.get("congregacao"):
            title_parts.append(str(d["congregacao"]))

        title = " | ".join(title_parts) if title_parts else f"Evento {d.get('id')}"
        start_iso = _to_iso_start(d["data"], d.get("horario"))

        eventos.append({
            "id": d.get("id"),
            "title": title,
            "start": start_iso,
            "allDay": False if d.get("horario") else True,
            "extendedProps": d
        })

    return eventos
