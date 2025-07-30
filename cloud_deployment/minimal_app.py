"""
Minimal Flask app for Render.com deployment test
"""
import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request

# Basic Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>ViralShortsAI - MINIMAL TEST</h1>
    <p>Status: <strong style="color: green;">ONLINE</strong></p>
    <p>Time: {}</p>
    <p>Python: {}</p>
    <p>Working Directory: {}</p>
    <a href="/test">Test API</a>
    """.format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sys.version,
        os.getcwd()
    )

@app.route('/test')
def test():
    return jsonify({
        "status": "success",
        "message": "Minimal app is working!",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "env_vars": {
            "PORT": os.environ.get("PORT"),
            "PYTHON_VERSION": os.environ.get("PYTHON_VERSION")
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting minimal Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
