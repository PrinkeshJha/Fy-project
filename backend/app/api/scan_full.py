import os
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.url_prediction import get_url_prediction
from app.services.cnn_prediction import get_cnn_prediction
from app.services.ensemble_service import ensemble_predict
from app.services.screenshot_service import capture_screenshot, WebsiteUnreachableError, InvalidURLError
from app.services.feature_extractor import extract_features
from explainability.shap_service import explain_features
from explainability.explanation_formatter import format_shap_explanation
from explainability.gradcam_service import generate_gradcam

router = APIRouter()

class ScanFullRequest(BaseModel):
    url: str

class ModelResult(BaseModel):
    prediction: str
    probability: float

class URLExplanation(BaseModel):
    method: str
    top_reasons: List[str]

class VisualExplanation(BaseModel):
    method: str
    heatmap_url: str

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
    url_explanation: Optional[URLExplanation] = None
    visual_explanation: Optional[VisualExplanation] = None

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
    url_explanation = None
    try:
        # We extract features directly so we can reuse them for SHAP
        features, _ = extract_features(url)
        url_result = get_url_prediction(url)
        
        # Best-effort SHAP explanation
        try:
            shap_res = explain_features(features)
            top_reasons = format_shap_explanation(shap_res)
            url_explanation = URLExplanation(method="SHAP", top_reasons=top_reasons)
        except Exception as e:
            print(f"SHAP explanation failed: {e}")
            
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
            
            # Best-effort Grad-CAM explanation
            try:
                heatmap_rel = generate_gradcam(abs_screenshot_path)
                heatmap_url = "/" + heatmap_rel.replace("\\", "/")
                visual_explanation = VisualExplanation(method="Grad-CAM", heatmap_url=heatmap_url)
            except Exception as e:
                print(f"Grad-CAM explanation failed: {e}")
                
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
        reasons=url_result.get("reasons", []),
        url_explanation=url_explanation,
        visual_explanation=visual_explanation if 'visual_explanation' in locals() else None
    )
