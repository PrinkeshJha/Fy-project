import json
import numpy as np
from pathlib import Path

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

CNN_DIR = Path(__file__).parent
DATASET_DIR = CNN_DIR / "dataset"
MODEL_PATH = CNN_DIR / "model.keras"
RESULTS_PATH = CNN_DIR / "evaluation_results.json"

def evaluate():
    if not TF_AVAILABLE:
        print("TensorFlow is not installed. Skipping evaluation.")
        return
        
    if not MODEL_PATH.exists():
        print("Model not found. Train first.")
        return
        
    print("Loading model for evaluation...")
    model = load_model(MODEL_PATH)
    
    datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)
    val_generator = datagen.flow_from_directory(
        DATASET_DIR,
        target_size=(224, 224),
        batch_size=8,
        class_mode='binary',
        subset='validation',
        shuffle=False # IMPORTANT: keep order for sklearn metrics
    )
    
    # Get true labels
    y_true = val_generator.classes
    
    # Predict
    print("Running predictions on validation set...")
    predictions = model.predict(val_generator)
    y_pred = (predictions > 0.5).astype(int).flatten()
    
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0,0,0,0)
    
    results = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1_score": float(f1),
        "confusion_matrix": {
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp)
        }
    }
    
    print("--- CNN Evaluation Results ---")
    print(f"Accuracy: {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall: {rec:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print(f"Confusion Matrix:\n{cm}")
    
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    evaluate()
