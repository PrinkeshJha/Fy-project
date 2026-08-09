import json
from pathlib import Path

# Constants for risk thresholds
SAFE_THRESHOLD = 0.30
PHISHING_THRESHOLD = 0.70

CONFIG_PATH = Path(__file__).parent.parent.parent / "ml" / "ensemble" / "weights_config.json"

def _load_weights():
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        return config.get('url_weight', 0.6), config.get('cnn_weight', 0.4)
    except Exception:
        # Fallback defaults if config is missing or corrupt
        return 0.6, 0.4

def ensemble_predict(url_probability: float, cnn_probability: float, url_weight: float = None, cnn_weight: float = None) -> dict:
    """
    Combines the probabilities from the URL model and CNN model using a weighted average.
    """
    if not (0.0 <= url_probability <= 1.0):
        raise ValueError(f"url_probability must be between 0.0 and 1.0, got {url_probability}")
    
    if not (0.0 <= cnn_probability <= 1.0):
        raise ValueError(f"cnn_probability must be between 0.0 and 1.0, got {cnn_probability}")

    if url_weight is None or cnn_weight is None:
        url_weight, cnn_weight = _load_weights()

    # Float arithmetic can sometimes produce sums like 1.0000000000000002
    if round(url_weight + cnn_weight, 5) != 1.0:
        raise ValueError(f"Weights must sum to 1.0, got {url_weight} and {cnn_weight}")

    final_probability = (url_weight * url_probability) + (cnn_weight * cnn_probability)

    if final_probability <= SAFE_THRESHOLD:
        risk_level = "SAFE"
    elif final_probability < PHISHING_THRESHOLD:
        risk_level = "SUSPICIOUS"
    else:
        risk_level = "PHISHING"

    final_prediction = "safe" if risk_level == "SAFE" else "phishing"

    return {
        "final_probability": final_probability,
        "risk_level": risk_level,
        "final_prediction": final_prediction
    }
