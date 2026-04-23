import os
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        # Fallback to empty string to avoid immediate crash if env var is missing
        self.api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.client = None

        if self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Anthropic Init Error: {e}")

    def ask_claude(self, system_prompt: str, user_input: str):
        """Standard method to get a structured response from Claude."""
        if not self.client:
            return "ERROR: API Key missing or invalid."

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API Error: {e}")
            return "ERROR"

    def orchestrate_discovery(self, course_code, scraper_results):
        # ... existing logic kept for compatibility ...
        return scraper_results