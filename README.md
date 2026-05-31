# O1 AI Lead Pipeline

## Prerequisites

- [Bun](https://bun.sh) — for frontend
- [Python 3.13+](https://python.org) — for backend
- [uv](https://docs.astral.sh/uv) — Python package manager

---

## Backend

```bash
cd backend

# Create .env and fill in your Supabase credentials
cp .env.example .env

# Install dependencies
uv sync

# Start the dev server
uv run uvicorn app.main:app --reload --port 8000
```

Runs on **http://localhost:8000**

---

## Frontend

```bash
cd frontend

# Install dependencies
bun install

# Start the dev server
bun run dev
```

Runs on **http://localhost:5173**
