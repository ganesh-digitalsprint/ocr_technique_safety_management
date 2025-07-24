from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "identity_card_db"
    
    # OCR Paths
    TESSERACT_PATH: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    POPPLER_PATH: Optional[str] = None
    
    # App Config
    UPLOAD_DIR: str = "uploads/temp"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf"
    
    # Database URL
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"

settings = Settings()