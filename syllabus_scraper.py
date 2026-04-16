import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class SyllabusScraper:
    def __init__(self, base_url='https://ggc.simplesyllabus.com'):
        self.base_url = base_url

    def get_course_context(self, course_code):
        """Extracts course title and description to improve OER search relevance."""
        # Simple Syllabus often requires JS, so this is a simplified metadata fetcher
        # for the prototype's logic flow.
        return {
            "course_code": course_code,
            "description": f"Standard curriculum for {course_code}.",
            "search_keywords": course_code.split()
        }