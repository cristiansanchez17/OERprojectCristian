from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from oer_agent import OERAgent

app = Flask(__name__)
CORS(app)
agent = OERAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/oer')
def oer_search():
    user_input = request.args.get('query', '')
    response = agent.get_response(user_input)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
