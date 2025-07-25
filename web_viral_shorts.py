from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import os
import sys
import json
import datetime
import threading
import logging
from dotenv import load_dotenv

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'app.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ViralShortsAI')

# Crea directory necessarie
for directory in ['data/downloads', 'data/processed', 'logs']:
    os.makedirs(directory, exist_ok=True)

# Carica variabili d'ambiente
load_dotenv()

# Inizializza Flask
app = Flask(__name__)

# Variabili globali
config = {}
process_running = False
search_results = []
process_status = "In attesa"
process_progress = 0

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ViralShortsAI</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #4285f4;
            color: white;
            padding: 10px 20px;
            margin-bottom: 20px;
        }
        h1, h2, h3 {
            margin-top: 0;
        }
        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
        }
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            font-size: 16px;
        }
        .tab button:hover {
            background-color: #ddd;
        }
        .tab button.active {
            background-color: #ccc;
        }
        .tabcontent {
            display: none;
            padding: 20px;
            border: 1px solid #ccc;
            border-top: none;
            animation: fadeEffect 1s;
        }
        @keyframes fadeEffect {
            from {opacity: 0;}
            to {opacity: 1;}
        }
        .card {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .btn {
            background-color: #4285f4;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn:hover {
            background-color: #3367d6;
        }
        .btn-secondary {
            background-color: #f1f1f1;
            color: #333;
        }
        .btn-secondary:hover {
            background-color: #ddd;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid transparent;
            border-radius: 4px;
        }
        .alert-success {
            color: #3c763d;
            background-color: #dff0d8;
            border-color: #d6e9c6;
        }
        .alert-danger {
            color: #a94442;
            background-color: #f2dede;
            border-color: #ebccd1;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>ViralShortsAI</h1>
            <p>Trova e rielabora YouTube Shorts virali</p>
        </div>
    </header>

    <div class="container">
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'Dashboard')">Dashboard</button>
            <button class="tablinks" onclick="openTab(event, 'Parametri')">Parametri</button>
            <button class="tablinks" onclick="openTab(event, 'Risultati')">Risultati</button>
            <button class="tablinks" onclick="openTab(event, 'Debug')">Debug</button>
        </div>

        <div id="Dashboard" class="tabcontent" style="display: block;">
            <h2>Dashboard</h2>
            
            <div class="card">
                <h3>Statistiche</h3>
                <p><strong>Video elaborati oggi:</strong> {{ stats.videos_today }}</p>
                <p><strong>Upload programmati:</strong> {{ stats.uploads }}</p>
                <p><strong>Video virali trovati:</strong> {{ stats.viral }}</p>
            </div>

            <div class="card">
                <h3>Azioni</h3>
                <form action="/start_process" method="post">
                    <button type="submit" class="btn" {% if process_running %}disabled{% endif %}>
                        Avvia ricerca
                    </button>
                </form>
                <br>
                <form action="/stop_process" method="post">
                    <button type="submit" class="btn btn-secondary" {% if not process_running %}disabled{% endif %}>
                        Interrompi
                    </button>
                </form>
            </div>

            <div class="card">
                <h3>Stato</h3>
                <p><strong>Processo:</strong> {{ process_status }}</p>
                <div style="width: 100%; background-color: #f1f1f1; border-radius: 4px;">
                    <div style="height: 20px; width: {{ process_progress }}%; background-color: #4CAF50; border-radius: 4px;"></div>
                </div>
                <p style="text-align: right;">{{ process_progress }}%</p>
            </div>

            {% if message %}
            <div class="alert {% if error %}alert-danger{% else %}alert-success{% endif %}">
                {{ message }}
            </div>
            {% endif %}
        </div>

        <div id="Parametri" class="tabcontent">
            <h2>Parametri</h2>
            
            <form action="/save_parameters" method="post">
                <div class="card">
                    <h3>Categorie</h3>
                    {% for category in categories %}
                    <label>
                        <input type="checkbox" name="category" value="{{ category }}" 
                            {% if category in config.categories %}checked{% endif %}>
                        {{ category.capitalize() }}
                    </label>
                    <br>
                    {% endfor %}
                </div>

                <div class="card">
                    <h3>Durate</h3>
                    {% for duration in durations %}
                    <label>
                        <input type="checkbox" name="duration" value="{{ duration }}" 
                            {% if duration|int in config.durations %}checked{% endif %}>
                        {{ duration }} secondi
                    </label>
                    <br>
                    {% endfor %}
                </div>

                <div class="card">
                    <h3>Lingua</h3>
                    <label>
                        <input type="radio" name="language" value="it" 
                            {% if config.language == 'it' %}checked{% endif %}>
                        Italiano
                    </label>
                    <br>
                    <label>
                        <input type="radio" name="language" value="en" 
                            {% if config.language == 'en' %}checked{% endif %}>
                        Inglese
                    </label>
                </div>

                <div class="card">
                    <h3>Hashtag</h3>
                    <input type="text" name="hashtags" value="{{ config.hashtags }}" style="width: 100%;">
                </div>

                <div class="card">
                    <h3>Numero massimo di video al giorno</h3>
                    <input type="number" name="max_videos" value="{{ config.max_videos_per_day }}" min="1" max="20">
                </div>

                <button type="submit" class="btn">Salva impostazioni</button>
            </form>
            <br>
            <a href="/reset_parameters" class="btn btn-secondary">Ripristina predefiniti</a>
        </div>

        <div id="Risultati" class="tabcontent">
            <h2>Risultati</h2>
            
            <div class="card">
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Titolo</th>
                        <th>Visualizzazioni</th>
                        <th>Stato</th>
                    </tr>
                    {% if search_results %}
                        {% for video in search_results %}
                        <tr>
                            <td>{{ video.id }}</td>
                            <td>{{ video.title }}</td>
                            <td>{{ video.view_count }}</td>
                            <td>{{ video.status }}</td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="4" style="text-align: center;">Nessun risultato disponibile</td>
                        </tr>
                    {% endif %}
                </table>
            </div>

            <a href="/refresh_results" class="btn">Aggiorna</a>
        </div>

        <div id="Debug" class="tabcontent">
            <h2>Debug</h2>
            
            <div class="card">
                <h3>Test download</h3>
                <form action="/force_download" method="post">
                    <input type="text" name="url" placeholder="URL YouTube Shorts" style="width: 100%;">
                    <br><br>
                    <button type="submit" class="btn">Download forzato</button>
                </form>
            </div>

            <div class="card">
                <h3>Log</h3>
                <div style="height: 200px; overflow-y: auto; background-color: #f5f5f5; padding: 10px; font-family: monospace;">
                    {{ log_content }}
                </div>
            </div>
        </div>
    </div>

    <script>
    function openTab(evt, tabName) {
        var i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.className += " active";
    }
    </script>
</body>
</html>
"""

# Funzioni di utilità
def load_config():
    """Carica la configurazione da file o crea default"""
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Errore nel parsing di config.json")
    
    # Configurazione predefinita
    return {
        "categories": os.getenv("DEFAULT_CATEGORIES", "gaming,comedy,music").split(","),
        "durations": [int(d) for d in os.getenv("DEFAULT_DURATIONS", "15,30,60").split(",")],
        "language": os.getenv("DEFAULT_LANGUAGE", "it"),
        "hashtags": os.getenv("DEFAULT_HASHTAGS", "#viral #shorts"),
        "max_videos_per_day": int(os.getenv("MAX_VIDEOS_PER_DAY", "5"))
    }

def save_config(new_config):
    """Salva la configurazione su file"""
    with open("config.json", "w") as f:
        json.dump(new_config, f, indent=4)

def read_log():
    """Legge il file di log"""
    log_path = os.path.join("logs", "app.log")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                return f.read()
        except:
            return "Errore nella lettura del log"
    return "Nessun log disponibile"

def mock_search_videos():
    """Simula la ricerca di video virali"""
    import random
    import time
    
    global process_status, process_progress
    
    videos = []
    total_steps = 5
    
    # Simula progresso
    for step in range(1, total_steps + 1):
        process_status = f"Passo {step}/{total_steps}: Ricerca video virali..."
        process_progress = int((step / total_steps) * 100)
        time.sleep(1)
    
    # Genera risultati casuali
    for i in range(10):
        video = {
            "id": f"vid_{random.randint(10000, 99999)}",
            "title": f"Video virale #{i+1}",
            "view_count": random.randint(50000, 10000000),
            "status": "Trovato"
        }
        videos.append(video)
        time.sleep(0.2)
    
    process_status = "Completato"
    return videos

def process_task():
    """Funzione che esegue il processo di ricerca in background"""
    global process_running, search_results, process_status, process_progress
    
    try:
        process_running = True
        
        # Ricerca video virali (simulata)
        search_results = mock_search_videos()
        
        # Aggiorna stato
        logger.info(f"Trovati {len(search_results)} video virali")
        
    except Exception as e:
        logger.error(f"Errore nel processo: {e}")
        process_status = f"Errore: {e}"
    finally:
        process_running = False

# Rotte Flask
@app.route('/')
def index():
    global config, search_results
    
    # Carica la configurazione
    if not config:
        config = load_config()
    
    # Statistiche
    stats = {
        "videos_today": len(search_results),
        "uploads": 0,
        "viral": len([v for v in search_results if v.get("view_count", 0) > 100000])
    }
    
    # Categorie e durate disponibili
    categories = ["gaming", "comedy", "music", "howto", "technology", "sports", "education"]
    durations = [15, 30, 60]
    
    # Leggi il log
    log_content = read_log()
    
    return render_template_string(
        HTML_TEMPLATE,
        config=config,
        stats=stats,
        process_running=process_running,
        process_status=process_status,
        process_progress=process_progress,
        search_results=search_results,
        categories=categories,
        durations=durations,
        log_content=log_content,
        message=request.args.get('message'),
        error=request.args.get('error')
    )

@app.route('/start_process', methods=['POST'])
def start_process():
    global process_running, process_status, process_progress
    
    if process_running:
        return redirect(url_for('index', message="Il processo è già in esecuzione", error=True))
    
    process_status = "Avvio..."
    process_progress = 0
    
    # Avvia il processo in un thread separato
    threading.Thread(target=process_task).start()
    
    logger.info("Processo avviato")
    return redirect(url_for('index', message="Processo avviato con successo"))

@app.route('/stop_process', methods=['POST'])
def stop_process():
    global process_running, process_status
    
    if not process_running:
        return redirect(url_for('index', message="Nessun processo in esecuzione", error=True))
    
    process_running = False
    process_status = "Interrotto"
    
    logger.info("Processo interrotto")
    return redirect(url_for('index', message="Processo interrotto"))

@app.route('/save_parameters', methods=['POST'])
def save_parameters():
    global config
    
    try:
        # Ottieni i parametri dal form
        categories = request.form.getlist('category')
        durations = [int(d) for d in request.form.getlist('duration')]
        language = request.form.get('language', 'it')
        hashtags = request.form.get('hashtags', '')
        max_videos = int(request.form.get('max_videos', 5))
        
        # Aggiorna la configurazione
        config = {
            "categories": categories,
            "durations": durations,
            "language": language,
            "hashtags": hashtags,
            "max_videos_per_day": max_videos
        }
        
        # Salva la configurazione
        save_config(config)
        
        logger.info("Parametri salvati")
        return redirect(url_for('index', message="Parametri salvati con successo"))
        
    except Exception as e:
        logger.error(f"Errore nel salvataggio dei parametri: {e}")
        return redirect(url_for('index', message=f"Errore nel salvataggio dei parametri: {e}", error=True))

@app.route('/reset_parameters')
def reset_parameters():
    global config
    
    # Ripristina i valori predefiniti
    config = {
        "categories": os.getenv("DEFAULT_CATEGORIES", "").split(","),
        "durations": [int(d) for d in os.getenv("DEFAULT_DURATIONS", "15,30,60").split(",")],
        "language": os.getenv("DEFAULT_LANGUAGE", "it"),
        "hashtags": os.getenv("DEFAULT_HASHTAGS", "#viral #shorts"),
        "max_videos_per_day": int(os.getenv("MAX_VIDEOS_PER_DAY", "5"))
    }
    
    # Salva la configurazione
    save_config(config)
    
    logger.info("Parametri ripristinati")
    return redirect(url_for('index', message="Parametri ripristinati ai valori predefiniti"))

@app.route('/refresh_results')
def refresh_results():
    return redirect(url_for('index', message="Risultati aggiornati"))

@app.route('/force_download', methods=['POST'])
def force_download():
    url = request.form.get('url', '')
    
    if not url:
        return redirect(url_for('index', message="URL non valido", error=True))
    
    try:
        logger.info(f"Modalità TEST avviata per URL: {url}")
        
        # Extract video ID from URL
        import re
        video_id_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)', url)
        if not video_id_match:
            return redirect(url_for('index', message="URL del video non valido", error=True))
        
        video_id = video_id_match.group(1)
        
        # Load configuration
        config = load_config()
        
        # Import required modules
        from database import Database
        from data.downloader import YouTubeShortsFinder
        from ai.whisper_transcriber import WhisperTranscriber
        from ai.gpt_captioner import GPTCaptioner
        from processing.editor import VideoEditor
        from monitoring.analyzer import PerformanceAnalyzer
        
        # Initialize components
        db_path = config['paths']['database']
        db = Database(db_path)
        
        finder = YouTubeShortsFinder(config, db)
        transcriber = WhisperTranscriber(config)
        captioner = GPTCaptioner(config)
        editor = VideoEditor(config, db)
        analyzer = PerformanceAnalyzer(config, db)
        
        logger.info(f"Componenti inizializzati per test video: {video_id}")
        
        # Step 1: Download video directly
        video_data = finder.download_video_direct(video_id, force=True)
        logger.info(f"Video scaricato: {video_data['title']}")
        
        # Step 2: Transcribe
        language = config['app_settings']['selected_language']
        transcription = transcriber.transcribe_video(
            video_data['file_path'],
            language=language,
            save_srt=True
        )
        
        key_moments = transcriber.find_key_moments(transcription)
        transcription['key_moments'] = key_moments
        logger.info("Trascrizione completata")
        
        # Step 3: Analyze viral potential
        viral_analysis = captioner.analyze_viral_potential(
            transcription, 
            video_data.get('category', 'Entertainment')
        )
        logger.info("Analisi virale completata")
        
        # Step 4: Process into clips with fallback
        clip_ids = editor.process_source_video(
            video_data['id'], 
            transcription,
            viral_analysis
        )
        
        if not clip_ids:
            logger.warning(f"Sistema fallback non ha creato clip per video {video_data['id']}")
        else:
            logger.info(f"Create {len(clip_ids)} clip da {video_data['title']}")
        
        # Step 5: Generate metadata
        for clip_id in clip_ids:
            clip = db.execute_query(
                "SELECT * FROM processed_clips WHERE id = ?", 
                (clip_id,)
            )[0]
            
            # Extract clip transcription segment
            clip_start = clip['start_time']
            clip_end = clip['end_time']
            
            clip_segments = []
            for segment in transcription['segments']:
                if segment['start'] >= clip_start and segment['end'] <= clip_end:
                    clip_segments.append(segment)
                    
            clip_transcription = {
                'segments': clip_segments
            }
            
            # Generate metadata
            metadata = captioner.generate_video_metadata(clip, clip_transcription)
            
            # Update clip with metadata
            db.execute_query(
                """
                UPDATE processed_clips
                SET title = ?, description = ?, hashtags = ?
                WHERE id = ?
                """,
                (
                    metadata['title'],
                    metadata['description'],
                    ','.join(metadata['hashtags']),
                    clip_id
                )
            )
        
        # Step 6: Generate report
        report = analyzer.generate_performance_report()
        logger.info("Report di test generato")
        
        db.close()
        
        return redirect(url_for('index', message=f"TEST COMPLETATO! Video: {video_data['title']}, Clip generate: {len(clip_ids)}"))
        
    except Exception as e:
        logger.error(f"Errore nella modalità test: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('index', message=f"Errore nella modalità test: {e}", error=True))

# Avvio dell'applicazione
if __name__ == "__main__":
    # Carica la configurazione iniziale
    config = load_config()
    
    print("=" * 50)
    print("ViralShortsAI - Versione Web")
    print("=" * 50)
    print("Apri il browser e vai a http://localhost:5000")
    print("Premi CTRL+C per terminare il server")
    
    app.run(debug=True)
