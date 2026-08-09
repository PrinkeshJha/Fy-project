from ml.cnn.predict import predict as cnn_predict

def get_cnn_prediction(image_path: str) -> dict:
    """
    Wrapper around the CNN model (Module 4).
    Evaluates the screenshot and returns a normalized prediction dictionary.
    Output: { "prediction": "phishing" | "legitimate", "probability": float (0.0 to 1.0) }
    """
    result = cnn_predict(image_path)
    
    # cnn_predict returns confidence as a percentage (0-100)
    prediction_label = result["prediction"].lower() # "phishing" or "legitimate"
    confidence = result["confidence"] / 100.0
    
    if prediction_label == "phishing":
        probability = confidence
    else:
        # If it predicts legitimate with 80% confidence, then probability of phishing is 20%
        probability = 1.0 - confidence
        
    return {
        "prediction": "phishing" if probability >= 0.5 else "legitimate",
        "probability": probability
    }
