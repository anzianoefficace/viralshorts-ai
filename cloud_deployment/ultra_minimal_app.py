"""
Ultra minimal Flask app for Render test
"""
import os
import sys

print("🚀 Starting ultra minimal app...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"PORT: {os.environ.get('PORT', 'NOT_SET')}")

try:
    from flask import Flask
    print("✅ Flask imported successfully")
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "Hello from Render! App is working!"
    
    if __name__ == '__main__':
        port = int(os.environ.get("PORT", 10000))
        print(f"🚀 Starting Flask on port {port}")
        app.run(host='0.0.0.0', port=port)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
