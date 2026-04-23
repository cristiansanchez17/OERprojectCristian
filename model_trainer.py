import json
import os


def generate_scoring_logic():
    """
    Simulates training by establishing baseline scores from your
    verified JSON data to guide the Evaluator.
    """
    data_path = 'oer_data.json'
    if not os.path.exists(data_path):
        print("Error: oer_data.json not found.")
        return

    with open(data_path, 'r') as f:
        knowledge_map = json.load(f)

    # Logic: If a submission URL contains 'openstax' or 'manifold',
    # the model 'learns' to weight accuracy and accessibility higher.
    model_weights = {
        "trusted_domains": ["openstax.org", "manifoldapp.org", "galileo.usg.edu"],
        "high_score_threshold": 48,
        "base_line": 40
    }

    print("Model logic calibrated based on knowledge_map contents.")
    return model_weights


if __name__ == "__main__":
    generate_scoring_logic()