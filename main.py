"""
ViralShortsAI - Automated viral short-form video content creator.
Main application module that coordinates all components and handles scheduling.
"""

import os
import sys
import json
import time
import logging
import traceback
import datetime
from datetime import datetime
from pathlib import Path

# Configura ImageMagick e forza il fallback OpenAI all'avvio
try:
    from moviepy_config import configure_imagemagick
    configure_imagemagick()
    
    from openai_patch import force_openai_fallback
    force_openai_fallback()
except Exception as e:
    print(f"[WARNING] Configurazione componenti opzionali fallita: {e}")

# Configurazione del logging di base per il debug iniziale
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger("ViralShortsAI")
logger.info("Avvio dell'applicazione ViralShortsAI...")

try:
    from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QMainWindow, QTabWidget, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QSpinBox, QDateTimeEdit, QGroupBox, QScrollArea
    from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from dotenv import load_dotenv
    
    logger.info("Moduli base caricati con successo")
except Exception as e:
    logger.error(f"Errore nel caricamento dei moduli base: {e}")
    traceback.print_exc()
    sys.exit(1)

# Import app modules
try:
    logger.info("Importazione dei moduli dell'applicazione...")
    
    logger.info("Caricamento del modulo database...")
    from database import Database
    
    logger.info("Caricamento del modulo downloader...")
    from data.downloader import YouTubeShortsFinder
    
    logger.info("Caricamento del modulo whisper_transcriber...")
    from ai.whisper_transcriber import WhisperTranscriber
    
    logger.info("Caricamento del modulo gpt_captioner...")
    from ai.gpt_captioner import GPTCaptioner
    
    logger.info("Caricamento del modulo editor...")
    from processing.editor import VideoEditor
    
    logger.info("Caricamento del modulo youtube_uploader...")
    from upload.youtube_uploader import YouTubeUploader
    
    logger.info("Caricamento del modulo analyzer...")
    from monitoring.analyzer import PerformanceAnalyzer
    
    logger.info("Caricamento del modulo app_gui...")
    from gui.app_gui import ViralShortsApp
    
    logger.info("Caricamento del modulo utils...")
    from utils import app_logger
    
    # Carica moduli avanzati di automazione
    logger.info("Caricamento moduli di automazione avanzata...")
    try:
        from scheduling.advanced_scheduler import AdvancedScheduler
        from monitoring.performance_monitor import PerformanceMonitor
        from monitoring.fallback_controller import OpenAIFallbackController
        from reporting.weekly_reporter import WeeklyReporter
        logger.info("✅ Moduli di automazione avanzata caricati")
    except Exception as e:
        logger.warning(f"⚠️ Alcuni moduli di automazione non disponibili: {e}")
    
    logger.info("Tutti i moduli dell'applicazione caricati con successo")
except Exception as e:
    logger.error(f"Errore nel caricamento dei moduli dell'applicazione: {e}")
    traceback.print_exc()
    sys.exit(1)

# Load environment variables
logger.info("Caricamento delle variabili d'ambiente...")
load_dotenv()

class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    log = pyqtSignal(str, str)  # level, message
    status = pyqtSignal(str)    # status message
    progress = pyqtSignal(int)  # progress percentage
    finished = pyqtSignal()     # worker completed
    error = pyqtSignal(str)     # error message


