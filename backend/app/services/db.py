from supabase import Client, create_client

from app.config import Settings
from app.schemas import Itinerary, TripRequest


def get_client(settings: Settings) -> Client | None:
    if not settings.supabase_configured:
        return None
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
        "itinerary": itinerary.model_dump(),
    }
    result = client.table("itineraries").insert(row).execute()
    if not result.data:
        return None
    return str(result.data[0].get("id"))
