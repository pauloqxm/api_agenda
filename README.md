## Rodar local
pip install -r requirements.txt
export DATABASE_PUBLIC_URL="postgres://..."
uvicorn app:app --host 0.0.0.0 --port 8000

## Endpoints
GET /health
GET /congregacoes
GET /calendario?start=2026-02-01&end=2026-03-01
GET /calendario?start=2026-02-01&end=2026-03-01&congregacao=SEDE
