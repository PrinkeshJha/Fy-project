import pytest
from app.services.feature_extractor import extract_features

def test_extract_features_safe_url():
    url = "https://www.google.com"
    features, reasons = extract_features(url)
    
    assert features["url_length"] == len(url)
    assert features["https"] == 1
    assert features["contains_at"] == 0
    assert features["contains_ip"] == 0
    assert features["suspicious_keywords"] == 0
    assert features["ssl_valid"] in [0, 1]  # depending on network

def test_extract_features_phishing_url():
    url = "http://login-verify-paypal-account.com@192.168.1.1/update"
    features, reasons = extract_features(url)
    
    assert features["https"] == 0
    assert features["contains_at"] == 1
    assert features["contains_ip"] == 1
    assert features["suspicious_keywords"] >= 3  # login, verify, paypal, account, update
    assert features["hyphens"] > 1
    assert "URL contains '@', which can hide the true destination" in reasons

def test_extract_features_high_entropy():
    url = "https://x123asdas123zxcasd.com"
    features, reasons = extract_features(url)
    
    assert features["entropy"] > 0

def test_extract_features_ip_domain():
    url = "http://8.8.8.8/test"
    features, reasons = extract_features(url)
    assert features["contains_ip"] == 1
