# Personalized Travel Itinerary Planner

**SkillWallet project:** Personalized Travel Itinerary Planner  
**Stack:** React + Vite, Python FastAPI, Google Gemini API, Supabase PostgreSQL.

A traveler enters a destination, travel dates, total budget, currency, interests, travel style, pace, group type, and number of travelers. The app returns a day-by-day itinerary with morning, afternoon, and evening activities, estimated costs, themes, and practical tips.

## Current functionality

- Responsive trip-planning form with client-side validation.
- FastAPI endpoints: `/api/health`, `/api/status`, and `POST /api/itineraries`.
- Gemini-powered itinerary generation when a backend API key is configured.
- Clearly labelled server-side demo fallback when Gemini is not configured.
- Browser-side demo fallback when the backend cannot be reached, so the deployed frontend remains demonstrable.
- Optional Supabase persistence; the service-role key stays on the backend.
- Download generated plan as JSON.
- Automated backend tests for health/status, demo generation, schema validation, date ranges, invalid inputs, and Gemini response validation.

**Important:** demo plans are examples, not verified travel advice. Confirm attractions, prices, opening hours, transport, and safety before relying on a plan. Live AI requires a Gemini key. Cloud persistence requires Supabase configuration.

## Run locally on Windows

### 1. Backend

Open PowerShell:

```powershell
cd C:\Users\YOUR_USER\Documents\SkillWallet-Travel-Planner\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` only if you have credentials. Start the API:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend

Open a second terminal:

```powershell
cd C:\Users\YOUR_USER\Documents\SkillWallet-Travel-Planner\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://127.0.0.1:5173`.

### 3. Tests

From the `backend` directory:

```powershell
pytest
```

Build the frontend:

```powershell
cd ..\frontend
npm run build
```

## Supabase setup (optional)

1. Create a Supabase project.
2. Open its SQL Editor and run `supabase/schema.sql`.
3. Add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` to `backend/.env`.
4. Keep the service-role key on the server only; never add it to `frontend/.env` or commit it.

The current database schema uses Row Level Security. This MVP saves via the backend service role and does not expose a public read endpoint for saved plans.

## Deployment

### Frontend — Netlify

This repository includes `netlify.toml`. Import the GitHub repository into Netlify. It configures:

- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `dist`

The frontend can demonstrate the planner in local demo mode without a backend. For live AI, deploy the backend first, then set Netlify environment variable `VITE_API_URL` to the deployed backend base URL (for example `https://your-api.example.com`, with no `/api` suffix), and trigger a new deploy.

### Backend — Render

This repository includes `render.yaml`. Create a Render web service from the repository using the blueprint. Add `GEMINI_API_KEY` for live AI. Add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` only if saving is required. Set `CORS_ORIGINS` to the exact Netlify site origin, such as `https://your-site.netlify.app` (no trailing slash). The backend health check is `/api/health`.

Do not commit real `.env` files, API keys, or service-role credentials.

## API quick reference

- `GET /api/health` — health check.
- `GET /api/status` — reports whether Gemini and Supabase credentials are configured.
- `POST /api/itineraries` — validates trip preferences and generates a plan.

Example request:

```json
{
  "destination": "Jaipur",
  "start_date": "2027-01-10",
  "end_date": "2027-01-12",
  "budget": 25000,
  "currency": "INR",
  "interests": ["food", "culture"],
  "travel_style": "mid-range",
  "pace": "moderate",
  "group_type": "friends",
  "travelers": 2
}
```

## SkillWallet completion checklist

Use the project workspace to mark each epic only after its corresponding evidence is complete.

- [x] **Pre-requisites / Vibe Coding Environment Setup:** React/Vite frontend and FastAPI backend project structure established.
- [ ] **Supabase Database Setup:** SQL schema is included, but a real Supabase project/table and credentials still need to be configured and verified.
- [x] **Preference Collection & Recommendation Engine:** Trip preferences validated and used to construct a personalized demo or Gemini prompt.
- [x] **Itinerary Generation & Personalization:** day-by-day itinerary with budget, interest, pace, group type, and traveler count.
- [x] **Productization & Deployment configuration:** Netlify and Render configuration files included.
- [ ] **Deployment:** must be completed and verified in the hosting dashboards.
- [ ] **Final Testing & Documentation:** backend tests pass in the current audit; run the frontend production build and verify a deployed end-to-end flow before submission.

**Verification report:** See `TEST-REPORT.md` for checks actually run and items blocked by unavailable credentials or platform-specific dependency installation. Do not claim the live Gemini integration, Supabase persistence, or deployment is verified until credentials are configured and a real request succeeds.
