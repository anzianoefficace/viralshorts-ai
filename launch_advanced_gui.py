"""
🚀 Launcher per ViralShortsAI Advanced Smart GUI
Punto di ingresso principale per l'interfaccia avanzata
"""

import sys
import os
import traceback
from pathlib import Path

# Aggiungi il path principale
current_dir = Path(__file__).parent
main_dir = current_dir.parent
sys.path.insert(0, str(main_dir))

from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor

from gui.advanced_gui import AdvancedSmartGUI
from gui.smart_notifications import notification_center, show_notification, NotificationType

class BackendLoader(QThread):
    """Thread per caricare il backend in background"""
    
    backend_loaded = pyqtSignal(object)
    progress_updated = pyqtSignal(str, int)
    error_occurred = pyqtSignal(str)
    
    def run(self):
        """Carica il backend"""
        try:
            self.progress_updated.emit("Initializing ViralShortsAI...", 10)
            
            # Importa il backend
            from main import ViralShortsBackend
            self.progress_updated.emit("Loading configuration...", 30)
            
            # Inizializza il backend
            backend = ViralShortsBackend()
            self.progress_updated.emit("Starting automation systems...", 60)
            
            # Verifica componenti
            status = backend.get_automation_status()
            self.progress_updated.emit("Components ready!", 90)
            
            self.progress_updated.emit("Launch complete!", 100)
            self.backend_loaded.emit(backend)
            
        except Exception as e:
            error_msg = f"Backend loading failed: {str(e)}"
            self.error_occurred.emit(error_msg)
            print(f"Backend error: {e}")
            traceback.print_exc()

class ModernSplashScreen(QWidget):
    """Splash screen moderno"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dell'interfaccia splash"""
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Center on screen
        from PyQt5.QtWidgets import QDesktopWidget
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        x = (screen_rect.width() - self.width()) // 2
        y = (screen_rect.height() - self.height()) // 2
        self.move(x, y)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Logo/Title
        title = QLabel("🚀 ViralShortsAI")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1976d2; margin: 20px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Advanced Smart GUI")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(subtitle)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Arial", 11))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #333; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # Progress bar simulata con stile
        self.progress_widget = QWidget()
        self.progress_widget.setFixedHeight(4)
        self.progress_widget.setStyleSheet("""
            QWidget {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_widget)
        
        # Background style
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
    
    def update_progress(self, message: str, progress: int):
        """Aggiorna il progresso"""
        self.status_label.setText(message)
        
        # Aggiorna barra progresso visuale
        progress_width = int((self.progress_widget.width() * progress) / 100)
        self.progress_widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976d2, stop:{progress/100} #1976d2,
                    stop:{progress/100} #e0e0e0, stop:1 #e0e0e0);
                border-radius: 2px;
            }}
        """)
        
        QApplication.processEvents()

class AdvancedLauncher:
    """Launcher principale per GUI avanzata"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ViralShortsAI Advanced GUI")
        self.app.setApplicationVersion("2.0")
        
        self.splash = None
        self.main_window = None
        self.backend = None
        
    def setup_splash(self):
        """Setup splash screen"""
        self.splash = ModernSplashScreen()
        self.splash.show()
        
        # Aggiorna splash per 1 secondo
        QTimer.singleShot(500, self.load_backend)
    
    def load_backend(self):
        """Carica il backend in background"""
        self.loader = BackendLoader()
        self.loader.backend_loaded.connect(self.on_backend_loaded)
        self.loader.progress_updated.connect(self.splash.update_progress)
        self.loader.error_occurred.connect(self.on_backend_error)
        self.loader.start()
    
    def on_backend_loaded(self, backend):
        """Callback quando backend è caricato"""
        self.backend = backend
        
        # Nasconde splash e mostra GUI principale
        QTimer.singleShot(1000, self.show_main_gui)
    
    def on_backend_error(self, error_message):
        """Callback per errori backend"""
        self.splash.update_progress(f"Error: {error_message}", 0)
        
        # Mostra GUI senza backend dopo 3 secondi
        QTimer.singleShot(3000, self.show_main_gui_without_backend)
    
    def show_main_gui(self):
        """Mostra GUI principale"""
        try:
            self.splash.close()
            
            # Crea GUI principale
            self.main_window = AdvancedSmartGUI(self.backend)
            self.main_window.show()
            
            # Mostra notifica di benvenuto
            show_notification(
                "🚀 ViralShortsAI Ready!",
                "Advanced Smart GUI loaded successfully",
                NotificationType.SUCCESS,
                4000
            )
            
            # Se backend disponibile, mostra status automazione
            if self.backend:
                try:
                    status = self.backend.get_automation_status()
                    running_components = sum(1 for comp in status.values() 
                                           if isinstance(comp, dict) and comp.get('initialized'))
                    
                    show_notification(
                        "🤖 Automation Status",
                        f"{running_components} automation components active",
                        NotificationType.INFO,
                        3000
                    )
                except Exception as e:
                    print(f"Status check error: {e}")
            
        except Exception as e:
            print(f"GUI launch error: {e}")
            traceback.print_exc()
    
    def show_main_gui_without_backend(self):
        """Mostra GUI senza backend"""
        try:
            self.splash.close()
            
            # Crea GUI senza backend
            self.main_window = AdvancedSmartGUI(None)
            self.main_window.show()
            
            # Mostra notifica di avviso
            show_notification(
                "⚠️ Limited Mode",
                "GUI loaded without backend - some features unavailable",
                NotificationType.WARNING,
                5000
            )
            
        except Exception as e:
            print(f"GUI launch error: {e}")
            traceback.print_exc()
    
    def run(self):
        """Avvia l'applicazione"""
        try:
            self.setup_splash()
            return self.app.exec_()
        except Exception as e:
            print(f"Application error: {e}")
            traceback.print_exc()
            return 1

def main():
    """Funzione principale"""
    print("🚀 Launching ViralShortsAI Advanced Smart GUI...")
    
    # Verifica dipendenze
    try:
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5 available")
    except ImportError:
        print("❌ PyQt5 not available. Please install: pip install PyQt5")
        return 1
    
    try:
        import matplotlib
        print("✅ Matplotlib available for charts")
    except ImportError:
        print("⚠️ Matplotlib not available - charts disabled")
    
    # Crea e avvia launcher
    launcher = AdvancedLauncher()
    return launcher.run()

if __name__ == "__main__":
    sys.exit(main())
