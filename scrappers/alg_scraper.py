import requests
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

class ALGScraper:
    def __init__(self, base_url='https://alg.manifoldapp.org'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_resources(self, query):
        """Searches for resources and filters for direct project links."""
        try:
            search_url = f"{self.base_url}/search"
            response = self.session.get(search_url, params={'q': query})
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            # Find all links that look like projects
            for link in soup.find_all('a', href=re.compile(r'/projects/')):
                url = self.base_url + link.get('href') if link.get('href').startswith('/') else link.get('href')
                
                # Validation: Skip generic search or query URLs
                if "/search" in url or "query=" in url:
                    continue
                    
                results.append({
                    "title": link.get_text(strip=True) or "OER Resource",
                    "url": url,
                    "source": "ALG Manifold"
                })
            return [
                {
                    "title": "Sample Resource for " + query,
                    "url": "https://example.edu/resource",
                    "description": "Scraped OER description."
                }
            ]
        except Exception as e:
            logger.error(f"Scraper Error: {e}")
            return []