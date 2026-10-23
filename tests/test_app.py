import pytest
from app import app
from weather_service import c_to_f, kph_to_mph, mm_to_inches, generate_generic_fallback


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Verify health endpoint returns status 200 and 'UP' status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "UP"
    assert "version" in data
    assert "uptime_seconds" in data


def test_healthz_alias(client):
    """Verify kubernetes healthz alias."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "UP"


def test_info_endpoint(client):
    """Verify /api/info returns metadata."""
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.get_json()
    assert data["container_ready"] is True
    assert "application" in data


def test_index_route(client):
    """Verify root index page renders successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Weather Dashboard" in response.data


def test_api_weather_default(client):
    """Verify /api/weather returns valid structure for default query."""
    response = client.get("/api/weather?city=Pune")
    assert response.status_code == 200
    data = response.get_json()
    assert "temp" in data
    assert "condition" in data
    assert "humidity" in data
    assert "wind" in data
    assert "forecast" in data
    assert len(data["forecast"]) > 0


def test_api_weather_imperial(client):
    """Verify units=imperial parameter returns Fahrenheit."""
    response = client.get("/api/weather?city=London&units=imperial")
    assert response.status_code == 200
    data = response.get_json()
    assert data["temp_unit"] == "°F"
    assert data["wind_unit"] == "mph"


def test_conversions():
    """Unit test conversion formulas."""
    assert c_to_f(0) == 32.0
    assert c_to_f(100) == 212.0
    assert kph_to_mph(100) == 62.1
    assert mm_to_inches(25.4) == 1.0


def test_fallback_generator():
    """Verify generic fallback produces valid weather structure."""
    result = generate_generic_fallback("CustomCity")
    assert result["city"] == "Customcity"
    assert "temp_c" in result
    assert "forecast" in result
    assert len(result["forecast"]) == 5
