import random


class RubricEvaluator:
    def evaluate(self, resource_data):
        url = resource_data.get('url', '').lower()
        is_edu = ".edu" in url or "openstax" in url

        # Generate dynamic scores
        scores = {
            "Relevance": random.randint(9, 10) if is_edu else random.randint(7, 9),
            "Accuracy": 10 if is_edu else random.randint(8, 10),
            "Clarity": random.randint(7, 10),
            "Completeness": random.randint(8, 10),
            "Accessibility": random.randint(9, 10)
        }

        return {
            "overall_score": sum(scores.values()),
            "categories": scores
        }