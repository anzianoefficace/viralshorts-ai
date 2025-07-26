"""
🚀 ViralShortsAI Render.com Deployment App - Versione Semplificata
"""

import os
import sys
import logging
from datetime import datetime
from threading import Thread
import time

# Configurazione logging per Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import Flask (sempre disponibile)
from flask import Flask, jsonify, request

# Inizializza Flask
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'render-viralshorts-key-2025')

# Variabili globali
backend = None
daily_poster = None
init_status = {'success': False, 'error': None, 'components': {}}

def init_app():
    """Inizializza l'applicazione per Render con debug completo"""
    global backend, daily_poster, init_status
    
    try:
        logger.info("🚀 Starting ViralShortsAI initialization...")
        
        # 1. Crea directory necessarie
        logger.info("📁 Creating directories...")
        directories = ['data/downloads', 'data/processed', 'data/uploads', 'data/reports', 'data/temp', 'logs']
        for dir_path in directories:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"✅ Created {dir_path}")
        
        # 2. Prova importazioni specifiche
        logger.info("📦 Testing imports...")
        
        # Aggiungi path corretti
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(current_dir)
        sys.path.insert(0, parent_dir)
        logger.info(f"Added path: {parent_dir}")
        
        # Test import database
        try:
            from database import Database
            logger.info("✅ Database import successful")
            init_status['components']['database'] = True
            
            # Test inizializzazione database
            db = Database('data/viral_shorts.db')
            db.close()
            logger.info("✅ Database initialized")
            
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            init_status['components']['database'] = False
        
        # Test import daily poster
        try:
            from daily_auto_poster import DailyAutoPoster
            logger.info("✅ DailyAutoPoster import successful")
            init_status['components']['daily_poster'] = True
        except Exception as e:
            logger.error(f"❌ DailyAutoPoster error: {e}")
            init_status['components']['daily_poster'] = False
        
        # Test import main backend
        try:
            from main import ViralShortsBackend
            logger.info("✅ ViralShortsBackend import successful")
            init_status['components']['backend'] = True
            
            # Inizializza backend
            backend = ViralShortsBackend()
            logger.info("✅ Backend initialized")
            
        except Exception as e:
            logger.error(f"❌ Backend error: {e}")
            init_status['components']['backend'] = False
        
        # Inizializza daily poster se possibile
        if 'DailyAutoPoster' in locals() and backend:
            try:
                daily_poster = DailyAutoPoster(backend=backend)
                logger.info("✅ Daily poster created")
                init_status['components']['poster_created'] = True
            except Exception as e:
                logger.error(f"❌ Daily poster creation error: {e}")
                init_status['components']['poster_created'] = False
        
        init_status['success'] = True
        logger.info("✅ ViralShortsAI initialization completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ General initialization error: {e}")
        init_status['error'] = str(e)
        return False

