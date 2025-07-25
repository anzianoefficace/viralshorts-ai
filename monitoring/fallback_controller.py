"""
🤖 OpenAI Fallback Controller per ViralShortsAI
Sistema di controllo automatico del fallback con monitoraggio quota e notifiche
"""

import os
import json
import logging
import datetime
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import openai
from openai_fallback import OpenAIFallbackEngine

class OpenAIFallbackController:
    """
    Controller per gestione automatica del fallback OpenAI
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.logger = logging.getLogger('ViralShortsAI.FallbackController')
        self.fallback_engine = OpenAIFallbackEngine()
        
        # Status interno
        self.fallback_active = False
        self.last_check = None
        self.consecutive_failures = 0
        self.quota_exhausted = False
        
        # Configurazione
        self.config = self._load_config()
        
        # Configurazione fallback
        self.auto_fallback_enabled = self.config.get('fallback_controller', {}).get('auto_fallback_enabled', True)
        self.check_interval = self.config.get('fallback_controller', {}).get('check_interval_minutes', 15)
        self.max_failures = self.config.get('fallback_controller', {}).get('max_consecutive_failures', 3)
        self.quota_reset_check = self.config.get('fallback_controller', {}).get('quota_reset_check_hours', 24)
        self.enable_notifications = self.config.get('fallback_controller', {}).get('enable_notifications', True)
        self.fallback_threshold = self.config.get('fallback_controller', {}).get('fallback_threshold_429_errors', 2)
        
        # Backup della chiave originale
        self.original_api_key = os.environ.get('OPENAI_API_KEY', '')
        
        # Setup logging
        self._setup_fallback_logging()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive fallback status"""
        return {
            'auto_fallback_enabled': self.auto_fallback_enabled,
            'quota_exhausted': self.quota_exhausted,
            'fallback_active': getattr(self, 'fallback_active', False),
            'consecutive_failures': getattr(self, 'consecutive_failures', 0),
            'last_check': getattr(self, 'last_check', None),
            'original_api_key_available': bool(self.original_api_key)
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Carica configurazione fallback"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Setup default fallback config
            if 'fallback_controller' not in config:
                config['fallback_controller'] = {
                    "auto_fallback_enabled": True,
                    "check_interval_minutes": 15,
                    "max_consecutive_failures": 3,
                    "quota_reset_check_hours": 24,
                    "enable_notifications": True,
                    "fallback_threshold_429_errors": 2
                }
                self._save_config(config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading fallback config: {e}")
            return self._get_default_fallback_config()
    
    def _save_config(self, config: Dict[str, Any]):
        """Salva configurazione"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def _get_default_fallback_config(self) -> Dict[str, Any]:
        """Configurazione fallback default"""
        return {
            "fallback_controller": {
                "auto_fallback_enabled": True,
                "check_interval_minutes": 15,
                "max_consecutive_failures": 3,
                "quota_reset_check_hours": 24,
                "enable_notifications": True,
                "fallback_threshold_429_errors": 2
            }
        }
    
    def _setup_fallback_logging(self):
        """Setup logging specifico per fallback"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # File di log specifico per fallback
            fallback_log = log_dir / f"fallback_{datetime.datetime.now().strftime('%Y%m%d')}.log"
            
            # Handler per file fallback
            fallback_handler = logging.FileHandler(fallback_log)
            fallback_handler.setLevel(logging.INFO)
            fallback_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fallback_handler.setFormatter(fallback_formatter)
            
            self.logger.addHandler(fallback_handler)
            
        except Exception as e:
            self.logger.error(f"Error setting up fallback logging: {e}")
    
    def check_openai_quota(self) -> Dict[str, Any]:
        """
        Controlla lo stato della quota OpenAI
        """
        try:
            # Test con chiamata minimale
            client = openai.OpenAI(api_key=self.original_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            
            # Se arriviamo qui, l'API funziona
            self.consecutive_failures = 0
            self.quota_exhausted = False
            
            status = {
                "api_available": True,
                "quota_ok": True,
                "error": None,
                "checked_at": datetime.datetime.now().isoformat()
            }
            
            self.logger.info("✅ OpenAI API quota check successful")
            return status
            
        except openai.RateLimitError as e:
            # Quota exceeded
            self.consecutive_failures += 1
            self.quota_exhausted = True
            
            status = {
                "api_available": False,
                "quota_ok": False,
                "error": "quota_exceeded",
                "error_details": str(e),
                "checked_at": datetime.datetime.now().isoformat()
            }
            
            self.logger.warning(f"⚠️ OpenAI quota exceeded: {e}")
            return status
            
        except Exception as e:
            # Altri errori API
            self.consecutive_failures += 1
            
            status = {
                "api_available": False,
                "quota_ok": False,
                "error": "api_error",
                "error_details": str(e),
                "checked_at": datetime.datetime.now().isoformat()
            }
            
            self.logger.error(f"❌ OpenAI API error: {e}")
            return status
    
    def activate_fallback(self, reason: str = "automatic") -> bool:
        """
        Attiva il sistema di fallback
        """
        try:
            if self.fallback_active:
                self.logger.info("🔄 Fallback already active")
                return True
            
            # Salva chiave originale se non già fatto
            if self.original_api_key and not os.environ.get('OPENAI_API_KEY_BACKUP'):
                os.environ['OPENAI_API_KEY_BACKUP'] = self.original_api_key
            
            # Disabilita chiave API
            os.environ['OPENAI_API_KEY'] = ''
            
            # Attiva flag fallback
            self.fallback_active = True
            
            # Log evento
            self.logger.warning(f"🚨 Fallback OpenAI ATTIVATO - Ragione: {reason}")
            
            # Notifica GUI se possibile
            self._send_fallback_notification("activated", reason)
            
            # Salva stato in config
            self._save_fallback_state(True, reason)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error activating fallback: {e}")
            return False
    
    def deactivate_fallback(self, reason: str = "manual") -> bool:
        """
        Disattiva il sistema di fallback
        """
        try:
            if not self.fallback_active:
                self.logger.info("✅ Fallback already inactive")
                return True
            
            # Ripristina chiave API originale
            backup_key = os.environ.get('OPENAI_API_KEY_BACKUP')
            if backup_key:
                os.environ['OPENAI_API_KEY'] = backup_key
                del os.environ['OPENAI_API_KEY_BACKUP']
            
            # Disattiva flag fallback
            self.fallback_active = False
            self.consecutive_failures = 0
            self.quota_exhausted = False
            
            # Log evento
            self.logger.info(f"✅ Fallback OpenAI DISATTIVATO - Ragione: {reason}")
            
            # Notifica GUI
            self._send_fallback_notification("deactivated", reason)
            
            # Salva stato in config
            self._save_fallback_state(False, reason)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deactivating fallback: {e}")
            return False
    
    def auto_manage_fallback(self) -> Dict[str, Any]:
        """
        Gestione automatica del fallback basata su controlli
        """
        try:
            if not self.config.get('fallback_controller', {}).get('auto_fallback_enabled', True):
                return {"status": "auto_management_disabled"}
            
            # Controlla quota
            quota_status = self.check_openai_quota()
            self.last_check = datetime.datetime.now()
            
            # Logica di attivazione/disattivazione
            max_failures = self.config.get('fallback_controller', {}).get('max_consecutive_failures', 3)
            
            # Se quota OK e fallback attivo, prova a disattivare
            if quota_status['quota_ok'] and self.fallback_active:
                self.deactivate_fallback("quota_restored")
                return {
                    "action": "fallback_deactivated",
                    "reason": "quota_restored",
                    "quota_status": quota_status
                }
            
            # Se quota NOK e fallback non attivo, attiva
            elif not quota_status['quota_ok'] and not self.fallback_active:
                if self.consecutive_failures >= max_failures:
                    self.activate_fallback("quota_exhausted")
                    return {
                        "action": "fallback_activated",
                        "reason": "quota_exhausted",
                        "quota_status": quota_status
                    }
            
            return {
                "action": "no_change",
                "fallback_active": self.fallback_active,
                "consecutive_failures": self.consecutive_failures,
                "quota_status": quota_status
            }
            
        except Exception as e:
            self.logger.error(f"Error in auto fallback management: {e}")
            return {"error": str(e)}
    
    def _send_fallback_notification(self, action: str, reason: str):
        """Invia notifica GUI del cambio stato fallback"""
        try:
            if not self.config.get('fallback_controller', {}).get('enable_notifications', True):
                return
            
            # Crea file di notifica per GUI
            notifications_dir = Path("data/notifications")
            notifications_dir.mkdir(exist_ok=True)
            
            notification = {
                "type": "fallback_status",
                "action": action,
                "reason": reason,
                "timestamp": datetime.datetime.now().isoformat(),
                "message": self._get_notification_message(action, reason)
            }
            
            notification_file = notifications_dir / f"fallback_{action}_{int(time.time())}.json"
            with open(notification_file, 'w', encoding='utf-8') as f:
                json.dump(notification, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📱 Notification sent: {notification['message']}")
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
    
    def _get_notification_message(self, action: str, reason: str) -> str:
        """Genera messaggio di notifica"""
        if action == "activated":
            if reason == "quota_exhausted":
                return "⚠️ Fallback GPT attivato per esaurimento quota OpenAI"
            else:
                return f"⚠️ Fallback GPT attivato: {reason}"
        elif action == "deactivated":
            if reason == "quota_restored":
                return "✅ OpenAI API ripristinata, fallback disattivato"
            else:
                return f"✅ Fallback disattivato: {reason}"
        return f"🔄 Stato fallback cambiato: {action} - {reason}"
    
    def _save_fallback_state(self, active: bool, reason: str):
        """Salva stato corrente del fallback"""
        try:
            state_file = Path("data/fallback_state.json")
            state = {
                "fallback_active": active,
                "last_change_reason": reason,
                "last_change_time": datetime.datetime.now().isoformat(),
                "consecutive_failures": self.consecutive_failures,
                "quota_exhausted": self.quota_exhausted
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error saving fallback state: {e}")
    
    def get_fallback_status(self) -> Dict[str, Any]:
        """Ottieni status completo del fallback"""
        try:
            return {
                "fallback_active": self.fallback_active,
                "quota_exhausted": self.quota_exhausted,
                "consecutive_failures": self.consecutive_failures,
                "last_check": self.last_check.isoformat() if self.last_check else None,
                "original_api_key_available": bool(self.original_api_key),
                "config": self.config.get('fallback_controller', {}),
                "auto_management_enabled": self.config.get('fallback_controller', {}).get('auto_fallback_enabled', True)
            }
        except Exception as e:
            self.logger.error(f"Error getting fallback status: {e}")
            return {"error": str(e)}
    
    def force_quota_check(self) -> Dict[str, Any]:
        """Forza controllo quota manuale"""
        try:
            self.logger.info("🔍 Forcing quota check...")
            quota_status = self.check_openai_quota()
            
            # Gestione automatica basata su risultato
            auto_result = self.auto_manage_fallback()
            
            return {
                "quota_check": quota_status,
                "auto_management_result": auto_result,
                "current_status": self.get_fallback_status()
            }
            
        except Exception as e:
            self.logger.error(f"Error in forced quota check: {e}")
            return {"error": str(e)}

# Istanza globale del controller
fallback_controller = OpenAIFallbackController()

if __name__ == "__main__":
    # Test del controller
    logging.basicConfig(level=logging.INFO)
    
    controller = OpenAIFallbackController()
    
    print("Testing fallback controller...")
    
    # Test controllo quota
    quota_status = controller.check_openai_quota()
    print("Quota status:", quota_status)
    
    # Test gestione automatica
    auto_result = controller.auto_manage_fallback()
    print("Auto management result:", auto_result)
    
    # Test status
    status = controller.get_fallback_status()
    print("Fallback status:", status)
