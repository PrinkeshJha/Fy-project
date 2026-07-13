import json
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Any

ML_DIR = Path(__file__).parent
MODEL_PATH = ML_DIR / "url_model.pkl"
FEATURE_NAMES_PATH = ML_DIR / "feature_names.json"

# Load globally to avoid loading on every request
try:
    clf = joblib.load(MODEL_PATH)
    with open(FEATURE_NAMES_PATH, "r") as f:
        feature_names = json.load(f)
except Exception as e:
    clf = None
    feature_names = None
    print(f"Warning: Could not load model or feature names. {e}")

def predict(feature_vector: Dict[str, float]) -> Dict[str, Any]:
    if clf is None or feature_names is None:
        raise RuntimeError("Model is not loaded.")
        
    # Ensure features are in the exact order the model expects
    features = []
    for fn in feature_names:
        if fn not in feature_vector:
            raise ValueError(f"Missing required feature: {fn}")
        features.append(feature_vector[fn])
        
    df = pd.DataFrame([features], columns=feature_names)
    
    prediction = clf.predict(df)[0]
    probabilities = clf.predict_proba(df)[0]
    
    # Random Forest classes are usually [0, 1]. index 1 is phishing.
    phishing_prob = probabilities[1] * 100
    
    if phishing_prob > 85:
        risk_level = "High"
    elif phishing_prob > 50:
        risk_level = "Medium"
    else:
        risk_level = "Low"
        
    return {
        "prediction": "Phishing" if prediction == 1 else "Safe",
        "confidence": round(float(phishing_prob if prediction == 1 else (100 - phishing_prob)), 2),
        "risk_level": risk_level
    }
