"""
🎨 Theme Helper Functions per ViralShortsAI
Funzioni utility per applicare il tema scuro minimalista
"""

from PyQt5.QtWidgets import QPushButton, QLabel, QFrame
from .dark_theme import DarkMinimalTheme

class ThemeHelper:
    """Helper per applicare proprietà del tema"""
    
    @staticmethod
    def apply_button_style(button: QPushButton, button_type: str = "default"):
        """Applica stile specifico ai bottoni"""
        button.setProperty("buttonType", button_type)
        return button
    
    @staticmethod
    def apply_label_style(label: QLabel, label_type: str = "default"):
        """Applica stile specifico alle label"""
        label.setProperty("labelType", label_type)
        return label
    
    @staticmethod
    def create_primary_button(text: str) -> QPushButton:
        """Crea bottone primario blu"""
        btn = QPushButton(text)
        btn.setProperty("buttonType", "primary")
        return btn
    
    @staticmethod
    def create_success_button(text: str) -> QPushButton:
        """Crea bottone successo verde"""
        btn = QPushButton(text)
        btn.setProperty("buttonType", "success")
        return btn
    
    @staticmethod
    def create_danger_button(text: str) -> QPushButton:
        """Crea bottone pericolo rosso"""
        btn = QPushButton(text)
        btn.setProperty("buttonType", "danger")
        return btn
    
    @staticmethod
    def create_warning_button(text: str) -> QPushButton:
        """Crea bottone warning arancione"""
        btn = QPushButton(text)
        btn.setProperty("buttonType", "warning")
        return btn
    
    @staticmethod
    def create_title_label(text: str) -> QLabel:
        """Crea label titolo"""
        label = QLabel(text)
        label.setProperty("labelType", "title")
        return label
    
    @staticmethod
    def create_subtitle_label(text: str) -> QLabel:
        """Crea label sottotitolo"""
        label = QLabel(text)
        label.setProperty("labelType", "subtitle")
        return label
    
    @staticmethod
    def create_muted_label(text: str) -> QLabel:
        """Crea label muted"""
        label = QLabel(text)
        label.setProperty("labelType", "muted")
        return label
    
    @staticmethod
    def create_success_label(text: str) -> QLabel:
        """Crea label successo"""
        label = QLabel(text)
        label.setProperty("labelType", "success")
        return label
    
    @staticmethod
    def create_error_label(text: str) -> QLabel:
        """Crea label errore"""
        label = QLabel(text)
        label.setProperty("labelType", "error")
        return label
    
    @staticmethod
    def create_warning_label(text: str) -> QLabel:
        """Crea label warning"""
        label = QLabel(text)
        label.setProperty("labelType", "warning")
        return label
    
    @staticmethod
    def create_card_frame() -> QFrame:
        """Crea frame card con tema scuro"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        return frame
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Ottieni colore per status"""
        status_colors = {
            'active': DarkMinimalTheme.COLORS['accent_green'],
            'inactive': DarkMinimalTheme.COLORS['text_muted'],
            'error': DarkMinimalTheme.COLORS['accent_red'],
            'warning': DarkMinimalTheme.COLORS['accent_orange'],
            'processing': DarkMinimalTheme.COLORS['accent_blue'],
            'success': DarkMinimalTheme.COLORS['accent_green'],
            'paused': DarkMinimalTheme.COLORS['accent_orange'],
            'stopped': DarkMinimalTheme.COLORS['text_disabled']
        }
        return status_colors.get(status.lower(), DarkMinimalTheme.COLORS['text_secondary'])
    
    @staticmethod
    def get_priority_color(priority: str) -> str:
        """Ottieni colore per priorità"""
        priority_colors = {
            'high': DarkMinimalTheme.COLORS['accent_red'],
            'medium': DarkMinimalTheme.COLORS['accent_orange'],
            'low': DarkMinimalTheme.COLORS['accent_green'],
            'critical': DarkMinimalTheme.COLORS['accent_red'],
            'normal': DarkMinimalTheme.COLORS['accent_blue']
        }
        return priority_colors.get(priority.lower(), DarkMinimalTheme.COLORS['text_secondary'])
