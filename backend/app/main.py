from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import GenerateResponse, ServiceStatus, TripRequest
from app.services.ai import generate_with_gemini
from app.services.db import save_itinerary
from app.services.demo import build_demo_itinerary

app = FastAPI(title="SkillWallet Travel Itinerary Planner", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status", response_model=ServiceStatus)
def status() -> ServiceStatus:
    settings = get_settings()
    return ServiceStatus(
        gemini_configured=settings.gemini_configured,
        supabase_configured=settings.supabase_configured,
        using_demo_fallback=not settings.gemini_configured,
    )


@app.post("/api/itineraries", response_model=GenerateResponse)
def create_itinerary(trip: TripRequest) -> GenerateResponse:
    settings = get_settings()
    notices: list[str] = []

    if settings.gemini_configured:
        itinerary = generate_with_gemini(trip, settings)
        source = "gemini"
    else:
        itinerary = build_demo_itinerary(trip)
        source = "demo"
        notices.append(
            "DEMO FALLBACK: GEMINI_API_KEY is missing. This itinerary is sample data, not live AI."
        )

    saved = False
    itinerary_id = None
    if settings.supabase_configured:
        try:
            itinerary_id = save_itinerary(settings, trip, itinerary, source)
            saved = bool(itinerary_id)
            if not saved:
                notices.append("Supabase insert returned no row. Check the itineraries table.")
        except Exception as exc:  # noqa: BLE001
            notices.append(f"Itinerary was generated but not saved. Supabase error: {exc}")
    else:
        notices.append(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to save trips."
        )

    return GenerateResponse(
        source=source,
        saved=saved,
        notices=notices,
        itinerary_id=itinerary_id,
        itinerary=itinerary,
    )
