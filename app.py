from flask import Flask, jsonify
from signals import generate_signals

app = Flask(__name__)

@app.route('/signals', methods=['GET'])
def signals():
    result = generate_signals()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
