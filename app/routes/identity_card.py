from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.controllers.ocr_controller import OCRController
from app.schemas.identity_card import OCRResult, IdentityCardResponse, FileUploadResponse
from typing import List

router = APIRouter(prefix="/api/v1/identity-cards", tags=["Identity Cards"])

# Initialize controller
ocr_controller = OCRController()

@router.post("/upload", response_model=OCRResult)
async def upload_identity_card(
    file: UploadFile = File(..., description="PDF file of identity card"),
    db: Session = Depends(get_db)
):
    """
    Upload and process an identity card PDF
    
    - **file**: PDF file containing identity card (Aadhaar, PAN, etc.)
    
    Returns extracted information including:
    - Name, Email, Contact
    - Aadhaar number, PAN number
    - Address details (city, state, pincode)
    """
    return await ocr_controller.process_identity_card(file, db)

@router.get("/{card_id}", response_model=IdentityCardResponse)
def get_identity_card(
    card_id: int,
    db: Session = Depends(get_db)
):
    """Get identity card details by ID"""
    return ocr_controller.get_identity_card(card_id, db)

@router.get("/", response_model=List[IdentityCardResponse])
def get_all_identity_cards(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to fetch"),
    db: Session = Depends(get_db)
):
    """Get all identity cards with pagination"""
    return ocr_controller.get_all_identity_cards(db, skip, limit)

@router.get("/health/check")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Identity Card OCR API is running"}