@app.route('/')
def dashboard():
    """Dashboard semplificata con debug info"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ViralShortsAI Debug Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
            .card {{ background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 8px; border: 1px solid #dee2e6; }}
            .success {{ color: #28a745; }}
            .error {{ color: #dc3545; }}
            .warning {{ color: #ffc107; }}
            .button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }}
            .button:hover {{ background: #0056b3; }}
            pre {{ background: #f1f1f1; padding: 10px; border-radius: 4px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <h1>🚀 ViralShortsAI Debug Dashboard</h1>
        
        <div class="card">
            <h3>🔧 System Status</h3>
            <p class="success">✅ Flask App: Running</p>
            <p class="success">✅ Platform: Render.com</p>
            <p class="success">✅ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="card">
            <h3>📦 Component Status</h3>
            <p>Initialization Success: <span class="{'success' if init_status['success'] else 'error'}">{'✅ Yes' if init_status['success'] else '❌ No'}</span></p>
            <p>Backend Available: <span class="{'success' if backend else 'error'}">{'✅ Yes' if backend else '❌ No'}</span></p>
            <p>Daily Poster Available: <span class="{'success' if daily_poster else 'error'}">{'✅ Yes' if daily_poster else '❌ No'}</span></p>
            
            <h4>Component Details:</h4>
            <pre>{init_status}</pre>
        </div>
        
        <div class="card">
            <h3>🧪 API Tests</h3>
            <button class="button" onclick="testAPI()">Test API</button>
            <button class="button" onclick="testStartPoster()">Test Start Poster</button>
            <button class="button" onclick="testStatus()">Test Status</button>
            <div id="test-results" style="margin-top: 10px;"></div>
        </div>
        
        <div class="card">
            <h3>📝 Actions</h3>
            <button class="button" onclick="location.href='/health'">Health Check</button>
            <button class="button" onclick="location.href='/api/debug'">Debug Info</button>
            <button class="button" onclick="location.reload()">Refresh</button>
        </div>
        
        <script>
        function showResult(result) {{
            document.getElementById('test-results').innerHTML = '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
        }}
        
        function testAPI() {{
            fetch('/api/test')
                .then(r => r.json())
                .then(showResult)
                .catch(e => showResult({{error: e.message}}));
        }}
        
        function testStartPoster() {{
            fetch('/api/start_poster', {{method: 'POST'}})
                .then(r => r.json())
                .then(showResult)
                .catch(e => showResult({{error: e.message}}));
        }}
        
        function testStatus() {{
            fetch('/api/status')
                .then(r => r.json())
                .then(showResult)
                .catch(e => showResult({{error: e.message}}));
        }}
        </script>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    """Health check dettagliato"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'viralshorts-render',
        'backend_ready': backend is not None,
        'poster_ready': daily_poster is not None,
        'init_status': init_status,
        'environment': {
            'python_path': sys.path[:3],
            'working_dir': os.getcwd(),
            'files_exist': {
                'database.py': os.path.exists('../database.py'),
                'main.py': os.path.exists('../main.py'),
                'daily_auto_poster.py': os.path.exists('../daily_auto_poster.py')
            }
        }
    })

@app.route('/api/debug')
def api_debug():
    """Debug API dettagliato"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'working_directory': os.getcwd(),
        'python_path': sys.path,
        'environment_vars': {k: v for k, v in os.environ.items() if 'SECRET' not in k and 'TOKEN' not in k and 'KEY' not in k},
        'init_status': init_status,
        'files_in_current_dir': os.listdir('.'),
        'files_in_parent_dir': os.listdir('..') if os.path.exists('..') else 'N/A',
        'backend_available': backend is not None,
        'poster_available': daily_poster is not None
    })

@app.route('/api/test')
def test_api():
    """Test API semplice"""
    return jsonify({
        'status': 'success',
        'message': 'API is working!',
        'timestamp': datetime.now().isoformat(),
        'poster_available': daily_poster is not None,
        'backend_available': backend is not None,
        'init_success': init_status['success']
    })

@app.route('/api/status')
def api_status():
    """Status API"""
    return jsonify({
        'system': {
            'online': True,
            'platform': 'Render.com',
            'timestamp': datetime.now().isoformat()
        },
        'poster': daily_poster.get_status() if daily_poster else {'is_running': False, 'error': 'Not available'},
        'database': {'connected': init_status['components'].get('database', False)},
        'init_status': init_status
    })

@app.route('/api/start_poster', methods=['POST'])
def start_poster():
    """Avvia daily poster con debug"""
    try:
        if daily_poster:
            daily_poster.start()
            return jsonify({'status': 'success', 'message': 'Daily poster started'})
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Daily poster not available',
                'debug': init_status
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'debug': init_status
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Starting ViralShortsAI Debug Mode on Render.com...")
    
    # Inizializza app
    init_success = init_app()
    logger.info(f"Initialization result: {init_success}")
    
    # Avvia Flask
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
