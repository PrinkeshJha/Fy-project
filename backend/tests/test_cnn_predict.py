import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_scan_image_invalid_path():
    response = client.post("/scan/image", json={"image": "screenshots/does_not_exist_at_all.png"})
    assert response.status_code == 400
    assert "Image not found" in response.json()["detail"]

def test_scan_image_empty_path():
    response = client.post("/scan/image", json={"image": "   "})
    assert response.status_code == 400
    assert "Image path cannot be empty" in response.json()["detail"]

# We cannot easily test the successful path here without ensuring model.keras and a valid image exist.
# The train.py generates placeholder images, but it's not guaranteed to have run before tests.
# So we test the API boundary logic mostly.
