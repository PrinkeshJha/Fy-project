from ml.predict import predict as rf_predict
from app.services.feature_extractor import extract_features

def get_url_prediction(url: str) -> dict:
    """
    Wrapper around the Random Forest model (Module 2).
    Extracts features for the URL and returns a normalized prediction dictionary.
    Output: { "prediction": "phishing" | "legitimate", "probability": float (0.0 to 1.0) }
    """
    features, reasons = extract_features(url)
    result = rf_predict(features)
    
    # rf_predict returns confidence as a percentage (0-100)
    # We need to normalize it to a 0-1 probability of being PHISHING
    prediction_label = result["prediction"].lower() # "phishing" or "safe"
    confidence = result["confidence"] / 100.0
    
    if prediction_label == "phishing":
        probability = confidence
    else:
        # If it predicts safe with 80% confidence, then probability of phishing is 20%
        probability = 1.0 - confidence
        
    return {
        "prediction": "phishing" if probability >= 0.5 else "legitimate",
        "probability": probability,
        "reasons": reasons
    }
