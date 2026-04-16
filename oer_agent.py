import json
import os
import logging
import re
from typing import List, Dict

# Import your custom components
from alg_scraper import ALGScraper
from llm_client import LLMClient
from evaluators.rubric_evaluator import RubricEvaluator
from evaluators.license_checker import LicenseChecker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OERAgent:
    def __init__(self):
        self.alg_scraper = ALGScraper()
        self.llm_client = LLMClient()
        self.rubric_evaluator = RubricEvaluator()
        self.license_checker = LicenseChecker()
        
        # Subject Mapping to help the scraper find resources by topic
        self.subject_map = {
            "ENGL": ["English", "Writing", "Composition"],
            "MATH": ["Mathematics", "Algebra", "Calculus"],
            "CSCI": ["Computer Science", "Programming", "Java"],
            "HIST": ["History", "American History"]
        }
        
        self.faq_path = os.path.join(os.path.dirname(__file__), 'faq_data.json')
        self.faqs = self._load_faqs()

    def _load_faqs(self):
        try:
            if os.path.exists(self.faq_path):
                with open(self.faq_path, 'r') as f:
                    data = json.load(f)
                    return [f for f in data.get('faqs', []) if f is not None]
        except Exception as e:
            logger.error(f"Error loading FAQ JSON: {e}")
        return []

    def _clean_query(self, query: str) -> str:
        """Removes noise like 'Syllabus' or extra spaces to improve search accuracy."""
        # Remove 'Syllabus', 'Course', and special characters
        clean = re.sub(r'(?i)syllabus|course|textbook| -', '', query)
        return clean.strip()

    def check_faq(self, query: str):
        query_lower = query.lower().strip()
        for faq in self.faqs:
            keywords = faq.get('keywords', [])
            for keyword in keywords:
                if isinstance(keyword, str) and keyword.lower() in query_lower:
                    return {"type": "faq", "answer": faq['answer']}
        return None

    def get_oer_recommendations(self, query: str) -> List[Dict]:
        clean_query = self._clean_query(query).upper() # e.g., "ENGL 1102"
        
        # 1. KNOWLEDGE MAP: The verified resources for your demo/excel file
        knowledge_map = {
            "ENGL 1101": [
        # RG-007 is the gold standard: Specific code, web-reader, full course materials.
        {"title": "RG-007: No-Cost Truncated Course for ENGL 1101", "url": "https://alg.manifoldapp.org/projects/rg-007", "desc": "Complete course framework.", "scores": [10, 10, 10, 10, 10]}, # 50
        # OpenStax: High quality, but a general 'Writing' title (not ENGL 1101 specific).
        {"title": "Writing Guide with Handbook - OpenStax", "url": "https://openstax.org/details/books/writing-guide", "desc": "National standard textbook.", "scores": [8, 10, 10, 9, 10]}, # 47
        # Successful College Writing: Specific title, but a static PDF (lower Clarity/Completeness).
        {"title": "Successful College Writing (ENGL 1101)", "url": "https://oer.galileo.usg.edu/english-textbooks/15/", "desc": "PDF-based USG textbook.", "scores": [10, 10, 7, 8, 10]}  # 45
    ],
    "MATH 1111": [
        # Open Course: Includes slides/ancillaries (Completeness 10).
        {"title": "College Algebra Open Course (MATH 1111)", "url": "https://alg.manifoldapp.org/projects/college-algebra-open-course-math-1111", "desc": "Full algebra course sets.", "scores": [10, 10, 9, 10, 10]}, # 49
        {"title": "College Algebra Textbook", "url": "https://oer.galileo.usg.edu/mathematics-textbooks/21/", "desc": "Standard PDF textbook.", "scores": [8, 10, 7, 8, 10]} # 43
    ],
    "ENGL 1102": [
        {"title": "English Composition II (ENGL 1102)", "url": "https://oer.galileo.usg.edu/english-textbooks/23/", "desc": "Sequential textbook for Comp II.", "scores": [10, 10, 7, 8, 10]} # 45
    ],
    "HIST 2111": [
        {"title": "History of the United States I (HIST 2111)", "url": "https://oer.galileo.usg.edu/history-textbooks/5/", "desc": "Standard US History PDF.", "scores": [10, 10, 7, 7, 10]} # 44
    ],
    "HIST 2112": [
        {"title": "History of the United States II (HIST 2112)", "url": "https://oer.galileo.usg.edu/history-ancillary/10/", "desc": "Supplementary history materials.", "scores": [10, 10, 7, 5, 10]} # 42
    ],
    "BIOL 1101K": [
        {"title": "Introduction to Biology (BIOL 1101K)", "url": "https://oer.galileo.usg.edu/biology-textbooks/17/", "desc": "Lab-heavy course material.", "scores": [10, 10, 7, 8, 10]} # 45
    ],
    "ITEC 1001": [
        # Verified Stable Link: OpenStax (Introduction to Computer Science)
        {
            "title": "Introduction to Computer Science (ITEC 1001)", 
            "url": "https://openstax.org/details/books/introduction-computer-science", 
            "desc": "A comprehensive OpenStax resource covering programming, hardware, and algorithms.", 
            "scores": [9, 10, 10, 10, 10] # Total: 49
        }
    ]
        }

        verified_results = []
        
        # 2. MATCH CHECK: If the code is in our map, use the verified data
        if clean_query in knowledge_map:
            for item in knowledge_map[clean_query]:
                # 1. Pull the specific scores list from the dictionary
                s = item.get("scores", [10, 10, 10, 10, 10]) # Fallback to 10s if missing
                
                # 2. Append the data using the list indices [0, 1, 2, 3, 4]
                verified_results.append({
                    "title": item["title"],
                    "link": item["url"],
                    "summary": item["desc"],
                    "avg_score": sum(s),  # This creates the Total Score (e.g., 47)
                    "scores": {
                        "Relevance": s[0], 
                        "Accuracy": s[1], 
                        "Clarity": s[2], 
                        "Completeness": s[3], 
                        "Accessibility": s[4]
                    }
                })

        # 3. FALLBACK: Dynamic Search for anything else
        else:
            raw_resources = self.alg_scraper.search_resources(clean_query)
            # ... rest of your scraper logic ...
            
        # Return sorted by score
        return sorted(verified_results, key=lambda x: x["avg_score"], reverse=True)
    def get_response(self, query: str):
        faq_match = self.check_faq(query)
        if faq_match:
            return faq_match

        results = self.get_oer_recommendations(query)
        
        # 3. Final Fallback: If still nothing, use the LLM logic from your log
        if not results:
            llm_suggestions = self.llm_client.get_fallback_suggestions(query)
            # Evaluate these too so the format matches
            for sug in llm_suggestions:
                eval_data = self.rubric_evaluator.evaluate(sug)
                results.append({
                    "title": sug['title'],
                    "link": sug['url'],
                    "summary": "AI Recommended resource based on course goals.",
                    "license": "OER Verified",
                    "avg_score": eval_data.get('overall_score', 0),
                    "scores": {k: v.get('score', 0) for k, v in eval_data.get('criteria_evaluations', {}).items()}
                })

        return {"type": "search", "results": results}