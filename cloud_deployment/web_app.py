"""
🌐 ViralShortsAI Cloud Web Interface
Dashboard di controllo remoto per gestire l'applicazione dal cloud
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import sys

# Aggiungi il path dell'app principale
sys.path.append('/app')

from database import Database
from daily_auto_poster import DailyAutoPoster
from main import ViralShortsBackend

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializzazione componenti
backend = None
daily_poster = None

def init_backend():
    """Inizializza backend se non già fatto"""
    global backend, daily_poster
    try:
        if backend is None:
            backend = ViralShortsBackend()
            daily_poster = backend.daily_poster if hasattr(backend, 'daily_poster') else None
            logger.info("✅ Backend inizializzato")
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione backend: {e}")

@app.route('/')
def dashboard():
    """Dashboard principale"""
    init_backend()
    
    try:
        # Status sistema
        system_status = {
            'online': True,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'uptime': '24/7'
        }
        
        # Status daily poster
        poster_status = {}
        if daily_poster:
            poster_status = daily_poster.get_status()
        else:
            poster_status = {
                'is_running': False,
                'posts_today': 0,
                'daily_target': 1,
                'consecutive_days': 0
            }
        
        # Stats database
        db = Database('data/viral_shorts.db')
        videos_ready = db.get_videos_ready_for_upload(limit=5)
        daily_stats = db.get_daily_upload_stats()
        db.close()
        
        return render_template('dashboard.html',
                             system_status=system_status,
                             poster_status=poster_status,
                             videos_ready=len(videos_ready),
                             daily_stats=daily_stats)
                             
    except Exception as e:
        logger.error(f"Errore dashboard: {e}")
        return render_template('error.html', error=str(e))

@app.route('/api/status')
def api_status():
    """API endpoint per status JSON"""
    init_backend()
    
    try:
        # Status sistema
        status = {
            'system': {
                'online': True,
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0-cloud'
            },
            'poster': daily_poster.get_status() if daily_poster else {'is_running': False},
            'database': {
                'connected': True,
                'videos_ready': 0
            }
        }
        
        # Check database
        try:
            db = Database('data/viral_shorts.db')
            videos = db.get_videos_ready_for_upload(limit=1)
            status['database']['videos_ready'] = len(videos)
            db.close()
        except Exception as e:
            status['database']['connected'] = False
            status['database']['error'] = str(e)
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start_poster', methods=['POST'])
def start_poster():
    """Avvia daily poster"""
    init_backend()
    
    try:
        if daily_poster:
            daily_poster.start()
            return jsonify({'status': 'success', 'message': 'Daily poster avviato'})
        else:
            return jsonify({'status': 'error', 'message': 'Daily poster non disponibile'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop_poster', methods=['POST'])
def stop_poster():
    """Ferma daily poster"""
    init_backend()
    
    try:
        if daily_poster:
            daily_poster.stop()
            return jsonify({'status': 'success', 'message': 'Daily poster fermato'})
        else:
            return jsonify({'status': 'error', 'message': 'Daily poster non disponibile'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/force_post', methods=['POST'])
def force_post():
    """Forza posting immediato"""
    init_backend()
    
    try:
        if daily_poster:
            # Simula posting (sostituire con logica reale)
            result = daily_poster.execute_daily_post()
            return jsonify({'status': 'success', 'message': 'Post forzato completato', 'result': result})
        else:
            return jsonify({'status': 'error', 'message': 'Daily poster non disponibile'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/config')
def config():
    """Pagina configurazione"""
    init_backend()
    
    try:
        # Carica configurazione attuale
        config_data = {}
        if daily_poster:
            config_data = daily_poster.config.__dict__
        
        return render_template('config.html', config=config_data)
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/update_config', methods=['POST'])
def update_config():
    """Aggiorna configurazione"""
    init_backend()
    
    try:
        if not daily_poster:
            return jsonify({'status': 'error', 'message': 'Daily poster non disponibile'}), 500
            
        data = request.get_json()
        
        # Aggiorna configurazione
        if 'daily_target' in data:
            daily_poster.config.daily_target = int(data['daily_target'])
        if 'optimal_times' in data:
            daily_poster.config.optimal_times = data['optimal_times']
        if 'max_posts_per_day' in data:
            daily_poster.config.max_posts_per_day = int(data['max_posts_per_day'])
            
        # Salva configurazione
        daily_poster.save_config()
        
        return jsonify({'status': 'success', 'message': 'Configurazione aggiornata'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logs')
def logs():
    """Visualizza logs"""
    try:
        # Leggi ultimi log
        log_files = []
        logs_dir = '/app/logs'
        
        if os.path.exists(logs_dir):
            for file in os.listdir(logs_dir):
                if file.endswith('.log'):
                    filepath = os.path.join(logs_dir, file)
                    size = os.path.getsize(filepath)
                    modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                    log_files.append({
                        'name': file,
                        'size': f"{size / 1024:.1f} KB",
                        'modified': modified.strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        return render_template('logs.html', log_files=log_files)
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/log/<filename>')
def get_log(filename):
    """Ottieni contenuto log file"""
    try:
        log_path = os.path.join('/app/logs', filename)
        
        if not os.path.exists(log_path) or not filename.endswith('.log'):
            return jsonify({'error': 'File non trovato'}), 404
            
        # Leggi ultime 100 righe
        with open(log_path, 'r') as f:
            lines = f.readlines()
            last_lines = lines[-100:] if len(lines) > 100 else lines
            
        return jsonify({
            'filename': filename,
            'lines': [line.strip() for line in last_lines],
            'total_lines': len(lines)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check per container"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'viralshorts-web'
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Pagina non trovata'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Errore interno del server'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
