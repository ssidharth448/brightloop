# Environment Setup & Execution Guide

---

## Prerequisites
- Python 3.12 or 3.13
- Docker & Docker Compose (or local PostgreSQL 16)
- Git

---

## 1. Environment Configuration

The application settings (`backend/app/core/config.py`) read from `../.env` relative to `backend/app/core/`, which points to the repository root `.env` (`c:\brightloop\.env`).

Create or ensure `.env` in the root repository directory (`c:\brightloop\.env`):

```env
# Database URL (psycopg v3 driver for PostgreSQL)
DATABASE_URL=postgresql+psycopg://brightloop_user:your_secure_password@localhost:5433/brightloop_db

# JWT settings
SECRET_KEY=brightloop-hackathon-super-secret-jwt-key-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Taxes
DEFAULT_TAX_RATE=18.0

# Docker Compose variables (Postgres & MySQL containers)
POSTGRES_DB=brightloop_db
POSTGRES_USER=brightloop_user
POSTGRES_PASSWORD=your_secure_password

MYSQL_DATABASE=brightloop_db
MYSQL_USER=brightloop_user
MYSQL_PASSWORD=your_secure_password
MYSQL_ROOT_PASSWORD=your_root_password
```

---

## 2. Start PostgreSQL via Docker

Run from the project root:

```bash
docker compose up -d postgres
```

Wait until healthy:
```bash
docker compose ps
```
PostgreSQL will be accessible on port `5433` (as mapped in `docker-compose.yml`: `"5433:5432"`).

---

## 3. Python Virtual Environment & Dependencies

From the project root or backend folder:

```bash
cd c:\brightloop\backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows PowerShell
pip install -r requirements.txt
```

*(Note: dependencies include `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pydantic`, `pydantic-settings`, `python-jose`, `passlib[bcrypt]`, `python-dateutil`, `pytest`, `httpx`)*.

---

## 4. Run Database Migrations

From `backend/`:

```bash
cd c:\brightloop\backend
alembic upgrade head
```

---

## 5. Run the Backend API

From `backend/`:

```bash
cd c:\brightloop\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health check:** [http://localhost:8000/](http://localhost:8000/)

---

## 6. Running Tests

```bash
cd c:\brightloop\backend
pytest tests/ -v
```
