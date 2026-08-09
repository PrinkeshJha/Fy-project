import pytest
from app.services.ensemble_service import ensemble_predict

def test_ensemble_predict_happy_path():
    result = ensemble_predict(0.92, 0.85, url_weight=0.6, cnn_weight=0.4)
    assert result["final_probability"] == pytest.approx((0.92 * 0.6) + (0.85 * 0.4), 0.001)
    assert result["risk_level"] == "PHISHING"
    assert result["final_prediction"] == "phishing"

def test_ensemble_predict_safe():
    result = ensemble_predict(0.1, 0.2, url_weight=0.5, cnn_weight=0.5)
    assert result["final_probability"] == pytest.approx(0.15, 0.001)
    assert result["risk_level"] == "SAFE"
    assert result["final_prediction"] == "safe"

def test_ensemble_predict_suspicious():
    result = ensemble_predict(0.4, 0.6, url_weight=0.5, cnn_weight=0.5)
    assert result["final_probability"] == pytest.approx(0.5, 0.001)
    assert result["risk_level"] == "SUSPICIOUS"
    assert result["final_prediction"] == "phishing"  # According to our boundary logic, SUSPICIOUS is treated as phishing

def test_ensemble_invalid_probabilities():
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        ensemble_predict(-0.1, 0.5)
        
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        ensemble_predict(0.5, 1.5)

def test_ensemble_invalid_weights():
    with pytest.raises(ValueError, match="Weights must sum to 1.0"):
        ensemble_predict(0.5, 0.5, url_weight=0.8, cnn_weight=0.8)
