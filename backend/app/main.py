from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import scan, capture, scan_image, scan_full

app = FastAPI(title="Phishing URL Detector API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router)
app.include_router(capture.router)
app.include_router(scan_image.router)
app.include_router(scan_full.router)

@app.get("/")
def read_root():
    return {"message": "Phishing URL Detector API is running. POST to /scan/url"}
