import json
import re

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
        raise HTTPException(
            status_code=502,
            detail=f"Gemini request failed: {exc}",
        ) from exc

    payload = _extract_json(text)
    try:
        return Itinerary.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail="Gemini JSON did not match the itinerary schema.",
        ) from exc
