# Backend

```bash
cp .env.example .env   # fill in your Supabase credentials
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Runs on **http://localhost:8000**
