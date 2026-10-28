import json
import re
from datetime import timedelta

from fastapi import HTTPException

from app.config import Settings
from app.schemas import Itinerary, TripRequest


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned a response that was not valid JSON.",
        ) from exc


def generate_with_gemini(trip: TripRequest, settings: Settings) -> Itinerary:
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise HTTPException(
            status_code=502,
            detail="google-generativeai is not installed on the backend.",
        ) from exc

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    prompt = f"""
You are a travel planner. Return ONLY valid JSON matching this shape:
{{
  "destination": "string",
  "summary": "string",
  "total_estimated_cost": number,
  "currency": "{trip.currency}",
  "tips": ["string"],
  "days": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "theme": "string",
      "daily_budget": number,
      "activities": [
        {{
          "time_of_day": "morning" | "afternoon" | "evening",
          "title": "string",
          "description": "string",
          "estimated_cost": number,
          "location": "string"
        }}
      ]
    }}
  ]
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
- Exactly {trip.days} days, consecutive dates starting {trip.start_date.isoformat()}.
- Each day must include morning, afternoon, and evening activities.
- Stay within the total budget.
- Be specific (real-sounding places, food, and neighborhoods).
- Do not include markdown.
"""

    try:
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
    except Exception as exc:  # noqa: BLE001 - surface provider errors as HTTP 502
        # Keep provider internals out of public API responses; details remain in
        # hosting logs if a platform logger is configured.
        raise HTTPException(
            status_code=502,
            detail="Gemini could not generate an itinerary. Check the API key, model, quota, and try again.",
        ) from exc

    payload = _extract_json(text)
    try:
        itinerary = Itinerary.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail="Gemini JSON did not match the itinerary schema.",
        ) from exc

    # Treat the user's submitted trip dates and currency as authoritative. AI output
    # is untrusted and must not silently change the requested trip.
    expected_dates = [
        (trip.start_date + timedelta(days=index)).isoformat()
        for index in range(trip.days)
    ]
    if len(itinerary.days) != trip.days:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned the wrong number of itinerary days. Please try again.",
        )

    required_slots = {"morning", "afternoon", "evening"}
    activity_total = 0.0
    daily_total = 0.0
    for index, day in enumerate(itinerary.days):
        # Normalize numbering/date so timezone or formatting mistakes cannot shift
        # the trip dates shown to the user.
        day.day = index + 1
        day.date = expected_dates[index]
        slots = [activity.time_of_day for activity in day.activities]
        if len(slots) != 3 or set(slots) != required_slots:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an incomplete day. Please try generating again.",
            )
        if any(activity.estimated_cost < 0 for activity in day.activities):
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an invalid activity cost. Please try again.",
            )
        activity_total += sum(activity.estimated_cost for activity in day.activities)
        daily_total += day.daily_budget

    if itinerary.total_estimated_cost < 0 or activity_total > trip.budget * 1.05:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned costs above the requested budget. Please try again.",
        )

    itinerary.destination = trip.destination
    itinerary.currency = trip.currency
    # Prefer the sum of the day budgets when it is sensible; keep all displayed
    # totals aligned with the user's budget ceiling.
    if daily_total > 0 and daily_total <= trip.budget * 1.05:
        itinerary.total_estimated_cost = round(min(daily_total, trip.budget), 2)
    else:
        itinerary.total_estimated_cost = round(min(activity_total, trip.budget), 2)
    return itinerary
