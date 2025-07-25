"""
🤖 Daily Auto Poster Control Panel
Pannello di controllo GUI per il sistema di posting automatico
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QGroupBox, QProgressBar, QTextEdit, QSpinBox, QTimeEdit, QCheckBox,
    QComboBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from datetime import datetime, timedelta
import json

try:
    from gui.dark_theme import DarkMinimalTheme
    from gui.theme_helper import ThemeHelper
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False

class DailyPosterControlPanel(QWidget):
    """Pannello di controllo per Daily Auto Poster"""
    
    status_updated = pyqtSignal(dict)
    
    def __init__(self, backend=None):
        super().__init__()
        self.backend = backend
        self.setup_ui()
        self.setup_timer()
        
        # Stato iniziale
        self.current_status = {
            'is_running': False,
            'posts_today': 0,
            'daily_target': 1,
            'consecutive_days': 0,
            'last_post_time': None,
            'next_scheduled_times': ["09:00", "15:00", "20:00"],
            'success_rate': 100.0
        }
        
        self.update_display()
    
    def setup_ui(self):
        """Setup interfaccia utente"""
        layout = QVBoxLayout(self)
        
        # Applica tema se disponibile
        if THEME_AVAILABLE:
            self.setStyleSheet(DarkMinimalTheme.get_complete_stylesheet())
        
        # === HEADER ===
        header = self.create_header()
        layout.addWidget(header)
        
        # === CONTROLLI PRINCIPALI ===
        controls = self.create_main_controls()
        layout.addWidget(controls)
        
        # === STATUS E STATISTICHE ===
        stats_layout = QHBoxLayout()
        
        # Status panel
        status_panel = self.create_status_panel()
        stats_layout.addWidget(status_panel, 1)
        
        # Statistics panel  
        stats_panel = self.create_statistics_panel()
        stats_layout.addWidget(stats_panel, 1)
        
        layout.addLayout(stats_layout)
        
        # === CONFIGURAZIONE ===
        config_panel = self.create_configuration_panel()
        layout.addWidget(config_panel)
        
        # === LOG ATTIVITÀ ===
        log_panel = self.create_log_panel()
        layout.addWidget(log_panel)
    
    def create_header(self):
        """Crea header del pannello"""
        header = QFrame()
        layout = QVBoxLayout(header)
        
        if THEME_AVAILABLE:
            title = ThemeHelper.create_title_label("🤖 Daily Auto Poster")
            subtitle = ThemeHelper.create_subtitle_label("Sistema di posting automatico giornaliero")
        else:
            title = QLabel("🤖 Daily Auto Poster")
            title.setFont(QFont("Arial", 18, QFont.Bold))
            subtitle = QLabel("Sistema di posting automatico giornaliero")
            subtitle.setFont(QFont("Arial", 10))
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return header
    
    def create_main_controls(self):
        """Crea controlli principali"""
        group = QGroupBox("🎛️ Controlli Principali")
        layout = QHBoxLayout(group)
        
        # Pulsante Start/Stop
        self.start_stop_btn = QPushButton("🚀 Avvia Auto Poster")
        if THEME_AVAILABLE:
            self.start_stop_btn.setProperty("buttonType", "success")
        self.start_stop_btn.setMinimumHeight(50)
        self.start_stop_btn.clicked.connect(self.toggle_auto_poster)
        
        # Pulsante Post Immediato
        self.post_now_btn = QPushButton("📤 Posta Ora")
        if THEME_AVAILABLE:
            self.post_now_btn.setProperty("buttonType", "primary")
        self.post_now_btn.setMinimumHeight(50)
        self.post_now_btn.clicked.connect(self.post_now)
        
        # Pulsante Forza Contenuto
        self.force_content_btn = QPushButton("🆘 Crea Contenuto Emergenza")
        if THEME_AVAILABLE:
            self.force_content_btn.setProperty("buttonType", "warning")
        self.force_content_btn.setMinimumHeight(50)
        self.force_content_btn.clicked.connect(self.force_emergency_content)
        
        layout.addWidget(self.start_stop_btn)
        layout.addWidget(self.post_now_btn)
        layout.addWidget(self.force_content_btn)
        
        return group
    
    def create_status_panel(self):
        """Crea pannello di status"""
        group = QGroupBox("📊 Status Corrente")
        layout = QVBoxLayout(group)
        
        # Indicatore principale
        status_layout = QHBoxLayout()
        
        self.status_indicator = QLabel("⭕ Stopped")
        self.status_indicator.setFont(QFont("Arial", 14, QFont.Bold))
        if THEME_AVAILABLE:
            self.status_indicator.setProperty("labelType", "error")
        
        status_layout.addWidget(QLabel("Sistema:"))
        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
        # Progress Bar Giornaliero
        progress_layout = QVBoxLayout()
        
        progress_label = QLabel("Progresso Giornaliero:")
        if THEME_AVAILABLE:
            progress_label.setProperty("labelType", "muted")
        
        self.daily_progress = QProgressBar()
        self.daily_progress.setMaximum(100)
        self.daily_progress.setValue(0)
        
        self.progress_text = QLabel("0/1 video pubblicati oggi")
        if THEME_AVAILABLE:
            self.progress_text.setProperty("labelType", "muted")
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.daily_progress)
        progress_layout.addWidget(self.progress_text)
        
        layout.addLayout(progress_layout)
        
        # Prossimi Orari
        schedule_layout = QVBoxLayout()
        
        schedule_label = QLabel("⏰ Prossimi Orari Programmati:")
        if THEME_AVAILABLE:
            schedule_label.setProperty("labelType", "muted")
        
        self.schedule_list = QLabel("09:00, 15:00, 20:00")
        self.schedule_list.setFont(QFont("monospace"))
        
        schedule_layout.addWidget(schedule_label)
        schedule_layout.addWidget(self.schedule_list)
        
        layout.addLayout(schedule_layout)
        
        return group
    
    def create_statistics_panel(self):
        """Crea pannello statistiche"""
        group = QGroupBox("📈 Statistiche")
        layout = QGridLayout(group)
        
        # Giorni consecutivi
        layout.addWidget(QLabel("🔥 Streak Consecutivi:"), 0, 0)
        self.consecutive_days = QLabel("0 giorni")
        self.consecutive_days.setFont(QFont("Arial", 12, QFont.Bold))
        if THEME_AVAILABLE:
            self.consecutive_days.setProperty("labelType", "success")
        layout.addWidget(self.consecutive_days, 0, 1)
        
        # Ultimo post
        layout.addWidget(QLabel("⏰ Ultimo Post:"), 1, 0)
        self.last_post_time = QLabel("Mai")
        if THEME_AVAILABLE:
            self.last_post_time.setProperty("labelType", "muted")
        layout.addWidget(self.last_post_time, 1, 1)
        
        # Success rate
        layout.addWidget(QLabel("✅ Success Rate:"), 2, 0)
        self.success_rate = QLabel("100%")
        self.success_rate.setFont(QFont("Arial", 12, QFont.Bold))
        if THEME_AVAILABLE:
            self.success_rate.setProperty("labelType", "success")
        layout.addWidget(self.success_rate, 2, 1)
        
        # Post questa settimana
        layout.addWidget(QLabel("📅 Questa Settimana:"), 3, 0)
        self.weekly_posts = QLabel("0 video")
        if THEME_AVAILABLE:
            self.weekly_posts.setProperty("labelType", "muted")
        layout.addWidget(self.weekly_posts, 3, 1)
        
        return group
    
    def create_configuration_panel(self):
        """Crea pannello configurazione"""
        group = QGroupBox("⚙️ Configurazione")
        layout = QGridLayout(group)
        
        # Target giornaliero
        layout.addWidget(QLabel("🎯 Target Giornaliero:"), 0, 0)
        self.daily_target_spin = QSpinBox()
        self.daily_target_spin.setRange(1, 10)
        self.daily_target_spin.setValue(1)
        self.daily_target_spin.valueChanged.connect(self.update_config)
        layout.addWidget(self.daily_target_spin, 0, 1)
        
        # Orario preferito 1
        layout.addWidget(QLabel("⏰ Orario 1:"), 1, 0)
        self.time1_edit = QTimeEdit()
        self.time1_edit.setTime(QTime(9, 0))
        self.time1_edit.timeChanged.connect(self.update_config)
        layout.addWidget(self.time1_edit, 1, 1)
        
        # Orario preferito 2
        layout.addWidget(QLabel("⏰ Orario 2:"), 2, 0)
        self.time2_edit = QTimeEdit()
        self.time2_edit.setTime(QTime(15, 0))
        self.time2_edit.timeChanged.connect(self.update_config)
        layout.addWidget(self.time2_edit, 2, 1)
        
        # Orario preferito 3
        layout.addWidget(QLabel("⏰ Orario 3:"), 3, 0)
        self.time3_edit = QTimeEdit()
        self.time3_edit.setTime(QTime(20, 0))
        self.time3_edit.timeChanged.connect(self.update_config)
        layout.addWidget(self.time3_edit, 3, 1)
        
        # Auto creazione contenuto
        self.auto_content_check = QCheckBox("🤖 Auto-crea contenuto se necessario")
        self.auto_content_check.setChecked(True)
        self.auto_content_check.stateChanged.connect(self.update_config)
        layout.addWidget(self.auto_content_check, 4, 0, 1, 2)
        
        return group
    
    def create_log_panel(self):
        """Crea pannello log"""
        group = QGroupBox("📜 Log Attività")
        layout = QVBoxLayout(group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        
        # Log di esempio
        initial_log = f"""[{datetime.now().strftime('%H:%M:%S')}] 🤖 Daily Auto Poster Control Panel inizializzato
