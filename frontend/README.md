# Frontend

React + TypeScript + Vite app for the FastAPI + React + Supabase mini project. See the [root README](../README.md) for full-stack setup (backend, local Supabase).

## Stack

- React 19 + React Router 7
- Zustand for auth state (`src/stores/useAuthStore.ts`)
- Axios client with automatic access-token refresh on 401 (`src/lib/api.ts`)
- Tailwind CSS 4 + shadcn/ui-style components (`src/components/ui`)
- React Hook Form + Zod for form validation

## Setup

```bash
cp .env.example .env   # set VITE_API_URL to the backend URL
pnpm install
pnpm dev
```

Runs on **http://localhost:5173**.

## Scripts

- `pnpm dev` — start the dev server
- `pnpm build` — typecheck and build for production
- `pnpm preview` — preview the production build
- `pnpm lint` / `pnpm format` / `pnpm check` — Biome lint/format

## Auth flow

The backend issues httpOnly `access_token` / `refresh_token` cookies (`withCredentials: true` on every request). `useAuthStore.initialize()` calls `GET /auth/me` on app mount to restore session state; `ProtectedRoute` redirects to `/login` while that's unresolved or unauthenticated. On a 401, the axios interceptor in `src/lib/api.ts` transparently calls `/auth/refresh` once and retries the original request before giving up and redirecting to `/login`.

Role-gated UI (e.g. the Admin page/link) checks `user.role` client-side for display only — the backend independently enforces `moderator`/`admin` access on the relevant endpoints.
