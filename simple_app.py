"""
ViralShortsAI - Simple Flask App for Render
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <h1>🚀 ViralShortsAI</h1>
    <p>✅ App is running on Render!</p>
    <p><a href="/health">Health Check</a></p>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "message": "ViralShortsAI is running successfully!",
        "app": "ViralShortsAI",
        "version": "1.0.0"
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        "app_name": "ViralShortsAI",
        "status": "online",
        "ready_for_automation": True
    })

if __name__ == '__main__':
    app.run(debug=True)
