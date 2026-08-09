import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ml.cnn.predict import predict

router = APIRouter()

class ScanImageRequest(BaseModel):
    image: str

class ScanImageResponse(BaseModel):
    prediction: str
    confidence: float

@router.post("/scan/image", response_model=ScanImageResponse)
def scan_image(request: ScanImageRequest):
    image_path = request.image.strip()
    if not image_path:
        raise HTTPException(status_code=400, detail="Image path cannot be empty")
        
    # Assuming path is relative to the backend root (e.g. 'screenshots/paypal.png')
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    absolute_image_path = os.path.join(root_dir, image_path)
    
    if not os.path.exists(absolute_image_path):
        raise HTTPException(status_code=400, detail=f"Image not found: {image_path}")
        
    try:
        # Run CNN prediction
        result = predict(absolute_image_path)
        
        return ScanImageResponse(
            prediction=result["prediction"],
            confidence=result["confidence"]
        )
        
    except ValueError as e:
        # Handle unreadable image or corrupt file
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
