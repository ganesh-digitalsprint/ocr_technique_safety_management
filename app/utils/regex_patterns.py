import re
from typing import Optional, Dict, Any

class RegexPatterns:
    # Aadhaar patterns
    AADHAAR_PATTERNS = [
        r'\b\d{4}\s*\d{4}\s*\d{4}\b',  # 1234 5678 9012
        r'\b\d{12}\b',  # 123456789012
    ]
    
    # PAN patterns
    PAN_PATTERNS = [
        r'\b[A-Z]{5}\d{4}[A-Z]{1}\b',  # ABCDE1234F
    ]
    
    # Email patterns
    EMAIL_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    ]
    
    # Phone patterns
    PHONE_PATTERNS = [
        r'\b(?:\+91|91)?[-.\s]?[6-9]\d{9}\b',  # Indian mobile
        r'\b\d{10}\b',  # 10 digit number
    ]
    
    # Pincode patterns
    PINCODE_PATTERNS = [
        r'\b\d{6}\b',  # 6 digit pincode
    ]
    
    # Name patterns (after specific keywords)
    NAME_PATTERNS = [
        r'(?:Name|NAME|name)[\s:]+([A-Za-z\s]{2,50})',
        r'(?:नाम|Name)[\s:]+([A-Za-z\s]{2,50})',
    ]

class DataExtractor:
    @staticmethod
    def extract_aadhaar(text: str) -> Optional[str]:
        """Extract Aadhaar number from text"""
        for pattern in RegexPatterns.AADHAAR_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean and validate
                clean_match = re.sub(r'\s+', '', match)
                if len(clean_match) == 12 and clean_match.isdigit():
                    return clean_match
        return None
    
    @staticmethod
    def extract_pan(text: str) -> Optional[str]:
        """Extract PAN number from text"""
        for pattern in RegexPatterns.PAN_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].upper()
        return None
    
    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract email from text"""
        for pattern in RegexPatterns.EMAIL_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].lower()
        return None
    
    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extract phone number from text"""
        for pattern in RegexPatterns.PHONE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean the match
                clean_match = re.sub(r'[^\d]', '', match)
                if len(clean_match) == 10 and clean_match[0] in '6789':
                    return clean_match
                elif len(clean_match) == 12 and clean_match.startswith('91'):
                    return clean_match[2:]
        return None
    
    @staticmethod
    def extract_pincode(text: str) -> Optional[str]:
        """Extract pincode from text"""
        for pattern in RegexPatterns.PINCODE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if match.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
                    return match
        return None
    
    @staticmethod
    def extract_name(text: str) -> Optional[str]:
        """Extract name from text"""
        for pattern in RegexPatterns.NAME_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                name = matches[0].strip()
                # Basic validation
                if 2 <= len(name) <= 50 and name.replace(' ', '').isalpha():
                    return name.title()
        return None
    
    @staticmethod
    def determine_card_type(text: str) -> str:
        """Determine card type based on text content"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['aadhaar', 'आधार', 'uidai']):
            return 'aadhaar'
        elif any(keyword in text_lower for keyword in ['income tax', 'pan card', 'permanent account']):
            return 'pan'
        elif any(keyword in text_lower for keyword in ['election', 'voter', 'electoral']):
            return 'voter_id'
        elif any(keyword in text_lower for keyword in ['driving', 'license', 'transport']):
            return 'driving_license'
        else:
            return 'unknown'
    
    @staticmethod
    def extract_all_data(text: str) -> Dict[str, Any]:
        """Extract all possible data from text"""
        return {
            'name': DataExtractor.extract_name(text),
            'email': DataExtractor.extract_email(text),
            'contact': DataExtractor.extract_phone(text),
            'aadhaar_number': DataExtractor.extract_aadhaar(text),
            'pan_number': DataExtractor.extract_pan(text),
            'pincode': DataExtractor.extract_pincode(text),
            'card_type': DataExtractor.determine_card_type(text),
            'raw_text': text
        }