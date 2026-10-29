````python
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

    # Remove Markdown code fences if Gemini includes them.
    fence = re.search(
        r"```(?:json)?\s*(\{.*\})\s*```",
        cleaned,
        re.DOTALL,
    )
    if fence:
        cleaned = fence.group(1)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Gemini returned invalid JSON.")
        raise HTTPException(
            status_code=502,
            detail="Gemini returned a response that was not valid JSON.",
        ) from exc


def generate_with_gemini(
    trip: TripRequest,
    settings: Settings,
) -> Itinerary:
    try:
        import google.generativeai as genai
    except ImportError as exc:
        logger.exception("Gemini SDK is not installed.")
        raise HTTPException(
            status_code=502,
            detail="Gemini SDK is not installed on the backend.",
        ) from exc

    if not settings.gemini_api_key.strip():
        logger.error("Gemini API key is not configured.")
        raise HTTPException(
            status_code=503,
            detail="Gemini API is not configured.",
        )

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)

        prompt = f"""
You are a travel planner. Return ONLY valid JSON matching this shape:

{{
  "destination": "string",
  "summary": "string",
  "total_estimated_cost": 0,
  "currency": "{trip.currency}",
  "tips": ["string"],
  "days": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "theme": "string",
      "daily_budget": 0,
      "activities": [
        {{
          "time_of_day": "morning",
          "title": "string",
          "description": "string",
          "estimated_cost": 0,
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
- Return exactly {trip.days} days, using consecutive dates starting {trip.start_date.isoformat()}.
- Each day must contain exactly three activities: morning, afternoon, and evening.
- Keep the total cost within the user's budget.
- Use realistic places, food, and neighborhoods.
- Return valid JSON only. Do not include Markdown or extra commentary.
"""

        response = model.generate_content(prompt)
        text = (response.text or "").strip()

        if not text:
            logger.error(
                "Gemini returned no text. Model: %s",
                settings.gemini_model,
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "Gemini returned no itinerary text. "
                    "Check the model response and API configuration."
                ),
            )

    except HTTPException:
        raise
    except Exception as exc:
        # Log the exception type and traceback on Render.
        # Do not expose provider errors or credentials to website visitors.
        logger.exception(
            "Gemini generation failed. Exception type: %s; model: %s",
            type(exc).__name__,
            settings.gemini_model,
        )
        raise HTTPException(
            status_code=502,
            detail=(
                "Gemini generation failed. "
                "Check the Render application logs for details."
            ),
        ) from exc

    payload = _extract_json(text)

    try:
        itinerary = Itinerary.model_validate(payload)
    except Exception as exc:
        logger.exception("Gemini JSON did not match the itinerary schema.")
        raise HTTPException(
            status_code=502,
            detail="Gemini JSON did not match the itinerary schema.",
        ) from exc

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
        # Keep the user's requested trip dates authoritative.
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

        activity_total += sum(
            activity.estimated_cost for activity in day.activities
        )
        daily_total += day.daily_budget

    if itinerary.total_estimated_cost < 0 or activity_total > trip.budget * 1.05:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned costs above the requested budget. Please try again.",
        )

    itinerary.destination = trip.destination
    itinerary.currency = trip.currency

    if 0 < daily_total <= trip.budget * 1.05:
        itinerary.total_estimated_cost = round(
            min(daily_total, trip.budget),
            2,
        )
    else:
        itinerary.total_estimated_cost = round(
            min(activity_total, trip.budget),
            2,
        )

    return itinerary
````
