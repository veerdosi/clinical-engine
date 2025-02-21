from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    # Return a mock response for a patient interaction
    return jsonify({
        "text": f"Mock response to '{user_input}': I'm feeling better now.",
        "timestamp": "2025-02-21T12:00:00"
    })

@app.route('/api/lab-report', methods=['GET'])
def lab_report():
    return jsonify({
        "report": "Mock lab report: CBC, CMP values within normal limits. Minor anomalies detected in inflammatory markers."
    })

@app.route('/api/imaging', methods=['GET'])
def imaging():
    return jsonify({
        "image_url": "https://via.placeholder.com/400x300?text=Mock+Chest+X-ray"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
