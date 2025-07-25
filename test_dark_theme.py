"""
🤖 Test per il nuovo tema scuro per ViralShortsAI
Testa l'applicazione del tema scuro minimalista
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from gui.dark_theme import DarkMinimalTheme
from gui.theme_helper import ThemeHelper

class TestDarkTheme(QWidget):
    """Widget di test per il tema scuro"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 ViralShortsAI - Dark Theme Test")
        self.setGeometry(100, 100, 800, 600)
        self.apply_theme()
        self.setup_ui()
    
    def apply_theme(self):
        """Applica il tema scuro"""
        self.setStyleSheet(DarkMinimalTheme.get_complete_stylesheet())
    
    def setup_ui(self):
        """Setup interfaccia di test"""
        layout = QVBoxLayout(self)
        
        # Titolo
        title = ThemeHelper.create_title_label("🎨 Dark Theme Test")
        layout.addWidget(title)
        
        # Sottotitolo
        subtitle = ThemeHelper.create_subtitle_label("Test dei componenti con tema scuro minimalista")
        layout.addWidget(subtitle)
        
        # Test bottoni
        buttons_layout = QHBoxLayout()
        
        primary_btn = ThemeHelper.create_primary_button("Primary Button")
        success_btn = ThemeHelper.create_success_button("Success Button")
        danger_btn = ThemeHelper.create_danger_button("Danger Button")
        warning_btn = ThemeHelper.create_warning_button("Warning Button")
        
        buttons_layout.addWidget(primary_btn)
        buttons_layout.addWidget(success_btn)
        buttons_layout.addWidget(danger_btn)
        buttons_layout.addWidget(warning_btn)
        
        layout.addLayout(buttons_layout)
        
        # Test label
        labels_layout = QVBoxLayout()
        
        success_label = ThemeHelper.create_success_label("✅ Operazione completata con successo")
        error_label = ThemeHelper.create_error_label("❌ Errore nel processo")
        warning_label = ThemeHelper.create_warning_label("⚠️ Attenzione: ricontrollare")
        muted_label = ThemeHelper.create_muted_label("Testo secondario e informazioni aggiuntive")
        
        labels_layout.addWidget(success_label)
        labels_layout.addWidget(error_label)
        labels_layout.addWidget(warning_label)
        labels_layout.addWidget(muted_label)
        
        layout.addLayout(labels_layout)
        
        # Test card
        card = ThemeHelper.create_card_frame()
        card_layout = QVBoxLayout(card)
        card_title = ThemeHelper.create_subtitle_label("📊 Card di Esempio")
        card_content = ThemeHelper.create_muted_label("Contenuto della card con tema scuro")
        card_layout.addWidget(card_title)
        card_layout.addWidget(card_content)
        
        layout.addWidget(card)

def main():
    """Test del tema scuro"""
    app = QApplication(sys.argv)
    app.setApplicationName("ViralShortsAI Dark Theme Test")
    
    window = TestDarkTheme()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