class ViralShortsWorker(QThread):
    """
    Worker thread that runs the main processing pipeline.
    Handles finding viral shorts, processing them, and uploading.
    """
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.signals = WorkerSignals()
        
        # Initialize components
        self.db = None
        self.finder = None
        self.transcriber = None
        self.captioner = None
        self.editor = None
        self.uploader = None
        self.analyzer = None
        
        self.running = False
        self.stop_requested = False
        
        # Test mode attributes
        self.test_mode = False
        self.test_video_url = None
        
    def initialize_components(self):
        """Initialize all application components."""
        try:
            # Esegui diagnosi di sistema
            app_logger.debug("[DIAGNOSTIC] Avvio diagnostica di sistema")
            app_logger.log_system_info()
            
            # Stampa il contenuto attuale della configurazione per debug
            app_logger.debug(f"[DEBUG] Configurazione: {json.dumps(self.config, indent=2)}")
            
            # Validate config structure first
            if not isinstance(self.config, dict):
                error_msg = "Invalid configuration structure: config is not a dictionary"
                self.signals.error.emit(error_msg)
                self.signals.log.emit("error", f"Failed to initialize components: {error_msg}")
                app_logger.error(f"[ERROR] {error_msg}")
                return False
                
            # Verifica la presenza della sezione 'paths' con metodo sicuro
            paths = self.config.get('paths')
            if not isinstance(paths, dict):
                # Crea una sezione paths predefinita se manca
                app_logger.warning("[WARNING] Sezione 'paths' non trovata o non valida nel file config.json")
                self.config['paths'] = {
                    'data': 'data',
                    'downloads': 'data/downloads',
                    'processed': 'data/processed',
                    'uploads': 'data/uploads',
                    'reports': 'data/reports',
                    'logs': 'logs',
                    'database': 'data/viral_shorts.db'
                }
                app_logger.info("[INFO] Creata sezione 'paths' predefinita")
                
                # Salva la configurazione aggiornata
                try:
                    with open('config.json', 'w') as f:
                        json.dump(self.config, f, indent=4)
                    app_logger.info("[INFO] Configurazione aggiornata salvata su file")
                except Exception as save_error:
                    app_logger.warning(f"[WARNING] Impossibile salvare la configurazione aggiornata: {save_error}")
            else:
                # Verifica che tutti i percorsi necessari siano presenti
                required_paths = {
                    'data': 'data',
                    'downloads': 'data/downloads',
                    'processed': 'data/processed',
                    'uploads': 'data/uploads',
                    'reports': 'data/reports',
                    'logs': 'logs',
                    'database': 'data/viral_shorts.db'
                }
                
                updated = False
                for key, default_path in required_paths.items():
                    if key not in paths:
                        self.config['paths'][key] = default_path
                        app_logger.warning(f"[WARNING] Percorso '{key}' mancante, impostato valore predefinito: {default_path}")
                        updated = True
                
                if updated:
                    try:
                        with open('config.json', 'w') as f:
                            json.dump(self.config, f, indent=4)
                        app_logger.info("[INFO] Configurazione aggiornata salvata su file")
                    except Exception as save_error:
                        app_logger.warning(f"[WARNING] Impossibile salvare la configurazione aggiornata: {save_error}")
            
            # Set up components and ensure directories exist
            try:
                # Ottieni il percorso del database in modo sicuro
                db_path = self.config.get('paths', {}).get('database', 'data/viral_shorts.db')
                app_logger.info(f"[INFO] Percorso database: {db_path}")
                
                # Crea la directory del database se necessario
                db_dir = os.path.dirname(db_path)
                Path(db_dir).mkdir(parents=True, exist_ok=True)
                app_logger.info(f"[INFO] Directory database creata/verificata: {db_dir}")
                
                # Assicurati che tutte le altre directory necessarie esistano
                for key, path in self.config.get('paths', {}).items():
                    if isinstance(path, str) and '/' in path:  # Salta file, considera solo cartelle
                        try:
                            Path(path).mkdir(parents=True, exist_ok=True)
                            app_logger.info(f"[INFO] Directory '{key}' creata/verificata: {path}")
                        except Exception as dir_error:
                            app_logger.warning(f"[WARNING] Impossibile creare la directory '{key}' ({path}): {dir_error}")
                
                # Verifica che il file delle credenziali YouTube esista
                youtube_credentials_path = os.path.join('data', 'youtube_credentials.json')
                if not os.path.exists(youtube_credentials_path):
                    app_logger.warning(f"[WARNING] File di credenziali YouTube non trovato: {youtube_credentials_path}")
                else:
                    app_logger.info(f"[INFO] File di credenziali YouTube trovato: {youtube_credentials_path}")
                
                # Inizializza i componenti dell'applicazione
                try:
                    self.db = Database(db_path)
                    app_logger.info("[INFO] Database inizializzato")
                except Exception as db_error:
                    app_logger.error(f"[ERROR] Errore nell'inizializzazione del database: {db_error}")
                    self.signals.error.emit(f"Database error: {db_error}")
                    raise
                
                try:
                    self.finder = YouTubeShortsFinder(self.config, self.db)
                    app_logger.info("[INFO] YouTube Shorts Finder inizializzato")
                except Exception as finder_error:
                    app_logger.error(f"[ERROR] Errore nell'inizializzazione dello Shorts Finder: {finder_error}")
                    self.signals.error.emit(f"Shorts Finder error: {finder_error}")
                    raise
                
                try:
                    self.transcriber = WhisperTranscriber(self.config)
                    app_logger.info("[INFO] Whisper Transcriber inizializzato")
                except Exception as trans_error:
                    app_logger.error(f"[ERROR] Errore nell'inizializzazione del Transcriber: {trans_error}")
                    self.signals.error.emit(f"Transcriber error: {trans_error}")
                    raise
                
                try:
                    self.captioner = GPTCaptioner(self.config)
                    app_logger.info("[INFO] GPT Captioner inizializzato")
                except Exception as cap_error:
                    app_logger.error(f"[ERROR] Errore nell'inizializzazione del Captioner: {cap_error}")
                    self.signals.error.emit(f"Captioner error: {cap_error}")
                    raise
                
                try:
                    self.editor = VideoEditor(self.config, self.db)
                    app_logger.info("[INFO] Video Editor inizializzato")
                except Exception as ed_error:
                    app_logger.error(f"[ERROR] Errore nell'inizializzazione dell'Editor: {ed_error}")
                    self.signals.error.emit(f"Editor error: {ed_error}")
                    raise
                
                try:
                    self.uploader = YouTubeUploader(self.config)
                    app_logger.info("[INFO] YouTube Uploader inizializzato")
                except Exception as up_error:
                    app_logger.error(f"[ERROR] Errore nell'inizializzazione dell'Uploader: {up_error}")
                    self.signals.error.emit(f"Uploader error: {up_error}")
                    raise
                
                try:
                    self.analyzer = PerformanceAnalyzer(self.config, self.db)
                    app_logger.info("[INFO] Performance Analyzer inizializzato")
                except Exception as an_error:
                    app_logger.error(f"[ERROR] Errore nell'inizializzazione dell'Analyzer: {an_error}")
                    self.signals.error.emit(f"Analyzer error: {an_error}")
                    raise
                
                app_logger.info("[SUCCESS] Tutti i componenti inizializzati con successo")
                return True
                
            except Exception as component_error:
                error_msg = f"Errore inizializzazione componente: {component_error}"
                self.signals.error.emit(error_msg)
                self.signals.log.emit("error", f"Failed to initialize components: {error_msg}")
                app_logger.error(f"[ERROR] {error_msg}")
                import traceback
                app_logger.error(f"[TRACE] {traceback.format_exc()}")
                return False
            
        except Exception as e:
            error_msg = f"Initialization error: {e}"
            self.signals.error.emit(error_msg)
            self.signals.log.emit("error", f"Failed to initialize components: {e}")
            app_logger.error(f"[ERROR] {error_msg}")
            import traceback
            app_logger.error(f"[TRACE] {traceback.format_exc()}")
            return False
    
    def log(self, level, message):
        """Log message and emit signal for GUI."""
        if level == "info":
            app_logger.info(message)
        elif level == "warning":
            app_logger.warning(message)
        elif level == "error":
            app_logger.error(message)
        elif level == "debug":
            app_logger.debug(message)
        
        self.signals.log.emit(level, message)
    
    def run(self):
        """Run the main processing pipeline."""
        self.running = True
        self.stop_requested = False
        
        # Initialize components
        self.log("info", "Inizializzazione dei componenti...")
        if not self.initialize_components():
            self.log("error", "Impossibile inizializzare i componenti dell'applicazione")
            self.running = False
            self.signals.finished.emit()
            return
        
        try:
            # Check if we're in test mode
            if self.test_mode and self.test_video_url:
                self.log("info", f"Modalità TEST attivata per URL: {self.test_video_url}")
                self.run_test_mode()
                return
            
            self.signals.status.emit("Ricerca video virali")
            self.log("info", "Inizia il processo di creazione contenuti")
            
            # Step 1: Find viral shorts
            self.log("info", "Ricerca di YouTube Shorts virali...")
            max_videos = self.config['app_settings']['max_videos_per_day']
            source_ids = self.finder.process_viral_shorts(max_videos)
            
            if not source_ids:
                self.log("warning", "Nessun video disponibile per il processing")
                self.signals.status.emit("Nessun video da processare")
                self.running = False
                self.signals.finished.emit()
                return
            
            self.log("info", f"Trovati {len(source_ids)} video da processare")
            
            # Step 2: Process each video
            total_videos = len(source_ids)
            processed_clips = []
            
            for i, video_id in enumerate(source_ids):
                if self.stop_requested:
                    break
                    
                try:
                    # Update progress
                    progress = int((i / total_videos) * 100)
                    self.signals.progress.emit(progress)
                    self.signals.status.emit(f"Elaborazione video {i+1}/{total_videos}")
                    
                    # Get video from database
                    video = self.db.execute_query(
                        "SELECT * FROM source_videos WHERE id = ?", 
                        (video_id,)
                    )[0]
                    
                    # Transcribe video
                    self.log("info", f"Trascrizione video: {video['title']}")
                    language = self.config['app_settings']['selected_language']
                    
                    transcription = self.transcriber.transcribe_video(
                        video['file_path'],
                        language=language,
                        save_srt=True
                    )
                    
                    # Find key moments
                    key_moments = self.transcriber.find_key_moments(transcription)
                    transcription['key_moments'] = key_moments
                    
                    # Analyze viral potential
                    self.log("info", f"Analisi potenziale virale: {video['title']}")
                    viral_analysis = self.captioner.analyze_viral_potential(
                        transcription, 
                        video['category']
                    )
                    
                    # Process into clips
                    self.log("info", f"Elaborazione in clip: {video['title']}")
                    clip_ids = self.editor.process_source_video(
                        video_id, 
                        transcription,
                        viral_analysis
                    )
                    
                    if not clip_ids:
                        self.log("warning", f"Nessuna clip creata per video {video_id}")
                        continue
                        
                    self.log("info", f"Create {len(clip_ids)} clip da {video['title']}")
                    
                    # Generate metadata for each clip
                    for clip_id in clip_ids:
                        clip = self.db.execute_query(
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
                        self.log("info", f"Generazione metadata per clip {clip_id}")
                        metadata = self.captioner.generate_video_metadata(
                            clip, clip_transcription
                        )
                        
                        # Update clip with metadata
                        self.db.execute_query(
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
                        
                        processed_clips.append(clip_id)
                        
                except Exception as e:
                    self.log("error", f"Errore nell'elaborazione del video {video_id}: {e}")
                    traceback.print_exc()
            
            # Step 3: Schedule uploads for processed clips
            if not self.stop_requested and processed_clips:
                self.log("info", f"Pianificazione upload per {len(processed_clips)} clip")
                
                # Authenticate YouTube uploader
                if not self.uploader.authenticate():
                    self.log("error", "Autenticazione YouTube fallita")
                    self.signals.status.emit("Errore autenticazione YouTube")
                    self.running = False
                    self.signals.finished.emit()
                    return
                
                # Get the clips to upload
                clips = []
                for clip_id in processed_clips:
                    clip = self.db.execute_query(
                        "SELECT * FROM processed_clips WHERE id = ?", 
                        (clip_id,)
                    )[0]
                    clips.append(clip)
                
                # Sort by viral score (descending)
                clips.sort(key=lambda x: x['viral_score'], reverse=True)
                
                # Limit to max uploads per day
                max_uploads = self.config['app_settings']['max_videos_per_day']
                clips = clips[:max_uploads]
                
                # Schedule uploads
                upload_times = self.config['upload']['upload_times']
                now = datetime.datetime.now()
                
                for i, clip in enumerate(clips):
                    if self.stop_requested:
                        break
                        
                    # Determine upload time
                    if i < len(upload_times):
                        # Parse time string (e.g. "12:00")
                        time_str = upload_times[i]
                        hour, minute = map(int, time_str.split(':'))
                        
                        upload_time = datetime.datetime.combine(
                            now.date(), datetime.time(hour=hour, minute=minute)
                        )
                        
                        # If time is in the past, schedule for tomorrow
                        if upload_time < now:
                            upload_time += datetime.timedelta(days=1)
                    else:
                        # Default to 3 hours from now
                        upload_time = now + datetime.timedelta(hours=3)
                    
                    # Schedule the upload
                    result = self.uploader.schedule_upload(clip, upload_time)
                    
                    if result:
                        # Add to uploaded_videos table
                        upload_data = {
                            'clip_id': clip['id'],
                            'youtube_id': result.get('youtube_id'),
                            'title': result['title'],
                            'description': result['description'],
                            'hashtags': ','.join(result['hashtags']) if isinstance(result['hashtags'], list) else result['hashtags'],
                            'upload_time': result.get('upload_time'),
                            'scheduled_time': result.get('scheduled_time', upload_time.isoformat()),
                            'visibility': result['visibility'],
                            'url': result.get('url')
                        }
                        
                        self.db.add_uploaded_video(upload_data)
                        
                        msg = "Caricato" if result.get('youtube_id') else "Pianificato"
                        self.log("info", f"{msg} video '{result['title']}'")
                    else:
                        self.log("error", f"Errore nella pianificazione upload per clip {clip['id']}")
            
            # Step 4: Collect metrics for previously uploaded videos
            self.log("info", "Raccolta metriche per video pubblicati")
            self.analyzer.collect_metrics(self.uploader)
            
            # Step 5: Generate performance report
            self.log("info", "Generazione report performance")
            report = self.analyzer.generate_performance_report()
            
            if report:
                if self.config['analytics']['auto_learning']:
                    # Update content strategy
                    self.log("info", "Aggiornamento strategia di contenuto")
                    strategy_updates = self.analyzer.update_content_strategy()
                    
                    if strategy_updates:
                        self.log("info", "Strategia aggiornata in base alle performance")
            
            self.log("info", "Processo completato con successo!")
            self.signals.status.emit("Processo completato")
            
        except Exception as e:
            self.log("error", f"Errore nel processo: {e}")
            traceback.print_exc()
            self.signals.status.emit("Errore nel processo")
            
        finally:
            # Clean up
            if self.db:
                self.db.close()
                
            self.running = False
            self.signals.finished.emit()
    
    def run_test_mode(self):
        """Run the complete pipeline in test mode for a single video URL."""
        try:
            self.signals.status.emit("Modalità TEST - Download video")
            self.signals.progress.emit(10)
            
            # Step 1: Download the test video directly (bypass search)
            self.log("info", f"Download diretto del video: {self.test_video_url}")
            
            # Extract video ID from URL
            import re
            video_id_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)', self.test_video_url)
            if not video_id_match:
                raise Exception("URL del video non valido")
            
            test_video_id = video_id_match.group(1)
            
            # Download video using downloader (direct method)
            video_data = self.finder.download_video_direct(test_video_id, force=True)
            if not video_data:
                raise Exception("Impossibile scaricare il video di test")
            
            self.log("info", f"Video scaricato con successo: {video_data['title']}")
            
            # Step 2: Transcribe video
            self.signals.status.emit("TEST - Trascrizione video")
            self.signals.progress.emit(30)
            
            language = self.config['app_settings']['selected_language']
            self.log("info", f"Trascrizione video: {video_data['title']}")
            
            transcription = self.transcriber.transcribe_video(
                video_data['file_path'],
                language=language,
                save_srt=True
            )
            
            # Find key moments
            key_moments = self.transcriber.find_key_moments(transcription)
            transcription['key_moments'] = key_moments
            
            # Step 3: Analyze viral potential
            self.signals.status.emit("TEST - Analisi potenziale virale")
            self.signals.progress.emit(50)
            
            self.log("info", f"Analisi potenziale virale: {video_data['title']}")
            viral_analysis = self.captioner.analyze_viral_potential(
                transcription, 
                video_data.get('category', 'Entertainment')
            )
            
            # Step 4: Process into clips (with fallback system)
            self.signals.status.emit("TEST - Generazione clip")
            self.signals.progress.emit(70)
            
            self.log("info", f"Elaborazione in clip con fallback: {video_data['title']}")
            clip_ids = self.editor.process_source_video(
                video_data['id'], 
                transcription,
                viral_analysis
            )
            
            if not clip_ids:
                self.log("warning", f"Sistema fallback non ha creato clip per video {video_data['id']}")
            else:
                self.log("info", f"Create {len(clip_ids)} clip da {video_data['title']}")
            
            # Step 5: Generate metadata for clips
            self.signals.status.emit("TEST - Generazione metadata")
            self.signals.progress.emit(85)
            
            processed_clips = []
            for clip_id in clip_ids:
                clip = self.db.execute_query(
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
                self.log("info", f"Generazione metadata per clip {clip_id}")
                metadata = self.captioner.generate_video_metadata(
                    clip, clip_transcription
                )
                
                # Update clip with metadata
                self.db.execute_query(
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
                
                processed_clips.append(clip_id)
            
            # Step 6: Generate test report
            self.signals.status.emit("TEST - Generazione report")
            self.signals.progress.emit(95)
            
            self.log("info", "Generazione report di test")
            report = self.analyzer.generate_performance_report()
            
            if report:
                self.log("info", "Report di test generato con successo")
            
            # Complete
            self.signals.progress.emit(100)
            self.signals.status.emit(f"TEST COMPLETATO - {len(processed_clips)} clip create")
            
            self.log("info", f"TEST MODE COMPLETATO! Video: {video_data['title']}, Clip: {len(processed_clips)}")
            
        except Exception as e:
            self.log("error", f"Errore in modalità test: {e}")
            traceback.print_exc()
            self.signals.status.emit("Errore in modalità test")
        
        finally:
            # Clean up
            if self.db:
                self.db.close()
                
            self.running = False
            self.signals.finished.emit()
    
    def stop(self):
        """Request the worker to stop."""
        self.stop_requested = True
        self.log("info", "Arresto richiesto, attendi il completamento...")


class ViralShortsBackend:
    """
    Main application backend class.
    Manages the worker thread, scheduling, and GUI integration.
    """
    
    def __init__(self, config_path="config.json"):
        """
        Initialize the backend with configuration.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        
        # Ensure paths exist
        for path_key, path_val in self.config['paths'].items():
            if path_key != 'database':  # Non creare una directory per il database
                os.makedirs(path_val, exist_ok=True)
        
        # Set up logger callbacks
        app_logger.add_callback(self.log_callback)
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Initialize advanced automation components
        try:
            self.advanced_scheduler = AdvancedScheduler(config_path)
            self.performance_monitor = PerformanceMonitor()
            self.fallback_controller = OpenAIFallbackController(config_path)
            self.weekly_reporter = WeeklyReporter()
            
            # Inizializza Daily Auto Poster
            from daily_auto_poster import DailyAutoPoster
            self.daily_poster = DailyAutoPoster(backend=self)
            app_logger.info("✅ Advanced automation components initialized")
        except Exception as e:
            app_logger.warning(f"⚠️ Advanced automation not available: {e}")
            self.advanced_scheduler = None
            self.performance_monitor = None
            self.fallback_controller = None
            self.weekly_reporter = None
            self.daily_poster = None
        
        # Worker thread
        self.worker = None
    
    def get_automation_status(self):
        """Get comprehensive automation status"""
        status = {
            'scheduler': None,
            'performance_monitor': None,
            'fallback_controller': None,
            'weekly_reporter': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if hasattr(self, 'advanced_scheduler') and self.advanced_scheduler:
                status['scheduler'] = self.advanced_scheduler.get_status()
        except Exception as e:
            status['scheduler'] = {'error': str(e)}
            
        try:
            if hasattr(self, 'performance_monitor') and self.performance_monitor:
                status['performance_monitor'] = {'initialized': True, 'youtube_api_available': self.performance_monitor.youtube_api_available}
        except Exception as e:
            status['performance_monitor'] = {'error': str(e)}
            
        try:
            if hasattr(self, 'fallback_controller') and self.fallback_controller:
                status['fallback_controller'] = {'initialized': True, 'auto_enabled': self.fallback_controller.auto_fallback_enabled}
        except Exception as e:
            status['fallback_controller'] = {'error': str(e)}
            
        try:
            if hasattr(self, 'weekly_reporter') and self.weekly_reporter:
                status['weekly_reporter'] = {'initialized': True}
        except Exception as e:
            status['weekly_reporter'] = {'error': str(e)}
            
        return status
    
    def start_advanced_scheduler(self):
        """Start the advanced scheduler"""
        if hasattr(self, 'advanced_scheduler') and self.advanced_scheduler:
            return self.advanced_scheduler.start()
        return False
    
    def stop_advanced_scheduler(self):
        """Stop the advanced scheduler"""
        if hasattr(self, 'advanced_scheduler') and self.advanced_scheduler:
            return self.advanced_scheduler.stop()
        return False
    
    def force_performance_monitoring(self):
        """Force performance monitoring update"""
        if hasattr(self, 'performance_monitor') and self.performance_monitor:
            try:
                self.performance_monitor.update_all_video_metrics()
                return {'success': True, 'message': 'Performance monitoring completed'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Performance monitor not available'}
    
    def generate_weekly_report(self):
        """Generate weekly report manually"""
        if hasattr(self, 'weekly_reporter') and self.weekly_reporter:
            try:
                report_path = self.weekly_reporter.generate_report()
                return {'success': True, 'report_path': report_path}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Weekly reporter not available'}
    
    def check_fallback_status(self):
        """Check OpenAI fallback status"""
        if hasattr(self, 'fallback_controller') and self.fallback_controller:
            try:
                return self.fallback_controller.get_status()
            except Exception as e:
                return {'error': str(e)}
        return {'error': 'Fallback controller not available'}
    
    def force_fallback_check(self):
        """Force fallback quota check"""
        if hasattr(self, 'fallback_controller') and self.fallback_controller:
            try:
                result = self.fallback_controller.check_openai_quota()
                return {'success': True, 'result': result}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Fallback controller not available'}
    
    def cleanup_temp_files(self):
        """Manual temp files cleanup"""
        if hasattr(self, 'advanced_scheduler') and self.advanced_scheduler:
            try:
                self.advanced_scheduler._cleanup_temp_files()
                return {'success': True, 'message': 'Temp files cleanup completed'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Advanced scheduler not available'}
        
        # Load last run date
        self.last_run_date = self.config.get('last_run_date')
        
        # If run_daily is enabled, schedule the task
        if self.config['app_settings']['run_daily']:
            self.schedule_daily_run()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default config if file doesn't exist or is invalid
            return {
                "app_settings": {
                    "run_daily": True,
                    "daily_run_time": "10:00",
                    "max_videos_per_day": 5,
                    "languages": ["en", "es", "fr", "de", "it"],
                    "selected_language": "en"
                },
                "youtube_search": {
                    "categories": {
                        "Entertainment": True,
                        "News": True,
                        "Sports": True,
                        "Curiosity": True,
                        "Lifestyle": True,
                        "Intrattenimento": True,
                        "Notizie": True,
                        "Sport": True,
                        "Curiosità": True
                    },
                    "min_views": 1000,
                    "published_within_hours": 48,
                    "copyright_filter": False,
                    "max_duration": 90
                },
                "video_processing": {
                    "clip_durations": {
                        "15": True,
                        "30": True,
                        "60": True
                    },
                    "add_subtitles": True,
                    "add_highlighted_text": True,
                    "font_size": 24,
                    "font_color": "#FFFFFF",
                    "highlight_color": "#FF0000"
                },
                "upload": {
                    "upload_times": ["12:00", "18:00", "21:00"],
                    "custom_hashtags": ["viral", "trending", "shorts"],
                    "visibility": "public",
                    "auto_publish": True
                },
                "analytics": {
                    "measure_after_hours": 24,
                    "viral_score_threshold": 50,
                    "auto_learning": True,
                    "data_retention_days": 90
                },
                "paths": {
                    "downloads": "data/downloads",
                    "processed": "data/processed",
                    "uploads": "data/uploads",
                    "logs": "logs",
                    "database": "data/viral_shorts.db"
                }
            }
    
    def save_config(self):
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def update_config(self, new_config):
        """Update configuration with new values."""
        self.config.update(new_config)
        self.save_config()
        
        # If run_daily setting changed, update scheduler
        if self.config['app_settings']['run_daily']:
            self.schedule_daily_run()
        else:
            self.unschedule_daily_run()
    
    def log_callback(self, level, message):
        """Callback for logger messages."""
        # This will be connected to GUI log display
        pass
    
    def schedule_daily_run(self):
        """Schedule the daily run."""
        # Remove any existing job
        self.unschedule_daily_run()
        
        # Parse time from config
        time_str = self.config['app_settings']['daily_run_time']
        hour, minute = map(int, time_str.split(':'))
        
        # Schedule the job
        self.scheduler.add_job(
            self.start_process,
            CronTrigger(hour=hour, minute=minute),
            id='daily_run',
            replace_existing=True
        )
        
        app_logger.info(f"Scheduled daily run at {time_str}")
    
    def unschedule_daily_run(self):
        """Remove the scheduled daily run."""
        if self.scheduler.get_job('daily_run'):
            self.scheduler.remove_job('daily_run')
            app_logger.info("Unscheduled daily run")
    
    def start_process(self):
        """Start the processing pipeline."""
        # Check if worker is already running
        if self.worker and self.worker.running:
            app_logger.warning("Process already running")
            return False
        
        # Create and start worker thread
        self.worker = ViralShortsWorker(self.config)
        
        # Connect signals (to be overridden by GUI)
        self.worker.signals.log.connect(self.log_callback)
        self.worker.signals.status.connect(lambda x: None)
        self.worker.signals.progress.connect(lambda x: None)
        self.worker.signals.finished.connect(self.process_finished)
        self.worker.signals.error.connect(lambda x: app_logger.error(x))
        
        # Start the worker
        self.worker.start()
        
        # Update last run date
        self.last_run_date = datetime.datetime.now().isoformat()
        self.config['last_run_date'] = self.last_run_date
        self.save_config()
        
        app_logger.info("Process started")
        return True
    
    def stop_process(self):
        """Stop the processing pipeline."""
        if self.worker and self.worker.running:
            self.worker.stop()
            return True
        return False
    
    def process_finished(self):
        """Called when the worker thread finishes."""
        app_logger.info("Process finished")
    
    def check_scheduled_uploads(self):
        """Check for and execute scheduled uploads."""
        try:
            # Initialize components
            if isinstance(self.config, dict) and isinstance(self.config.get('paths'), dict):
                db_path = self.config['paths'].get('database')
                if db_path and os.path.isfile(db_path):
                    db = Database(db_path)
                    uploader = YouTubeUploader(self.config)
                    
                    if uploader.authenticate():
                        # Check for scheduled uploads
                        uploaded_ids = uploader.check_scheduled_uploads(db)
                        
                        if uploaded_ids:
                            app_logger.info(f"Uploaded {len(uploaded_ids)} scheduled videos")
                        
                        db.close()
                        return len(uploaded_ids)
                    else:
                        app_logger.error("Failed to authenticate with YouTube")
                        return 0
                else:
                    app_logger.error(f"Database path not found: {db_path}")
                    return 0
            else:
                app_logger.error("Invalid configuration structure")
                return 0
                
        except Exception as e:
            app_logger.error(f"Error checking scheduled uploads: {e}")
            return 0
    
    def auto_upload_next_video(self):
        """Carica automaticamente il prossimo video pronto per il posting"""
        try:
            app_logger.info("🚀 Avviando auto-upload video...")
            
            if isinstance(self.config, dict) and isinstance(self.config.get('paths'), dict):
                db_path = self.config['paths'].get('database')
                if db_path and os.path.isfile(db_path):
                    db = Database(db_path)
                    uploader = YouTubeUploader(self.config)
                    
                    if uploader.authenticate():
                        # Cerca video pronti per l'upload
                        videos = db.get_videos_ready_for_upload()
                        
                        if videos:
                            video = videos[0]  # Prendi il primo disponibile
                            app_logger.info(f"📹 Uploading video: {video.get('title', 'Unknown')}")
                            
                            # Esegui upload
                            result = uploader.upload_video_from_db(video['id'], db)
                            
                            if result:
                                app_logger.info(f"✅ Video {video['id']} caricato con successo!")
                                db.close()
                                return True
                            else:
                                app_logger.error(f"❌ Errore upload video {video['id']}")
                                db.close()
                                return False
                        else:
                            app_logger.warning("⚠️ Nessun video pronto per l'upload")
                            db.close()
                            return False
                    else:
                        app_logger.error("❌ Autenticazione YouTube fallita")
                        return False
                else:
                    app_logger.error(f"❌ Database non trovato: {db_path}")
                    return False
            else:
                app_logger.error("❌ Configurazione non valida")
                return False
                
        except Exception as e:
            app_logger.error(f"❌ Errore auto-upload: {e}")
            return False
    
    def search_and_process_emergency_content(self, query: str):
        """Cerca e processa contenuto di emergenza per il posting giornaliero"""
        try:
            app_logger.info(f"🆘 Creando contenuto di emergenza: {query}")
            
            # Configura parametri per contenuto veloce
            temp_config = self.config.copy()
            temp_config.update({
                'search_results_limit': 1,  # Solo 1 video per velocità
                'max_duration': 30,  # Massimo 30 secondi
                'auto_upload': False  # Non uplodare subito
            })
            
            # Avvia worker con query di emergenza
            if not self.worker or not self.worker.running:
                self.start_worker(search_query=query, emergency_mode=True)
                
                # Aspetta che finisca (max 5 minuti)
                timeout = 300  # 5 minuti
                start_time = time.time()
                
                while self.worker.running and (time.time() - start_time) < timeout:
                    time.sleep(10)
                    app_logger.info("⏳ Aspettando completamento contenuto emergenza...")
                
                if self.worker.running:
                    app_logger.warning("⚠️ Timeout creazione contenuto emergenza")
                    self.worker.stop()
                    return False
                else:
                    app_logger.info("✅ Contenuto di emergenza creato")
                    return True
            else:
                app_logger.warning("⚠️ Worker già in esecuzione")
                return False
                
        except Exception as e:
            app_logger.error(f"❌ Errore creazione contenuto emergenza: {e}")
            return False
    
    def start_daily_auto_poster(self):
        """Avvia il sistema di posting automatico giornaliero"""
        try:
            if self.daily_poster:
                self.daily_poster.start_daily_scheduler()
                app_logger.info("🤖 Daily Auto Poster avviato!")
                return True
            else:
                app_logger.error("❌ Daily Auto Poster non disponibile")
                return False
        except Exception as e:
            app_logger.error(f"❌ Errore avvio Daily Auto Poster: {e}")
            return False
    
    def stop_daily_auto_poster(self):
        """Ferma il sistema di posting automatico giornaliero"""
        try:
            if self.daily_poster:
                self.daily_poster.stop_daily_scheduler()
                app_logger.info("🛑 Daily Auto Poster fermato!")
                return True
            else:
                return False
        except Exception as e:
            app_logger.error(f"❌ Errore stop Daily Auto Poster: {e}")
            return False
    
    def get_daily_poster_status(self):
        """Ottieni status del daily auto poster"""
        try:
            if self.daily_poster:
                return self.daily_poster.get_status_dict()
            else:
                return {
                    'is_running': False,
                    'posts_today': 0,
                    'daily_target': 1,
                    'consecutive_days': 0,
                    'error': 'Daily poster not available'
                }
        except Exception as e:
            app_logger.error(f"❌ Errore status Daily Auto Poster: {e}")
            return {'error': str(e)}
    
    def shutdown(self):
        """Shutdown the backend properly."""
        # Stop worker if running
        if self.worker and self.worker.running:
            self.worker.stop()
            self.worker.wait()
            
        # Shutdown scheduler
        if self.scheduler.running:
            self.scheduler.shutdown()
            
        app_logger.info("Backend shutdown")


class ViralShortsApp(ViralShortsApp):
    """
    Extended ViralShortsApp class with backend integration.
    Inherits from the base GUI class and adds backend functionality.
    """
    
    def __init__(self):
        # Initialize backend
        self.backend = ViralShortsBackend()
        
        # Initialize base GUI
        super().__init__()
        
        # Connect backend
        self.connect_backend()
        
        # Check for scheduled uploads
        QThread.currentThread().msleep(500)  # Short delay for UI to load
        self.check_scheduled_uploads()
        
        # Setup timer for periodic checks
        self.setup_timers()
    
    def connect_backend(self):
        """Connect GUI components to backend functionality."""
        # Connect logger
        self.backend.log_callback = self.log_message
        
        # Connect buttons
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.on_start_clicked)
        
        # Connect checkboxes
        self.daily_checkbox.stateChanged.connect(self.on_daily_changed)
        
        # Connect config options
        self.config_save_button = QPushButton("Salva impostazioni")
        self.config_save_button.clicked.connect(self.save_config_changes)
        
        # Add save button to config tab
        config_tab = self.findChild(QTabWidget).widget(1)
        config_layout = config_tab.layout()
        config_layout.addWidget(self.config_save_button)
        
        # Connect debug buttons
        self.force_download_button.clicked.connect(self.on_force_download)
        self.regen_metadata_button.clicked.connect(self.on_regen_metadata)
    
    def setup_timers(self):
        """Setup timers for periodic tasks."""
        # Check scheduled uploads every 5 minutes
        self.upload_timer = QTimer(self)
        self.upload_timer.timeout.connect(self.check_scheduled_uploads)
        self.upload_timer.start(5 * 60 * 1000)  # 5 minutes
    
    def log_message(self, level, message):
        """Add a log message to the log area."""
        # Add timestamp
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        
        # Define color based on level
        color = 'black'
        if level == 'error':
            color = 'red'
        elif level == 'warning':
            color = 'orange'
        elif level == 'info':
            color = 'green'
        
        # Format message with HTML
        html_message = f'<span style="color:{color}"><b>[{timestamp}]</b> {message}</span>'
        
        # Add to log area
        self.log_area.append(html_message)
        
        # Scroll to bottom
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
    
    def on_start_clicked(self):
        """Handle start button click."""
        if self.backend.worker and self.backend.worker.running:
            # Stop if running
            self.backend.stop_process()
            self.start_button.setText("▶️ Avvia ora")
            self.status_label.setText("🔴 Arresto in corso...")
        else:
            # Start if not running
            if self.backend.start_process():
                self.start_button.setText("⏹️ Ferma")
                self.status_label.setText("⏳ Processo in esecuzione...")
                
                # Connect worker signals
                self.backend.worker.signals.status.connect(self.update_status)
                self.backend.worker.signals.progress.connect(self.update_progress)
                self.backend.worker.signals.finished.connect(self.process_finished)
    
    def on_daily_changed(self, state):
        """Handle daily checkbox change."""
        self.backend.config['app_settings']['run_daily'] = bool(state)
        
        if state:
            self.backend.schedule_daily_run()
        else:
            self.backend.unschedule_daily_run()
            
        self.backend.save_config()
    
    def save_config_changes(self):
        """Save configuration changes from UI."""
        # Update config from UI components
        
        # Categories
        for cat, checkbox in self.cat_checkboxes.items():
            self.backend.config['youtube_search']['categories'][cat] = checkbox.isChecked()
        
        # Durations
        self.backend.config['video_processing']['clip_durations']['15'] = self.duration_15.isChecked()
        self.backend.config['video_processing']['clip_durations']['30'] = self.duration_30.isChecked()
        self.backend.config['video_processing']['clip_durations']['60'] = self.duration_60.isChecked()
        
        # Max videos
        self.backend.config['app_settings']['max_videos_per_day'] = self.max_videos.value()
        
        # Language
        lang_map = {
            "Italiano": "it",
            "Inglese": "en",
            "Spagnolo": "es",
            "Francese": "fr"
        }
        selected_lang = self.language_dropdown.currentText()
        self.backend.config['app_settings']['selected_language'] = lang_map.get(selected_lang, "en")
        
        # Hashtags
        if self.hashtag_input.text():
            hashtags = [tag.strip() for tag in self.hashtag_input.text().split(',')]
            self.backend.config['upload']['custom_hashtags'] = hashtags
        
        # Save config
        self.backend.save_config()
        self.log_message("info", "Configurazione salvata")
    
    def update_status(self, status):
        """Update status label."""
        self.status_label.setText(f"⏳ {status}")
    
    def update_progress(self, progress):
        """Update progress (placeholder for progress bar)."""
        # If we had a progress bar, we would update it here
        self.log_message("info", f"Progresso: {progress}%")
    
    def process_finished(self):
        """Handle process completion."""
        self.start_button.setText("▶️ Avvia ora")
        self.status_label.setText("🟢 Sistema pronto")
        self.log_message("info", "Processo completato")
        
        # Update results tab
        self.update_results_table()
    
    def update_results_table(self):
        """Update the results table with latest data."""
        try:
            # Initialize database
            db_path = self.backend.config['paths']['database']
            db = Database(db_path)
            
            # Query for recent uploads with analytics
            query = """
            SELECT 
                uv.title,
                a.views,
                a.likes,
                a.comments,
                a.viral_score,
                a.retention_rate
            FROM uploaded_videos uv
            JOIN analytics a ON uv.id = a.upload_id
            ORDER BY uv.upload_time DESC
            LIMIT 100
            """
            
            results = db.execute_query(query)
            
            # Clear table
            self.results_table.setRowCount(0)
            
            # Add rows
            for i, row in enumerate(results):
                self.results_table.insertRow(i)
                
                # Title
                self.results_table.setItem(i, 0, QTableWidgetItem(row['title']))
                
                # Views
                self.results_table.setItem(i, 1, QTableWidgetItem(str(row['views'])))
                
                # Likes
                self.results_table.setItem(i, 2, QTableWidgetItem(str(row['likes'])))
                
                # Comments
                self.results_table.setItem(i, 3, QTableWidgetItem(str(row['comments'])))
                
                # Viral score
                score_item = QTableWidgetItem(f"{row['viral_score']:.1f}")
                self.results_table.setItem(i, 4, score_item)
                
                # Retention
                retention_item = QTableWidgetItem(f"{row['retention_rate']:.1f}%")
                self.results_table.setItem(i, 5, retention_item)
            
            # Resize columns to content
            self.results_table.resizeColumnsToContents()
            
            # Close database
            db.close()
            
        except Exception as e:
            self.log_message("error", f"Errore nell'aggiornamento risultati: {e}")
    
    def check_scheduled_uploads(self):
        """Check for scheduled uploads."""
        count = self.backend.check_scheduled_uploads()
        if count > 0:
            self.log_message("info", f"Caricati {count} video programmati")
            
            # Update results table
            self.update_results_table()
    
    def on_force_download(self):
        """Force download a specific video URL with test mode processing."""
        url = self.manual_url_input.text().strip()
        if not url:
            self.log_message("warning", "Inserisci un URL valido")
            return
        
        self.log_message("info", f"Test mode processing richiesto per: {url}")
        
        # Start test processing in worker thread
        self.start_test_processing(url)
    
    def on_regen_metadata(self):
        """Regenerate metadata using GPT."""
        self.log_message("info", "Rigenerazione metadata richiesta")
        
        # This would be implemented with a worker thread
        # For simplicity, just show a message
        self.log_message("info", "Funzionalità non implementata in questa demo")
    
    def start_test_processing(self, video_url):
        """Start test mode processing for a single video URL."""
        if self.backend.worker and self.backend.worker.running:
            self.log_message("warning", "Processo già in esecuzione")
            return
        
        self.log_message("info", f"Avvio test processing per: {video_url}")
        
        # Create and configure worker with test mode
        self.backend.worker = ViralShortsWorker(self.backend.config)
        self.backend.worker.test_mode = True
        self.backend.worker.test_video_url = video_url
        
        # Connect signals
        self.backend.worker.signals.status.connect(self.status_label.setText)
        self.backend.worker.signals.progress.connect(self.progress_bar.setValue)
        self.backend.worker.signals.finished.connect(self.on_worker_finished)
        
        # Start worker in test mode
        self.backend.worker.start()
        
        # Update GUI state
        self.start_button.setText("Stop")
        self.start_button.setEnabled(True)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Shutdown backend
        self.backend.shutdown()
        event.accept()


    # === ADVANCED AUTOMATION METHODS ===
    
    def start_advanced_scheduler(self):
        """Avvia lo scheduler avanzato"""
        try:
            if hasattr(self.backend, 'advanced_scheduler') and self.backend.advanced_scheduler:
                self.backend.advanced_scheduler.start()
                app_logger.info("🕒 Advanced scheduler started")
                return True
            else:
                app_logger.warning("⚠️ Advanced scheduler not available")
                return False
        except Exception as e:
            app_logger.error(f"Error starting advanced scheduler: {e}")
            return False
    
    def stop_advanced_scheduler(self):
        """Ferma lo scheduler avanzato"""
        try:
            if hasattr(self.backend, 'advanced_scheduler') and self.backend.advanced_scheduler:
                self.backend.advanced_scheduler.stop()
                app_logger.info("🛑 Advanced scheduler stopped")
                return True
            return False
        except Exception as e:
            app_logger.error(f"Error stopping advanced scheduler: {e}")
            return False
    
    def force_performance_monitoring(self):
        """Forza aggiornamento metriche performance"""
        try:
            if hasattr(self.backend, 'performance_monitor') and self.backend.performance_monitor:
                result = self.backend.performance_monitor.update_video_metrics()
                app_logger.info(f"📈 Performance monitoring completed: {result}")
                return result
            else:
                app_logger.warning("⚠️ Performance monitor not available")
                return {"error": "performance_monitor_not_available"}
        except Exception as e:
            app_logger.error(f"Error in performance monitoring: {e}")
            return {"error": str(e)}


def main():
    """Main entry point for the application."""
    try:
        logger.info("Inizializzazione dell'applicazione Qt...")
        # Initialize the application
        app = QApplication(sys.argv)
        
        logger.info("Creazione della finestra principale...")
        window = ViralShortsApp()
        
        logger.info("Visualizzazione della finestra principale...")
        window.show()
        
        # Avvia advanced scheduler se disponibile
        try:
            if hasattr(window.backend, 'advanced_scheduler') and window.backend.advanced_scheduler:
                window.backend.advanced_scheduler.start()
                logger.info("🕒 Advanced automation scheduler started")
        except Exception as e:
            logger.warning(f"⚠️ Advanced scheduler startup failed: {e}")
        
        logger.info("Avvio del loop dell'applicazione...")
        # Run the application loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Errore critico nell'avvio dell'applicazione: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Avvio della funzione main...")
    main()
