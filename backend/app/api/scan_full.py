import os
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.url_prediction import get_url_prediction
from app.services.cnn_prediction import get_cnn_prediction
from app.services.ensemble_service import ensemble_predict
from app.services.screenshot_service import capture_screenshot, WebsiteUnreachableError, InvalidURLError

router = APIRouter()

class ScanFullRequest(BaseModel):
    url: str

class ModelResult(BaseModel):
    prediction: str
    probability: float

class ScanFullResponse(BaseModel):
    url: str
    final_prediction: str
    risk_score: float
    risk_level: str
    url_model: ModelResult
    cnn_model: Optional[ModelResult] = None
    screenshot: Optional[str] = None
    note: Optional[str] = None
    reasons: Optional[List[str]] = None

@router.post("/scan/full", response_model=ScanFullResponse)
async def scan_full(request: ScanFullRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
        
    # Overall timeout for the whole pipeline to ensure it doesn't hang
    # We will enforce a generous 30s timeout on this endpoint's execution
    try:
        return await asyncio.wait_for(_run_full_pipeline(url), timeout=30.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Full scan pipeline timed out.")

async def _run_full_pipeline(url: str) -> ScanFullResponse:
    # 1. Evaluate URL model (Random Forest)
    try:
        url_result = get_url_prediction(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"URL Model evaluation failed: {str(e)}")

    url_prob = url_result["probability"]
    
    cnn_result = None
    screenshot_path = None
    note = None

    # 2. Capture Screenshot
    try:
        abs_screenshot_path = await capture_screenshot(url, full_page=True)
        # Convert to relative path for the API
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        screenshot_path = os.path.relpath(abs_screenshot_path, start=root_dir).replace("\\", "/")
        
        # 3. Evaluate CNN Model
        try:
            cnn_pred = get_cnn_prediction(abs_screenshot_path)
            cnn_result = {
                "prediction": cnn_pred["prediction"],
                "probability": cnn_pred["probability"]
            }
        except Exception as e:
            note = f"Visual analysis failed: {str(e)}"
            
    except InvalidURLError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WebsiteUnreachableError as e:
        note = f"Visual analysis unavailable: website unreachable"
    except Exception as e:
        note = f"Screenshot capture failed: {str(e)}"

    # 4. Ensemble Fusion
    if cnn_result:
        # Full ensemble
        ensemble_result = ensemble_predict(url_prob, cnn_result["probability"])
    else:
        # Graceful degradation: Fall back to URL model only
        ensemble_result = ensemble_predict(url_prob, url_prob, url_weight=1.0, cnn_weight=0.0)
        
    return ScanFullResponse(
        url=url,
        final_prediction=ensemble_result["final_prediction"],
        risk_score=round(ensemble_result["final_probability"] * 100, 2),
        risk_level=ensemble_result["risk_level"],
        url_model=ModelResult(
            prediction=url_result["prediction"],
            probability=round(url_prob * 100, 2)
        ),
        cnn_model=ModelResult(
            prediction=cnn_result["prediction"],
            probability=round(cnn_result["probability"] * 100, 2)
        ) if cnn_result else None,
        screenshot=screenshot_path,
        note=note,
        reasons=url_result.get("reasons", [])
    )
