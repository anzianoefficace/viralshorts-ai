"""
🎨 Dark Modern Minimal Theme per ViralShortsAI
Sistema di theming completo con design scuro e minimalista
"""

class DarkMinimalTheme:
    """Tema scuro minimalista moderno"""
    
    # === COLORI PRINCIPALI ===
    COLORS = {
        # Background colors
        'bg_primary': '#0D1117',      # Background principale (molto scuro)
        'bg_secondary': '#161B22',    # Background secondario (grigio scuro)
        'bg_tertiary': '#21262D',     # Background terziario (grigio medio)
        'bg_card': '#1C2128',         # Background card/panel
        'bg_hover': '#262C36',        # Background hover
        'bg_selected': '#2F3349',     # Background selected
        
        # Text colors
        'text_primary': '#F0F6FC',    # Testo principale (bianco soft)
        'text_secondary': '#8B949E',  # Testo secondario (grigio chiaro)
        'text_muted': '#6E7681',      # Testo muted (grigio scuro)
        'text_disabled': '#484F58',   # Testo disabilitato
        
        # Border colors
        'border_primary': '#30363D',  # Bordi principali
        'border_secondary': '#21262D', # Bordi secondari
        'border_focus': '#388BFD',    # Bordi focus
        
        # Accent colors
        'accent_blue': '#388BFD',     # Blu principale
        'accent_green': '#3FB950',    # Verde (success)
        'accent_red': '#F85149',      # Rosso (error/danger)
        'accent_orange': '#D29922',   # Arancione (warning)
        'accent_purple': '#A5A5FF',   # Viola (info)
        'accent_pink': '#F778BA',     # Rosa (special)
        
        # Status colors
        'success': '#238636',         # Verde scuro
        'warning': '#9A6700',         # Arancione scuro
        'error': '#DA3633',           # Rosso scuro
        'info': '#0969DA',            # Blu scuro
        
        # Gradient colors
        'gradient_start': '#0D1117',
        'gradient_end': '#161B22',
    }
    
    # === STILI COMPONENTI ===
    @staticmethod
    def get_main_window_style():
        """Stile finestra principale"""
        return f"""
        QMainWindow {{
            background-color: {DarkMinimalTheme.COLORS['bg_primary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: none;
        }}
        
        QMainWindow::separator {{
            background-color: {DarkMinimalTheme.COLORS['border_primary']};
            width: 1px;
            height: 1px;
        }}
        """
    
    @staticmethod
    def get_button_style():
        """Stile bottoni moderni"""
        return f"""
        QPushButton {{
            background-color: {DarkMinimalTheme.COLORS['bg_tertiary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 13px;
            font-weight: 500;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {DarkMinimalTheme.COLORS['bg_hover']};
            border-color: {DarkMinimalTheme.COLORS['border_focus']};
        }}
        
        QPushButton:pressed {{
            background-color: {DarkMinimalTheme.COLORS['bg_selected']};
        }}
        
        QPushButton:disabled {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            color: {DarkMinimalTheme.COLORS['text_disabled']};
            border-color: {DarkMinimalTheme.COLORS['border_secondary']};
        }}
        
        /* Bottoni colorati */
        QPushButton[buttonType="primary"] {{
            background-color: {DarkMinimalTheme.COLORS['accent_blue']};
            border-color: {DarkMinimalTheme.COLORS['accent_blue']};
            color: white;
        }}
        
        QPushButton[buttonType="primary"]:hover {{
            background-color: #2F7ED8;
        }}
        
        QPushButton[buttonType="success"] {{
            background-color: {DarkMinimalTheme.COLORS['accent_green']};
            border-color: {DarkMinimalTheme.COLORS['accent_green']};
            color: white;
        }}
        
        QPushButton[buttonType="success"]:hover {{
            background-color: #2EA043;
        }}
        
        QPushButton[buttonType="danger"] {{
            background-color: {DarkMinimalTheme.COLORS['accent_red']};
            border-color: {DarkMinimalTheme.COLORS['accent_red']};
            color: white;
        }}
        
        QPushButton[buttonType="danger"]:hover {{
            background-color: #E5484D;
        }}
        
        QPushButton[buttonType="warning"] {{
            background-color: {DarkMinimalTheme.COLORS['accent_orange']};
            border-color: {DarkMinimalTheme.COLORS['accent_orange']};
            color: white;
        }}
        
        QPushButton[buttonType="warning"]:hover {{
            background-color: #BB8009;
        }}
        """
    
    @staticmethod
    def get_input_style():
        """Stile input e text fields"""
        return f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            selection-background-color: {DarkMinimalTheme.COLORS['accent_blue']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {DarkMinimalTheme.COLORS['border_focus']};
            background-color: {DarkMinimalTheme.COLORS['bg_tertiary']};
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {DarkMinimalTheme.COLORS['bg_primary']};
            color: {DarkMinimalTheme.COLORS['text_disabled']};
            border-color: {DarkMinimalTheme.COLORS['border_secondary']};
        }}
        """
    
    @staticmethod
    def get_groupbox_style():
        """Stile group box"""
        return f"""
        QGroupBox {{
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 8px;
            font-weight: 600;
            font-size: 14px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px 0 8px;
            color: {DarkMinimalTheme.COLORS['accent_blue']};
            background-color: {DarkMinimalTheme.COLORS['bg_primary']};
        }}
        """
    
    @staticmethod
    def get_tab_style():
        """Stile tab widget"""
        return f"""
        QTabWidget::pane {{
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 8px;
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            padding: 0px;
        }}
        
        QTabWidget::tab-bar {{
            alignment: left;
        }}
        
        QTabBar::tab {{
            background-color: {DarkMinimalTheme.COLORS['bg_tertiary']};
            color: {DarkMinimalTheme.COLORS['text_secondary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 12px 20px;
            margin-right: 2px;
            min-width: 100px;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border-color: {DarkMinimalTheme.COLORS['border_focus']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {DarkMinimalTheme.COLORS['bg_hover']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
        }}
        """
    
    @staticmethod
    def get_scrollbar_style():
        """Stile scrollbar minimalista"""
        return f"""
        QScrollBar:vertical {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {DarkMinimalTheme.COLORS['text_muted']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        QScrollBar:horizontal {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            height: 12px;
            border-radius: 6px;
            margin: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {DarkMinimalTheme.COLORS['text_muted']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
        }}
        """
    
    @staticmethod
    def get_table_style():
        """Stile tabelle"""
        return f"""
        QTableWidget {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 8px;
            gridline-color: {DarkMinimalTheme.COLORS['border_primary']};
            selection-background-color: {DarkMinimalTheme.COLORS['bg_selected']};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {DarkMinimalTheme.COLORS['bg_selected']};
        }}
        
        QHeaderView::section {{
            background-color: {DarkMinimalTheme.COLORS['bg_tertiary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            padding: 8px;
            font-weight: 600;
        }}
        """
    
    @staticmethod
    def get_progress_style():
        """Stile progress bar"""
        return f"""
        QProgressBar {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            text-align: center;
            color: {DarkMinimalTheme.COLORS['text_primary']};
            font-weight: 500;
        }}
        
        QProgressBar::chunk {{
            background-color: {DarkMinimalTheme.COLORS['accent_blue']};
            border-radius: 5px;
        }}
        """
    
    @staticmethod
    def get_combo_style():
        """Stile combo box"""
        return f"""
        QComboBox {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            min-width: 100px;
        }}
        
        QComboBox:hover {{
            border-color: {DarkMinimalTheme.COLORS['border_focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border: 2px solid {DarkMinimalTheme.COLORS['text_secondary']};
            border-top: none;
            border-left: none;
            width: 6px;
            height: 6px;
            transform: rotate(45deg);
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {DarkMinimalTheme.COLORS['bg_tertiary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            selection-background-color: {DarkMinimalTheme.COLORS['bg_selected']};
        }}
        """
    
    @staticmethod
    def get_label_style():
        """Stile label"""
        return f"""
        QLabel {{
            color: {DarkMinimalTheme.COLORS['text_primary']};
            background-color: transparent;
            font-size: 13px;
        }}
        
        QLabel[labelType="title"] {{
            font-size: 18px;
            font-weight: 700;
            color: {DarkMinimalTheme.COLORS['text_primary']};
            margin: 8px 0px;
        }}
        
        QLabel[labelType="subtitle"] {{
            font-size: 14px;
            font-weight: 600;
            color: {DarkMinimalTheme.COLORS['accent_blue']};
            margin: 4px 0px;
        }}
        
        QLabel[labelType="muted"] {{
            color: {DarkMinimalTheme.COLORS['text_muted']};
            font-size: 12px;
        }}
        
        QLabel[labelType="success"] {{
            color: {DarkMinimalTheme.COLORS['accent_green']};
            font-weight: 600;
        }}
        
        QLabel[labelType="error"] {{
            color: {DarkMinimalTheme.COLORS['accent_red']};
            font-weight: 600;
        }}
        
        QLabel[labelType="warning"] {{
            color: {DarkMinimalTheme.COLORS['accent_orange']};
            font-weight: 600;
        }}
        """
    
    @staticmethod
    def get_complete_stylesheet():
        """Stylesheet completo per l'applicazione"""
        return f"""
        /* === TEMA SCURO MINIMALISTA MODERNO === */
        {DarkMinimalTheme.get_main_window_style()}
        {DarkMinimalTheme.get_button_style()}
        {DarkMinimalTheme.get_input_style()}
        {DarkMinimalTheme.get_groupbox_style()}
        {DarkMinimalTheme.get_tab_style()}
        {DarkMinimalTheme.get_scrollbar_style()}
        {DarkMinimalTheme.get_table_style()}
        {DarkMinimalTheme.get_progress_style()}
        {DarkMinimalTheme.get_combo_style()}
        {DarkMinimalTheme.get_label_style()}
        
        /* === WIDGETS SPECIFICI === */
        QFrame {{
            background-color: {DarkMinimalTheme.COLORS['bg_card']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 8px;
        }}
        
        QSplitter::handle {{
            background-color: {DarkMinimalTheme.COLORS['border_primary']};
        }}
        
        QMenuBar {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: none;
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {DarkMinimalTheme.COLORS['bg_hover']};
        }}
        
        QMenu {{
            background-color: {DarkMinimalTheme.COLORS['bg_tertiary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 16px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {DarkMinimalTheme.COLORS['bg_selected']};
        }}
        
        QStatusBar {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            color: {DarkMinimalTheme.COLORS['text_secondary']};
            border: none;
            padding: 4px;
        }}
        
        QCheckBox {{
            color: {DarkMinimalTheme.COLORS['text_primary']};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 3px;
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {DarkMinimalTheme.COLORS['accent_blue']};
            border-color: {DarkMinimalTheme.COLORS['accent_blue']};
        }}
        
        QRadioButton {{
            color: {DarkMinimalTheme.COLORS['text_primary']};
            spacing: 8px;
        }}
        
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 8px;
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {DarkMinimalTheme.COLORS['accent_blue']};
            border-color: {DarkMinimalTheme.COLORS['accent_blue']};
        }}
        
        QSlider::groove:horizontal {{
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            height: 6px;
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {DarkMinimalTheme.COLORS['accent_blue']};
            border: 1px solid {DarkMinimalTheme.COLORS['accent_blue']};
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        
        QSlider::sub-page:horizontal {{
            background-color: {DarkMinimalTheme.COLORS['accent_blue']};
            border-radius: 3px;
        }}
        
        QSpinBox {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            padding: 6px;
        }}
        
        QSpinBox:focus {{
            border-color: {DarkMinimalTheme.COLORS['border_focus']};
        }}
        
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {DarkMinimalTheme.COLORS['bg_tertiary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            width: 16px;
        }}
        
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {DarkMinimalTheme.COLORS['bg_hover']};
        }}
        
        QToolTip {{
            background-color: {DarkMinimalTheme.COLORS['bg_tertiary']};
            color: {DarkMinimalTheme.COLORS['text_primary']};
            border: 1px solid {DarkMinimalTheme.COLORS['border_primary']};
            border-radius: 6px;
            padding: 8px;
            font-size: 12px;
        }}
        """
    
    @staticmethod
    def get_card_style(border_color=None):
        """
        Ottieni stile per card/pannelli
        
        Args:
            border_color (str): Colore bordo personalizzato
            
        Returns:
            str: CSS per card
        """
        border = border_color or DarkMinimalTheme.COLORS['accent_blue']
        
        return f"""
        QFrame {{
            background-color: {DarkMinimalTheme.COLORS['bg_secondary']};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 12px;
        }}
        
        QFrame:hover {{
            border-color: {DarkMinimalTheme.COLORS['accent_blue']};
        }}
        """
    
    @staticmethod
    def get_status_colors():
        """
        Colori per stati diversi
        
        Returns:
            dict: Dizionario colori per stati
        """
        return {
            'success': DarkMinimalTheme.COLORS['accent_green'],
            'warning': DarkMinimalTheme.COLORS['accent_orange'], 
            'error': DarkMinimalTheme.COLORS['accent_red'],
            'info': DarkMinimalTheme.COLORS['accent_blue'],
            'active': DarkMinimalTheme.COLORS['accent_blue'],
            'inactive': DarkMinimalTheme.COLORS['text_muted']
        }
