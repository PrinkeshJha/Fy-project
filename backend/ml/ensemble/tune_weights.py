import json
import random
from pathlib import Path

# Try to import pandas, gracefully handle if not present by generating a pure python dict approach if needed
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from app.services.ensemble_service import SAFE_THRESHOLD, PHISHING_THRESHOLD

ENSEMBLE_DIR = Path(__file__).parent
DATASET_PATH = ENSEMBLE_DIR / "validation_data.csv"
CONFIG_PATH = ENSEMBLE_DIR / "weights_config.json"

WEIGHT_COMBOS = [
    (0.50, 0.50),
    (0.55, 0.45),
    (0.60, 0.40),
    (0.65, 0.35),
    (0.70, 0.30),
    (0.75, 0.25),
    (0.80, 0.20)
]

def generate_synthetic_data():
    print(f"Generating synthetic validation data at {DATASET_PATH}...")
    print("WARNING: This is placeholder data! Replace with real validation data (RF/CNN output pairs) before using tuning results.")
    
    if not HAS_PANDAS:
        print("Pandas is not installed. Please install pandas for weight tuning.")
        return False
        
    data = []
    for _ in range(100):
        # Generate some synthetic scores
        # 50 legitimate, 50 phishing
        is_phishing = random.choice([True, False])
        
        if is_phishing:
            actual_label = 1
            rf_prob = random.uniform(0.6, 0.99)
            cnn_prob = random.uniform(0.4, 0.99)
        else:
            actual_label = 0
            rf_prob = random.uniform(0.01, 0.4)
            cnn_prob = random.uniform(0.01, 0.6)
            
        data.append({
            "url": "http://synthetic.com",
            "actual_label": actual_label,
            "rf_probability": rf_prob,
            "cnn_probability": cnn_prob
        })
        
    df = pd.DataFrame(data)
    df.to_csv(DATASET_PATH, index=False)
    return True

def evaluate_metrics(y_true, y_pred):
    """Calculate basic metrics."""
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)
    
    accuracy = (tp + tn) / len(y_true) if y_true else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return accuracy, precision, recall, f1

def tune_weights():
    if not HAS_PANDAS:
        print("Pandas is not installed. Please 'pip install pandas' to run tuning.")
        return
        
    if not DATASET_PATH.exists():
        success = generate_synthetic_data()
        if not success: return
        
    df = pd.read_csv(DATASET_PATH)
    
    print(f"\nEvaluating {len(WEIGHT_COMBOS)} weight combinations...")
    print(f"{'URL Wt':<8} | {'CNN Wt':<8} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10}")
    print("-" * 70)
    
    best_f1 = -1
    best_combo = None
    
    for url_wt, cnn_wt in WEIGHT_COMBOS:
        y_true = df['actual_label'].tolist()
        y_pred = []
        
        for _, row in df.iterrows():
            final_prob = (url_wt * row['rf_probability']) + (cnn_wt * row['cnn_probability'])
            
            # Binary boundary decision: treat SUSPICIOUS and PHISHING as positive (1), SAFE as negative (0)
            # This is a judgment call to prioritize recall on suspicious items
            prediction = 1 if final_prob > SAFE_THRESHOLD else 0
            y_pred.append(prediction)
            
        acc, prec, rec, f1 = evaluate_metrics(y_true, y_pred)
        
        print(f"{url_wt:<8} | {cnn_wt:<8} | {acc:<10.4f} | {prec:<10.4f} | {rec:<10.4f} | {f1:<10.4f}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_combo = (url_wt, cnn_wt)
            
    print("-" * 70)
    print(f"Best combination found: URL={best_combo[0]}, CNN={best_combo[1]} (F1: {best_f1:.4f})")
    
    # Save the best configuration
    config = {
        "url_weight": best_combo[0],
        "cnn_weight": best_combo[1]
    }
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
        
    print(f"Saved best weights to {CONFIG_PATH}")

if __name__ == "__main__":
    tune_weights()
