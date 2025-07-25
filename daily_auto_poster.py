"""
🤖 Daily Auto Poster per ViralShortsAI
Sistema di posting automatico giornaliero con AI scheduling
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import os
import sqlite3
from dataclasses import dataclass
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_poster.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PostingConfig:
    """Configurazione per il posting automatico"""
    enabled: bool = True
    daily_target: int = 1  # Minimo 1 video al giorno
    optimal_times: List[str] = None  # ["09:00", "15:00", "20:00"]
    weekday_multiplier: float = 1.0
    weekend_multiplier: float = 1.2
    min_interval_hours: int = 6  # Minimo tra un post e l'altro
    max_posts_per_day: int = 3
    backup_content_days: int = 7  # Giorni di backup content
    
    def __post_init__(self):
        if self.optimal_times is None:
            self.optimal_times = ["09:00", "15:00", "20:00"]

class DailyAutoPoster:
    """Sistema di posting automatico intelligente"""
    
    def __init__(self, backend=None, config_file="daily_poster_config.json"):
        self.backend = backend
        self.config_file = config_file
        self.config = self.load_config()
        self.is_running = False
        self.scheduler_thread = None
        self.db_path = "data/viral_shorts.db"
        
        # Statistiche
        self.stats = {
            'posts_today': 0,
            'posts_this_week': 0,
            'posts_this_month': 0,
            'last_post_time': None,
            'consecutive_days': 0,
            'success_rate': 100.0
        }
        
        self.load_stats()
        logger.info("🤖 Daily Auto Poster inizializzato")
    
    def load_config(self) -> PostingConfig:
        """Carica configurazione da file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return PostingConfig(**data)
            else:
                # Configurazione di default
                config = PostingConfig()
                self.save_config(config)
                return config
        except Exception as e:
            logger.error(f"Errore caricamento config: {e}")
            return PostingConfig()
    
    def save_config(self, config: PostingConfig = None):
        """Salva configurazione su file"""
        try:
            config = config or self.config
            with open(self.config_file, 'w') as f:
                json.dump(config.__dict__, f, indent=2)
            logger.info("✅ Configurazione salvata")
        except Exception as e:
            logger.error(f"Errore salvataggio config: {e}")
    
    def load_stats(self):
        """Carica statistiche dal database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crea tabella statistiche se non esiste
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_poster_stats (
                    date TEXT PRIMARY KEY,
                    posts_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    last_post_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Carica stats di oggi
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT posts_count, success_count, last_post_time 
                FROM daily_poster_stats 
                WHERE date = ?
            """, (today,))
            
            result = cursor.fetchone()
            if result:
                self.stats['posts_today'] = result[0]
                self.stats['last_post_time'] = result[2]
            
            # Calcola streak consecutivi
            self.calculate_consecutive_days(cursor)
            
            conn.close()
            logger.info(f"📊 Stats caricate: {self.stats['posts_today']} post oggi")
            
        except Exception as e:
            logger.error(f"Errore caricamento stats: {e}")
    
    def calculate_consecutive_days(self, cursor):
        """Calcola giorni consecutivi di posting"""
        try:
            cursor.execute("""
                SELECT date, posts_count 
                FROM daily_poster_stats 
                WHERE posts_count > 0 
                ORDER BY date DESC
            """)
            
            results = cursor.fetchall()
            consecutive = 0
            current_date = datetime.now().date()
            
            for date_str, posts in results:
                post_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                expected_date = current_date - timedelta(days=consecutive)
                
                if post_date == expected_date and posts > 0:
                    consecutive += 1
                else:
                    break
            
            self.stats['consecutive_days'] = consecutive
            
        except Exception as e:
            logger.error(f"Errore calcolo consecutive days: {e}")
    
    def update_stats(self, success: bool = True):
        """Aggiorna statistiche post"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO daily_poster_stats 
                (date, posts_count, success_count, last_post_time)
                VALUES (
                    ?, 
                    COALESCE((SELECT posts_count FROM daily_poster_stats WHERE date = ?), 0) + 1,
                    COALESCE((SELECT success_count FROM daily_poster_stats WHERE date = ?), 0) + ?,
                    ?
                )
            """, (today, today, today, 1 if success else 0, now))
            
            conn.commit()
            conn.close()
            
            # Aggiorna stats in memoria
            self.stats['posts_today'] += 1
            if success:
                self.stats['last_post_time'] = now
            
            logger.info(f"📊 Stats aggiornate: {self.stats['posts_today']} post oggi")
            
        except Exception as e:
            logger.error(f"Errore aggiornamento stats: {e}")
    
    def get_optimal_posting_time(self) -> str:
        """Calcola l'orario ottimale per il prossimo post"""
        try:
            now = datetime.now()
            today_posts = self.stats['posts_today']
            
            # Se abbiamo già raggiunto il target giornaliero
            if today_posts >= self.config.daily_target:
                # Programma per domani mattina
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(hour=9, minute=0, second=0).strftime('%H:%M')
            
            # Orari ottimali rimanenti per oggi
            remaining_times = []
            for time_str in self.config.optimal_times:
                hour, minute = map(int, time_str.split(':'))
                post_time = now.replace(hour=hour, minute=minute, second=0)
                
                # Solo se è nel futuro
                if post_time > now:
                    remaining_times.append(time_str)
            
            if remaining_times:
                return remaining_times[0]
            else:
                # Se non ci sono orari ottimali rimasti, posta tra 2-4 ore
                next_time = now + timedelta(hours=random.randint(2, 4))
                return next_time.strftime('%H:%M')
                
        except Exception as e:
            logger.error(f"Errore calcolo orario ottimale: {e}")
            return "09:00"  # Default fallback
    
    def check_content_availability(self) -> bool:
        """Controlla se c'è contenuto disponibile per il posting"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Cerca video pronti ma non ancora pubblicati
            cursor.execute("""
                SELECT COUNT(*) FROM videos 
                WHERE status = 'processed' 
                AND uploaded = 0
                AND created_at >= date('now', '-7 days')
            """)
            
            available_count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"📹 Contenuto disponibile: {available_count} video")
            return available_count > 0
            
        except Exception as e:
            logger.error(f"Errore controllo contenuto: {e}")
            return False
    
    def create_emergency_content(self) -> bool:
        """Crea contenuto di emergenza se necessario"""
        try:
            logger.info("🚨 Creando contenuto di emergenza...")
            
            # Lista di query di backup per contenuto
            emergency_queries = [
                "motivation quotes",
                "life hacks",
                "funny moments",
                "quick tips",
                "amazing facts",
                "daily wisdom",
                "success stories",
                "positive thoughts"
            ]
            
            # Scegli query random
            query = random.choice(emergency_queries)
            
            # Se abbiamo il backend, cerca e processa contenuto
            if self.backend:
                logger.info(f"🔍 Cercando contenuto: {query}")
                
                # Simula processo di creazione contenuto
                result = self.backend.search_and_process_emergency_content(query)
                
                if result:
                    logger.info("✅ Contenuto di emergenza creato con successo")
                    return True
            
            # Fallback: marca come creato per evitare loop infiniti
            logger.warning("⚠️ Contenuto di emergenza non disponibile")
            return False
            
        except Exception as e:
            logger.error(f"Errore creazione contenuto emergenza: {e}")
            return False
    
    def execute_daily_post(self) -> bool:
        """Esegue il posting giornaliero"""
        try:
            logger.info("🚀 Iniziando processo di posting giornaliero...")
            
            # 1. Controlla se abbiamo già postato abbastanza oggi
            if self.stats['posts_today'] >= self.config.daily_target:
                logger.info(f"✅ Target giornaliero già raggiunto: {self.stats['posts_today']}/{self.config.daily_target}")
                return True
            
            # 2. Controlla disponibilità contenuto
            if not self.check_content_availability():
                logger.warning("⚠️ Nessun contenuto disponibile, creando contenuto di emergenza...")
                if not self.create_emergency_content():
                    logger.error("❌ Impossibile creare contenuto di emergenza")
                    return False
                
                # Aspetta un po' per il processing
                time.sleep(30)
            
            # 3. Esegui il posting
            if self.backend:
                try:
                    logger.info("📤 Avviando processo di upload...")
                    result = self.backend.auto_upload_next_video()
                    
                    if result:
                        logger.info("🎉 Video pubblicato con successo!")
                        self.update_stats(success=True)
                        
                        # Programma il prossimo post
                        self.schedule_next_post()
                        return True
                    else:
                        logger.error("❌ Errore durante l'upload")
                        self.update_stats(success=False)
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ Errore processo upload: {e}")
                    self.update_stats(success=False)
                    return False
            else:
                logger.warning("⚠️ Backend non disponibile - simulando posting")
                self.update_stats(success=True)
                return True
                
        except Exception as e:
            logger.error(f"❌ Errore processo posting: {e}")
            return False
    
    def schedule_next_post(self):
        """Programma il prossimo post"""
        try:
            next_time = self.get_optimal_posting_time()
            logger.info(f"📅 Prossimo post programmato per: {next_time}")
            
            # Cancella job esistenti per evitare duplicati
            schedule.clear('daily_post')
            
            # Programma nuovo job
            schedule.every().day.at(next_time).do(self.execute_daily_post).tag('daily_post')
            
        except Exception as e:
            logger.error(f"Errore programmazione prossimo post: {e}")
    
    def start_daily_scheduler(self):
        """Avvia lo scheduler giornaliero"""
        try:
            if self.is_running:
                logger.warning("⚠️ Scheduler già in esecuzione")
                return
            
            logger.info("🤖 Avviando Daily Auto Poster...")
            
            # Cancella tutti i job esistenti
            schedule.clear()
            
            # Programma posting giornaliero per tutti gli orari ottimali
            for time_str in self.config.optimal_times:
                schedule.every().day.at(time_str).do(self.check_and_post).tag('daily_post')
                logger.info(f"⏰ Job programmato per: {time_str}")
            
            # Job di controllo ogni ora per sicurezza
            schedule.every().hour.do(self.hourly_check).tag('hourly_check')
            
            # Job di manutenzione giornaliero
            schedule.every().day.at("00:01").do(self.daily_maintenance).tag('maintenance')
            
            self.is_running = True
            
            # Avvia thread scheduler
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("✅ Daily Auto Poster avviato con successo!")
            
            # Esegui un controllo immediato
            self.immediate_check()
            
        except Exception as e:
            logger.error(f"❌ Errore avvio scheduler: {e}")
    
    def stop_daily_scheduler(self):
        """Ferma lo scheduler giornaliero"""
        try:
            logger.info("🛑 Fermando Daily Auto Poster...")
            
            self.is_running = False
            schedule.clear()
            
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            
            logger.info("✅ Daily Auto Poster fermato")
            
        except Exception as e:
            logger.error(f"❌ Errore stop scheduler: {e}")
    
    def _run_scheduler(self):
        """Loop principale dello scheduler"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Controlla ogni minuto
            except Exception as e:
                logger.error(f"Errore loop scheduler: {e}")
                time.sleep(60)
    
    def check_and_post(self):
        """Controlla se è necessario postare e lo fa"""
        try:
            current_hour = datetime.now().hour
            
            # Evita posting notturno (23-06)
            if current_hour >= 23 or current_hour <= 6:
                logger.info("🌙 Orario notturno - skip posting")
                return
            
            # Controlla se abbiamo già postato abbastanza oggi
            if self.stats['posts_today'] >= self.config.daily_target:
                logger.info(f"✅ Target giornaliero già raggiunto: {self.stats['posts_today']}")
                return
            
            # Controlla intervallo minimo dal last post
            if self.stats['last_post_time']:
                last_post = datetime.fromisoformat(self.stats['last_post_time'])
                hours_since = (datetime.now() - last_post).total_seconds() / 3600
                
                if hours_since < self.config.min_interval_hours:
                    logger.info(f"⏱️ Intervallo minimo non rispettato: {hours_since:.1f}h < {self.config.min_interval_hours}h")
                    return
            
            # Esegui posting
            logger.info("🎯 Condizioni soddisfatte - eseguendo posting...")
            self.execute_daily_post()
            
        except Exception as e:
            logger.error(f"Errore check_and_post: {e}")
    
    def hourly_check(self):
        """Controllo orario per garantire almeno 1 post al giorno"""
        try:
            now = datetime.now()
            
            # Se è sera (dopo le 18) e non abbiamo ancora postato oggi
            if now.hour >= 18 and self.stats['posts_today'] == 0:
                logger.warning("🚨 ALERT: Nessun post oggi e si sta facendo sera!")
                
                # Forza un posting di emergenza
                logger.info("⚡ Forzando posting di emergenza...")
                self.execute_daily_post()
            
            # Log status ogni 6 ore
            if now.hour % 6 == 0 and now.minute == 0:
                self.log_daily_status()
                
        except Exception as e:
            logger.error(f"Errore hourly_check: {e}")
    
    def daily_maintenance(self):
        """Manutenzione giornaliera"""
        try:
            logger.info("🔧 Eseguendo manutenzione giornaliera...")
            
            # Reset contatori giornalieri
            self.stats['posts_today'] = 0
            
            # Ricarica stats dal database
            self.load_stats()
            
            # Log report giornaliero
            self.generate_daily_report()
            
            logger.info("✅ Manutenzione giornaliera completata")
            
        except Exception as e:
            logger.error(f"Errore manutenzione giornaliera: {e}")
    
    def immediate_check(self):
        """Controllo immediato per vedere se dobbiamo postare subito"""
        try:
            now = datetime.now()
            
            # Se non abbiamo ancora postato oggi e siamo in orario buono
            if (self.stats['posts_today'] == 0 and 
                7 <= now.hour <= 22):
                
                logger.info("🚀 Primo avvio oggi - eseguendo controllo immediato...")
                
                # Aspetta un po' per non essere troppo aggressivi
                time.sleep(5)
                self.check_and_post()
                
        except Exception as e:
            logger.error(f"Errore controllo immediato: {e}")
    
    def log_daily_status(self):
        """Log dello status giornaliero"""
        try:
            logger.info(f"""
📊 === DAILY AUTO POSTER STATUS ===
📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}
📈 Post oggi: {self.stats['posts_today']}/{self.config.daily_target}
🔥 Giorni consecutivi: {self.stats['consecutive_days']}
⏰ Ultimo post: {self.stats['last_post_time'] or 'N/A'}
✅ Scheduler attivo: {self.is_running}
🎯 Prossimi orari: {self.config.optimal_times}
=================================""")
        except Exception as e:
            logger.error(f"Errore log status: {e}")
    
    def generate_daily_report(self):
        """Genera report giornaliero dettagliato"""
        try:
            report = f"""
🎯 === DAILY POSTING REPORT ===
Data: {datetime.now().strftime('%Y-%m-%d')}

📊 STATISTICHE:
• Post pubblicati oggi: {self.stats['posts_today']}
• Target giornaliero: {self.config.daily_target}
• Streak consecutivi: {self.stats['consecutive_days']} giorni
• Success rate: {self.stats['success_rate']:.1f}%

⚙️ CONFIGURAZIONE:
• Orari ottimali: {', '.join(self.config.optimal_times)}
• Intervallo minimo: {self.config.min_interval_hours}h
• Max post/giorno: {self.config.max_posts_per_day}

✅ Status: {'TARGET RAGGIUNTO' if self.stats['posts_today'] >= self.config.daily_target else 'IN CORSO'}
==============================="""
            
            logger.info(report)
            
            # Salva report su file
            with open(f"logs/daily_report_{datetime.now().strftime('%Y-%m-%d')}.txt", 'w') as f:
                f.write(report)
                
        except Exception as e:
            logger.error(f"Errore generazione report: {e}")
    
    def get_status_dict(self) -> Dict:
        """Restituisce status come dizionario per GUI"""
        return {
            'is_running': self.is_running,
            'posts_today': self.stats['posts_today'],
            'daily_target': self.config.daily_target,
            'consecutive_days': self.stats['consecutive_days'],
            'last_post_time': self.stats['last_post_time'],
            'next_scheduled_times': self.config.optimal_times,
            'success_rate': self.stats['success_rate']
        }

# Funzioni di utilità per integrazione
def start_daily_poster(backend=None) -> DailyAutoPoster:
    """Avvia il daily auto poster"""
    poster = DailyAutoPoster(backend=backend)
    poster.start_daily_scheduler()
    return poster

def stop_daily_poster(poster: DailyAutoPoster):
    """Ferma il daily auto poster"""
    if poster:
        poster.stop_daily_scheduler()

if __name__ == "__main__":
    # Test standalone
    print("🤖 Testing Daily Auto Poster...")
    
    poster = DailyAutoPoster()
    poster.log_daily_status()
    
    print("✅ Test completato!")
