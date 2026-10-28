from app.config import Settings
from app.schemas import Itinerary, TripRequest


def get_client(settings: Settings):
    """Create the Supabase client only when credentials are configured."""
    if not settings.supabase_configured:
        return None
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError(
            "Supabase is configured but the supabase package is not installed."
        ) from exc
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def save_itinerary(
    settings: Settings,
    trip: TripRequest,
    itinerary: Itinerary,
    source: str,
) -> str | None:
    client = get_client(settings)
    if client is None:
        return None

    row = {
        "destination": trip.destination,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "budget": trip.budget,
        "currency": trip.currency,
        "interests": trip.interests,
        "travel_style": trip.travel_style,
        "pace": trip.pace,
        "group_type": trip.group_type,
        "travelers": trip.travelers,
        "source": source,
        "itinerary": itinerary.model_dump(mode="json"),
    }
    result = client.table("itineraries").insert(row).execute()
    if not result.data:
        return None
    return str(result.data[0].get("id"))
