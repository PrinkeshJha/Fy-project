import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.screenshot_service import WebsiteUnreachableError

client = TestClient(app)

@patch("app.api.scan_full.get_url_prediction")
@patch("app.api.scan_full.capture_screenshot", new_callable=AsyncMock)
@patch("app.api.scan_full.get_cnn_prediction")
def test_scan_full_happy_path(mock_cnn, mock_screenshot, mock_url):
    # Mock URL model
    mock_url.return_value = {"prediction": "phishing", "probability": 0.92, "reasons": ["Has IP"]}
    
    # Mock screenshot
    mock_screenshot.return_value = "e:/Fy-project/backend/screenshots/test.png"
    
    # Mock CNN model
    mock_cnn.return_value = {"prediction": "phishing", "probability": 0.85}
    
    response = client.post("/scan/full", json={"url": "http://evil.com"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["url"] == "http://evil.com"
    assert data["final_prediction"] == "phishing"
    # Using default 0.6 / 0.4 weights: (0.92 * 0.6) + (0.85 * 0.4) = 0.552 + 0.34 = 0.892 -> 89.2%
    assert data["risk_score"] == pytest.approx(89.2, 0.1)
    assert data["risk_level"] == "PHISHING"
    
    assert data["url_model"]["probability"] == 92.0
    assert data["cnn_model"]["probability"] == 85.0
    
    assert "test.png" in data["screenshot"]
    assert data["note"] is None
    assert "Has IP" in data["reasons"]

@patch("app.api.scan_full.get_url_prediction")
@patch("app.api.scan_full.capture_screenshot", new_callable=AsyncMock)
def test_scan_full_graceful_degradation(mock_screenshot, mock_url):
    # Mock URL model
    mock_url.return_value = {"prediction": "phishing", "probability": 0.92, "reasons": []}
    
    # Mock screenshot failure
    mock_screenshot.side_effect = WebsiteUnreachableError("Timeout")
    
    response = client.post("/scan/full", json={"url": "http://unreachable-evil.com"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["url"] == "http://unreachable-evil.com"
    assert data["cnn_model"] is None
    assert data["screenshot"] is None
    assert "unreachable" in data["note"].lower()
    
    # Since CNN failed, it uses URL only (probability 0.92 -> 92.0%)
    assert data["risk_score"] == 92.0
