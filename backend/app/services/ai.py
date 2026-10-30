import json
import logging
import re
from datetime import timedelta

from fastapi import HTTPException

from app.config import Settings
from app.schemas import Itinerary, TripRequest

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Gemini returned invalid JSON.")
        raise HTTPException(status_code=502, detail="Gemini returned a response that was not valid JSON.") from exc


def generate_with_gemini(trip: TripRequest, settings: Settings) -> Itinerary:
    if not settings.gemini_api_key.strip():
        raise HTTPException(status_code=503, detail="Gemini API is not configured.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        logger.exception("Google Gen AI SDK is not installed.")
        raise HTTPException(status_code=502, detail="Google Gen AI SDK is not installed on the backend.") from exc

    prompt = f'''You are a travel planner. Return ONLY valid JSON matching this shape:
{{
  "destination": "string", "summary": "string", "total_estimated_cost": 0,
  "currency": "{trip.currency}", "tips": ["string"],
  "days": [{{"day": 1, "date": "YYYY-MM-DD", "theme": "string", "daily_budget": 0,
    "activities": [{{"time_of_day": "morning", "title": "string", "description": "string", "estimated_cost": 0, "location": "string"}}]}}]
}}
Trip:
- Destination: {trip.destination}
- Dates: {trip.start_date.isoformat()} to {trip.end_date.isoformat()} ({trip.days} days)
- Budget: {trip.currency} {trip.budget} total
- Interests: {", ".join(trip.interests)}
- Travel style: {trip.travel_style}
- Pace: {trip.pace}
- Group: {trip.group_type}, {trip.travelers} traveler(s)
Rules:
- Return exactly {trip.days} days, with consecutive dates starting {trip.start_date.isoformat()}.
- Each day must contain exactly three activities: morning, afternoon, and evening.
- Keep total estimated cost within the user's budget.
- Use realistic places, food, and neighborhoods.
- Return JSON only, with no Markdown or commentary.
'''

    try:
        # New supported Google Gen AI SDK; use low thinking for faster itinerary responses.
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Gemini returned an empty response")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini generation failed. Exception type: %s; model: %s", type(exc).__name__, settings.gemini_model)
        raise HTTPException(status_code=502, detail="Gemini generation failed. Check the Render application logs for details.") from exc

    payload = _extract_json(text)
    try:
        itinerary = Itinerary.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini JSON did not match the itinerary schema.")
        raise HTTPException(status_code=502, detail="Gemini JSON did not match the itinerary schema.") from exc

    expected_dates = [(trip.start_date + timedelta(days=index)).isoformat() for index in range(trip.days)]
    if len(itinerary.days) != trip.days:
        raise HTTPException(status_code=502, detail="Gemini returned the wrong number of itinerary days. Please try again.")

    required_slots = {"morning", "afternoon", "evening"}
    activity_total = 0.0
    daily_total = 0.0
    for index, day in enumerate(itinerary.days):
        day.day = index + 1
        day.date = expected_dates[index]
        slots = [activity.time_of_day for activity in day.activities]
        if len(slots) != 3 or set(slots) != required_slots:
            raise HTTPException(status_code=502, detail="Gemini returned an incomplete day. Please try generating again.")
        if any(activity.estimated_cost < 0 for activity in day.activities):
            raise HTTPException(status_code=502, detail="Gemini returned an invalid activity cost. Please try again.")
        activity_total += sum(activity.estimated_cost for activity in day.activities)
        daily_total += day.daily_budget

    if itinerary.total_estimated_cost < 0 or activity_total > trip.budget * 1.05:
        raise HTTPException(status_code=502, detail="Gemini returned costs above the requested budget. Please try again.")

    itinerary.destination = trip.destination
    itinerary.currency = trip.currency
    itinerary.total_estimated_cost = round(min(daily_total if 0 < daily_total <= trip.budget * 1.05 else activity_total, trip.budget), 2)
    return itinerary
