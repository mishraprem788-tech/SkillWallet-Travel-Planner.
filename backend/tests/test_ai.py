import json
import sys
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.config import Settings
from app.schemas import TripRequest
from app.services.ai import generate_with_gemini
from tests.conftest import valid_payload


def _payload(trip: TripRequest) -> dict:
    days = []
    for index in range(trip.days):
        current = trip.start_date + timedelta(days=index)
        days.append(
            {
                "day": index + 1,
                "date": current.isoformat(),
                "theme": "Local discovery",
                "daily_budget": trip.budget / trip.days,
                "activities": [
                    {
                        "time_of_day": slot,
                        "title": f"{slot.title()} activity",
                        "description": "Sample activity; confirm details before travel.",
                        "estimated_cost": trip.budget / (trip.days * 3),
                        "location": trip.destination,
                    }
                    for slot in ("morning", "afternoon", "evening")
                ],
            }
        )
    return {
        "destination": "Wrong destination from model",
        "summary": "A sample itinerary",
        "total_estimated_cost": trip.budget,
        "currency": "USD",
        "tips": ["Confirm current prices and opening hours."],
        "days": days,
    }


def _install_fake_gemini(monkeypatch, response_text: str) -> None:
    fake = SimpleNamespace(
        configure=lambda **kwargs: None,
        GenerativeModel=lambda model: SimpleNamespace(
            generate_content=lambda prompt: SimpleNamespace(text=response_text)
        ),
    )
    monkeypatch.setitem(sys.modules, "google.generativeai", fake)


def test_gemini_result_is_normalized_to_requested_trip(monkeypatch):
    trip = TripRequest.model_validate(valid_payload())
    _install_fake_gemini(monkeypatch, json.dumps(_payload(trip)))
    settings = Settings(gemini_api_key="test-key", gemini_model="test-model")

    result = generate_with_gemini(trip, settings)

    assert result.destination == trip.destination
    assert result.currency == trip.currency
    assert len(result.days) == trip.days
    assert [day.date for day in result.days] == [
        (trip.start_date + timedelta(days=index)).isoformat()
        for index in range(trip.days)
    ]


def test_gemini_rejects_missing_day(monkeypatch):
    trip = TripRequest.model_validate(valid_payload())
    payload = _payload(trip)
    payload["days"] = payload["days"][:-1]
    _install_fake_gemini(monkeypatch, json.dumps(payload))
    settings = Settings(gemini_api_key="test-key", gemini_model="test-model")

    with pytest.raises(HTTPException) as exc:
        generate_with_gemini(trip, settings)

    assert exc.value.status_code == 502
    assert "wrong number" in exc.value.detail


def test_gemini_rejects_missing_time_slot(monkeypatch):
    trip = TripRequest.model_validate(valid_payload())
    payload = _payload(trip)
    payload["days"][0]["activities"] = payload["days"][0]["activities"][:2]
    _install_fake_gemini(monkeypatch, json.dumps(payload))
    settings = Settings(gemini_api_key="test-key", gemini_model="test-model")

    with pytest.raises(HTTPException) as exc:
        generate_with_gemini(trip, settings)

    assert exc.value.status_code == 502
    assert "incomplete day" in exc.value.detail
