from typing import Dict

class RubricEvaluator:
    """Evaluates OER resources using the GGC quality rubric"""
    
    def __init__(self):
        self.criteria = [
            'Relevance', 'Accuracy', 'Clarity', 
            'Completeness', 'Accessibility'
        ]
    
    # Inside your RubricEvaluator class
    def evaluate(self, resource):
    # 1. Define 'relevance' based on Course Code match
        course_code = resource.get('course_code', '').lower()
        title = resource.get('title', '').lower()
    
        if course_code and course_code in title:
            relevance = 10
        elif "composition" in title or "algebra" in title: # Subject match
            relevance = 7
        else:
            relevance = 5

    # 2. Define 'accuracy' (High for verified USG sources)
    # If it's a .edu or galileo link, it's highly accurate
        url = resource.get('url', '')
        accuracy = 10 if "galileo" in url or "manifold" in url else 8

    # 3. Define 'clarity' (Web-readers are clearer than PDFs)
        clarity = 10 if "manifold" in url or "openstax" in url else 7

    # 4. Define 'completeness' (Does it have a description/summary?)
        desc = resource.get('description', '')
        completeness = 10 if len(desc) > 100 else 6

    # 5. Define 'accessibility' (HTTPS is safer/more accessible)
        accessibility = 10 if url.startswith('https') else 5

    # 6. NOW these terms are defined, so we can add them up
        total_score = relevance + accuracy + clarity + completeness + accessibility
    
        return {
            "overall_score": total_score,
            "criteria_evaluations": {
                "Relevance": {"score": relevance},
                "Accuracy": {"score": accuracy},
                "Clarity": {"score": clarity},
                "Completeness": {"score": completeness},
                "Accessibility": {"score": accessibility}
        }
    }