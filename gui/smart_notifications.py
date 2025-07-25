"""
🔔 Smart Notification System per ViralShortsAI Advanced GUI
Sistema di notifiche intelligenti con toast, alerts e monitoring
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import threading
import time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsOpacityEffect, QApplication, QDesktopWidget,
    QSystemTrayIcon, QMenu, QAction, QMessageBox
)

from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, 
    pyqtSignal, QObject, QThread
)

from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QPen

class NotificationType:
    """Tipi di notifiche"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    VIRAL = "viral"
    AUTOMATION = "automation"

class ToastNotification(QFrame):
    """Widget toast notification moderno"""
    
    clicked = pyqtSignal()
    
    def __init__(self, title: str, message: str, notification_type: str = NotificationType.INFO, duration: int = 5000):
        super().__init__()
        self.duration = duration
        self.notification_type = notification_type
        self.setup_ui(title, message)
        self.setup_animations()
        
        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_notification)
        
        # Mostra la notifica
        self.show_notification()
    
    def setup_ui(self, title: str, message: str):
        """Setup dell'interfaccia toast"""
        self.setFixedSize(350, 80)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Stili in base al tipo
        styles = {
            NotificationType.INFO: {"bg": "#2196F3", "icon": "ℹ️"},
            NotificationType.SUCCESS: {"bg": "#4CAF50", "icon": "✅"},
            NotificationType.WARNING: {"bg": "#FF9800", "icon": "⚠️"},
            NotificationType.ERROR: {"bg": "#F44336", "icon": "❌"},
            NotificationType.VIRAL: {"bg": "#E91E63", "icon": "🔥"},
            NotificationType.AUTOMATION: {"bg": "#9C27B0", "icon": "🤖"}
        }
        
        style = styles.get(self.notification_type, styles[NotificationType.INFO])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {style["bg"]};
                border-radius: 8px;
                border: none;
            }}
            QLabel {{
                color: white;
                border: none;
                background: transparent;
            }}
            QPushButton {{
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                color: white;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
        """)
        
        # Layout principale
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Icon
        icon_label = QLabel(style["icon"])
        icon_label.setFont(QFont("Arial", 16))
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        content_layout.addWidget(title_label)
        
        message_label = QLabel(message)
        message_label.setFont(QFont("Arial", 9))
        message_label.setWordWrap(True)
        content_layout.addWidget(message_label)
        
        layout.addLayout(content_layout)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setFont(QFont("Arial", 8))
        close_btn.clicked.connect(self.hide_notification)
        layout.addWidget(close_btn)
    
    def setup_animations(self):
        """Setup animazioni"""
        # Fade in animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self.close)
    
    def show_notification(self):
        """Mostra la notifica"""
        # Posiziona in basso a destra
        desktop = QApplication.desktop().availableGeometry()
        x = desktop.width() - self.width() - 20
        y = desktop.height() - self.height() - 60
        self.move(x, y)
        
        self.show()
        self.fade_in.start()
        
        # Auto-hide
        if self.duration > 0:
            self.hide_timer.start(self.duration)
    
    def hide_notification(self):
        """Nasconde la notifica"""
        self.hide_timer.stop()
        self.fade_out.start()
    
    def mousePressEvent(self, event):
        """Handle click"""
        self.clicked.emit()
        self.hide_notification()

class NotificationCenter(QObject):
    """Centro notifiche smart"""
    
    def __init__(self):
        super().__init__()
        self.active_toasts = []
        self.notification_history = []
        self.max_toasts = 5
        
        # Configurazione
        self.settings = {
            'desktop_notifications': True,
            'viral_alerts': True,
            'automation_alerts': True,
            'sound_enabled': True,
            'max_history': 100
        }
    
    def show_toast(self, title: str, message: str, notification_type: str = NotificationType.INFO, duration: int = 5000):
        """Mostra toast notification"""
        if not self.settings['desktop_notifications']:
            return
        
        # Limita numero di toast attivi
        if len(self.active_toasts) >= self.max_toasts:
            self.active_toasts[0].hide_notification()
            self.active_toasts.pop(0)
        
        # Crea toast
        toast = ToastNotification(title, message, notification_type, duration)
        toast.clicked.connect(lambda: self.on_toast_clicked(toast))
        
        # Posiziona correttamente se ci sono altri toast
        if self.active_toasts:
            last_toast = self.active_toasts[-1]
            new_y = last_toast.y() - toast.height() - 10
            toast.move(toast.x(), new_y)
        
        self.active_toasts.append(toast)
        
        # Aggiungi alla cronologia
        self.add_to_history(title, message, notification_type)
        
        # Rimuovi dalla lista quando si chiude
        toast.fade_out.finished.connect(lambda: self.remove_toast(toast))
    
    def remove_toast(self, toast):
        """Rimuove toast dalla lista"""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            
        # Riposiziona toast rimanenti
        self.reposition_toasts()
    
    def reposition_toasts(self):
        """Riposiziona i toast attivi"""
        desktop = QApplication.desktop().availableGeometry()
        base_y = desktop.height() - 60
        
        for i, toast in enumerate(self.active_toasts):
            y = base_y - (toast.height() + 10) * (i + 1)
            toast.move(toast.x(), y)
    
    def add_to_history(self, title: str, message: str, notification_type: str):
        """Aggiunge notifica alla cronologia"""
        notification = {
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'message': message,
            'type': notification_type
        }
        
        self.notification_history.append(notification)
        
        # Mantieni solo le ultime N notifiche
        if len(self.notification_history) > self.settings['max_history']:
            self.notification_history = self.notification_history[-self.settings['max_history']:]
    
    def on_toast_clicked(self, toast):
        """Gestisce click su toast"""
        print(f"Toast clicked: {toast.notification_type}")
    
    def show_viral_alert(self, video_title: str, metrics: Dict[str, Any]):
        """Mostra alert per video virale"""
        if not self.settings['viral_alerts']:
            return
        
        views = metrics.get('views', 0)
        engagement = metrics.get('engagement_rate', 0)
        
        title = "🔥 Video Going Viral!"
        message = f"{video_title}\n👁️ {views:,} views | 💬 {engagement:.1f}% engagement"
        
        self.show_toast(title, message, NotificationType.VIRAL, 8000)
        
        # System tray notification
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)
    
    def show_automation_alert(self, event: str, status: str, details: str = ""):
        """Mostra alert per eventi di automazione"""
        if not self.settings['automation_alerts']:
            return
        
        title = f"🤖 Automation: {event}"
        message = f"Status: {status}"
        if details:
            message += f"\n{details}"
        
        notification_type = NotificationType.SUCCESS if status == "Success" else NotificationType.WARNING
        
        self.show_toast(title, message, notification_type, 4000)
    
    def show_error_alert(self, error_type: str, error_message: str):
        """Mostra alert per errori"""
        title = f"❌ Error: {error_type}"
        message = error_message
        
        self.show_toast(title, message, NotificationType.ERROR, 7000)
    
    def show_quota_warning(self, service: str, usage_percent: float):
        """Mostra warning per quota"""
        title = f"⚠️ Quota Warning: {service}"
        message = f"Usage: {usage_percent:.1f}%\nConsider upgrading or optimizing usage"
        
        self.show_toast(title, message, NotificationType.WARNING, 6000)
    
    def show_success_message(self, title: str, message: str):
        """Mostra messaggio di successo"""
        self.show_toast(title, message, NotificationType.SUCCESS, 3000)
    
    def get_notification_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Ottieni cronologia notifiche"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_notifications = []
        for notification in self.notification_history:
            notification_time = datetime.fromisoformat(notification['timestamp'])
            if notification_time >= cutoff_time:
                recent_notifications.append(notification)
        
        return recent_notifications
    
    def clear_history(self):
        """Pulisci cronologia"""
        self.notification_history = []
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Aggiorna impostazioni"""
        self.settings.update(new_settings)

class SmartMonitoringThread(QThread):
    """Thread per monitoring intelligente e notifiche automatiche"""
    
    notification_triggered = pyqtSignal(str, str, str)  # title, message, type
    
    def __init__(self, backend, notification_center):
        super().__init__()
        self.backend = backend
        self.notification_center = notification_center
        self.running = True
        self.check_interval = 30  # secondi
        
        # Thresholds per alerts
        self.viral_threshold = 10000  # views
        self.engagement_threshold = 5.0  # percentage
        self.quota_warning_threshold = 80.0  # percentage
        
        # Stato precedente per rilevare cambiamenti
        self.previous_state = {}
    
    def run(self):
        """Loop principale di monitoring"""
        while self.running:
            try:
                self.check_video_performance()
                self.check_automation_status()
                self.check_quota_usage()
                self.check_system_health()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def check_video_performance(self):
        """Controlla performance video per rilevare virali"""
        try:
            # Simula controllo performance (da sostituire con logica reale)
            import random
            
            # Simula video che diventa virale
            if random.random() < 0.05:  # 5% chance
                video_data = {
                    'title': 'Amazing AI Generated Content',
                    'views': random.randint(15000, 50000),
                    'engagement_rate': random.uniform(6.0, 12.0)
                }
                
                if video_data['views'] > self.viral_threshold:
                    self.notification_center.show_viral_alert(
                        video_data['title'], 
                        video_data
                    )
                    
        except Exception as e:
            print(f"Performance check error: {e}")
    
    def check_automation_status(self):
        """Controlla status automazione"""
        try:
            if not self.backend:
                return
                
            status = self.backend.get_automation_status()
            
            # Controlla se scheduler si è fermato
            scheduler_running = status.get('scheduler', {}).get('running', False)
            prev_scheduler = self.previous_state.get('scheduler_running', True)
            
            if prev_scheduler and not scheduler_running:
                self.notification_center.show_automation_alert(
                    "Scheduler", "Stopped", "Daily automation pipeline stopped"
                )
            elif not prev_scheduler and scheduler_running:
                self.notification_center.show_automation_alert(
                    "Scheduler", "Started", "Daily automation pipeline resumed"
                )
            
            self.previous_state['scheduler_running'] = scheduler_running
            
        except Exception as e:
            print(f"Automation status check error: {e}")
    
    def check_quota_usage(self):
        """Controlla usage quota servizi"""
        try:
            # Simula controllo quota (da sostituire con logica reale)
            import random
            
            services = ['OpenAI', 'YouTube API', 'Storage']
            
            for service in services:
                usage = random.uniform(70, 95)
                prev_usage = self.previous_state.get(f'{service}_usage', 0)
                
                # Alert se supera threshold
                if usage > self.quota_warning_threshold and prev_usage <= self.quota_warning_threshold:
                    self.notification_center.show_quota_warning(service, usage)
                
                self.previous_state[f'{service}_usage'] = usage
                
        except Exception as e:
            print(f"Quota check error: {e}")
    
    def check_system_health(self):
        """Controlla salute generale del sistema"""
        try:
            # Controlla spazio disco, memoria, etc.
            import shutil
            
            # Controlla spazio disco
            disk_usage = shutil.disk_usage('.')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            if free_percent < 10:  # Meno del 10% libero
                self.notification_center.show_error_alert(
                    "Low Disk Space", 
                    f"Only {free_percent:.1f}% disk space remaining"
                )
                
        except Exception as e:
            print(f"System health check error: {e}")
    
    def stop(self):
        """Ferma il monitoring"""
        self.running = False

# Singleton notification center
notification_center = NotificationCenter()

def show_notification(title: str, message: str, notification_type: str = NotificationType.INFO, duration: int = 5000):
    """Funzione helper per mostrare notifiche"""
    notification_center.show_toast(title, message, notification_type, duration)

def show_viral_alert(video_title: str, metrics: Dict[str, Any]):
    """Helper per alert virali"""
    notification_center.show_viral_alert(video_title, metrics)

def show_automation_alert(event: str, status: str, details: str = ""):
    """Helper per alert automazione"""
    notification_center.show_automation_alert(event, status, details)

def show_error(error_type: str, error_message: str):
    """Helper per errori"""
    notification_center.show_error_alert(error_type, error_message)

def show_success(title: str, message: str):
    """Helper per successi"""
    notification_center.show_success_message(title, message)

# Test del sistema di notifiche
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test notifiche
    show_notification("Welcome", "ViralShortsAI Smart Notifications Ready!", NotificationType.SUCCESS)
    
    QTimer.singleShot(2000, lambda: show_viral_alert("Test Video", {'views': 25000, 'engagement_rate': 8.5}))
    QTimer.singleShot(4000, lambda: show_automation_alert("Cleanup", "Success", "Removed 15 temp files"))
    QTimer.singleShot(6000, lambda: show_error("OpenAI API", "Quota exceeded"))
    
    sys.exit(app.exec_())
