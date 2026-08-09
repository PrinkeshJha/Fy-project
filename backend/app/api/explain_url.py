from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.feature_extractor import extract_features
from app.services.url_prediction import get_url_prediction
from explainability.shap_service import explain_features
from explainability.explanation_formatter import format_shap_explanation

router = APIRouter()

class ExplainURLRequest(BaseModel):
    url: str

class TopFeature(BaseModel):
    feature: str
    value: float
    impact: float
    direction: str

class Explanation(BaseModel):
    top_features: List[TopFeature]
    top_reasons: List[str]

class ExplainURLResponse(BaseModel):
    url: str
    prediction: str
    probability: float
    explanation: Optional[Explanation] = None

@router.post("/explain/url", response_model=ExplainURLResponse)
def explain_url(request: ExplainURLRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
        
    try:
        # 1. Extract features (we need the vector for SHAP)
        features, _ = extract_features(url)
        
        # 2. Get prediction
        url_result = get_url_prediction(url)
        prediction = url_result["prediction"]
        probability = round(url_result["probability"] * 100, 2)
        
        # 3. Compute SHAP explanations
        shap_result = explain_features(features)
        
        # 4. Format into human readable strings
        top_reasons = format_shap_explanation(shap_result)
        
        explanation = Explanation(
            top_features=[TopFeature(**f) for f in shap_result["top_features"]],
            top_reasons=top_reasons
        )
        
        return ExplainURLResponse(
            url=url,
            prediction=prediction,
            probability=probability,
            explanation=explanation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")
