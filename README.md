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

# Create .env and fill in your Supabase + Postgres credentials.
# ALLOWED_ORIGINS (a JSON list of your frontend origins) is required.
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

Run the checks with `uv run pytest`, `uv run ruff check .` and `uv run mypy app`.

### Production settings

| Setting | Why |
|---|---|
| `COOKIE_SECURE=true` | Sends the session cookies only over HTTPS. Required when the frontend and API are on different sites. |
| `ALLOWED_ORIGINS` | Explicit `http(s)` origins only. `*` is rejected because cookies are sent. |
| `ENABLE_DOCS=false` | Hides `/docs`, `/redoc` and `/openapi.json`. |
| `RATE_LIMIT_ENABLED` | In-process limits on login, signup, refresh and password endpoints. They apply per worker, so also limit at your proxy. |

Behind a reverse proxy, set `FORWARDED_ALLOW_IPS` to the proxy's address. The container starts uvicorn with `--proxy-headers`, which then reports the real client address to the rate limiter and to Supabase. The backend also sends that address to Supabase as `X-Forwarded-For`, so configure Supabase Auth to trust it, or all users share one rate-limit budget.

The image runs as a non-root user and needs `backend/uv.lock` (committed). Rebuild the lock with `uv lock` after changing dependencies.

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

> **Note:** `docker-compose.yml` and the `docker/` directory described here are not part of this repository yet. Use a hosted Supabase project, or add those files before following this section.

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

**Caveat:** because the role lives in the JWT, a *promotion* only takes effect the next time that user's token is refreshed, up to the JWT expiry window (10 minutes). A user logged in before the hook was enabled won't have the claim until their session refreshes.

A *demotion* applies at once: `require_admin` and `require_moderator_or_admin` also check the stored role in `profiles`, so a token that still says `admin` is refused after the user is demoted. This costs one small query per admin request. A banned or deleted user keeps a valid token until it expires, but the profile row is removed with the user (foreign key to `auth.users`), which ends admin access.

---

## Database access to `profiles`

The `harden_profiles` migration enables row level security on `public.profiles` and removes the `anon` and `authenticated` privileges, so nobody can change a role through the Supabase Data API. The backend connects as the table owner and is not affected. The token hook role (`supabase_auth_admin`) gets a read-only policy.

On an existing project, after running migrations, remove profile rows whose user no longer exists and then run:

```sql
ALTER TABLE public.profiles VALIDATE CONSTRAINT profiles_id_fkey;
```

Check in the dashboard that RLS shows as enabled for `profiles`.

---

## Password reset email

The reset flow exchanges the one-time token hash from the email. In the Supabase dashboard, open **Authentication → Email Templates → Reset Password** and make the link:

```
{{ .SiteURL }}/reset-password?token_hash={{ .TokenHash }}
```

Set **Site URL** to the frontend origin. The page forwards `token_hash` to `POST /auth/reset-password`, which calls Supabase `/auth/v1/verify`. After a successful reset, all of the user's sessions are signed out. Changing a password signs out the user's other sessions.

This app asks for the current password before a change, but that check lives in this backend. Someone holding a stolen access token could call Supabase's own user-update endpoint directly. Check the email-provider settings in your Supabase project for a secure password change or reauthentication option, and turn it on if it is available.

---

## Project layout

```
backend/    FastAPI app (app/api, app/core, app/models, app/repositories, app/schemas)
frontend/   React + Vite app (src/pages, src/components, src/stores, src/lib)
docker/     Local Supabase stack config (Postgres init, GoTrue, auth proxy)
```
