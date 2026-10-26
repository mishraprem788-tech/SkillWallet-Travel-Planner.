from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas import TripRequest
from app.services.demo import build_demo_itinerary
from tests.conftest import valid_payload


def test_trip_request_normalizes_fields():
    trip = TripRequest.model_validate(valid_payload())
    assert trip.currency == "INR"
    assert trip.days == 3
    assert trip.interests == ["food", "culture"]


def test_rejects_end_before_start():
    start = date.today() + timedelta(days=10)
    with pytest.raises(ValidationError):
        TripRequest.model_validate(
            valid_payload(
                start_date=start.isoformat(),
                end_date=(start - timedelta(days=1)).isoformat(),
            )
        )


def test_rejects_unknown_interest():
    with pytest.raises(ValidationError):
        TripRequest.model_validate(valid_payload(interests=["skydiving-pro"]))


def test_demo_itinerary_covers_each_day():
    trip = TripRequest.model_validate(valid_payload())
    itinerary = build_demo_itinerary(trip)
    assert len(itinerary.days) == trip.days
    assert itinerary.summary.startswith("DEMO")
    assert itinerary.total_estimated_cost == trip.budget
    assert {day.activities[0].title for day in itinerary.days} <= {
        "Neighborhood breakfast",
        "Old-town walk",
    }


def test_demo_itinerary_fourteen_days():
    start = date.today() + timedelta(days=1)
    trip = TripRequest.model_validate(
        valid_payload(
            start_date=start.isoformat(),
            end_date=(start + timedelta(days=13)).isoformat(),
            interests=["nature", "history", "relaxation"],
            budget=140000,
        )
    )
    itinerary = build_demo_itinerary(trip)
    assert len(itinerary.days) == 14
    assert itinerary.days[0].date == start.isoformat()
    assert itinerary.days[-1].date == (start + timedelta(days=13)).isoformat()
    assert itinerary.total_estimated_cost == 140000
