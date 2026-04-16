import os
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY', '')

    def orchestrate_discovery(self, course_code, scraper_results):
        """
        Uses LLM logic to rank scraper results. 
        If no API key, it acts as a pass-through for the best scraper result.
        """
        if not self.api_key:
            logger.info("No API Key found. Running LLMClient in fallback mode.")
            # Fallback: Just return the first valid result from the scraper
            if scraper_results:
                best_match = scraper_results[0]
                best_match['identified_by'] = 'Scraper (Fallback)'
                return [best_match]
            return []

        # Real API logic would go here
        return scraper_results 