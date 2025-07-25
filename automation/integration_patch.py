"""
🔗 ViralShortsAI - Smart Automation Integration Patch
Seamless integration with existing system
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QGroupBox, QLabel

# Add automation module to path
automation_path = os.path.join(os.path.dirname(__file__), 'automation')
if automation_path not in sys.path:
    sys.path.append(automation_path)

from automation.smart_scheduler import SmartSchedulerManager, integrate_smart_scheduler_with_backend, add_smart_automation_gui_controls
from utils import app_logger

class SmartAutomationPatch:
    """
    🎯 Patch to seamlessly integrate Smart Automation with existing ViralShortsAI
    
    This replaces your basic automation with AI-powered smart automation
    without breaking existing functionality.
    """
    
    @staticmethod
    def patch_main_backend(backend_instance):
        """
        🔧 Patch the main backend to use smart automation
        
        Replace this in your main.py ViralShortsBackend.__init__:
        
        # OLD CODE:
        # self.worker = None
        
        # NEW CODE:
        from automation.integration_patch import SmartAutomationPatch
        SmartAutomationPatch.patch_main_backend(self)
        """
        try:
            # Initialize smart scheduler
            backend_instance.smart_scheduler = SmartSchedulerManager(
                backend_instance.config, 
                backend_instance
            )
            
            # Store original methods as fallbacks
            backend_instance._original_start_process = backend_instance.start_process
            backend_instance._original_stop_process = backend_instance.stop_process
            
            # Override with smart automation methods
            def smart_start_process():
                """Smart automation start process"""
                try:
                    app_logger.info("🚀 Starting Smart Automation Pipeline")
                    backend_instance.smart_scheduler.start_smart_automation()
                    
                except Exception as e:
                    app_logger.error(f"Smart automation failed, falling back to basic mode: {e}")
                    backend_instance._original_start_process()
            
            def smart_stop_process():
                """Smart automation stop process"""
                try:
                    backend_instance.smart_scheduler.stop_automation()
                except Exception as e:
                    app_logger.error(f"Error stopping smart automation: {e}")
                    backend_instance._original_stop_process()
            
            def smart_check_scheduled_uploads():
                """Enhanced scheduled upload checking"""
                try:
                    # Use smart scheduler's enhanced upload checking
                    if hasattr(backend_instance, 'smart_scheduler') and backend_instance.smart_scheduler.task_executor:
                        # Smart upload monitoring
                        status = backend_instance.smart_scheduler.get_automation_status()
                        app_logger.info(f"Smart automation status: {status['running']} running tasks")
                        return status.get('uploaded_videos', 0)
                    else:
                        # Fallback to original method
                        return backend_instance._original_check_scheduled_uploads()
                        
                except Exception as e:
                    app_logger.error(f"Error in smart upload checking: {e}")
                    return backend_instance._original_check_scheduled_uploads()
            
            # Store original for fallback
            backend_instance._original_check_scheduled_uploads = backend_instance.check_scheduled_uploads
            
            # Replace methods
            backend_instance.start_process = smart_start_process
            backend_instance.stop_process = smart_stop_process
            backend_instance.check_scheduled_uploads = smart_check_scheduled_uploads
            
            # Add smart automation status method
            def get_smart_automation_status():
                """Get smart automation status"""
                if hasattr(backend_instance, 'smart_scheduler'):
                    return backend_instance.smart_scheduler.get_automation_status()
                else:
                    return {'running': False, 'error': 'Smart automation not initialized'}
            
            backend_instance.get_smart_automation_status = get_smart_automation_status
            
            app_logger.info("✅ Smart Automation successfully patched into backend")
            
        except Exception as e:
            app_logger.error(f"❌ Failed to patch smart automation: {e}")
            # Keep original functionality if patching fails
    
    @staticmethod
    def patch_main_gui(gui_instance):
        """
        🖥️ Patch the main GUI to include smart automation controls
        
        Add this to your ViralShortsApp.__init__ after creating tabs:
        
        from automation.integration_patch import SmartAutomationPatch
        SmartAutomationPatch.patch_main_gui(self)
        """
        try:
            # Find the tabs widget
            tabs_widget = None
            for child in gui_instance.findChildren(QWidget):
                if hasattr(child, 'addTab'):
                    tabs_widget = child
                    break
            
            if tabs_widget:
                # Create smart automation tab
                smart_tab = SmartAutomationPatch._create_smart_automation_tab(gui_instance)
                tabs_widget.addTab(smart_tab, "🧠 Smart AI")
                
                app_logger.info("✅ Smart Automation tab added to GUI")
            
            # Enhance existing controls
            SmartAutomationPatch._enhance_existing_controls(gui_instance)
            
        except Exception as e:
            app_logger.error(f"❌ Failed to patch GUI: {e}")
    
    @staticmethod
    def _create_smart_automation_tab(gui_instance):
        """Create the smart automation tab"""
        from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                   QPushButton, QLabel, QGroupBox, 
                                   QTextEdit, QProgressBar, QCheckBox)
        
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Status Group
        status_group = QGroupBox("📊 Smart Automation Status")
        status_layout = QVBoxLayout()
        
        # Status labels
        gui_instance.smart_status_label = QLabel("🟢 Ready")
        gui_instance.smart_stats_label = QLabel("Stats: No runs yet")
        gui_instance.smart_next_run_label = QLabel("Next run: Not scheduled")
        
        status_layout.addWidget(gui_instance.smart_status_label)
        status_layout.addWidget(gui_instance.smart_stats_label)
        status_layout.addWidget(gui_instance.smart_next_run_label)
        status_group.setLayout(status_layout)
        
        # Control Group
        control_group = QGroupBox("🎮 Smart Controls")
        control_layout = QVBoxLayout()
        
        # Main controls
        controls_row1 = QHBoxLayout()
        gui_instance.smart_start_btn = QPushButton("🚀 Start Smart Automation")
        gui_instance.smart_stop_btn = QPushButton("🛑 Stop Automation")
        gui_instance.smart_stop_btn.setEnabled(False)
        
        controls_row1.addWidget(gui_instance.smart_start_btn)
        controls_row1.addWidget(gui_instance.smart_stop_btn)
        
        # Emergency controls
        controls_row2 = QHBoxLayout()
        gui_instance.emergency_content_btn = QPushButton("🚨 Emergency Content")
        gui_instance.optimize_content_btn = QPushButton("🔥 Optimize Content")
        
        controls_row2.addWidget(gui_instance.emergency_content_btn)
        controls_row2.addWidget(gui_instance.optimize_content_btn)
        
        # Settings
        gui_instance.smart_auto_mode_cb = QCheckBox("🧠 Full AI Mode")
        gui_instance.smart_auto_mode_cb.setChecked(True)
        
        control_layout.addLayout(controls_row1)
        control_layout.addLayout(controls_row2)
        control_layout.addWidget(gui_instance.smart_auto_mode_cb)
        control_group.setLayout(control_layout)
        
        # Performance Group
        performance_group = QGroupBox("📈 Performance Metrics")
        performance_layout = QVBoxLayout()
        
        gui_instance.viral_success_rate = QLabel("Viral Success Rate: --")
        gui_instance.automation_efficiency = QLabel("Automation Efficiency: --")
        gui_instance.content_pipeline_status = QLabel("Pipeline Status: --")
        
        performance_layout.addWidget(gui_instance.viral_success_rate)
        performance_layout.addWidget(gui_instance.automation_efficiency)
        performance_layout.addWidget(gui_instance.content_pipeline_status)
        performance_group.setLayout(performance_layout)
        
        # Smart Log
        log_group = QGroupBox("📝 Smart Automation Log")
        log_layout = QVBoxLayout()
        
        gui_instance.smart_log = QTextEdit()
        gui_instance.smart_log.setReadOnly(True)
        gui_instance.smart_log.setMaximumHeight(200)
        log_layout.addWidget(gui_instance.smart_log)
        log_group.setLayout(log_layout)
        
        # Add all groups to main layout
        layout.addWidget(status_group)
        layout.addWidget(control_group)
        layout.addWidget(performance_group)
        layout.addWidget(log_group)
        
        tab.setLayout(layout)
        
        # Connect signals
        SmartAutomationPatch._connect_smart_automation_signals(gui_instance)
        
        return tab
    
    @staticmethod
    def _connect_smart_automation_signals(gui_instance):
        """Connect smart automation signals"""
        try:
            # Connect buttons
            gui_instance.smart_start_btn.clicked.connect(
                lambda: SmartAutomationPatch._start_smart_automation(gui_instance)
            )
            
            gui_instance.smart_stop_btn.clicked.connect(
                lambda: SmartAutomationPatch._stop_smart_automation(gui_instance)
            )
            
            gui_instance.emergency_content_btn.clicked.connect(
                lambda: SmartAutomationPatch._trigger_emergency_content(gui_instance)
            )
            
            gui_instance.optimize_content_btn.clicked.connect(
                lambda: SmartAutomationPatch._trigger_content_optimization(gui_instance)
            )
            
            # Set up status update timer
            from PyQt5.QtCore import QTimer
            gui_instance.smart_status_timer = QTimer()
            gui_instance.smart_status_timer.timeout.connect(
                lambda: SmartAutomationPatch._update_smart_status(gui_instance)
            )
            gui_instance.smart_status_timer.start(5000)  # Update every 5 seconds
            
        except Exception as e:
            app_logger.error(f"Error connecting smart automation signals: {e}")
    
    @staticmethod
    def _start_smart_automation(gui_instance):
        """Start smart automation from GUI"""
        try:
            gui_instance.smart_start_btn.setEnabled(False)
            gui_instance.smart_stop_btn.setEnabled(True)
            gui_instance.smart_status_label.setText("🟡 Starting...")
            
            # Start smart automation
            gui_instance.backend.start_process()
            
            gui_instance.smart_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Smart Automation started")
            
        except Exception as e:
            app_logger.error(f"Error starting smart automation: {e}")
            gui_instance.smart_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")
    
    @staticmethod
    def _stop_smart_automation(gui_instance):
        """Stop smart automation from GUI"""
        try:
            gui_instance.backend.stop_process()
            
            gui_instance.smart_start_btn.setEnabled(True)
            gui_instance.smart_stop_btn.setEnabled(False)
            gui_instance.smart_status_label.setText("🟢 Ready")
            
            gui_instance.smart_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Smart Automation stopped")
            
        except Exception as e:
            app_logger.error(f"Error stopping smart automation: {e}")
    
    @staticmethod
    def _trigger_emergency_content(gui_instance):
        """Trigger emergency content generation"""
        try:
            if hasattr(gui_instance.backend, 'smart_scheduler'):
                gui_instance.backend.smart_scheduler.force_emergency_content_generation()
                gui_instance.smart_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Emergency content generation triggered")
            else:
                gui_instance.smart_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Smart scheduler not available")
                
        except Exception as e:
            app_logger.error(f"Error triggering emergency content: {e}")
    
    @staticmethod
    def _trigger_content_optimization(gui_instance):
        """Trigger content optimization"""
        try:
            if hasattr(gui_instance.backend, 'smart_scheduler'):
                gui_instance.backend.smart_scheduler.optimize_existing_content()
                gui_instance.smart_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔥 Content optimization triggered")
            else:
                gui_instance.smart_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Smart scheduler not available")
                
        except Exception as e:
            app_logger.error(f"Error triggering content optimization: {e}")
    
    @staticmethod
    def _update_smart_status(gui_instance):
        """Update smart automation status in GUI"""
        try:
            if hasattr(gui_instance.backend, 'get_smart_automation_status'):
                status = gui_instance.backend.get_smart_automation_status()
                
                # Update status label
                if status.get('running', False):
                    running_tasks = status.get('running_tasks', 0)
                    gui_instance.smart_status_label.setText(f"🟡 Running ({running_tasks} tasks)")
                else:
                    gui_instance.smart_status_label.setText("🟢 Ready")
                
                # Update stats
                stats = status.get('stats', {})
                total_runs = stats.get('total_runs', 0)
                successful_runs = stats.get('successful_runs', 0)
                avg_viral_score = stats.get('average_viral_score', 0)
                
                gui_instance.smart_stats_label.setText(
                    f"Runs: {successful_runs}/{total_runs} | Avg Viral: {avg_viral_score:.1f}"
                )
                
                # Update performance metrics
                performance = status.get('performance_stats', {})
                viral_rate = performance.get('viral_success_rate', 0)
                success_rate = performance.get('success_rate', 0)
                
                gui_instance.viral_success_rate.setText(f"Viral Success Rate: {viral_rate:.1f}%")
                gui_instance.automation_efficiency.setText(f"Automation Efficiency: {success_rate:.1f}%")
                
                # Update pipeline status
                running_tasks = status.get('running_tasks', 0)
                completed_tasks = status.get('completed_tasks', 0)
                gui_instance.content_pipeline_status.setText(
                    f"Pipeline: {running_tasks} running, {completed_tasks} completed"
                )
                
                # Update next run time
                next_run = stats.get('next_scheduled_run')
                if next_run:
                    from datetime import datetime
                    next_run_dt = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
                    gui_instance.smart_next_run_label.setText(
                        f"Next run: {next_run_dt.strftime('%Y-%m-%d %H:%M')}"
                    )
                
        except Exception as e:
            app_logger.error(f"Error updating smart status: {e}")
    
    @staticmethod
    def _enhance_existing_controls(gui_instance):
        """Enhance existing GUI controls with smart automation hints"""
        try:
            # Find and enhance the existing start button
            if hasattr(gui_instance, 'start_button'):
                original_text = gui_instance.start_button.text()
                gui_instance.start_button.setText(f"🧠 {original_text} (Smart Mode)")
            
            # Add tooltip to indicate smart mode
            if hasattr(gui_instance, 'start_button'):
                gui_instance.start_button.setToolTip(
                    "Uses AI-powered Smart Automation for optimal content creation and scheduling"
                )
            
        except Exception as e:
            app_logger.error(f"Error enhancing existing controls: {e}")

# Easy integration functions

def integrate_smart_automation(backend_instance, gui_instance=None):
    """
    🎯 One-line integration function
    
    Usage in your main.py:
    
    from automation.integration_patch import integrate_smart_automation
    
    # In ViralShortsBackend.__init__:
    integrate_smart_automation(self)
    
    # In ViralShortsApp.__init__ (after creating tabs):
    integrate_smart_automation(self.backend, self)
    """
    try:
        # Patch backend
        SmartAutomationPatch.patch_main_backend(backend_instance)
        
        # Patch GUI if provided
        if gui_instance:
            SmartAutomationPatch.patch_main_gui(gui_instance)
        
        app_logger.info("🎯 Smart Automation integration completed successfully")
        
    except Exception as e:
        app_logger.error(f"❌ Smart Automation integration failed: {e}")

def add_requirements():
    """
    📋 Add required dependencies to requirements.txt
    
    Call this function to get the list of new dependencies needed
    """
    new_requirements = [
        "redis>=4.6.0",
        "celery>=5.3.0", 
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "asyncio",
        "threading"
    ]
    
    requirements_path = "requirements.txt"
    
    try:
        # Read existing requirements
        existing = []
        if os.path.exists(requirements_path):
            with open(requirements_path, 'r') as f:
                existing = f.read().splitlines()
        
        # Add new requirements that aren't already present
        to_add = []
        for req in new_requirements:
            package_name = req.split('>=')[0].split('==')[0]
            if not any(package_name in line for line in existing):
                to_add.append(req)
        
        if to_add:
            with open(requirements_path, 'a') as f:
                f.write('\n# Smart Automation Dependencies\n')
                for req in to_add:
                    f.write(f"{req}\n")
            
            app_logger.info(f"📋 Added {len(to_add)} new requirements to requirements.txt")
            app_logger.info("Run: pip install -r requirements.txt")
        else:
            app_logger.info("📋 All required dependencies already in requirements.txt")
            
    except Exception as e:
        app_logger.error(f"Error updating requirements.txt: {e}")
        return new_requirements  # Return list for manual installation

if __name__ == "__main__":
    # Auto-add requirements when run directly
    add_requirements()
