import pytest
from explainability.shap_service import explain_features
from app.services.feature_extractor import extract_features

def test_explain_features_success():
    # We use a dummy URL to generate a valid feature vector
    features, _ = extract_features("http://example.com")
    
    result = explain_features(features)
    
    assert "top_features" in result
    top_features = result["top_features"]
    
    assert len(top_features) == 5
    
    # Check shape of the returned features
    for f in top_features:
        assert "feature" in f
        assert "value" in f
        assert "impact" in f
        assert "direction" in f
        
        assert isinstance(f["impact"], float)
        assert f["direction"] in ["phishing", "legitimate"]
        
def test_explain_features_missing_key():
    # Provide an incomplete dictionary
    features = {"domain_age": 10}
    with pytest.raises(ValueError, match="Missing required feature"):
        explain_features(features)
