from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.services.feature_extractor import extract_features
from ml.predict import predict

router = APIRouter()

class ScanRequest(BaseModel):
    url: str

class ScanResponse(BaseModel):
    url: str
    prediction: str
    confidence: float
    risk_level: str
    reasons: List[str]

@router.post("/scan/url", response_model=ScanResponse)
def scan_url(request: ScanRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
        
    try:
        # Extract features and reasons
        features, reasons = extract_features(url)
        
        # Predict using the ML model
        result = predict(features)
        
        return ScanResponse(
            url=url,
            prediction=result["prediction"],
            confidence=result["confidence"],
            risk_level=result["risk_level"],
            reasons=reasons
        )
    except Exception as e:
        # Avoid crashing the endpoint, return a 500 with the error message
        raise HTTPException(status_code=500, detail=str(e))
