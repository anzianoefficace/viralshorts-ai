"""
Logger module for ViralShortsAI.
Provides standardized logging functionality across the application.
"""

import os
import sys
import logging
import datetime
import platform
import traceback
import importlib
import subprocess
from logging.handlers import RotatingFileHandler

class Logger:
    """
    Custom logger class for ViralShortsAI application.
    Provides methods for logging with different severity levels and
    formats logs for both console and file output.
    """
    
    # ANSI color codes for terminal output
    COLORS = {
        'INFO': '\033[92m',  # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[91m\033[1m',  # Bold Red
        'DEBUG': '\033[94m',  # Blue
        'RESET': '\033[0m'  # Reset to default color
    }
    
    def __init__(self, name, log_dir='logs'):
        """
        Initialize the logger with a name and log directory.
        
        Args:
            name (str): Name of the logger (typically module name)
            log_dir (str): Directory to store log files
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Generate log filename with current date
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'viral_shorts_{today}.log')
        
        # File handler with rotation (10MB max size, 5 backup files)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.callbacks = []
        
        # Run system diagnostics on initialization
        self.run_system_diagnostics()
    
    def add_callback(self, callback):
        """
        Add a callback function that will be called with each log message.
        Useful for updating GUI log display.
        
        Args:
            callback (callable): Function to call with (level, message) args
        """
        self.callbacks.append(callback)
        
    def _log_with_color(self, level, message):
        """
        Log a message with the specified level and call all callbacks.
        
        Args:
            level (str): Log level (INFO, WARNING, etc.)
            message (str): The message to log
        """
        # Standard logging
        log_method = getattr(self.logger, level.lower())
        log_method(message)
        
        # Call all callbacks with colored message
        colored_msg = f"{self.COLORS.get(level.upper(), '')}{message}{self.COLORS['RESET']}"
        for callback in self.callbacks:
            try:
                callback(level, colored_msg)
            except Exception as e:
                self.logger.error(f"Error in log callback: {e}")
    
    def info(self, message):
        """Log an info level message."""
        self._log_with_color('info', message)
    
    def warning(self, message):
        """Log a warning level message."""
        self._log_with_color('warning', message)
    
    def error(self, message):
        """Log an error level message."""
        self._log_with_color('error', message)
    
    def critical(self, message):
        """Log a critical level message."""
        self._log_with_color('critical', message)
    
    def debug(self, message):
        """Log a debug level message."""
        self._log_with_color('debug', message)
        
    def exception(self, message):
        """Log an exception with traceback."""
        tb = traceback.format_exc()
        self._log_with_color('error', f"{message}\n{tb}")
        
    def run_system_diagnostics(self):
        """Run system diagnostics and log system information."""
        try:
            self.debug("=== SYSTEM DIAGNOSTICS ===")
            
            # System information
            self.debug(f"Platform: {platform.platform()}")
            self.debug(f"Python Version: {sys.version}")
            
            # Current working directory and file structure
            self.debug(f"Current Working Directory: {os.getcwd()}")
            
            # Check important directories
            self._check_directory_structure()
            
            # Check Python packages
            self._check_required_packages()
            
            # Check configuration files
            self._check_configuration_files()
            
            self.debug("=== DIAGNOSTICS COMPLETE ===")
        except Exception as e:
            self.error(f"Error running diagnostics: {e}")
            self.exception("Diagnostics failed")
            
    def _check_directory_structure(self):
        """Check if required directories exist and log their status."""
        required_dirs = [
            'data',
            'data/downloads',
            'data/processed',
            'data/uploads',
            'data/reports',
            'logs'
        ]
        
        self.debug("Checking directory structure:")
        for directory in required_dirs:
            exists = os.path.exists(directory)
            status = "EXISTS" if exists else "MISSING"
            self.debug(f"  - {directory}: {status}")
            
            if not exists:
                # Try to create the directory
                try:
                    os.makedirs(directory, exist_ok=True)
                    self.debug(f"    Created directory: {directory}")
                except Exception as e:
                    self.warning(f"    Failed to create directory {directory}: {e}")
                    
    def _check_required_packages(self):
        """Check for required Python packages and log their status."""
        required_packages = [
            'PyQt5',
            'apscheduler',
            'python-dotenv',
            'google-auth',
            'google-auth-oauthlib',
            'google-auth-httplib2',
            'google-api-python-client',
            'openai',
            'moviepy',
            'matplotlib',
            'pandas'
        ]
        
        self.debug("Checking required Python packages:")
        for package in required_packages:
            try:
                pkg = importlib.import_module(package.split('[')[0])  # Handle cases like 'package[extra]'
                version = getattr(pkg, '__version__', 'Unknown version')
                self.debug(f"  - {package}: INSTALLED (version: {version})")
            except ImportError:
                self.warning(f"  - {package}: NOT INSTALLED")
                
    def _check_configuration_files(self):
        """Check for required configuration files and log their status."""
        required_files = [
            'config.json',
            '.env',
            'data/youtube_credentials.json'
        ]
        
        self.debug("Checking configuration files:")
        for file in required_files:
            exists = os.path.exists(file)
            status = "EXISTS" if exists else "MISSING"
            self.debug(f"  - {file}: {status}")
            
            if exists and file.endswith('.json'):
                # Check if it's valid JSON
                try:
                    import json
                    with open(file, 'r') as f:
                        json.load(f)
                    self.debug(f"    Valid JSON format")
                except Exception as e:
                    self.warning(f"    Invalid JSON format: {e}")
                    
    def log_system_info(self):
        """Log detailed system information for troubleshooting."""
        try:
            self.debug("=== DETAILED SYSTEM INFORMATION ===")
            
            # Python paths
            self.debug(f"PYTHONPATH: {sys.path}")
            
            # Environment variables relevant to the app
            self.debug("Environment Variables:")
            for var in ['PYTHONPATH', 'PATH', 'OPENAI_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS']:
                value = os.environ.get(var, 'Not set')
                # Mask sensitive information
                if var in ['OPENAI_API_KEY']:
                    value = f"{value[:6]}..." if value != 'Not set' else value
                self.debug(f"  - {var}: {value}")
                
            # Database status
            self._check_database_status()
                
            self.debug("=== END SYSTEM INFORMATION ===")
        except Exception as e:
            self.error(f"Error logging system info: {e}")
            
    def _check_database_status(self):
        """Check the status of the SQLite database."""
        db_path = 'data/viral_shorts.db'
        self.debug(f"Checking database: {db_path}")
        
        if not os.path.exists(db_path):
            self.warning(f"Database file doesn't exist: {db_path}")
            return
            
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            self.debug(f"Database tables: {[t[0] for t in tables]}")
            
            conn.close()
            self.debug("Database connection successful")
        except Exception as e:
            self.error(f"Database check error: {e}")
            self.exception("Database check failed")


# Global logger instance
app_logger = Logger('ViralShortsAI')
