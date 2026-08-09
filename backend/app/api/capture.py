import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.screenshot_service import capture_screenshot, InvalidURLError, WebsiteUnreachableError

router = APIRouter()

class CaptureRequest(BaseModel):
    url: str

class CaptureResponse(BaseModel):
    image: str

@router.post("/capture", response_model=CaptureResponse)
async def capture_url(request: CaptureRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
        
    try:
        # Capture screenshot
        image_path = await capture_screenshot(url, full_page=True)
        
        # Convert absolute path to relative or simple recognizable string for the API response
        # Using forward slashes for cross-platform consistency
        relative_path = os.path.relpath(image_path, start=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        relative_path = relative_path.replace("\\", "/")
        
        return CaptureResponse(image=relative_path)
        
    except InvalidURLError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WebsiteUnreachableError as e:
        raise HTTPException(status_code=502, detail=f"Website Unreachable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
