from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import scan, capture, scan_image, scan_full, explain_url, explain_image

app = FastAPI(title="Phishing URL Detector API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os

app.include_router(scan.router)
app.include_router(capture.router)
app.include_router(scan_image.router)
app.include_router(scan_full.router)
app.include_router(explain_url.router)
app.include_router(explain_image.router)

# Mount static files for screenshots and generated explanations
root_dir = os.path.dirname(os.path.dirname(__file__))
screenshots_dir = os.path.join(root_dir, "screenshots")
if not os.path.exists(screenshots_dir):
    os.makedirs(screenshots_dir)
app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")

explanations_dir = os.path.join(root_dir, "generated", "explanations")
if not os.path.exists(explanations_dir):
    os.makedirs(explanations_dir)
app.mount("/generated/explanations", StaticFiles(directory=explanations_dir), name="explanations")

@app.get("/")
def read_root():
    return {"message": "Phishing URL Detector API is running. POST to /scan/url"}