[{datetime.now().strftime('%H:%M:%S')}] 📊 Caricamento configurazione...
[{datetime.now().strftime('%H:%M:%S')}] ✅ Sistema pronto per l'uso
"""
        self.log_text.setPlainText(initial_log)
        
        layout.addWidget(self.log_text)
        
        # Pulsanti log
        log_buttons = QHBoxLayout()
        
        clear_log_btn = QPushButton("🗑️ Pulisci Log")
        clear_log_btn.clicked.connect(self.clear_log)
        
        export_log_btn = QPushButton("💾 Esporta Log")
        export_log_btn.clicked.connect(self.export_log)
        
        log_buttons.addWidget(clear_log_btn)
        log_buttons.addWidget(export_log_btn)
        log_buttons.addStretch()
        
        layout.addLayout(log_buttons)
        
        return group
    
    def setup_timer(self):
        """Setup timer per aggiornamenti automatici"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(10000)  # Aggiorna ogni 10 secondi
    
    def toggle_auto_poster(self):
        """Toggle stato auto poster"""
        try:
            if self.backend:
                if self.current_status['is_running']:
                    # Ferma
                    success = self.backend.stop_daily_auto_poster()
                    if success:
                        self.add_log("🛑 Daily Auto Poster fermato")
                        self.start_stop_btn.setText("🚀 Avvia Auto Poster")
                        if THEME_AVAILABLE:
                            self.start_stop_btn.setProperty("buttonType", "success")
                else:
                    # Avvia  
                    success = self.backend.start_daily_auto_poster()
                    if success:
                        self.add_log("🚀 Daily Auto Poster avviato")
                        self.start_stop_btn.setText("🛑 Ferma Auto Poster")
                        if THEME_AVAILABLE:
                            self.start_stop_btn.setProperty("buttonType", "danger")
                
                # Forza aggiornamento status
                self.update_status()
            else:
                self.add_log("❌ Backend non disponibile")
                
        except Exception as e:
            self.add_log(f"❌ Errore toggle auto poster: {e}")
    
    def post_now(self):
        """Forza posting immediato"""
        try:
            self.add_log("📤 Forzando posting immediato...")
            self.post_now_btn.setEnabled(False)
            
            if self.backend:
                success = self.backend.auto_upload_next_video()
                if success:
                    self.add_log("✅ Video pubblicato con successo!")
                else:
                    self.add_log("❌ Errore durante il posting")
            else:
                self.add_log("❌ Backend non disponibile")
            
            self.post_now_btn.setEnabled(True)
            self.update_status()
            
        except Exception as e:
            self.add_log(f"❌ Errore posting immediato: {e}")
            self.post_now_btn.setEnabled(True)
    
    def force_emergency_content(self):
        """Forza creazione contenuto di emergenza"""
        try:
            self.add_log("🆘 Creando contenuto di emergenza...")
            self.force_content_btn.setEnabled(False)
            
            if self.backend:
                # Lista di query di emergenza
                emergency_queries = [
                    "motivation quotes", "life hacks", "funny moments",
                    "quick tips", "amazing facts", "success stories"
                ]
                
                import random
                query = random.choice(emergency_queries)
                
                success = self.backend.search_and_process_emergency_content(query)
                if success:
                    self.add_log(f"✅ Contenuto di emergenza creato: {query}")
                else:
                    self.add_log("❌ Errore creazione contenuto emergenza")
            else:
                self.add_log("❌ Backend non disponibile")
            
            self.force_content_btn.setEnabled(True)
            
        except Exception as e:
            self.add_log(f"❌ Errore contenuto emergenza: {e}")
            self.force_content_btn.setEnabled(True)
    
    def update_status(self):
        """Aggiorna status dal backend"""
        try:
            if self.backend:
                status = self.backend.get_daily_poster_status()
                if status and 'error' not in status:
                    self.current_status.update(status)
                    self.update_display()
        except Exception as e:
            self.add_log(f"❌ Errore aggiornamento status: {e}")
    
    def update_display(self):
        """Aggiorna visualizzazione con status corrente"""
        try:
            status = self.current_status
            
            # Status indicator
            if status['is_running']:
                self.status_indicator.setText("🟢 Attivo")
                if THEME_AVAILABLE:
                    self.status_indicator.setProperty("labelType", "success")
            else:
                self.status_indicator.setText("⭕ Fermo")
                if THEME_AVAILABLE:
                    self.status_indicator.setProperty("labelType", "error")
            
            # Progress bar
            progress = (status['posts_today'] / max(status['daily_target'], 1)) * 100
            self.daily_progress.setValue(min(int(progress), 100))
            self.progress_text.setText(f"{status['posts_today']}/{status['daily_target']} video pubblicati oggi")
            
            # Statistiche
            self.consecutive_days.setText(f"{status['consecutive_days']} giorni")
            self.success_rate.setText(f"{status['success_rate']:.1f}%")
            
            if status['last_post_time']:
                try:
                    last_time = datetime.fromisoformat(status['last_post_time'])
                    self.last_post_time.setText(last_time.strftime('%d/%m %H:%M'))
                except:
                    self.last_post_time.setText("Errore formato")
            else:
                self.last_post_time.setText("Mai")
            
            # Orari programmati
            if status['next_scheduled_times']:
                times_str = ", ".join(status['next_scheduled_times'])
                self.schedule_list.setText(times_str)
            
            # Emetti segnale per altri componenti
            self.status_updated.emit(status)
            
        except Exception as e:
            self.add_log(f"❌ Errore update display: {e}")
    
    def update_config(self):
        """Aggiorna configurazione"""
        try:
            config = {
                'daily_target': self.daily_target_spin.value(),
                'optimal_times': [
                    self.time1_edit.time().toString('HH:mm'),
                    self.time2_edit.time().toString('HH:mm'),
                    self.time3_edit.time().toString('HH:mm')
                ],
                'auto_content': self.auto_content_check.isChecked()
            }
            
            self.add_log("⚙️ Configurazione aggiornata")
            
        except Exception as e:
            self.add_log(f"❌ Errore aggiornamento config: {e}")
    
    def add_log(self, message: str):
        """Aggiungi messaggio al log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        current_text = self.log_text.toPlainText()
        self.log_text.setPlainText(current_text + log_entry + "\n")
        
        # Scroll automatico
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Pulisci log"""
        self.log_text.clear()
        self.add_log("🗑️ Log pulito")
    
    def export_log(self):
        """Esporta log su file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"daily_poster_log_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(self.log_text.toPlainText())
            
            self.add_log(f"💾 Log esportato: {filename}")
            
        except Exception as e:
            self.add_log(f"❌ Errore esportazione log: {e}")
    
    def get_current_status(self):
        """Restituisce status corrente per uso esterno"""
        return self.current_status.copy()

# Widget compatto per dashboard
class DailyPosterWidget(QFrame):
    """Widget compatto per mostrare status daily poster in dashboard"""
    
    def __init__(self, backend=None):
        super().__init__()
        self.backend = backend
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI compatta"""
        layout = QVBoxLayout(self)
        
        # Applica tema se disponibile
        if THEME_AVAILABLE:
            self.setStyleSheet(DarkMinimalTheme.get_card_style())
        
        # Header
        header = QHBoxLayout()
        
        if THEME_AVAILABLE:
            title = ThemeHelper.create_subtitle_label("🤖 Auto Poster")
        else:
            title = QLabel("🤖 Auto Poster")
            title.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.status_dot = QLabel("⭕")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.status_dot)
        
        layout.addLayout(header)
        
        # Stats compatte
        self.stats_label = QLabel("0/1 oggi • 0 giorni streak")
        if THEME_AVAILABLE:
            self.stats_label.setProperty("labelType", "muted")
        
        layout.addWidget(self.stats_label)
        
        # Progress mini
        self.mini_progress = QProgressBar()
        self.mini_progress.setMaximumHeight(4)
        self.mini_progress.setTextVisible(False)
        
        layout.addWidget(self.mini_progress)
    
    def update_status(self, status_dict):
        """Aggiorna status compatto"""
        try:
            # Status dot
            if status_dict.get('is_running', False):
                self.status_dot.setText("🟢")
            else:
                self.status_dot.setText("⭕")
            
            # Stats compatte
            posts_today = status_dict.get('posts_today', 0)
            daily_target = status_dict.get('daily_target', 1)
            consecutive = status_dict.get('consecutive_days', 0)
            
            self.stats_label.setText(f"{posts_today}/{daily_target} oggi • {consecutive} giorni streak")
            
            # Progress
            progress = (posts_today / max(daily_target, 1)) * 100
            self.mini_progress.setValue(min(int(progress), 100))
            
        except Exception as e:
            print(f"Errore update status widget: {e}")
