import pandas as pd
import json
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from pathlib import Path

# Paths
ML_DIR = Path(__file__).parent
DATASET_PATH = ML_DIR / "datasets" / "synthetic_phishing_data.csv"
MODEL_PATH = ML_DIR / "url_model.pkl"
FEATURE_NAMES_PATH = ML_DIR / "feature_names.json"

def train():
    if not DATASET_PATH.exists():
        print(f"Dataset not found at {DATASET_PATH}")
        return

    # NOTE: This is using a small synthetic dataset for testing purposes.
    # REPLACE WITH A REAL DATASET (e.g. PhishTank / UCI phishing dataset) BEFORE PRODUCTION USE.
    df = pd.read_csv(DATASET_PATH)
    
    # Handle missing values
    df.fillna(0, inplace=True)
    
    # Separate features and labels
    if 'Label' not in df.columns:
        print("Missing 'Label' column in dataset.")
        return
        
    y = df['Label']
    X = df.drop(columns=['Label'])
    
    # Save exact feature names and order
    feature_names = list(X.columns)
    with open(FEATURE_NAMES_PATH, "w") as f:
        json.dump(feature_names, f)

    # Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train Random Forest
    print("Training RandomForestClassifier...")
    clf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
    clf.fit(X_train, y_train)
    
    # Save model
    joblib.dump(clf, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Feature names saved to {FEATURE_NAMES_PATH}")

    # Optionally, we can save the test set for the evaluate_model.py script to use exactly
    test_data = X_test.copy()
    test_data['Label'] = y_test
    test_data.to_csv(ML_DIR / "datasets" / "test_split.csv", index=False)
    print("Test split saved for evaluation.")

if __name__ == "__main__":
    train()
