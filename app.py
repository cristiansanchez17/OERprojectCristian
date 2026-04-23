from flask import Flask, request, jsonify, render_template
from flask_cors import CORS


# 1. Initialize the app first
app = Flask(__name__)
CORS(app)

# 2. Import and initialize the agent AFTER app setup
from oer_agent import OERAgent
agent = OERAgent()

@app.route('/')
def home():
    # This serves your index.html file
    return render_template('index.html')

@app.route('/oer')
def oer_api():
    query = request.args.get('query', "")
    user_id = request.remote_addr
    try:
        response = agent.get_response(query, user_id)
        if not response:
            return jsonify({"type": "faq", "answer": "No response from agent."})
        return jsonify(response)
    except Exception as e:
        return jsonify({"type": "faq", "answer": f"System Error: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)