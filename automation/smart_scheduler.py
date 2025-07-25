"""
⚡ ViralShortsAI - Smart Scheduler Integration
Replaces the basic scheduler with AI-powered automation
"""

import os
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from utils import app_logger
from automation.task_executor import TaskExecutor

class SmartSchedulerManager:
    """
    🧠 Smart Scheduler that replaces your current ViralShortsWorker
    
    This integrates seamlessly with your existing GUI and backend
    while providing advanced automation capabilities.
    """
    
    def __init__(self, config: Dict, backend_instance):
        self.config = config
        self.backend = backend_instance
        self.logger = app_logger
        
        # Initialize components (like your existing worker)
        self.db = None
        self.finder = None
        self.transcriber = None
        self.captioner = None
        self.editor = None
        self.uploader = None
        self.analyzer = None
        
        # Smart automation components
        self.task_executor = None
        self.automation_thread = None
        self.running = False
        
        # Performance tracking
        self.automation_stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'average_videos_per_run': 0,
            'average_viral_score': 0,
            'last_run_time': None,
            'next_scheduled_run': None
        }
        
        self.logger.info("🧠 Smart Scheduler Manager initialized")
    
    def initialize_components(self):
        """
        Initialize all components (enhanced version of your existing method)
        """
        try:
            self.logger.info("🔧 Initializing Smart Automation Components...")
            
            # Import and initialize (like your existing code)
            from database import Database
            from data.downloader import YouTubeShortsFinder
            from ai.whisper_transcriber import WhisperTranscriber
            from ai.gpt_captioner import GPTCaptioner
            from processing.editor import VideoEditor
            from upload.youtube_uploader import YouTubeUploader
            from monitoring.analyzer import PerformanceAnalyzer
            
            # Initialize database
            db_path = self.config['paths']['database']
            self.db = Database(db_path)
            self.logger.info("✅ Database initialized")
            
            # Initialize components
            self.finder = YouTubeShortsFinder(self.config, self.db)
            self.logger.info("✅ YouTube Shorts Finder initialized")
            
            self.transcriber = WhisperTranscriber(self.config)
            self.logger.info("✅ Whisper Transcriber initialized")
            
            self.captioner = GPTCaptioner(self.config)
            self.logger.info("✅ GPT Captioner initialized")
            
            self.editor = VideoEditor(self.config, self.db)
            self.logger.info("✅ Video Editor initialized")
            
            self.uploader = YouTubeUploader(self.config)
            self.logger.info("✅ YouTube Uploader initialized")
            
            self.analyzer = PerformanceAnalyzer(self.config, self.db)
            self.logger.info("✅ Performance Analyzer initialized")
            
            # Initialize smart task executor
            components = {
                'finder': self.finder,
                'transcriber': self.transcriber,
                'captioner': self.captioner,
                'editor': self.editor,
                'uploader': self.uploader,
                'analyzer': self.analyzer
            }
            
            self.task_executor = TaskExecutor(self.config, self.db, components)
            self.logger.info("✅ Smart Task Executor initialized")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize components: {e}")
            return False
    
    def start_smart_automation(self, test_mode: bool = False, test_url: str = None):
        """
        🚀 Start the smart automation pipeline
        
        This replaces your existing run() method with intelligent automation
        """
        if self.running:
            self.logger.warning("Smart automation is already running")
            return
        
        self.running = True
        
        # Initialize components if not already done
        if not self.task_executor:
            if not self.initialize_components():
                self.running = False
                return
        
        # Start automation in separate thread
        self.automation_thread = threading.Thread(
            target=self._run_automation_loop,
            args=(test_mode, test_url),
            daemon=True
        )
        self.automation_thread.start()
        
        self.logger.info("🚀 Smart Automation started")
    
    def _run_automation_loop(self, test_mode: bool = False, test_url: str = None):
        """
        Main automation loop (runs in separate thread)
        """
        try:
            # Set up asyncio event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if test_mode and test_url:
                # Run test mode (single video processing)
                loop.run_until_complete(self._run_test_mode(test_url))
            else:
                # Run full automation pipeline
                loop.run_until_complete(self._run_smart_pipeline())
                
        except Exception as e:
            self.logger.error(f"Error in automation loop: {e}")
            self.automation_stats['failed_runs'] += 1
        finally:
            self.running = False
    
    async def _run_test_mode(self, test_url: str):
        """
        🧪 Run test mode for single video
        
        Enhanced version of your existing test mode
        """
        self.logger.info(f"🧪 Running Smart Test Mode for: {test_url}")
        
        try:
            # Create test task
            test_task = {
                'id': f"test_{int(datetime.now().timestamp())}",
                'type': 'test_video_processing',
                'priority': 5,  # Highest priority
                'params': {
                    'url': test_url,
                    'test_mode': True
                },
                'estimated_duration': 300,
                'dependencies': []
            }
            
            # Execute test task
            result = await self.task_executor._execute_test_video_processing(test_task)
            
            self.logger.info(f"✅ Test mode completed: {result}")
            
            # Update GUI if available
            if hasattr(self.backend, 'signals'):
                self.backend.signals.status.emit("Test completato")
                self.backend.signals.log.emit("info", f"Test completato per {test_url}")
            
        except Exception as e:
            self.logger.error(f"❌ Test mode failed: {e}")
            if hasattr(self.backend, 'signals'):
                self.backend.signals.error.emit(f"Test fallito: {e}")
    
    async def _run_smart_pipeline(self):
        """
        🧠 Run the main smart automation pipeline
        
        This is the heart of the smart automation system
        """
        self.logger.info("🧠 Starting Smart Automation Pipeline")
        
        try:
            # Update stats
            self.automation_stats['total_runs'] += 1
            self.automation_stats['last_run_time'] = datetime.now().isoformat()
            
            # Notify GUI
            if hasattr(self.backend, 'signals'):
                self.backend.signals.status.emit("Smart Automation in corso...")
                self.backend.signals.log.emit("info", "🚀 Avvio Smart Automation Pipeline")
            
            # 1. Create smart content pipeline
            max_videos = self.config['app_settings']['max_videos_per_day']
            pipeline_tasks = self.task_executor.create_smart_content_pipeline(max_videos)
            
            # 2. Execute pipeline with intelligent scheduling
            await self.task_executor.execute_smart_pipeline()
            
            # 3. Monitor execution and collect results
            await self._monitor_pipeline_execution()
            
            # 4. Generate final report and update learning
            await self._finalize_automation_run()
            
            self.automation_stats['successful_runs'] += 1
            
            # Notify completion
            if hasattr(self.backend, 'signals'):
                self.backend.signals.status.emit("Smart Automation completata")
                self.backend.signals.log.emit("info", "✅ Smart Automation Pipeline completata con successo")
                self.backend.signals.finished.emit()
            
        except Exception as e:
            self.logger.error(f"❌ Smart automation pipeline failed: {e}")
            self.automation_stats['failed_runs'] += 1
            
            if hasattr(self.backend, 'signals'):
                self.backend.signals.error.emit(f"Smart Automation fallita: {e}")
    
    async def _monitor_pipeline_execution(self):
        """Monitor the execution of the smart pipeline"""
        self.logger.info("📊 Monitoring pipeline execution...")
        
        monitoring_duration = 30  # minutes
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < monitoring_duration * 60:
            # Get current status
            status = self.task_executor.get_automation_status()
            
            # Log progress
            self.logger.info(
                f"Pipeline Status - Running: {status['running_tasks']}, "
                f"Completed: {status['completed_tasks']}, "
                f"Failed: {status['failed_tasks']}"
            )
            
            # Update GUI if available
            if hasattr(self.backend, 'signals'):
                progress_msg = (
                    f"Esecuzione task: {status['running_tasks']} attivi, "
                    f"{status['completed_tasks']} completati"
                )
                self.backend.signals.log.emit("info", progress_msg)
            
            # Check if all tasks are completed
            total_queued = sum(status['queue_sizes'].values())
            if status['running_tasks'] == 0 and total_queued == 0:
                self.logger.info("✅ All pipeline tasks completed")
                break
            
            # Wait before next check
            await asyncio.sleep(60)  # Check every minute
    
    async def _finalize_automation_run(self):
        """Finalize the automation run with reports and learning"""
        self.logger.info("📈 Finalizing automation run...")
        
        try:
            # Get final status
            final_status = self.task_executor.get_automation_status()
            
            # Update automation stats
            performance_stats = final_status['performance_stats']
            self.automation_stats['average_viral_score'] = performance_stats.get('viral_success_rate', 0)
            
            # Calculate videos processed
            completed_tasks = final_status['completed_tasks']
            videos_processed = self._count_videos_processed(completed_tasks)
            
            # Update average videos per run
            total_runs = self.automation_stats['total_runs']
            current_avg = self.automation_stats['average_videos_per_run']
            new_avg = ((current_avg * (total_runs - 1)) + videos_processed) / total_runs
            self.automation_stats['average_videos_per_run'] = new_avg
            
            # Generate automation report
            automation_report = self._generate_automation_report(final_status)
            
            # Save report
            self._save_automation_report(automation_report)
            
            # Schedule next run if daily automation is enabled
            if self.config['app_settings']['run_daily']:
                next_run = self._calculate_next_run_time()
                self.automation_stats['next_scheduled_run'] = next_run.isoformat()
                self.logger.info(f"📅 Next automation run scheduled for: {next_run}")
            
        except Exception as e:
            self.logger.error(f"Error finalizing automation run: {e}")
    
    def _count_videos_processed(self, completed_tasks: int) -> int:
        """Count total videos processed in this run"""
        # This would analyze completed tasks to count videos
        # For now, return an estimate based on task completion
        return max(1, completed_tasks // 4)  # Assuming 4 tasks per video on average
    
    def _generate_automation_report(self, final_status: Dict) -> Dict[str, Any]:
        """Generate comprehensive automation report"""
        return {
            'run_timestamp': datetime.now().isoformat(),
            'automation_stats': self.automation_stats,
            'execution_summary': {
                'total_tasks': final_status['completed_tasks'] + final_status['failed_tasks'],
                'successful_tasks': final_status['completed_tasks'],
                'failed_tasks': final_status['failed_tasks'],
                'success_rate': (
                    final_status['completed_tasks'] / 
                    max(1, final_status['completed_tasks'] + final_status['failed_tasks'])
                ) * 100
            },
            'performance_metrics': final_status['performance_stats'],
            'resource_utilization': final_status['resource_usage'],
            'recommendations': self._generate_optimization_recommendations(final_status)
        }
    
    def _generate_optimization_recommendations(self, status: Dict) -> List[str]:
        """Generate optimization recommendations based on run results"""
        recommendations = []
        
        performance = status['performance_stats']
        
        # Performance-based recommendations
        if performance.get('viral_success_rate', 0) < 60:
            recommendations.append(
                "Consider adjusting content selection criteria to improve viral potential"
            )
        
        if performance.get('success_rate', 0) < 90:
            recommendations.append(
                "Review failed tasks to identify and resolve common issues"
            )
        
        # Resource utilization recommendations
        if status['resource_usage'].get('cpu_usage', 0) > 80:
            recommendations.append(
                "Consider reducing concurrent tasks to optimize CPU usage"
            )
        
        # Queue management recommendations
        queue_sizes = status['queue_sizes']
        total_queued = sum(queue_sizes.values())
        if total_queued > 20:
            recommendations.append(
                "High task queue detected - consider increasing processing capacity"
            )
        
        return recommendations
    
    def _save_automation_report(self, report: Dict):
        """Save automation report to file"""
        try:
            reports_dir = Path(self.config['paths']['reports'])
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"smart_automation_report_{timestamp}.json"
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"📄 Automation report saved: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save automation report: {e}")
    
    def _calculate_next_run_time(self) -> datetime:
        """Calculate next automation run time"""
        now = datetime.now()
        
        # Get configured run time
        daily_run_time = self.config['app_settings']['daily_run_time']
        hour, minute = map(int, daily_run_time.split(':'))
        
        # Calculate next run (tomorrow at the same time)
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the time has already passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def stop_automation(self):
        """Stop the smart automation"""
        self.logger.info("🛑 Stopping Smart Automation...")
        self.running = False
        
        if self.automation_thread and self.automation_thread.is_alive():
            # Give thread time to finish gracefully
            self.automation_thread.join(timeout=30)
        
        self.logger.info("✅ Smart Automation stopped")
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status for GUI"""
        status = {
            'running': self.running,
            'stats': self.automation_stats,
            'components_initialized': self.task_executor is not None
        }
        
        if self.task_executor:
            executor_status = self.task_executor.get_automation_status()
            status.update(executor_status)
        
        return status
    
    def force_emergency_content_generation(self):
        """Force emergency content generation"""
        if not self.task_executor:
            self.logger.error("Task executor not initialized")
            return
        
        emergency_task = {
            'id': f"emergency_{int(datetime.now().timestamp())}",
            'type': 'emergency_content_generation',
            'priority': 5,  # Highest priority
            'params': {'reason': 'manual_trigger'},
            'estimated_duration': 600,
            'dependencies': []
        }
        
        self.task_executor.add_task_to_queue(emergency_task)
        self.logger.info("🚨 Emergency content generation triggered")
    
    def optimize_existing_content(self):
        """Trigger optimization of existing content"""
        if not self.task_executor:
            self.logger.error("Task executor not initialized")
            return
        
        optimization_task = {
            'id': f"optimization_{int(datetime.now().timestamp())}",
            'type': 'viral_optimization',
            'priority': 3,
            'params': {'target': 'low_performing_content'},
            'estimated_duration': 300,
            'dependencies': []
        }
        
        self.task_executor.add_task_to_queue(optimization_task)
        self.logger.info("🔥 Content optimization triggered")

# Integration helper functions for your existing code

def integrate_smart_scheduler_with_backend(backend_instance):
    """
    🔌 Integration function to replace existing worker with smart scheduler
    
    Call this from your ViralShortsBackend.__init__ method
    """
    # Replace the basic worker with smart scheduler
    backend_instance.smart_scheduler = SmartSchedulerManager(
        backend_instance.config, 
        backend_instance
    )
    
    # Override start_process method to use smart automation
    def smart_start_process():
        """Enhanced start_process using smart automation"""
        if backend_instance.smart_scheduler.running:
            app_logger.warning("Smart automation already running")
            return
        
        backend_instance.smart_scheduler.start_smart_automation()
    
    # Override stop_process method
    def smart_stop_process():
        """Enhanced stop_process using smart automation"""
        backend_instance.smart_scheduler.stop_automation()
    
    # Replace methods
    backend_instance.start_process = smart_start_process
    backend_instance.stop_process = smart_stop_process
    
    app_logger.info("🔌 Smart Scheduler integrated with backend")

def add_smart_automation_gui_controls(gui_instance):
    """
    🖥️ Add smart automation controls to GUI
    
    Call this from your ViralShortsApp.__init__ method
    """
    from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QGroupBox, QLabel
    
    # Create smart automation control group
    smart_group = QGroupBox("🧠 Smart Automation")
    smart_layout = QVBoxLayout()
    
    # Emergency content generation button
    emergency_btn = QPushButton("🚨 Emergency Content Generation")
    emergency_btn.clicked.connect(lambda: gui_instance.backend.smart_scheduler.force_emergency_content_generation())
    smart_layout.addWidget(emergency_btn)
    
    # Content optimization button
    optimize_btn = QPushButton("🔥 Optimize Existing Content")
    optimize_btn.clicked.connect(lambda: gui_instance.backend.smart_scheduler.optimize_existing_content())
    smart_layout.addWidget(optimize_btn)
    
    # Automation status label
    status_label = QLabel("Status: Ready")
    smart_layout.addWidget(status_label)
    
    smart_group.setLayout(smart_layout)
    
    # Add to debug tab (or create new tab)
    debug_tab = gui_instance.findChild(QWidget, "debug_tab")
    if debug_tab and hasattr(debug_tab, 'layout'):
        debug_tab.layout().addWidget(smart_group)
    
    app_logger.info("🖥️ Smart Automation GUI controls added")
