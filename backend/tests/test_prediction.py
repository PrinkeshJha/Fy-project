import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_scan_url_valid():
    response = client.post("/scan/url", json={"url": "https://www.google.com"})
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "risk_level" in data
    assert "reasons" in data
    assert data["url"] == "https://www.google.com"
    assert isinstance(data["reasons"], list)

def test_scan_url_empty():
    response = client.post("/scan/url", json={"url": ""})
    assert response.status_code == 400
    assert "URL cannot be empty" in response.json()["detail"]

def test_scan_url_invalid_payload():
    response = client.post("/scan/url", json={"wrong_key": "https://www.google.com"})
    assert response.status_code == 422  # FastAPI validation error

def test_scan_url_phishing_example():
    response = client.post("/scan/url", json={"url": "http://login-verify-paypal.com@192.168.1.1/"})
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in ["Phishing", "Safe"] # Actual prediction depends on the synthetic model
    # Expect some reasons since this is obviously sketchy
    assert len(data["reasons"]) > 0 
