# FastAPI + React + Supabase Mini

A minimal full-stack starter: FastAPI backend (cookie-based auth against Supabase Auth, Postgres via `asyncpg`) and a React + Vite frontend, with role-based access (`user` / `moderator` / `admin`).

## Prerequisites

- [Node.js](https://nodejs.org) + [pnpm](https://pnpm.io) — for the frontend
- [Python 3.13+](https://python.org) — for the backend
- [uv](https://docs.astral.sh/uv) — Python package manager
- [Docker](https://docker.com) — only if you want a local Supabase stack instead of a hosted project (see below)

---

## Backend

```bash
cd backend

# Create .env and fill in your Supabase + Postgres credentials
cp .env.example .env

# Install dependencies
uv sync

# Apply database migrations (creates/updates the profiles table)
uv run python -m app.core.migrate
# Add a new migration file: backend/migrations/new_migration.sh <description>
# Files are named `<UTC timestamp>_<description>.sql` and applied in filename order.

# Start the dev server
uv run uvicorn app.main:app --reload --port 8000
```

Runs on **http://localhost:8000**. Interactive docs at `/docs`.

---

## Frontend

```bash
cd frontend

# Create .env
cp .env.example .env

# Install dependencies
pnpm install

# Start the dev server
pnpm dev
```

Runs on **http://localhost:5173**

---

## Local Supabase (optional)

`docker-compose.yml` runs a throwaway local stack (Postgres + GoTrue + an nginx proxy that mimics hosted Supabase's `/auth/v1` routing) so you don't need a hosted Supabase project for local development:

```bash
docker compose up -d
```

This exposes:
- Postgres on `localhost:54322`
- A Supabase-shaped auth API on `http://localhost:54321`

Point `backend/.env` at it:

```
POSTGRES_SERVER=localhost
POSTGRES_PORT=54322
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

SUPABASE_URL=http://localhost:54321
SUPABASE_PUBLISHABLE_KEY=<any non-empty string — GoTrue here doesn't check it>
SUPABASE_SECRET_KEY=<any non-empty string — unused by this stack>
```

The container's GoTrue instance uses a fixed local-only ES256 keypair (see `docker-compose.yml`), so JWT verification in the backend works unchanged. `GOTRUE_MAILER_AUTOCONFIRM=true` means signups are confirmed immediately — no email step required locally.

Migrations run automatically on first `docker compose up` via `docker/01_app_migrations.sh`; re-run `uv run python -m app.core.migrate` from `backend/` after adding new migration files.

This is dev-only — production still points at a hosted Supabase project.

---

## Role claim in the JWT (Custom Access Token Hook)

Authorization checks (`require_admin`, `require_moderator_or_admin` in `backend/app/core/dependencies.py`) read the user's role straight from the JWT's `app_metadata.user_role` claim instead of querying the DB on every request. That claim is populated by a Postgres function (`public.custom_access_token_hook`, added by a migration) that Supabase Auth calls at token-mint time (login and refresh).

- **Local docker-compose stack**: already wired up via `GOTRUE_HOOK_CUSTOM_ACCESS_TOKEN_ENABLED` / `GOTRUE_HOOK_CUSTOM_ACCESS_TOKEN_URI` in `docker-compose.yml`. Nothing to do beyond running the migrations.
- **Hosted Supabase project**: enable it manually — Dashboard → **Authentication → Hooks** → enable the "Customize Access Token (JWT) Claims" hook → select `public.custom_access_token_hook`. Also set Dashboard → **Authentication → Settings** → JWT expiry to `600` seconds, to match the local stack's `GOTRUE_JWT_EXP`.

**Caveat:** because the role now lives in the JWT, a role change (e.g. promoting/demoting a user via `/admin/users/{id}/role`) only takes effect the next time that user's token is refreshed — up to the JWT expiry window (10 minutes), not instantly. A user logged in before the hook was enabled won't have the claim until their session naturally refreshes.

---

## Project layout

```
backend/    FastAPI app (app/api, app/core, app/models, app/repositories, app/schemas)
frontend/   React + Vite app (src/pages, src/components, src/stores, src/lib)
docker/     Local Supabase stack config (Postgres init, GoTrue, auth proxy)
```
