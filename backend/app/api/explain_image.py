import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.cnn_prediction import get_cnn_prediction
from explainability.gradcam_service import generate_gradcam

router = APIRouter()

class ExplainImageRequest(BaseModel):
    image: str

class ExplainImageResponse(BaseModel):
    cnn_prediction: str
    confidence: float
    heatmap_url: str
    original_image_url: str

@router.post("/explain/image", response_model=ExplainImageResponse)
def explain_image(request: ExplainImageRequest):
    # The frontend is sending the relative path from the backend root
    # e.g., "screenshots/paypal.png"
    image_path = request.image.strip()
    
    if not image_path:
        raise HTTPException(status_code=400, detail="Image path cannot be empty")
        
    # Resolve the absolute path
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    abs_image_path = os.path.join(root_dir, os.path.normpath(image_path))
    
    if not os.path.exists(abs_image_path):
        raise HTTPException(status_code=400, detail=f"Image not found at {image_path}")
        
    try:
        # 1. Get prediction
        cnn_result = get_cnn_prediction(abs_image_path)
        prediction = cnn_result["prediction"]
        confidence = round(cnn_result["probability"] * 100, 2)
        
        # 2. Generate Grad-CAM heatmap
        heatmap_rel_path = generate_gradcam(abs_image_path)
        
        # We ensure paths use forward slashes for URLs
        heatmap_url = "/" + heatmap_rel_path.replace("\\", "/")
        original_image_url = "/" + image_path.replace("\\", "/")
        
        return ExplainImageResponse(
            cnn_prediction=prediction,
            confidence=confidence,
            heatmap_url=heatmap_url,
            original_image_url=original_image_url
        )
        
    except ValueError as e:
        # Grad-CAM specific internal errors
        raise HTTPException(status_code=500, detail=f"Failed to generate heatmap: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")
