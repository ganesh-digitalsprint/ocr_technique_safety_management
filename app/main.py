from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import identity_card
from app.config.database import create_tables
from app.core.config import settings
import os

# Create FastAPI app
app = FastAPI(
    title="Identity Card OCR API",
    description="Extract data from identity card PDFs using OCR",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(identity_card.router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create database tables
    create_tables()
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    print("🚀 Identity Card OCR API started successfully!")
    print(f"📁 Upload directory: {settings.UPLOAD_DIR}")
    print(f"🔧 Tesseract path: {settings.TESSERACT_PATH}")

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Identity Card OCR API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )