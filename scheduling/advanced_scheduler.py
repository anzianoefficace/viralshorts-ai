"""
🕒 Advanced Scheduler System per ViralShortsAI
Sistema di scheduling avanzato con retry, logging e controllo configurabile
"""

import os
import json
import time
import logging
import datetime
from datetime import datetime, timedelta
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

class AdvancedScheduler:
    """
    Sistema di scheduling avanzato con funzionalità enterprise
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.logger = logging.getLogger('ViralShortsAI.Scheduler')
        self.scheduler = BackgroundScheduler()
        self.config = self._load_config()
        self.retry_counts = {}
        
        # Setup event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        
        self._setup_jobs()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carica configurazione scheduler"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Imposta valori default per scheduling se non esistono
            if 'scheduler' not in config:
                config['scheduler'] = {
                    "daily_pipeline": {
                        "enabled": True,
                        "time": "08:00",
                        "max_retries": 3,
                        "retry_interval_minutes": 30
                    },
                    "cleanup_temp": {
                        "enabled": True,
                        "interval_hours": 6,
                        "file_age_hours": 24
                    },
                    "performance_monitoring": {
                        "enabled": True,
                        "interval_hours": 6
                    },
                    "weekly_report": {
                        "enabled": True,
                        "day_of_week": "sun",
                        "time": "23:59"
                    }
                }
                self._save_config(config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Errore caricamento config scheduler: {e}")
            return self._get_default_config()
    
    def _save_config(self, config: Dict[str, Any]):
        """Salva configurazione aggiornata"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Errore salvataggio config: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configurazione default"""
        return {
            "scheduler": {
                "daily_pipeline": {
                    "enabled": True,
                    "time": "08:00",
                    "max_retries": 3,
                    "retry_interval_minutes": 30
                },
                "cleanup_temp": {
                    "enabled": True,
                    "interval_hours": 6,
                    "file_age_hours": 24
                },
                "performance_monitoring": {
                    "enabled": True,
                    "interval_hours": 6
                },
                "weekly_report": {
                    "enabled": True,
                    "day_of_week": "sun",
                    "time": "23:59"
                }
            }
        }
    
    def _setup_jobs(self):
        """Setup tutti i job schedulati"""
        scheduler_config = self.config.get('scheduler', {})
        
        # 1. Pipeline giornaliera
        if scheduler_config.get('daily_pipeline', {}).get('enabled', True):
            time_str = scheduler_config.get('daily_pipeline', {}).get('time', '08:00')
            hour, minute = map(int, time_str.split(':'))
            
            self.scheduler.add_job(
                func=self._execute_daily_pipeline,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_pipeline',
                name='Daily Pipeline Execution',
                misfire_grace_time=1800  # 30 minuti di grazia
            )
            self.logger.info(f"📅 Scheduled daily pipeline at {time_str}")
        
        # 2. Cleanup file temporanei
        if scheduler_config.get('cleanup_temp', {}).get('enabled', True):
            interval_hours = scheduler_config.get('cleanup_temp', {}).get('interval_hours', 6)
            
            self.scheduler.add_job(
                func=self._cleanup_temp_files,
                trigger=IntervalTrigger(hours=interval_hours),
                id='cleanup_temp',
                name='Temporary Files Cleanup'
            )
            self.logger.info(f"🧹 Scheduled temp cleanup every {interval_hours} hours")
        
        # 3. Monitoraggio performance
        if scheduler_config.get('performance_monitoring', {}).get('enabled', True):
            interval_hours = scheduler_config.get('performance_monitoring', {}).get('interval_hours', 6)
            
            self.scheduler.add_job(
                func=self._monitor_performance,
                trigger=IntervalTrigger(hours=interval_hours),
                id='performance_monitoring',
                name='Video Performance Monitoring'
            )
            self.logger.info(f"📈 Scheduled performance monitoring every {interval_hours} hours")
        
        # 4. Report settimanale
        if scheduler_config.get('weekly_report', {}).get('enabled', True):
            day_of_week = scheduler_config.get('weekly_report', {}).get('day_of_week', 'sun')
            time_str = scheduler_config.get('weekly_report', {}).get('time', '23:59')
            hour, minute = map(int, time_str.split(':'))
            
            self.scheduler.add_job(
                func=self._generate_weekly_report,
                trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
                id='weekly_report',
                name='Weekly Report Generation'
            )
            self.logger.info(f"📊 Scheduled weekly report on {day_of_week} at {time_str}")
    
    def _execute_daily_pipeline(self):
        """Esegue la pipeline giornaliera con retry automatico"""
        job_id = 'daily_pipeline'
        
        try:
            self.logger.info("🚀 Starting daily pipeline execution...")
            
            # Import del backend per eseguire la pipeline
            from main import ViralShortsBackend
            
            # Crea istanza backend e esegue pipeline
            backend = ViralShortsBackend()
            success = backend.start_pipeline()
            
            if success:
                self.logger.info("✅ Daily pipeline completed successfully")
                self.retry_counts[job_id] = 0  # Reset retry count
            else:
                raise Exception("Pipeline returned failure status")
                
        except Exception as e:
            self.logger.error(f"❌ Error stopping scheduler: {e}")
            return False
    
    def is_running(self):
        """Check if scheduler is running"""
        return self.scheduler.running if self.scheduler else False
    
    def get_jobs(self):
        """Get all scheduled jobs"""
        if not self.scheduler:
            return []
        return self.scheduler.get_jobs()
    
    def get_status(self):
        """Get detailed scheduler status"""
        return {
            'running': self.is_running(),
            'jobs_count': len(self.get_jobs()) if self.scheduler else 0,
            'next_run_time': self._get_next_run_time(),
            'total_executions': getattr(self, 'total_executions', 0),
            'failed_executions': getattr(self, 'failed_executions', 0)
        }
    
    def _get_next_run_time(self):
        """Get next scheduled run time"""
        if not self.scheduler:
            return None
        
        jobs = self.get_jobs()
        if not jobs:
            return None
            
        next_times = []
        for job in jobs:
            if hasattr(job, 'next_run_time') and job.next_run_time:
                next_times.append(job.next_run_time)
            elif hasattr(job, 'trigger') and hasattr(job.trigger, 'get_next_fire_time'):
                try:
                    next_time = job.trigger.get_next_fire_time(None, datetime.now())
                    if next_time:
                        next_times.append(next_time)
                except:
                    pass
                    
        return min(next_times) if next_times else None
    
    def _cleanup_temp_files(self):
        """Pulizia automatica file temporanei"""
        try:
            self.logger.info("🧹 Starting temporary files cleanup...")
            
            # Directory da pulire
            temp_dirs = [
                Path("data/temp"),
                Path("data/cache"),
                Path("logs"),
                Path(".")  # Directory root per file temp
            ]
            
            file_age_hours = self.config.get('scheduler', {}).get('cleanup_temp', {}).get('file_age_hours', 24)
            cutoff_time = datetime.now() - timedelta(hours=file_age_hours)
            
            total_cleaned = 0
            total_size = 0
            
            for temp_dir in temp_dirs:
                if not temp_dir.exists():
                    continue
                
                # Pattern di file temporanei da eliminare
                temp_patterns = [
                    "*.tmp", "*.temp", "*temp*", 
                    "temp-audio.*", "temp-video.*",
                    "*.log.1", "*.log.2"  # Log rotativi vecchi
                ]
                
                for pattern in temp_patterns:
                    for file_path in temp_dir.glob(pattern):
                        try:
                            if file_path.is_file():
                                # Controlla età del file
                                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                                
                                if file_time < cutoff_time:
                                    file_size = file_path.stat().st_size
                                    file_path.unlink()
                                    
                                    total_cleaned += 1
                                    total_size += file_size
                                    self.logger.debug(f"Deleted temp file: {file_path}")
                                    
                        except Exception as e:
                            self.logger.warning(f"Could not delete {file_path}: {e}")
            
            self.logger.info(f"✅ Cleanup completed: {total_cleaned} files, {total_size/1024/1024:.2f} MB freed")
            
        except Exception as e:
            self.logger.error(f"❌ Temp cleanup failed: {e}")
    
    def _monitor_performance(self):
        """Monitoraggio performance video caricati"""
        try:
            self.logger.info("📈 Starting performance monitoring...")
            
            from monitoring.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            results = monitor.update_video_metrics()
            
            self.logger.info(f"✅ Performance monitoring completed: {results.get('updated_videos', 0)} videos updated")
            
        except Exception as e:
            self.logger.error(f"❌ Performance monitoring failed: {e}")
    
    def _generate_weekly_report(self):
        """Genera report settimanale"""
        try:
            self.logger.info("📊 Starting weekly report generation...")
            
            from reporting.weekly_reporter import WeeklyReporter
            
            reporter = WeeklyReporter()
            report_path = reporter.generate_report()
            
            self.logger.info(f"✅ Weekly report generated: {report_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Weekly report generation failed: {e}")
    
    def _handle_job_retry(self, job_id: str, job_func: Callable, error: Exception):
        """Gestisce retry automatici per job falliti"""
        max_retries = self.config.get('scheduler', {}).get('daily_pipeline', {}).get('max_retries', 3)
        retry_interval = self.config.get('scheduler', {}).get('daily_pipeline', {}).get('retry_interval_minutes', 30)
        
        if job_id not in self.retry_counts:
            self.retry_counts[job_id] = 0
        
        self.retry_counts[job_id] += 1
        
        if self.retry_counts[job_id] <= max_retries:
            self.logger.warning(f"🔄 Scheduling retry {self.retry_counts[job_id]}/{max_retries} for {job_id} in {retry_interval} minutes")
            
            # Schedule retry
            retry_time = datetime.now() + timedelta(minutes=retry_interval)
            
            self.scheduler.add_job(
                func=job_func,
                trigger='date',
                run_date=retry_time,
                id=f'{job_id}_retry_{self.retry_counts[job_id]}',
                name=f'Retry {self.retry_counts[job_id]} for {job_id}'
            )
        else:
            self.logger.error(f"💥 Max retries exceeded for {job_id}. Manual intervention required.")
    
    def _job_executed(self, event):
        """Callback per job eseguiti con successo"""
        self.logger.debug(f"✅ Job executed successfully: {event.job_id}")
    
    def _job_error(self, event):
        """Callback per job con errori"""
        self.logger.error(f"❌ Job failed: {event.job_id}, Exception: {event.exception}")
    
    def start(self):
        """Avvia il scheduler"""
        try:
            self.scheduler.start()
            self.logger.info("🕒 Advanced Scheduler started successfully")
            
            # Log job programmati
            jobs = self.scheduler.get_jobs()
            self.logger.info(f"📋 Active jobs: {len(jobs)}")
            for job in jobs:
                self.logger.info(f"  - {job.name} (ID: {job.id}) - Next run: {job.next_run_time}")
                
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
    
    def stop(self):
        """Ferma il scheduler"""
        try:
            self.scheduler.shutdown()
            self.logger.info("🛑 Scheduler stopped")
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    def force_run_job(self, job_id: str):
        """Forza l'esecuzione immediata di un job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                self.logger.info(f"🚀 Forced execution of job: {job_id}")
                return True
            else:
                self.logger.error(f"Job not found: {job_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error forcing job execution: {e}")
            return False
    
    def get_job_status(self) -> Dict[str, Any]:
        """Restituisce status di tutti i job"""
        try:
            jobs = self.scheduler.get_jobs()
            status = {
                "scheduler_running": self.scheduler.running,
                "total_jobs": len(jobs),
                "jobs": []
            }
            
            for job in jobs:
                job_info = {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                status["jobs"].append(job_info)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting job status: {e}")
            return {"error": str(e)}

# Istanza globale scheduler
advanced_scheduler = AdvancedScheduler()

if __name__ == "__main__":
    # Test del scheduler
    logging.basicConfig(level=logging.INFO)
    
    scheduler = AdvancedScheduler()
    scheduler.start()
    
    print("Scheduler started. Press Ctrl+C to stop...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
