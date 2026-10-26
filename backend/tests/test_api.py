from datetime import date, timedelta

from tests.conftest import valid_payload


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_status_reports_demo_mode(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert body["gemini_configured"] is False
    assert body["supabase_configured"] is False
    assert body["using_demo_fallback"] is True


def test_generate_demo_without_credentials(client):
    response = client.post("/api/itineraries", json=valid_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "demo"
    assert body["saved"] is False
    assert any("DEMO FALLBACK" in notice for notice in body["notices"])
    itinerary = body["itinerary"]
    assert itinerary["destination"] == "Jaipur"
    assert len(itinerary["days"]) == 3
    assert itinerary["total_estimated_cost"] == 25000
    for day in itinerary["days"]:
        assert len(day["activities"]) == 3
        times = [item["time_of_day"] for item in day["activities"]]
        assert times == ["morning", "afternoon", "evening"]


def test_generate_one_day_trip(client):
    start = (date.today() + timedelta(days=5)).isoformat()
    response = client.post(
        "/api/itineraries",
        json=valid_payload(start_date=start, end_date=start, budget=9000),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["itinerary"]["days"]) == 1
    assert body["itinerary"]["total_estimated_cost"] == 9000


def test_rejects_invalid_payload(client):
    response = client.post(
        "/api/itineraries",
        json=valid_payload(destination="x", budget=0, interests=[]),
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    fields = {item["loc"][-1] for item in detail}
    assert "destination" in fields
    assert "budget" in fields
    assert "interests" in fields


def test_rejects_trip_longer_than_14_days(client):
    start = date.today() + timedelta(days=10)
    response = client.post(
        "/api/itineraries",
        json=valid_payload(
            start_date=start.isoformat(),
            end_date=(start + timedelta(days=14)).isoformat(),
        ),
    )
    assert response.status_code == 422
