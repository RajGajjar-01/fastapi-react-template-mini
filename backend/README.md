# FastAPI Production-Ready Backend

A professional, scaffolded FastAPI backend built with security, scalability, and code quality in mind. Managed using [Astral uv](https://github.com/astral-sh/uv).

## 🚀 Features

- **🛡️ Security**: Pre-configured security headers (XSS, Clickjacking, HSTS, MIME-sniffing) and CORS policies.
- **⚡ Performance**: Built on FastAPI and Uvicorn for asynchronous high performance.
- **🚦 Rate Limiting**: Integrated `slowapi` to protect endpoints from abuse.
- **⚙️ Configuration**: Type-safe environment variable management via `pydantic-settings`.
- **✨ Code Quality**: Pre-configured `Ruff` linting/formatting and `pre-commit` hooks.
- **📦 Modern Tooling**: Fast dependency management and project isolation using `uv`.

## 📁 Project Structure

```text
backend/
├── app/
│   ├── main.py              # Application entry point & middleware assembly
│   ├── config.py            # Pydantic settings & env loading
│   ├── api/
│   │   └── routes/
│   │       └── health.py    # Health check endpoints
│   ├── core/
│   │   └── security.py      # Rate limiter & security initialization
│   └── middleware/
│       └── security_headers.py # Custom security headers
├── .env.example             # Template for environment variables
├── .gitignore               # Standard Python & Env ignore rules
├── .pre-commit-config.yaml  # Pre-commit hook definitions
└── pyproject.toml           # Project dependencies & Ruff config
```

## 🛠️ Getting Started

### 1. Prerequisites
Ensure you have [uv](https://github.com/astral-sh/uv) installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Environment Setup
Clone the template `.env` and fill in your values:
```bash
cp .env.example .env
```

### 3. Install Hooks
Install the pre-commit hooks to ensure code quality on every commit:
```bash
uv run pre-commit install
```

## 🏃 Running the Application

Start the development server with hot-reload:
```bash
uv run uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.
- **Interactive Docs**: `http://localhost:8000/api/docs`
- **Health Check**: `http://localhost:8000/api/health`

## 🧹 Code Quality

Run these commands to maintain code standards:

| Task | Command |
| :--- | :--- |
| **Lint** | `uv run ruff check .` |
| **Format** | `uv run ruff format .` |
| **Manual Hooks** | `uv run pre-commit run --all-files` |
