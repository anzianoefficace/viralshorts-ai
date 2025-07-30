"""
Super simple Flask app for Render with gunicorn
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World! ViralShortsAI is working on Render!"

@app.route('/health')
def health():
    return {"status": "ok", "message": "App is running"}

if __name__ == '__main__':
    app.run(debug=True)
