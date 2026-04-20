# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run the backend API
```bash
source .venv/bin/activate
uvicorn api:app --reload
```

### Run the tkinter frontend
```bash
source .venv/bin/activate
python main.py
```

### Open the web frontend
```bash
xdg-open http://localhost:8000/static/index.html
```
> Requires the backend API to be running first.

### Install dependencies
```bash
pip install -r requirements.txt
```

## Architecture

This is a two-process password manager: a **tkinter desktop GUI** (`main.py`) that communicates with a **FastAPI backend** (`api.py`) over HTTP on `localhost:8000`. Both processes must be running simultaneously.

### Authentication flow
1. On first launch, `main.py` checks if `master.key` exists (via `auth.py`). If not, it prompts the user to create a master password, which is bcrypt-hashed and written to `master.key`.
2. On subsequent launches, the user enters their master password; `main.py` calls `POST /login` on the API, which verifies the bcrypt hash and returns a short-lived JWT (30 min, HS256).
3. All subsequent API calls (`POST /passwords`, `GET /passwords/{website}`) include the JWT in the `Authorization: Bearer` header. The API validates the token via the `verify_token` dependency.

### Data persistence
- **`database.py`**: SQLAlchemy ORM backed by `passwords.db` (SQLite). The `Password` model stores `website`, `email`, and an **encrypted** password string. The session is a module-level singleton.
- **Encryption**: `secret.key` contains a Fernet symmetric key. The API loads this key at startup and uses it to encrypt passwords before storage and decrypt them on retrieval. Both `main.py` (legacy, if used directly) and `api.py` use the same `secret.key`.

### Key files
| File | Role |
|---|---|
| `main.py` | tkinter GUI, login screen, API client |
| `api.py` | FastAPI app — `/login`, `/passwords` CRUD, JWT auth |
| `auth.py` | bcrypt master password set/verify/check |
| `database.py` | SQLAlchemy engine, `Password` model, session |
| `static/index.html` | Web frontend — browser-based client for the API |

### Persistent state files (not committed)
- `master.key` — bcrypt hash of the master password
- `secret.key` — Fernet encryption key (must exist before starting the API)
- `passwords.db` — SQLite database

`secret.key` must be generated once and kept stable; rotating it invalidates all stored passwords.
