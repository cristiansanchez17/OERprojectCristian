from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from oer_agent import OERAgent

app = Flask(__name__)
CORS(app)  # This allows your HTML file to talk to the server

agent = OERAgent()

@app.route('/')
def home():
    # This serves your index.html file
    return render_template('index.html')

@app.route('/oer')
def oer_api():
    # Adding "" as a default ensures the query is never None
    query = request.args.get('query', "") 
    response = agent.get_response(query)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 