from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "online"
    assert data["service"] == "FoodPulse SLO Decision API"


def test_localities_endpoint():
    response = client.get("/localities")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 5
    assert "Singanallur" in data["localities"]


def test_evaluate_valid_locality():
    response = client.post(
        "/evaluate",
        json={
            "locality": "Singanallur"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["locality"] == "Singanallur"
    assert "SLI" in data
    assert "SLO" in data
    assert "error_budget_remaining" in data
    assert "user_impact" in data
    assert "rainfall_mm" in data
    assert "priority_score" in data
    assert "priority" in data
    assert "recommendation" in data


def test_evaluate_unknown_locality():
    response = client.post(
        "/evaluate",
        json={
            "locality": "Chennai"
        }
    )

    assert response.status_code == 404

    data = response.json()

    assert "not found" in data["detail"]


def test_evaluate_missing_locality():
    response = client.post(
        "/evaluate",
        json={}
    )

    assert response.status_code == 422