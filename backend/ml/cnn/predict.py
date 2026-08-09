import os
import numpy as np
from pathlib import Path

# Try to import tensorflow, fallback gracefully for tests if not available yet
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing.image import load_img, img_to_array
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

ML_DIR = Path(__file__).parent
MODEL_PATH = ML_DIR / "model.keras"

model = None

def load_cnn_model():
    global model
    if not TF_AVAILABLE:
        print("TensorFlow not available. CNN model will not be loaded.")
        return
        
    if not MODEL_PATH.exists():
        print(f"CNN model not found at {MODEL_PATH}. Prediction will fail until trained.")
        return
        
    try:
        model = load_model(MODEL_PATH)
    except Exception as e:
        print(f"Failed to load CNN model: {e}")

# Load model once at module initialization
load_cnn_model()

def predict(image_path: str) -> dict:
    global model
    
    if not os.path.exists(image_path):
        raise ValueError(f"Image not found at {image_path}")
        
    if not TF_AVAILABLE:
        raise RuntimeError("TensorFlow is not installed.")
        
    if model is None:
        raise RuntimeError("CNN Model is not loaded. Train the model first.")

    try:
        # Load and preprocess image to match MobileNetV2 inputs
        # MobileNetV2 expects 224x224 RGB
        img = load_img(image_path, target_size=(224, 224))
        img_array = img_to_array(img)
        
        # Normalize pixel values to [0, 1] as typically done for ImageDataGenerator rescale=1./255
        img_array = img_array / 255.0
        
        # Expand dimensions to create a batch of 1
        img_batch = np.expand_dims(img_array, axis=0)
        
        # Predict
        predictions = model.predict(img_batch, verbose=0)[0] # softmax returns an array of probabilities
        
        # Classes: 0: legit ss, 1: phishing ss, 2: waste ss
        phishing_prob = predictions[1]
        
        is_phishing = phishing_prob > 0.5
        
        confidence = float(phishing_prob * 100 if is_phishing else (1 - phishing_prob) * 100)
        
        return {
            "prediction": "Phishing" if is_phishing else "Legitimate",
            "confidence": round(confidence, 2)
        }
        
    except Exception as e:
        raise ValueError(f"Failed to process image {image_path}: {str(e)}")
