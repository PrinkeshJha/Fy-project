import pandas as pd
import json
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from pathlib import Path

ML_DIR = Path(__file__).parent
TEST_DATA_PATH = ML_DIR / "datasets" / "test_split.csv"
MODEL_PATH = ML_DIR / "url_model.pkl"
RESULTS_PATH = ML_DIR / "evaluation_results.json"

def evaluate():
    if not TEST_DATA_PATH.exists() or not MODEL_PATH.exists():
        print("Missing test data or model.")
        return

    df = pd.read_csv(TEST_DATA_PATH)
    y_test = df['Label']
    X_test = df.drop(columns=['Label'])

    clf = joblib.load(MODEL_PATH)
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else y_pred

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        roc_auc = 0.0 # handle single class case in tiny synthetic dataset

    cm = confusion_matrix(y_test, y_pred)
    # cm is [[TN, FP], [FN, TP]]
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0,0,0,0)
    
    # Explicitly calculate false negative rate
    fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    results = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": {
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp)
        },
        "false_negative_rate": fn_rate
    }

    print("--- Evaluation Results ---")
    print(f"Accuracy: {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall: {rec:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print(f"ROC AUC: {roc_auc:.4f}")
    print(f"Confusion Matrix:\n{cm}")
    print(f"False Negatives: {fn} (Rate: {fn_rate:.4f})")

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=4)
    print(f"Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    evaluate()
