import fitz  # PyMuPDF
import io
import os
import tempfile
import logging
from PIL import Image
from typing import List
import gc
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class PDFService:
    @staticmethod
    def convert_pdf_to_images(pdf_path: str) -> List[Image.Image]:
        """Convert PDF to images using PyMuPDF with proper resource management"""
        try:
            return PDFService.pdf_to_images_pymupdf(pdf_path)
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            raise
    
    @staticmethod
    def pdf_to_images_pymupdf(pdf_path: str) -> List[Image.Image]:
        """Convert PDF to images using PyMuPDF with improved cleanup"""
        logger.info(f"Converting PDF to images: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = None
        images = []
        temp_files = []
        
        try:
            # Open PDF document
            doc = fitz.open(pdf_path)
            logger.info(f"Opened PDF with {len(doc)} pages")
            
            # Process each page
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    
                    # Convert page to image using memory buffer instead of temp file
                    # This avoids the file locking issue
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                    
                    # Convert to PIL Image directly from memory
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    images.append(img)
                    
                    # Clean up pixmap
                    pix = None
                    
                    logger.debug(f"Processed page {page_num + 1}")
                    
                except Exception as e:
                    logger.error(f"Error processing page {page_num}: {str(e)}")
                    continue
            
            if not images:
                raise Exception("No images could be extracted from PDF")
            
            logger.info(f"Successfully converted PDF to {len(images)} images")
            return images
            
        except Exception as e:
            logger.error(f"Failed to convert PDF: {str(e)}")
            # Clean up any images that were created
            for img in images:
                try:
                    img.close()
                except:
                    pass
            raise Exception(f"Failed to convert PDF using PyMuPDF: {str(e)}")
            
        finally:
            # Clean up document
            if doc:
                try:
                    doc.close()
                except Exception as e:
                    logger.warning(f"Error closing PDF document: {e}")
            
            # Clean up any temporary files (fallback)
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Could not clean up temp file {temp_file}: {e}")
            
            # Force garbage collection
            gc.collect()
    
    @staticmethod
    def pdf_to_images_alternative(pdf_path: str) -> List[Image.Image]:
        """Alternative PDF conversion method using temporary directory"""
        logger.info(f"Using alternative PDF conversion for: {pdf_path}")
        
        images = []
        doc = None
        temp_dir = None
        
        try:
            # Create a temporary directory for this conversion
            temp_dir = tempfile.mkdtemp(prefix="pdf_convert_")
            logger.debug(f"Created temp directory: {temp_dir}")
            
            # Open PDF
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    
                    # Create unique filename for this page
                    temp_filename = f"page_{page_num}_{uuid.uuid4().hex[:8]}.png"
                    temp_image_path = os.path.join(temp_dir, temp_filename)
                    
                    # Get pixmap and save to temp file
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    pix.save(temp_image_path)
                    
                    # Load image from file
                    img = Image.open(temp_image_path)
                    # Create a copy in memory so we can delete the temp file
                    img_copy = img.copy()
                    img.close()
                    
                    # Clean up temp file immediately
                    try:
                        os.unlink(temp_image_path)
                    except Exception as e:
                        logger.warning(f"Could not delete temp image {temp_image_path}: {e}")
                    
                    images.append(img_copy)
                    pix = None
                    
                except Exception as e:
                    logger.error(f"Error processing page {page_num}: {e}")
                    continue
            
            return images
            
        except Exception as e:
            logger.error(f"Alternative PDF conversion failed: {e}")
            # Clean up any created images
            for img in images:
                try:
                    img.close()
                except:
                    pass
            raise
            
        finally:
            # Clean up document
            if doc:
                try:
                    doc.close()
                except:
                    pass
            
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.debug(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Could not clean up temp directory {temp_dir}: {e}")
            
            gc.collect()
    
    @staticmethod
    def get_pdf_info(pdf_path: str) -> dict:
        """Get information about a PDF file"""
        try:
            doc = fitz.open(pdf_path)
            info = {
                'page_count': len(doc),
                'metadata': doc.metadata,
                'is_encrypted': doc.needs_pass,
            }
            doc.close()
            return info
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def validate_pdf(pdf_path: str) -> bool:
        """Validate if file is a proper PDF"""
        try:
            doc = fitz.open(pdf_path)
            is_valid = len(doc) > 0
            doc.close()
            return is_valid
        except Exception:
            return False