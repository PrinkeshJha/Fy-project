import json
import joblib
import pandas as pd
from pathlib import Path

# Try to import shap, fallback for tests if not available
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

ML_DIR = Path(__file__).parent.parent / "ml"
MODEL_PATH = ML_DIR / "url_model.pkl"
FEATURE_NAMES_PATH = ML_DIR / "feature_names.json"

_explainer = None
_feature_names = None

def get_explainer():
    """
    Loads the RF model and feature names, and initializes the TreeExplainer.
    Caches the explainer to avoid repeated setup overhead.
    """
    global _explainer, _feature_names
    
    if not SHAP_AVAILABLE:
        print("SHAP is not installed.")
        return None
        
    if _explainer is not None:
        return _explainer
        
    try:
        model = joblib.load(MODEL_PATH)
        with open(FEATURE_NAMES_PATH, "r") as f:
            _feature_names = json.load(f)
            
        # Initialize TreeExplainer for Random Forest
        _explainer = shap.TreeExplainer(model)
        return _explainer
    except Exception as e:
        print(f"Failed to load explainer: {e}")
        return None

# Initialize on load
get_explainer()

def explain_features(feature_vector: dict) -> dict:
    """
    Computes SHAP values for a single feature vector.
    Returns the top 5 contributing features.
    """
    if not SHAP_AVAILABLE or _explainer is None or _feature_names is None:
        raise RuntimeError("SHAP explainer is not available.")
        
    # Ensure exact order as expected by model
    features = []
    for fn in _feature_names:
        if fn not in feature_vector:
            raise ValueError(f"Missing required feature: {fn}")
        features.append(feature_vector[fn])
        
    df = pd.DataFrame([features], columns=_feature_names)
    
    # Calculate SHAP values
    import numpy as np
    shap_values = _explainer.shap_values(df)
    
    # Handle different SHAP output formats (list of arrays vs single 3D array vs 2D array)
    if isinstance(shap_values, list):
        phishing_shap_values = np.array(shap_values[1])
    else:
        shap_arr = np.array(shap_values)
        if len(shap_arr.shape) == 3: # (n_samples, n_features, n_classes)
            phishing_shap_values = shap_arr[:, :, 1]
        else:
            phishing_shap_values = shap_arr
            
    # Flatten to get just the 1D array of impacts for this sample
    phishing_shap_values = phishing_shap_values.flatten()
        
    # Zip features, raw values, and shap impacts
    feature_impacts = []
    for i, feature_name in enumerate(_feature_names):
        impact = float(phishing_shap_values[i])
        raw_val = float(features[i])
        direction = "phishing" if impact > 0 else "legitimate"
        
        feature_impacts.append({
            "feature": feature_name,
            "value": raw_val,
            "impact": impact,
            "direction": direction,
            "abs_impact": abs(impact)
        })
        
    # Sort by absolute impact descending
    feature_impacts.sort(key=lambda x: x["abs_impact"], reverse=True)
    
    # Get top 5, strip the temp abs_impact key
    top_5 = []
    for fi in feature_impacts[:5]:
        top_5.append({
            "feature": fi["feature"],
            "value": fi["value"],
            "impact": round(fi["impact"], 4),
            "direction": fi["direction"]
        })
        
    return {
        "top_features": top_5
    }
