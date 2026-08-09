import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.services.feature_extractor import extract_features
from ml.predict import predict as predict_rf
from app.services.screenshot_service import capture_screenshot
from ml.cnn.predict import predict as predict_cnn

router = APIRouter()

class ScanRequest(BaseModel):
    url: str

class Tag(BaseModel):
    type: str
    label: str

class ScanResponse(BaseModel):
    url: str
    verdict: str
    confidence: float
    tags: List[Tag]

@router.post("/scan/url", response_model=ScanResponse)
async def scan_url(request: ScanRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
        
    try:
        # 1. Extract URL features
        features, reasons = extract_features(url)
        
        # 2. Predict using Random Forest
        rf_result = predict_rf(features)
        
        # 3. Capture screenshot
        image_path = None
        try:
            image_path = await capture_screenshot(url, full_page=True)
        except Exception as e:
            print(f"Screenshot failed: {e}")
            
        # 4. Predict using CNN
        cnn_result = {"prediction": "Legitimate", "confidence": 0.0}
        if image_path:
            try:
                cnn_result = predict_cnn(image_path)
            except Exception as e:
                print(f"CNN failed: {e}")
                
        # 5. Combine Results
        rf_conf = rf_result["confidence"]
        cnn_conf = cnn_result["confidence"]
        rf_is_phish = rf_result["prediction"] == "Phishing"
        cnn_is_phish = cnn_result["prediction"] == "Phishing"
        
        # Calculate combined phishing probability
        rf_phish_prob = rf_conf if rf_is_phish else (100 - rf_conf)
        cnn_phish_prob = cnn_conf if cnn_is_phish else (100 - cnn_conf)
        
        combined_phish_prob = (rf_phish_prob + cnn_phish_prob) / 2
        
        if combined_phish_prob > 80:
            verdict = "danger"
            final_conf = combined_phish_prob
        elif combined_phish_prob > 50:
            verdict = "warning"
            final_conf = combined_phish_prob
        else:
            verdict = "safe"
            final_conf = 100 - combined_phish_prob
            
        # 6. Format tags
        tags = []
        for reason in reasons:
            tags.append(Tag(type="warning", label=reason))
            
        if rf_is_phish:
            tags.append(Tag(type="danger", label=f"URL Model: {rf_conf}% Phishing"))
        else:
            tags.append(Tag(type="safe", label=f"URL Model: Safe"))
            
        if image_path:
            if cnn_is_phish:
                tags.append(Tag(type="danger", label=f"Image Model: {cnn_conf}% Phishing"))
            else:
                tags.append(Tag(type="safe", label=f"Image Model: Safe"))
        else:
            tags.append(Tag(type="warning", label="Could not capture screenshot for CNN"))

        return ScanResponse(
            url=url,
            verdict=verdict,
            confidence=round(final_conf, 2),
            tags=tags
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
