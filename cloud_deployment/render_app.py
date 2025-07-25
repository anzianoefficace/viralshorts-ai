"""
🚀 ViralShortsAI Render.com Deployment App
Versione ottimizzata per hosting gratuito su Render.com
"""

import os
import sys
import logging
from datetime import datetime
from threading import Thread
import time

# Aggiungi il path dell'app
sys.path.append('/opt/render/project/src')
sys.path.append(os.path.dirname(__file__))

# Configurazione logging per Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import componenti principali
try:
    from flask import Flask, render_template, jsonify, request
    from database import Database
    from daily_auto_poster import DailyAutoPoster
    from main import ViralShortsBackend
    logger.info("✅ Imports successful")
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    # Fallback per ambiente Render
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "ViralShortsAI is starting up..."
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "service": "viralshorts-render"})

# Configurazione Flask per Render
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'render-viralshorts-key-2025')

# Variabili globali
backend = None
daily_poster = None

def init_app():
    """Inizializza l'applicazione per Render"""
    global backend, daily_poster
    
    try:
        logger.info("🚀 Initializing ViralShortsAI for Render...")
        
        # Crea directory necessarie
        os.makedirs('data/downloads', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)
        os.makedirs('data/uploads', exist_ok=True)
        os.makedirs('data/reports', exist_ok=True)
        os.makedirs('data/temp', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Inizializza database
        logger.info("📊 Initializing database...")
        db = Database('data/viral_shorts.db')
        db.close()
        
        # Inizializza backend (senza GUI)
        logger.info("🔧 Initializing backend...")
        backend = ViralShortsBackend()
        
        # Inizializza daily poster
        if hasattr(backend, 'daily_poster'):
            daily_poster = backend.daily_poster
            logger.info("🤖 Daily poster available")
        else:
            # Crea daily poster standalone
            daily_poster = DailyAutoPoster(backend=backend)
            logger.info("🤖 Daily poster created standalone")
        
        logger.info("✅ ViralShortsAI initialized successfully for Render!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Initialization error: {e}")
        return False

def start_daily_poster():
    """Avvia daily poster in background"""
    if daily_poster:
        try:
            logger.info("🚀 Starting daily poster...")
            daily_poster.start()
            logger.info("✅ Daily poster started")
        except Exception as e:
            logger.error(f"❌ Error starting daily poster: {e}")

def background_tasks():
    """Task in background per mantenere l'app attiva"""
    while True:
        try:
            # Mantieni l'app sveglia (Render può dormire dopo inattività)
            logger.info("💓 Heartbeat - keeping app alive")
            
            # Controlla status daily poster
            if daily_poster:
                status = daily_poster.get_status()
                logger.info(f"🤖 Daily poster status: {status.get('is_running', False)}")
            
            # Aspetta 5 minuti
            time.sleep(300)
            
        except Exception as e:
            logger.error(f"❌ Background task error: {e}")
            time.sleep(60)

# Routes Flask
@app.route('/')
def dashboard():
    """Dashboard principale"""
    try:
        if not backend:
            return render_template_safe('loading.html')
        
        # Status sistema
        system_status = {
            'online': True,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'platform': 'Render.com Free',
            'uptime': '24/7'
        }
        
        # Status daily poster
        poster_status = daily_poster.get_status() if daily_poster else {
            'is_running': False,
            'posts_today': 0,
            'daily_target': 1,
            'consecutive_days': 0
        }
        
        # Stats database
        try:
            db = Database('data/viral_shorts.db')
            videos_ready = db.get_videos_ready_for_upload(limit=5)
            daily_stats = db.get_daily_upload_stats()
            db.close()
        except:
            videos_ready = []
            daily_stats = {'uploads_count': 0, 'public_uploads': 0}
        
        return render_template_safe('render_dashboard.html',
                                  system_status=system_status,
                                  poster_status=poster_status,
                                  videos_ready=len(videos_ready),
                                  daily_stats=daily_stats)
                                  
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"<h1>ViralShortsAI</h1><p>Status: Initializing...</p><p>Error: {e}</p>"

@app.route('/health')
def health_check():
    """Health check per Render"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'viralshorts-render',
        'backend_ready': backend is not None,
        'poster_ready': daily_poster is not None
    }
    
    if daily_poster:
        status['poster_status'] = daily_poster.get_status()
    
    return jsonify(status)

@app.route('/api/status')
def api_status():
    """API status"""
    try:
        status = {
            'system': {
                'online': True,
                'platform': 'Render.com',
                'timestamp': datetime.now().isoformat()
            },
            'poster': daily_poster.get_status() if daily_poster else {'is_running': False},
            'database': {'connected': True}
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start_poster', methods=['POST'])
def start_poster():
    """Avvia daily poster"""
    try:
        if daily_poster:
            daily_poster.start()
            return jsonify({'status': 'success', 'message': 'Daily poster started'})
        else:
            return jsonify({'status': 'error', 'message': 'Daily poster not available'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/force_post', methods=['POST'])
def force_post():
    """Forza posting immediato"""
    try:
        if daily_poster:
            result = daily_poster.execute_daily_post()
            return jsonify({'status': 'success', 'message': 'Forced post completed', 'result': result})
        else:
            return jsonify({'status': 'error', 'message': 'Daily poster not available'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logs')
def view_logs():
    """Visualizza logs"""
    try:
        logs = []
        logs_dir = 'logs'
        if os.path.exists(logs_dir):
            for file in os.listdir(logs_dir):
                if file.endswith('.log'):
                    logs.append(file)
        
        return f"<h1>Logs</h1><ul>{''.join([f'<li>{log}</li>' for log in logs])}</ul>"
    except Exception as e:
        return f"<h1>Logs Error</h1><p>{e}</p>"

def render_template_safe(template_name, **context):
    """Render template con fallback"""
    try:
        return render_template(template_name, **context)
    except:
        # Fallback HTML se template non disponibile
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ViralShortsAI Cloud</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .card {{ background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 8px; }}
                .status {{ color: green; font-weight: bold; }}
                .button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <h1>🚀 ViralShortsAI Cloud</h1>
            <div class="card">
                <h3>System Status</h3>
                <p class="status">✅ Online - Running on Render.com</p>
                <p>Platform: Free Cloud Hosting</p>
                <p>Last Update: {context.get('system_status', {}).get('last_update', 'Now')}</p>
            </div>
            <div class="card">
                <h3>Daily Auto Poster</h3>
                <p>Status: {'🟢 Active' if context.get('poster_status', {}).get('is_running') else '🔴 Inactive'}</p>
                <p>Posts Today: {context.get('poster_status', {}).get('posts_today', 0)}</p>
                <p>Target: {context.get('poster_status', {}).get('daily_target', 1)}</p>
                <button class="button" onclick="fetch('/api/start_poster', {{method: 'POST'}}).then(() => location.reload())">Start Poster</button>
                <button class="button" onclick="fetch('/api/force_post', {{method: 'POST'}}).then(() => alert('Post forced!')).catch(e => alert('Error: ' + e))">Force Post</button>
            </div>
            <div class="card">
                <h3>Quick Stats</h3>
                <p>Videos Ready: {context.get('videos_ready', 0)}</p>
                <p>Uploads Today: {context.get('daily_stats', {}).get('uploads_count', 0)}</p>
            </div>
        </body>
        </html>
        """

if __name__ == '__main__':
    logger.info("🚀 Starting ViralShortsAI on Render.com...")
    
    # Inizializza app
    init_success = init_app()
    
    if init_success:
        # Avvia daily poster in background
        poster_thread = Thread(target=start_daily_poster, daemon=True)
        poster_thread.start()
        
        # Avvia task di background
        background_thread = Thread(target=background_tasks, daemon=True)
        background_thread.start()
    
    # Avvia Flask (Render gestisce il port automaticamente)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
