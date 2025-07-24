import pytesseract
from PIL import Image
import os
from typing import List, Dict, Any
from app.core.config import settings
from app.utils.regex_patterns import DataExtractor

class OCRService:
    def __init__(self):
        # Set tesseract path
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from a single image using OCR"""
        try:
            # OCR configuration for better results
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@.-:/ '
            
            # Extract text
            text = pytesseract.image_to_string(image, config=custom_config, lang='eng+hin')
            return text.strip()
        except Exception as e:
            raise Exception(f"OCR failed: {str(e)}")
    
    def extract_text_from_images(self, images: List[Image.Image]) -> str:
        """Extract text from multiple images"""
        all_text = []
        
        for i, image in enumerate(images):
            try:
                text = self.extract_text_from_image(image)
                if text.strip():
                    all_text.append(f"--- Page {i+1} ---\n{text}")
            except Exception as e:
                print(f"Failed to extract text from page {i+1}: {str(e)}")
                continue
        
        return "\n\n".join(all_text)
    
    def process_identity_card(self, images: List[Image.Image]) -> Dict[str, Any]:
        """Process identity card images and extract structured data"""
        try:
            # Extract raw text from all images
            raw_text = self.extract_text_from_images(images)
            
            if not raw_text.strip():
                raise Exception("No text could be extracted from the images")
            
            # Extract structured data using regex patterns
            extracted_data = DataExtractor.extract_all_data(raw_text)
            
            return extracted_data
        except Exception as e:
            raise Exception(f"Failed to process identity card: {str(e)}")