# Personalized Travel Itinerary Planner

SkillWallet MVP: React + Vite frontend, FastAPI backend, Supabase storage, and Google Gemini itinerary generation.

If `GEMINI_API_KEY` is missing, the app still runs and returns a **labelled DEMO FALLBACK** itinerary. It does not pretend Gemini is connected. If Supabase credentials are missing, plans are generated but **not saved**.

## Credentials you actually need

| Variable | Where | Required for |
|---|---|---|
| `GEMINI_API_KEY` | `backend/.env` | Live AI itineraries |
| `GEMINI_MODEL` | `backend/.env` | Optional. Default `gemini-2.0-flash` |
| `SUPABASE_URL` | `backend/.env` | Saving itineraries |
| `SUPABASE_SERVICE_ROLE_KEY` | `backend/.env` | Saving itineraries (backend only) |
| `VITE_API_URL` | `frontend/.env` | Frontend → API URL. Default `http://127.0.0.1:8000` |

Do not put Gemini or Supabase keys in the frontend.

## Setup

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and add keys when you have them.

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend (second terminal)

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open http://127.0.0.1:5173

### 3. Supabase table (only if you want saves)

In the Supabase SQL editor, run `supabase/schema.sql`.

Then set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env` and restart the API.

## Checks

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

```powershell
cd frontend
npm run build
```

## API

- `GET /api/health`
- `GET /api/status` — reports whether Gemini and Supabase are configured
- `POST /api/itineraries` — generate (and optionally save) a plan
