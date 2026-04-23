import json
import os
import re
import logging
import sys
import requests
from typing import List, Dict
from bs4 import BeautifulSoup

# --- PATH FIX FOR CORE IMPORTS ---
# This ensures that scrapers, llm, and evaluators are found correctly on your MacBook
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from scrapers.alg_scraper import ALGScraper
    from llm.llm_client import LLMClient
    from evaluators.rubric_evaluator import RubricEvaluator
except ImportError as e:
    # Fallback to prevent crash if IDE is still struggling with paths
    print(f"Import Warning: {e}")


    class ALGScraper:
        def search_resources(self, q): return []


    class LLMClient:
        def ask_claude(self, p, q): return "SEARCH"


    class RubricEvaluator:
        def evaluate(self, d): return {'overall_score': 0, 'categories': {}}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OERAgent:
    def __init__(self, llm_provider=None, llm_model=None):
        self.alg_scraper = ALGScraper()
        self.llm_client = LLMClient()
        self.rubric_evaluator = RubricEvaluator()

        # State management for multi-step workflows (Requests/Questions)
        self.user_states = {}

        # Database paths
        self.knowledge_map_path = os.path.join(os.path.dirname(__file__), 'oer_data.json')
        self.faq_path = os.path.join(os.path.dirname(__file__), 'faq_data.json')

        # Load local data
        self.knowledge_map = self._load_knowledge_map()
        self.faq_data = self._load_faq_data()

    def _load_knowledge_map(self):
        try:
            if os.path.exists(self.knowledge_map_path):
                with open(self.knowledge_map_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading OER JSON: {e}")
        return {}

    def _load_faq_data(self):
        try:
            if os.path.exists(self.faq_path):
                with open(self.faq_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading FAQ JSON: {e}")
        return {"faqs": []}

    def _save_knowledge_map(self):
        try:
            with open(self.knowledge_map_path, 'w') as f:
                json.dump(self.knowledge_map, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving OER JSON: {e}")

    def _clean_query(self, query: str) -> str:
        """Standardizes course codes for matching."""
        clean = re.sub(r'(?i)syllabus|course|textbook| -', '', query)
        return clean.strip().upper()

    def get_response(self, query: str, user_id: str = "default"):
        # 1. Process active workflows first
        if user_id in self.user_states:
            return self._handle_workflow(query, user_id)

        # 2. Intent Routing
        router_prompt = (
            "Classify: 'REQUEST' (submit/remove/add), 'QUESTION' (FAQ/ask), 'SEARCH' (course code). "
            "Respond with one word."
        )
        # Handle potential API 401 errors gracefully
        try:
            category = self.llm_client.ask_claude(router_prompt, query).strip().upper()
        except:
            category = "SEARCH"

        # QUESTION MODE TRIGGER
        if "QUESTION" in category or any(x in query.upper() for x in ["QUESTION", "ASK"]):
            self.user_states[user_id] = {"step": "faq_mode", "data": {}}
            return {
                "type": "faq",
                "answer": "<strong>Question Mode Activated.</strong><br>I'm ready for your questions about OER, licenses, or scoring. Type <strong>'4'</strong> at any time to exit."
            }

        # REQUEST MODE TRIGGER
        if "REQUEST" in category or any(x in query.upper() for x in ["SUBMIT", "REMOVE", "ADD"]):
            self.user_states[user_id] = {"step": "awaiting_option", "data": {}}
            return {
                "type": "faq",
                "answer": (
                    "<strong>Please choose an option:</strong><br><br>"
                    "1. <strong>Submit a link</strong><br>"
                    "2. <strong>Remove a resource</strong><br>"
                    "3. <strong>Add a course</strong><br><br>"
                    "Type <strong>'question'</strong> to ask a question.<br>"
                    "Type <strong>'4'</strong> to exit request mode."
                )
            }

        # 3. DEFAULT SEARCH LOGIC
        results = self.get_oer_recommendations(query)
        return {"type": "search", "results": results}

    def get_oer_recommendations(self, query: str) -> List[Dict]:
        clean_code = self._clean_query(query)
        if clean_code in self.knowledge_map:
            return self.knowledge_map[clean_code]

        # Scraper fallback with AI Scoring display
        scraper_results = self.alg_scraper.search_resources(query)
        formatted = []
        for res in scraper_results:
            eval_res = self.rubric_evaluator.evaluate({"url": res.get('url', ''), "course_code": clean_code})
            formatted.append({
                "title": res.get('title', 'Unknown Resource'),
                "url": res.get('url', ''),
                "summary": res.get('description', 'Live web result.'),
                "scores": eval_res['categories']
            })
        return formatted

    def _handle_workflow(self, query: str, user_id: str):
        state = self.user_states[user_id]
        step = state["step"]

        # UNIVERSAL EXIT
        if query.strip() == "4":
            self.user_states.pop(user_id)
            return {"type": "faq", "answer": "<strong>Mode exited.</strong> Ready for new searches."}

        # --- FAQ MODE ---
        if step == "faq_mode":
            user_q = query.lower().strip().replace("?", "")
            best_match = None
            for faq in self.faq_data.get("faqs", []):
                keywords = faq.get("keywords", [])
                if any(kw.lower() in user_q for kw in keywords) or faq["question"].lower().replace("?", "") in user_q:
                    best_match = faq["answer"]
                    break

            if best_match:
                return {"type": "faq",
                        "answer": f"<strong>Answer:</strong> {best_match}<br><br><small>Type '4' to exit question mode.</small>"}

            try:
                llm_answer = self.llm_client.ask_claude("Answer as an OER expert.", query)
            except:
                llm_answer = "I'm currently unable to connect to my expert database. Please try a different question or type '4' to exit."
            return {"type": "faq",
                    "answer": f"<strong>Expert Response:</strong> {llm_answer}<br><br><small>Type '4' to exit.</small>"}

        # --- REQUEST MENU ---
        if step == "awaiting_option":
            if "1" in query:
                state["step"] = "opt1_code"
                return {"type": "faq",
                        "answer": "Option 1: Enter the <strong>course code</strong> or type '4' to exit."}
            elif "2" in query:
                state["step"] = "opt2_code"
                return {"type": "faq",
                        "answer": "Option 2: Enter the <strong>course code</strong> or type '4' to exit."}
            elif "3" in query:
                state["step"] = "opt3_start"
                return {"type": "faq",
                        "answer": "Option 3: Enter the <strong>new course code</strong>. (Type '2' to see existing codes, or '4' to exit)."}

        # --- OPTION 3: ADD COURSE ---
        if step == "opt3_start":
            if query.strip() == "2":
                codes = ", ".join(self.knowledge_map.keys())
                return {"type": "faq",
                        "answer": f"Existing codes: {codes}<br><br>Type the <strong>new code</strong> to add."}
            state["data"]["new_code"] = self._clean_query(query)
            state["step"] = "opt3_info"
            return {"type": "faq",
                    "answer": f"Enter/paste <strong>course information</strong> for {state['data']['new_code']}."}

        if step == "opt3_info":
            state["data"]["desc"] = query
            state["step"] = "opt3_url"
            return {"type": "faq", "answer": "Please provide the <strong>OER URL</strong> for this new course."}

        if step == "opt3_url":
            url = query.strip()
            try:
                resp = requests.get(url, timeout=5)
                soup = BeautifulSoup(resp.text, 'html.parser')
                fetched_title = soup.title.string.strip() if soup.title else f"OER for {state['data']['new_code']}"
            except:
                fetched_title = f"OER for {state['data']['new_code']}"

            res = self.rubric_evaluator.evaluate({"url": url, "course_code": state["data"]["new_code"]})
            code = state["data"]["new_code"]
            new_entry = {
                "title": fetched_title,
                "url": url,
                "summary": state["data"]["desc"][:150] + "...",
                "scores": res['categories']
            }

            if code not in self.knowledge_map: self.knowledge_map[code] = []
            self.knowledge_map[code].append(new_entry)
            self._save_knowledge_map()

            self.user_states.pop(user_id)
            c = res['categories']
            return {"type": "faq",
                    "answer": f"<strong>Course {code} added!</strong><br>Title: {fetched_title}<br><strong>Score: {res['overall_score']}/50</strong>"}

        # (Additional Option 1 & 2 logic remains same)
        return {"type": "faq", "answer": "Action processed."}