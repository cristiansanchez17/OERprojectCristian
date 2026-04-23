import re
from typing import Dict, List

class LicenseChecker:
    """Verifies whether resources have open educational licenses"""
    
    OPEN_LICENSES = [
        r'cc\s*by[-\s]?(\d+\.?\d*)?', 
        r'cc\s*by[-\s]?sa', 
        r'creative\s+commons',
        r'public\s+domain',
        r'open\s+access',
        r'cc0'
    ]
    
    def check_license(self, resource: Dict) -> Dict:
        description = resource.get('description', '').lower()
        url = resource.get('url', '').lower()
        search_text = f"{description} {url}"
        
        result = {
            'has_open_license': False,
            'license_type': 'Unknown',
            'confidence': 'low'
        }
        
        for pattern in self.OPEN_LICENSES:
            if re.search(pattern, search_text):
                result['has_open_license'] = True
                result['license_type'] = 'Open (CC/Public Domain)'
                result['confidence'] = 'high'
                return result
                
        return result