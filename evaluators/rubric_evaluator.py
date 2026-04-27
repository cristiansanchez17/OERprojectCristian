import random


class RubricEvaluator:
    def evaluate(self, resource_data):
        url = resource_data.get('url', '').lower()
        # Simulated AI Analysis: Check for trusted educational domains
        is_trusted = any(domain in url for domain in ["openstax", "edu", "org"])

        # Logic to generate unique scores per category (out of 10)
        # In a real AI, this would use NLP to scan the webpage content
        scores = {
            "Relevance": random.randint(8, 10) if is_trusted else random.randint(5, 8),
            "Accuracy": 10 if "openstax" in url else random.randint(7, 9),
            "Clarity": random.randint(7, 10),
            "Completeness": random.randint(6, 10),
            "Accessibility": 10 if "manifold" in url else random.randint(8, 10)
        }

        overall = sum(scores.values())
        return {
            "overall_score": overall,
            "categories": scores
        }