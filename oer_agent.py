import json
import os
import re
import logging


class OERAgent:
    def __init__(self):
        # 1. Setup Paths
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_map_path = os.path.join(self.base_path, 'oer_data.json')
        self.faq_path = os.path.join(self.base_path, 'faq_data.json')

        # 2. Initialize Data
        self.user_states = {}
        self.knowledge_map = self._load_json(self.knowledge_map_path)
        self.faq_data = self._load_json(self.faq_path)

        # 3. Startup Debug (Check your terminal for these!)
        print(f"--- OER Agent Initialized ---")
        print(f"Knowledge Base: {list(self.knowledge_map.keys())}")

    def _load_json(self, path):
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return {}

    def _save_knowledge_map(self):
        try:
            with open(self.knowledge_map_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_map, f, indent=4)
        except Exception as e:
            print(f"Save Error: {e}")

    def _clean_query(self, query: str) -> str:
        """Standardizes input to 'DEPT ####' or 'DEPT ####K' format.

        BUG FIX: Old regex r'([A-Z]{4})\s*(\d{4})' would drop trailing
        letter suffixes like the 'K' in 'BIOL 1101K', causing lookups to
        silently fail. Updated to r'([A-Z]{3,4})\s*(\d{4}[A-Z]?)' to
        capture optional suffix and support 3-letter dept codes.
        """
        q = query.upper().strip()
        match = re.search(r'([A-Z]{3,4})\s*(\d{4}[A-Z]?)', q)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        return q

    def calculate_rubric_score(self, url: str, code: str) -> dict:
        """Simple deterministic scoring logic for OER resources.

        NOTE: rubric_evaluator.py uses random.randint() which produces
        different scores every evaluation — violating consistency. This
        method is intentionally deterministic and is the correct one to use.
        """
        url = url.lower()
        cats = {"Relevance": 7, "Accuracy": 8, "Clarity": 8, "Completeness": 8, "Accessibility": 10}

        if "galileo" in url or "usg.edu" in url:
            cats["Accuracy"] = 10
            cats["Relevance"] = 10
        if "manifold" in url or "openstax" in url:
            cats["Clarity"] = 10
            cats["Completeness"] = 10

        return {"total": sum(cats.values()), "categories": cats}

    def get_response(self, query: str, user_id: str = "default"):
        user_query = query.strip().upper()
        clean_code = self._clean_query(query)

        # PRIORITY 1: GLOBAL EXIT
        if user_query in ["EXIT", "QUIT", "STOP", "4"]:
            self.user_states.pop(user_id, None)
            return {"type": "faq", "answer": "<strong>System Reset.</strong> Ready for search."}

        # PRIORITY 2: SEARCH (Matches "ENGL 1101", "BIOL 1101K" etc.)
        if clean_code in self.knowledge_map:
            self.user_states.pop(user_id, None)  # Exit any menu if searching
            return self._format_search_response(self.knowledge_map[clean_code])

        # PRIORITY 3: ACTIVE WORKFLOW
        if user_id in self.user_states:
            # BUG FIX: If the user is in a workflow but types a valid-looking
            # course code that isn't in the map, it fell through to workflow.
            # That's correct behavior — keep it, but handle gracefully inside.
            return self._handle_workflow(query, user_id)

        # PRIORITY 4: MENU TRIGGER
        if any(x in user_query for x in ["REQUEST", "ADD", "REMOVE", "SUBMIT"]):
            self.user_states[user_id] = {"step": "awaiting_option", "data": {}}
            return {"type": "faq",
                    "answer": "<strong>Options:</strong> 1. Score a Resource | 2. Remove a Resource | 3. Add a Course"}

        # PRIORITY 5: QUESTION MODE TRIGGER
        # BUG FIX: "question" keyword was advertised in the UI welcome message
        # but had NO handler here — it just fell through to _handle_faq which
        # also failed (wrong field name). Now we set a question state so the
        # agent knows to treat the NEXT message as an FAQ query, and we confirm
        # to the user they're in question mode.
        if "QUESTION" in user_query:
            self.user_states[user_id] = {"step": "awaiting_question", "data": {}}
            return {"type": "faq",
                    "answer": "❓ <strong>Question Mode.</strong> What would you like to know about OER? (Type <em>exit</em> to return to search.)"}

        # PRIORITY 6: FAQ/QUESTION FALLBACK
        return self._handle_faq(query)

    def _handle_workflow(self, query: str, user_id: str):
        state = self.user_states[user_id]
        step = state["step"]
        user_query = query.strip().lower()

        # Standard Exit
        if user_query in ["exit", "quit", "4"]:
            self.user_states.pop(user_id)
            return {"type": "faq",
                    "answer": "<strong>Mode Exited.</strong> You can now search by course code or type 'question'."}

        # BUG FIX: Handle the question mode step added in get_response above.
        # Previously there was no "awaiting_question" step so users who typed
        # "question" would get stuck — their follow-up question had no handler.
        if step == "awaiting_question":
            self.user_states.pop(user_id)
            return self._handle_faq(query)

        if step == "awaiting_option":
            if "1" in query:
                state["step"] = "opt1_code"
                return {"type": "faq", "answer": "Enter <strong>Course Code</strong> (e.g. ENGL 1101):"}
            if "2" in query:
                state["step"] = "opt2_code"
                return {"type": "faq", "answer": "Enter <strong>Course Code</strong> to manage resources:"}
            if "3" in query:
                state["step"] = "opt3_start"
                return {"type": "faq", "answer": "Enter <strong>New Course Code</strong> to add. <br><em>Type '2' to "
                                                 "display a list of all courses registered in the system.</em>"}
            return {"type": "faq",
                    "answer": "Please choose <strong>1</strong>, <strong>2</strong>, or <strong>3</strong>. Type <em>exit</em> to cancel."}

        if step == "opt1_code":
            state["data"]["code"] = query.strip().upper()
            state["step"] = "opt1_url"
            return {"type": "faq", "answer": "Paste the <strong>OER URL</strong>:"}

        if step == "opt1_url":
            url = query.strip()
            res = self.calculate_rubric_score(url, state["data"].get("code", ""))

            cats = res["categories"]
            score_txt = (f"Rel: {cats['Relevance']} | Acc: {cats['Accuracy']} | "
                         f"Cla: {cats['Clarity']} | Comp: {cats['Completeness']} | "
                         f"Accs: {cats['Accessibility']}")

            self.user_states.pop(user_id)
            return {
                "type": "faq",
                "answer": (f"<strong>URL Scored:</strong> {url}<br>"
                           f"📊 <strong>Total Score: {res['total']}/50</strong><br>"
                           f"<small>{score_txt}</small><br>Mode exited.")
            }

        if step == "opt2_code":
            # BUG FIX: The opt2_code block used raw query for lookup but the
            # knowledge_map is keyed by cleaned codes like "ENGL 1101". Without
            # _clean_query here, "ENGL1101" (no space) would fail to find the course.
            code = self._clean_query(query)
            if code in self.knowledge_map and self.knowledge_map[code]:
                state["data"]["code"] = code
                state["step"] = "opt2_url"
                output = [f"Found resources for <strong>{code}</strong>:<br>"]
                for i, r in enumerate(self.knowledge_map[code]):
                    output.append(f"{i + 1}. {r['title']}<br><small>{r['url']}</small><br>")
                output.append("<br>Paste the <strong>URL</strong> of the resource you want to remove:")
                return {"type": "faq", "answer": "".join(output)}
            return {"type": "faq",
                    "answer": f"No resources found for <strong>{code}</strong>. Type <em>exit</em> to restart."}

        if step == "opt2_url":
            target_url = query.strip()
            code = state["data"]["code"]
            original_count = len(self.knowledge_map[code])
            self.knowledge_map[code] = [r for r in self.knowledge_map[code] if r['url'] != target_url]

            if len(self.knowledge_map[code]) < original_count:
                self._save_knowledge_map()
                self.user_states.pop(user_id)
                return {"type": "faq", "answer": "<strong>Resource Removed.</strong>"}
            return {"type": "faq", "answer": "URL not found in list. Try again or type <em>exit</em>."}

        # OPTION 3: ADD NEW COURSE
        if step == "opt3_start":
            if query.strip() == '2':
                existing_courses = list(self.knowledge_map.keys())
                if not existing_courses:
                    return {"type": "faq",
                            "answer": "No courses currently in system. Please enter <strong>New Course Code</strong> to add:"}
                course_list = ", ".join(existing_courses)
                return {"type": "faq",
                        "answer": f"<strong>Current Courses:</strong> {course_list}<br><br>Please enter the <strong>"
                                  f"New Course Code</strong> you wish to add:"}
            state["data"]["new_code"] = self._clean_query(query)
            state["step"] = "opt3_info"
            return {"type": "faq",
                    "answer": f"Enter a brief <strong>description</strong> for <em>{state['data']['new_code']}</em>:"}

        if step == "opt3_info":
            state["data"]["desc"] = query
            state["step"] = "opt3_url"
            return {"type": "faq", "answer": "Enter the <strong>URL</strong> for this resource:"}

        if step == "opt3_url":
            url = query.strip()
            code = state["data"]["new_code"]
            res = self.calculate_rubric_score(url, code)

            if code not in self.knowledge_map:
                self.knowledge_map[code] = []

            self.knowledge_map[code].append({
                "title": f"OER Resource for {code}",
                "url": url,
                "summary": state["data"]["desc"],
                "scores": res["categories"]
            })

            self._save_knowledge_map()
            self.user_states.pop(user_id)
            return {"type": "faq",
                    "answer": f"<strong>Success!</strong> Course {code} added with a score of {res['total']}/50."}

        return {"type": "faq", "answer": "Processing your request..."}

    def _handle_faq(self, query):
        """Keyword matching against FAQ question text.

        BUG FIX: Original code called faq.get("keywords", []) but faq_data.json
        has NO "keywords" field — only "question" and "answer". This meant every
        FAQ lookup returned [] and the match never fired, making question mode
        completely non-functional. Fix: match against words in the "question" field.
        """
        q = query.lower()
        best_match = None
        best_score = 0

        for faq in self.faq_data.get("faqs", []):
            question_words = set(faq.get("question", "").lower().split())
            query_words = set(q.split())
            # Score = number of overlapping meaningful words (ignore short stop words)
            overlap = len([w for w in query_words & question_words if len(w) > 3])
            if overlap > best_score:
                best_score = overlap
                best_match = faq

        if best_match and best_score > 0:
            return {"type": "faq", "answer": best_match["answer"]}

        return {"type": "faq",
                "answer": "I couldn't find an answer to that. Try rephrasing, or search by course code (e.g. <strong>ENGL 1101</strong>)."}

    def _format_search_response(self, results):
        """Return structured results array for the frontend to render as cards.

        BUG FIX: Original returned {"type": "search", "answer": html_string}.
        The frontend (index.html line 109) checks data.results and iterates
        with data.results.forEach(...) — it never uses data.answer for search
        type. Also, the frontend uses book.link but JSON stores the field as
        "url". Fix: return a "results" list and remap "url" -> "link".
        """
        if not results:
            return {"type": "faq", "answer": "No resources found for that course code."}

        formatted = []
        for r in results:
            formatted.append({
                "title": r.get("title", "Untitled Resource"),
                "link": r.get("url", "#"),  # frontend uses book.link
                "summary": r.get("summary", ""),
                "scores": r.get("scores", {})
            })

        return {"type": "search", "results": formatted}