from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.identity_card import IdentityCard, CardType
from app.schemas.identity_card import IdentityCardCreate, IdentityCardResponse, OCRResult
from app.services.pdf_service import PDFService
from app.services.ocr_service import OCRService
from app.utils.file_utils import FileUtils
import time
import os
import gc
import logging
from typing import Dict, Any, List
import threading
import atexit
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class OCRController:
    def __init__(self):
        self.pdf_service = PDFService()
        self.ocr_service = OCRService()
        self.file_utils = FileUtils()
        self._cleanup_queue = []
        self._cleanup_lock = threading.Lock()
        
        # Register cleanup on exit
        atexit.register(self._final_cleanup)
    
    async def process_identity_card(
        self, 
        file: UploadFile, 
        db: Session = Depends(get_db)
    ) -> OCRResult:
        """Process uploaded identity card PDF"""
        start_time = time.time()
        temp_file_path = None
        images = []
        
        try:
            # Validate file
            self.file_utils.validate_file(file)
            
            # Save uploaded file temporarily
            temp_file_path = await self.file_utils.save_temp_file(file)
            logger.info(f"Temporary file saved: {temp_file_path}")
            
            # Convert PDF to images with proper cleanup
            images = await self._convert_pdf_safely(temp_file_path)
            
            if not images:
                raise HTTPException(status_code=400, detail="Could not extract images from PDF")
            
            # Extract data using OCR
            extracted_data = self.ocr_service.process_identity_card(images)
            
            # Create database record
            card_data = IdentityCardCreate(
                filename=file.filename,
                card_type=CardType(extracted_data.get('card_type', 'unknown')),
                name=extracted_data.get('name'),
                email=extracted_data.get('email'),
                contact=extracted_data.get('contact'),
                aadhaar_number=extracted_data.get('aadhaar_number'),
                pan_number=extracted_data.get('pan_number'),
                pincode=extracted_data.get('pincode'),
                raw_text=extracted_data.get('raw_text')
            )
            
            # Save to database
            db_card = IdentityCard(**card_data.dict())
            db.add(db_card)
            db.commit()
            db.refresh(db_card)
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                success=True,
                message="Identity card processed successfully",
                data=IdentityCardResponse.from_orm(db_card),
                processing_time=round(processing_time, 2)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            processing_time = time.time() - start_time
            return OCRResult(
                success=False,
                message=f"Processing failed: {str(e)}",
                processing_time=round(processing_time, 2)
            )
        finally:
            # Clean up resources in proper order
            await self._cleanup_resources(images, temp_file_path)
    
    async def _convert_pdf_safely(self, temp_file_path: str) -> List:
        """Convert PDF to images with proper resource management"""
        try:
            # Ensure file is not locked by closing any previous handles
            gc.collect()  # Force garbage collection
            
            # Convert PDF to images
            images = self.pdf_service.convert_pdf_to_images(temp_file_path)
            
            # Force garbage collection after conversion
            gc.collect()
            
            return images
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            # Force cleanup of any temporary files created by PyMuPDF
            self._cleanup_pymupdf_temp_files()
            raise
    
    async def _cleanup_resources(self, images: List, temp_file_path: str):
        """Clean up all resources with proper error handling"""
        # Clear images first
        if images:
            try:
                images.clear()
                del images
            except Exception as e:
                logger.warning(f"Error clearing images: {e}")
        
        # Force garbage collection to release file handles
        gc.collect()
        
        # Clean up PyMuPDF temporary files
        self._cleanup_pymupdf_temp_files()
        
        # Clean up main temporary file
        if temp_file_path:
            await self._safe_file_cleanup(temp_file_path)
    
    def _cleanup_pymupdf_temp_files(self):
        """Clean up temporary files created by PyMuPDF"""
        import tempfile
        temp_dir = tempfile.gettempdir()
        
        try:
            temp_path = Path(temp_dir)
            # Look for PyMuPDF temporary files (usually start with 'tmp' and end with image extensions)
            for pattern in ['tmp*.ppm', 'tmp*.png', 'tmp*.jpg', 'tmp*.jpeg']:
                for temp_file in temp_path.glob(pattern):
                    try:
                        if temp_file.exists():
                            temp_file.unlink()
                            logger.debug(f"Cleaned up PyMuPDF temp file: {temp_file}")
                    except Exception as e:
                        logger.debug(f"Could not clean PyMuPDF temp file {temp_file}: {e}")
                        # Add to cleanup queue for later
                        with self._cleanup_lock:
                            self._cleanup_queue.append(str(temp_file))
        except Exception as e:
            logger.warning(f"Error during PyMuPDF temp file cleanup: {e}")
    
    async def _safe_file_cleanup(self, file_path: str):
        """Safely clean up a file with multiple strategies"""
        if not file_path or not os.path.exists(file_path):
            return
        
        # Strategy 1: Direct cleanup
        try:
            os.unlink(file_path)
            logger.info(f"Successfully cleaned up: {file_path}")
            return
        except (PermissionError, OSError) as e:
            logger.warning(f"Direct cleanup failed for {file_path}: {e}")
        
        # Strategy 2: Force cleanup with retries
        success = await self._force_cleanup_file(file_path)
        if success:
            return
        
        # Strategy 3: Add to delayed cleanup queue
        with self._cleanup_lock:
            self._cleanup_queue.append(file_path)
            logger.info(f"Added {file_path} to delayed cleanup queue")
    
    async def _force_cleanup_file(self, file_path: str, max_attempts: int = 5) -> bool:
        """Force cleanup of a file with multiple attempts and strategies"""
        import asyncio
        
        for attempt in range(max_attempts):
            try:
                # Force garbage collection before each attempt
                gc.collect()
                
                # Small delay to allow file handles to be released
                await asyncio.sleep(0.1 * (attempt + 1))
                
                if os.path.exists(file_path):
                    # Try different cleanup strategies
                    if attempt < 2:
                        # Standard unlink
                        os.unlink(file_path)
                    elif attempt < 4:
                        # Try with Path
                        Path(file_path).unlink()
                    else:
                        # Last resort: try to rename first, then delete
                        temp_name = f"{file_path}.delete_me"
                        try:
                            os.rename(file_path, temp_name)
                            os.unlink(temp_name)
                        except:
                            os.unlink(file_path)
                    
                    logger.info(f"Force cleanup successful on attempt {attempt + 1}: {file_path}")
                    return True
                else:
                    logger.info(f"File already deleted: {file_path}")
                    return True
                    
            except (PermissionError, OSError) as e:
                if attempt < max_attempts - 1:
                    logger.warning(f"Cleanup attempt {attempt + 1} failed for {file_path}: {e}. Retrying...")
                else:
                    logger.error(f"Failed to cleanup file after {max_attempts} attempts: {file_path}: {e}")
        
        return False
    
    def _final_cleanup(self):
        """Final cleanup on application exit"""
        with self._cleanup_lock:
            if self._cleanup_queue:
                logger.info(f"Performing final cleanup of {len(self._cleanup_queue)} files")
                for file_path in self._cleanup_queue:
                    try:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                            logger.debug(f"Final cleanup successful: {file_path}")
                    except Exception as e:
                        logger.warning(f"Final cleanup failed for {file_path}: {e}")
                
                self._cleanup_queue.clear()
    
    def get_identity_card(self, card_id: int, db: Session) -> IdentityCardResponse:
        """Get identity card by ID"""
        card = db.query(IdentityCard).filter(IdentityCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="Identity card not found")
        return IdentityCardResponse.from_orm(card)
    
    def get_all_identity_cards(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[IdentityCardResponse]:
        """Get all identity cards with pagination"""
        cards = db.query(IdentityCard).offset(skip).limit(limit).all()
        return [IdentityCardResponse.from_orm(card) for card in cards]