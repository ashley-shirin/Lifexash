# LifeXash

A personal productivity PWA: daily planner, notes with tags, and a mood journal.

**Stack:** React (Vite) · FastAPI · MySQL 9.7 · SQLAlchemy 2.0 · Alembic · JWT auth

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations
frontend/   React + Vite single-page app
```

## Prerequisites

- Python 3.12+ · Node.js 20+ · MySQL 9.x running on `localhost:3306`

## 1. Create the database

Run this in MySQL Workbench or with `mysql -u root -p`:

```sql
CREATE DATABASE lifexash CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'lifexash_user'@'localhost' IDENTIFIED BY 'choose_a_password';
GRANT ALL PRIVILEGES ON lifexash.* TO 'lifexash_user'@'localhost';
```

## 2. Backend (PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env        # then edit .env: DB password + JWT_SECRET_KEY
alembic upgrade head               # creates all tables
uvicorn app.main:app --reload      # http://localhost:8000
```

Check: <http://localhost:8000/api/health> → `{"status":"ok"}`. Interactive API docs: <http://localhost:8000/docs>.

## 3. Frontend (second terminal)

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev                        # http://localhost:5173
```

## Database migrations

After changing a model in `backend/app/models/`:

```powershell
alembic revision --autogenerate -m "describe the change"
# review the new file in alembic/versions/, then:
alembic upgrade head
```
