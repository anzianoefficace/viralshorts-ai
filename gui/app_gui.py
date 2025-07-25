"""
GUI module for ViralShortsAI.
Handles the graphical user interface using PyQt5 with modern dark theme.
"""

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QCheckBox, QLineEdit, QTextEdit, QComboBox, QSpinBox, QTableWidget,
    QTableWidgetItem, QFileDialog, QTabWidget, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QTime
from .dark_theme import DarkMinimalTheme
import sys
import json
import os

class ViralShortsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ViralShortsAI - Dark Edition")
        self.setGeometry(100, 100, 1000, 700)
        self.config = self.load_config()
        self.apply_dark_theme()
        self.init_ui()
    
    def apply_dark_theme(self):
        """Applica il tema scuro minimalista"""
        self.setStyleSheet(DarkMinimalTheme.get_complete_stylesheet())

    def load_config(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                return json.load(f)
        else:
            return {}

    def save_config(self):
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header con pulsante GUI avanzata
        header_layout = QHBoxLayout()
        
        title_label = QLabel("ViralShortsAI")
        title_label.setProperty("labelType", "title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Pulsante per GUI avanzata
        advanced_gui_btn = QPushButton("🚀 Launch Advanced GUI")
        advanced_gui_btn.setProperty("buttonType", "primary")
        advanced_gui_btn.clicked.connect(self.launch_advanced_gui)
        header_layout.addWidget(advanced_gui_btn)
        
        layout.addLayout(header_layout)

        tabs = QTabWidget()
        tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        tabs.addTab(self.create_config_tab(), "Parametri")
        tabs.addTab(self.create_results_tab(), "Risultati")
        tabs.addTab(self.create_debug_tab(), "Debug")

        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def launch_advanced_gui(self):
        """Lancia la GUI avanzata"""
        try:
            import subprocess
            import sys
            import os
            
            # Path al launcher della GUI avanzata
            launcher_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "launch_advanced_gui.py")
            
            if os.path.exists(launcher_path):
                # Lancia la GUI avanzata in un processo separato
                subprocess.Popen([sys.executable, launcher_path])
                
                # Mostra messaggio di conferma
                QMessageBox.information(self, "Advanced GUI", 
                                      "🚀 Advanced Smart GUI is launching...\n\n"
                                      "The new interface will open in a separate window with:\n"
                                      "• Real-time dashboard\n"
                                      "• Smart notifications\n"
                                      "• Advanced automation controls\n"
                                      "• Analytics charts")
            else:
                QMessageBox.warning(self, "Error", 
                                  f"Advanced GUI launcher not found at:\n{launcher_path}")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch Advanced GUI:\n{str(e)}")

    # --- Dashboard Tab ---
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.status_label = QLabel("🟢 Sistema pronto")
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        self.start_button = QPushButton("▶️ Avvia ora")
        self.start_button.clicked.connect(self.start_process)

        self.daily_checkbox = QCheckBox("Esegui ogni giorno alle 10:00")
        self.daily_checkbox.setChecked(self.config.get("daily_run", False))

        layout.addWidget(self.status_label)
        layout.addWidget(self.daily_checkbox)
        layout.addWidget(self.start_button)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log_area)

        widget.setLayout(layout)
        return widget

    def start_process(self):
        self.log_area.append("✅ Avvio processo...")
        # Qui puoi collegare la logica main.py
        self.status_label.setText("⏳ Processo in esecuzione...")

    # --- Configurazione Parametri ---
    def create_config_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Categorie
        cat_group = QGroupBox("Categorie")
        cat_layout = QHBoxLayout()
        self.cat_checkboxes = {}
        for cat in ["Intrattenimento", "Notizie", "Sport", "Curiosità", "Lifestyle"]:
            cb = QCheckBox(cat)
            cb.setChecked(True)
            self.cat_checkboxes[cat] = cb
            cat_layout.addWidget(cb)
        cat_group.setLayout(cat_layout)

        # Durate
        duration_group = QGroupBox("Durata clip")
        duration_layout = QHBoxLayout()
        self.duration_15 = QCheckBox("15s")
        self.duration_30 = QCheckBox("30s")
        self.duration_60 = QCheckBox("60s")
        self.duration_15.setChecked(True)
        self.duration_30.setChecked(True)
        self.duration_60.setChecked(True)
        for d in [self.duration_15, self.duration_30, self.duration_60]:
            duration_layout.addWidget(d)
        duration_group.setLayout(duration_layout)

        # Max video
        self.max_videos = QSpinBox()
        self.max_videos.setRange(1, 50)
        self.max_videos.setValue(5)

        # Lingua
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(["Italiano", "Inglese", "Spagnolo", "Francese"])
        self.language_dropdown.setCurrentText("Italiano")

        # Hashtag
        self.hashtag_input = QLineEdit()
        self.hashtag_input.setPlaceholderText("Inserisci hashtag personalizzati separati da virgola")

        layout.addWidget(cat_group)
        layout.addWidget(duration_group)
        layout.addWidget(QLabel("Max video al giorno:"))
        layout.addWidget(self.max_videos)
        layout.addWidget(QLabel("Lingua:"))
        layout.addWidget(self.language_dropdown)
        layout.addWidget(QLabel("Hashtag personalizzati:"))
        layout.addWidget(self.hashtag_input)

        widget.setLayout(layout)
        return widget

    # --- Risultati ---
    def create_results_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Titolo", "Views", "Like", "Commenti", "Viral Score", "Retention"
        ])

        layout.addWidget(self.results_table)
        widget.setLayout(layout)
        return widget

    # --- Debug ---
    def create_debug_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.manual_url_input = QLineEdit()
        self.manual_url_input.setPlaceholderText("Incolla URL di un video da forzare")

        self.force_download_button = QPushButton("Scarica da URL")
        self.regen_metadata_button = QPushButton("Rigenera metadata GPT")
        self.only_processing_checkbox = QCheckBox("Solo elaborazione, non pubblicare")
        
        # YouTube auth section
        auth_group = QGroupBox("YouTube Authentication")
        auth_layout = QVBoxLayout()
        self.youtube_auth_button = QPushButton("🔑 Forza Ri-autenticazione YouTube")
        self.youtube_auth_button.clicked.connect(self.force_youtube_reauth)
        auth_layout.addWidget(self.youtube_auth_button)
        auth_group.setLayout(auth_layout)

        layout.addWidget(QLabel("Test URL forzato:"))
        layout.addWidget(self.manual_url_input)
        layout.addWidget(self.force_download_button)
        layout.addWidget(self.regen_metadata_button)
        layout.addWidget(self.only_processing_checkbox)
        layout.addWidget(auth_group)

        widget.setLayout(layout)
        return widget

    def force_youtube_reauth(self):
        """
        Force YouTube re-authentication by removing the current token.
        This method is called when the user clicks the YouTube re-auth button.
        """
        reply = QMessageBox.question(
            self,
            "Conferma Riautenticazione",
            "Vuoi davvero riautenticare l'account YouTube? Questo rimuoverà il token di accesso attuale.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.delete_youtube_token()
            if success:
                QMessageBox.information(
                    self,
                    "Riautenticazione Avviata",
                    "Il token è stato rimosso. Riavvia l'app per avviare il processo di autenticazione."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Errore",
                    "Errore durante la cancellazione del token. Controlla i permessi o il file .env."
                )
            
    def update_env_file(self, key, value):
        """
        Update a key-value pair in the .env file.
        
        Args:
            key (str): The key to update
            value (str): The new value
        """
        try:
            # Read the .env file
            with open(".env", "r") as f:
                lines = f.readlines()
                
            # Find and replace the line with the key
            new_lines = []
            key_found = False
            for line in lines:
                if line.startswith(f"{key}="):
                    new_lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    new_lines.append(line)
                    
            # If key not found, add it
            if not key_found:
                new_lines.append(f"{key}={value}\n")
                
            # Write back the .env file
            with open(".env", "w") as f:
                f.writelines(new_lines)
                
            self.log_area.append(f"✅ File .env aggiornato con nuovo token")
        except Exception as e:
            self.log_area.append(f"❌ Errore nell'aggiornamento del file .env: {e}")

    def delete_youtube_token(self):
        """
        Delete YouTube refresh token from .env file and credentials file.
        This is useful when you want to force a complete re-authentication.
        
        Returns:
            bool: True if the token was successfully deleted, False otherwise
        """
        try:
            # Rimuovi token da .env
            self.log_area.append("🗑️ Rimozione token YouTube da .env...")
            with open(".env", "r") as file:
                lines = file.readlines()
                
            with open(".env", "w") as file:
                for line in lines:
                    if not line.startswith("YOUTUBE_REFRESH_TOKEN"):
                        file.write(line)
            
            # Cerca e rimuovi anche file di credenziali se esiste
            from upload.youtube_uploader import YouTubeUploader
            from pathlib import Path
            
            # Load config
            with open("config.json", "r") as f:
                config = json.load(f)
                
            # Get credentials path
            uploader = YouTubeUploader(config)
            credentials_path = uploader.credentials_path
            
            if Path(credentials_path).exists():
                self.log_area.append(f"🗑️ Rimozione file credenziali da {credentials_path}...")
                Path(credentials_path).unlink()
                
            self.log_area.append("✅ Token YouTube rimosso con successo")
            self.status_label.setText("🟠 Token YouTube rimosso")
            return True
                
        except Exception as e:
            self.log_area.append(f"❌ Errore nella rimozione del token: {e}")
            return False


# Avvio diretto se eseguito come script principale
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ViralShortsApp()
    window.show()
    sys.exit(app.exec_())
