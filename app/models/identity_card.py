from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.config.database import Base
import enum

class CardType(enum.Enum):
    AADHAAR = "aadhaar"
    PAN = "pan"
    VOTER_ID = "voter_id"
    DRIVING_LICENSE = "driving_license"
    UNKNOWN = "unknown"

class IdentityCard(Base):
    __tablename__ = "identity_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    card_type = Column(Enum(CardType), default=CardType.UNKNOWN)
    
    # Extracted fields
    name = Column(String(255))
    email = Column(String(255))
    contact = Column(String(20))
    aadhaar_number = Column(String(12))
    pan_number = Column(String(10))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    
    # Extracted raw text
    raw_text = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())