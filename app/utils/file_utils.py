import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from app.core.config import settings
import logging
from pathlib import Path
import asyncio
import gc

logger = logging.getLogger(__name__)

class FileUtils:
    @staticmethod
    def validate_file(file: UploadFile):
        """Validate uploaded file"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Check file extension
        allowed_extensions = ['.pdf']
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (e.g., max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if hasattr(file, 'size') and file.size > max_size:
            raise HTTPException(
                status_code=400, 
                detail="File size too large. Maximum size: 10MB"
            )
    
    @staticmethod
    async def save_temp_file(file: UploadFile) -> str:
        """Save uploaded file to temporary location with proper file handling"""
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        temp_file_path = os.path.join(settings.UPLOAD_DIR, temp_filename)
        
        try:
            # Ensure file pointer is at the beginning
            await file.seek(0)
            
            # Save file with proper async handling
            async with aiofiles.open(temp_file_path, 'wb') as temp_file:
                # Read in chunks to handle large files better
                chunk_size = 8192  # 8KB chunks
                while chunk := await file.read(chunk_size):
                    await temp_file.write(chunk)
            
            # Verify file was saved
            if not os.path.exists(temp_file_path):
                raise HTTPException(status_code=500, detail="Failed to save temporary file")
            
            logger.info(f"Temporary file saved successfully: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            # Clean up partial file if it exists
            if os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            logger.error(f"Failed to save temporary file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    @staticmethod
    async def cleanup_temp_file(file_path: str) -> bool:
        """Clean up temporary file with enhanced error handling"""
        if not file_path or not os.path.exists(file_path):
            return True
        
        # Force garbage collection to release any handles
        gc.collect()
        
        # Try multiple cleanup strategies
        strategies = [
            lambda: os.unlink(file_path),
            lambda: Path(file_path).unlink(),
            lambda: FileUtils._rename_and_delete(file_path)
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                strategy()
                logger.info(f"Temp file cleanup successful with strategy {i+1}: {file_path}")
                return True
                
            except (PermissionError, OSError) as e:
                if i < len(strategies) - 1:
                    logger.warning(f"Cleanup strategy {i+1} failed for {file_path}: {e}. Trying next strategy...")
                    await asyncio.sleep(0.1)  # Brief delay before next attempt
                else:
                    logger.error(f"All cleanup strategies failed for {file_path}: {e}")
                    return False
        
        return False
    
    @staticmethod
    def _rename_and_delete(file_path: str):
        """Rename file before deletion - sometimes helps with locked files"""
        temp_name = f"{file_path}.delete_me_{uuid.uuid4().hex[:8]}"
        os.rename(file_path, temp_name)
        os.unlink(temp_name)
    
    @staticmethod
    async def ensure_file_closed(file_path: str, max_wait: float = 2.0):
        """Ensure file is not being used by another process"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                # Try to open the file exclusively
                with open(file_path, 'r+b') as f:
                    pass  # File is accessible
                return True
            except (PermissionError, OSError):
                await asyncio.sleep(0.1)
        
        logger.warning(f"File may still be in use after {max_wait}s: {file_path}")
        return False
    
    @staticmethod
    def cleanup_directory(directory: str, pattern: str = "*"):
        """Clean up files in a directory matching a pattern"""
        try:
            dir_path = Path(directory)
            if dir_path.exists():
                for file_path in dir_path.glob(pattern):
                    if file_path.is_file():
                        try:
                            file_path.unlink()
                            logger.debug(f"Cleaned up: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to cleanup {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning directory {directory}: {e}")
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """Get information about a file"""
        try:
            stat_info = os.stat(file_path)
            return {
                'size': stat_info.st_size,
                'created': stat_info.st_ctime,
                'modified': stat_info.st_mtime,
                'exists': True
            }
        except Exception:
            return {'exists': False}