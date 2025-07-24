from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.models.identity_card import CardType
import re

class IdentityCardBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class IdentityCardCreate(IdentityCardBase):
    filename: str
    card_type: CardType = CardType.UNKNOWN
    raw_text: Optional[str] = None

class IdentityCardResponse(IdentityCardBase):
    id: int
    filename: str
    card_type: CardType
    raw_text: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OCRResult(BaseModel):
    success: bool
    message: str
    data: Optional[IdentityCardResponse] = None
    processing_time: Optional[float] = None

class FileUploadResponse(BaseModel):
    message: str
    filename: str
    size: int
    content_type: str