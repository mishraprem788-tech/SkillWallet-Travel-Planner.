from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def valid_payload(**overrides):
    start = date.today() + timedelta(days=10)
    payload = {
        "destination": "Jaipur",
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=2)).isoformat(),
        "budget": 25000,
        "currency": "inr",
        "interests": ["food", "culture"],
        "travel_style": "mid-range",
        "pace": "moderate",
        "group_type": "friends",
        "travelers": 2,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
