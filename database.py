"""
Database module for ViralShortsAI.
Handles database operations for storing video data, analytics, and performance metrics.
"""

import os
import sqlite3
import json
import datetime
from utils import app_logger

class Database:
    """
    Database class for managing SQLite operations.
    Handles videos, analytics, and application settings storage.
    """
    
    def __init__(self, db_path):
        """
        Initialize database connection and create tables if they don't exist.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = app_logger
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
    def connect(self):
        """Establish connection to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            self.logger.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.logger.debug("Database connection closed")
            
    def create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            # Source videos table (original videos downloaded)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS source_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT UNIQUE,
                title TEXT,
                channel TEXT,
                url TEXT,
                views INTEGER,
                likes INTEGER,
                duration INTEGER,
                category TEXT,
                downloaded_at TIMESTAMP,
                file_path TEXT,
                copyright_status TEXT,
                metadata TEXT
            )
            ''')
            
            # Processed clips table (clips created from source videos)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                clip_duration INTEGER,
                start_time INTEGER,
                end_time INTEGER,
                file_path TEXT,
                subtitle_path TEXT,
                created_at TIMESTAMP,
                viral_score FLOAT,
                title TEXT,
                description TEXT,
                hashtags TEXT,
                FOREIGN KEY (source_id) REFERENCES source_videos (id) ON DELETE CASCADE
            )
            ''')
            
            # Uploaded videos table (videos uploaded to YouTube)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploaded_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id INTEGER,
                youtube_id TEXT UNIQUE,
                title TEXT,
                description TEXT,
                hashtags TEXT,
                upload_time TIMESTAMP,
                scheduled_time TIMESTAMP,
                visibility TEXT,
                url TEXT,
                FOREIGN KEY (clip_id) REFERENCES processed_clips (id) ON DELETE CASCADE
            )
            ''')
            
            # Analytics table (performance metrics for uploaded videos)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER,
                timestamp TIMESTAMP,
                views INTEGER,
                likes INTEGER,
                comments INTEGER,
                retention_rate FLOAT,
                ctr FLOAT,
                viral_score FLOAT,
                FOREIGN KEY (upload_id) REFERENCES uploaded_videos (id) ON DELETE CASCADE
            )
            ''')
            
            # Videos table (unified video storage)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT UNIQUE,
                title TEXT,
                description TEXT,
                duration INTEGER,
                upload_date TIMESTAMP,
                download_path TEXT,
                status TEXT DEFAULT 'downloaded',
                processed BOOLEAN DEFAULT 0,
                uploaded BOOLEAN DEFAULT 0,
                hashtags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Settings table (for storing application settings)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP
            )
            ''')
            
            # Tasks table (for tracking scheduled and completed tasks)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                status TEXT,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                params TEXT,
                result TEXT,
                error TEXT
            )
            ''')
            
            self.conn.commit()
            self.logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise
            
    def add_source_video(self, video_data):
        """
        Add a new source video to the database.
        
        Args:
            video_data (dict): Dictionary with video information
            
        Returns:
            int: ID of the inserted record
        """
        try:
            # Convert metadata dict to JSON string
            if 'metadata' in video_data and isinstance(video_data['metadata'], dict):
                video_data['metadata'] = json.dumps(video_data['metadata'])
                
            # Ensure downloaded_at is set
            if 'downloaded_at' not in video_data:
                video_data['downloaded_at'] = datetime.datetime.now().isoformat()
                
            # Extract fields from video_data that match table columns
            columns = self.get_table_columns('source_videos')
            filtered_data = {k: v for k, v in video_data.items() if k in columns}
            
            # Build the SQL query
            placeholders = ', '.join(['?'] * len(filtered_data))
            columns_str = ', '.join(filtered_data.keys())
            values = list(filtered_data.values())
            
            query = f"INSERT INTO source_videos ({columns_str}) VALUES ({placeholders})"
            
            self.cursor.execute(query, values)
            self.conn.commit()
            
            video_id = self.cursor.lastrowid
            self.logger.info(f"Added source video with ID: {video_id}")
            return video_id
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Error adding source video: {e}")
            raise
    
    def get_table_columns(self, table_name):
        """
        Get column names for a table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            list: List of column names
        """
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        return [row['name'] for row in self.cursor.fetchall()]
    
    def add_processed_clip(self, clip_data):
        """
        Add a processed clip to the database.
        
        Args:
            clip_data (dict): Dictionary with clip information
            
        Returns:
            int: ID of the inserted record
        """
        try:
            # Convert hashtags list to comma-separated string
            if 'hashtags' in clip_data and isinstance(clip_data['hashtags'], list):
                clip_data['hashtags'] = ','.join(clip_data['hashtags'])
                
            # Ensure created_at is set
            if 'created_at' not in clip_data:
                clip_data['created_at'] = datetime.datetime.now().isoformat()
                
            columns = self.get_table_columns('processed_clips')
            filtered_data = {k: v for k, v in clip_data.items() if k in columns}
            
            placeholders = ', '.join(['?'] * len(filtered_data))
            columns_str = ', '.join(filtered_data.keys())
            values = list(filtered_data.values())
            
            query = f"INSERT INTO processed_clips ({columns_str}) VALUES ({placeholders})"
            
            self.cursor.execute(query, values)
            self.conn.commit()
            
            clip_id = self.cursor.lastrowid
            self.logger.info(f"Added processed clip with ID: {clip_id}")
            return clip_id
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Error adding processed clip: {e}")
            raise
    
    def add_uploaded_video(self, upload_data):
        """
        Add an uploaded video to the database.
        
        Args:
            upload_data (dict): Dictionary with upload information
            
        Returns:
            int: ID of the inserted record
        """
        try:
            # Convert hashtags list to comma-separated string
            if 'hashtags' in upload_data and isinstance(upload_data['hashtags'], list):
                upload_data['hashtags'] = ','.join(upload_data['hashtags'])
                
            # Ensure upload_time is set
            if 'upload_time' not in upload_data:
                upload_data['upload_time'] = datetime.datetime.now().isoformat()
                
            columns = self.get_table_columns('uploaded_videos')
            filtered_data = {k: v for k, v in upload_data.items() if k in columns}
            
            placeholders = ', '.join(['?'] * len(filtered_data))
            columns_str = ', '.join(filtered_data.keys())
            values = list(filtered_data.values())
            
            query = f"INSERT INTO uploaded_videos ({columns_str}) VALUES ({placeholders})"
            
            self.cursor.execute(query, values)
            self.conn.commit()
            
            upload_id = self.cursor.lastrowid
            self.logger.info(f"Added uploaded video with ID: {upload_id}")
            return upload_id
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Error adding uploaded video: {e}")
            raise
    
    def add_analytics(self, analytics_data):
        """
        Add analytics data for an uploaded video.
        
        Args:
            analytics_data (dict): Dictionary with analytics information
            
        Returns:
            int: ID of the inserted record
        """
        try:
            # Ensure timestamp is set
            if 'timestamp' not in analytics_data:
                analytics_data['timestamp'] = datetime.datetime.now().isoformat()
                
            columns = self.get_table_columns('analytics')
            filtered_data = {k: v for k, v in analytics_data.items() if k in columns}
            
            placeholders = ', '.join(['?'] * len(filtered_data))
            columns_str = ', '.join(filtered_data.keys())
            values = list(filtered_data.values())
            
            query = f"INSERT INTO analytics ({columns_str}) VALUES ({placeholders})"
            
            self.cursor.execute(query, values)
            self.conn.commit()
            
            analytics_id = self.cursor.lastrowid
            self.logger.debug(f"Added analytics with ID: {analytics_id}")
            return analytics_id
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Error adding analytics: {e}")
            raise
    
    def get_pending_uploads(self, limit=None):
        """
        Get processed clips that haven't been uploaded yet.
        
        Args:
            limit (int, optional): Maximum number of records to return
            
        Returns:
            list: List of dictionaries containing clip information
        """
        try:
            query = """
            SELECT pc.* FROM processed_clips pc
            LEFT JOIN uploaded_videos uv ON pc.id = uv.clip_id
            WHERE uv.id IS NULL
            ORDER BY pc.viral_score DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
                
            self.cursor.execute(query)
            results = [dict(row) for row in self.cursor.fetchall()]
            
            # Convert hashtags string back to list
            for clip in results:
                if 'hashtags' in clip and clip['hashtags']:
                    clip['hashtags'] = clip['hashtags'].split(',')
            
            return results
        except sqlite3.Error as e:
            self.logger.error(f"Error getting pending uploads: {e}")
            raise
    
    def get_uploaded_videos_without_analytics(self, hours_ago=24):
        """
        Get uploaded videos that need analytics collection.
        
        Args:
            hours_ago (int): Get videos uploaded at least this many hours ago
            
        Returns:
            list: List of dictionaries containing upload information
        """
        try:
            min_time = (datetime.datetime.now() - 
                      datetime.timedelta(hours=hours_ago)).isoformat()
            
            query = """
            SELECT uv.* FROM uploaded_videos uv
            LEFT JOIN analytics a ON uv.id = a.upload_id
            WHERE a.id IS NULL AND uv.upload_time < ?
            """
            
            self.cursor.execute(query, (min_time,))
            results = [dict(row) for row in self.cursor.fetchall()]
            
            # Convert hashtags string back to list
            for video in results:
                if 'hashtags' in video and video['hashtags']:
                    video['hashtags'] = video['hashtags'].split(',')
            
            return results
        except sqlite3.Error as e:
            self.logger.error(f"Error getting videos without analytics: {e}")
            raise
    
    def get_best_performing_categories(self, days=30, limit=3):
        """
        Get best performing video categories based on viral scores.
        
        Args:
            days (int): Consider videos from the last N days
            limit (int): Maximum number of categories to return
            
        Returns:
            list: List of dictionaries with category and average score
        """
        try:
            min_time = (datetime.datetime.now() - 
                      datetime.timedelta(days=days)).isoformat()
            
            query = """
            SELECT sv.category, AVG(a.viral_score) as avg_score, COUNT(*) as count
            FROM analytics a
            JOIN uploaded_videos uv ON a.upload_id = uv.id
            JOIN processed_clips pc ON uv.clip_id = pc.id
            JOIN source_videos sv ON pc.source_id = sv.id
            WHERE uv.upload_time > ?
            GROUP BY sv.category
            HAVING count >= 3
            ORDER BY avg_score DESC
            LIMIT ?
            """
            
            self.cursor.execute(query, (min_time, limit))
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting best categories: {e}")
            raise
    
    def get_best_performing_durations(self, days=30):
        """
        Get best performing clip durations based on viral scores.
        
        Args:
            days (int): Consider videos from the last N days
            
        Returns:
            list: List of dictionaries with duration and average score
        """
        try:
            min_time = (datetime.datetime.now() - 
                      datetime.timedelta(days=days)).isoformat()
            
            query = """
            SELECT pc.clip_duration, AVG(a.viral_score) as avg_score, COUNT(*) as count
            FROM analytics a
            JOIN uploaded_videos uv ON a.upload_id = uv.id
            JOIN processed_clips pc ON uv.clip_id = pc.id
            WHERE uv.upload_time > ?
            GROUP BY pc.clip_duration
            HAVING count >= 3
            ORDER BY avg_score DESC
            """
            
            self.cursor.execute(query, (min_time,))
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting best durations: {e}")
            raise
            
    def get_videos_for_analysis(self, limit=50):
        """
        Get videos with complete analytics for analysis.
        
        Args:
            limit (int): Maximum number of videos to return
            
        Returns:
            list: List of dictionaries with video and analytics data
        """
        try:
            query = """
            SELECT 
                uv.id as upload_id, 
                uv.title, 
                uv.youtube_id,
                uv.upload_time,
                pc.clip_duration,
                sv.category,
                a.views,
                a.likes,
                a.comments,
                a.retention_rate,
                a.ctr,
                a.viral_score
            FROM uploaded_videos uv
            JOIN processed_clips pc ON uv.clip_id = pc.id
            JOIN source_videos sv ON pc.source_id = sv.id
            JOIN analytics a ON uv.id = a.upload_id
            ORDER BY uv.upload_time DESC
            LIMIT ?
            """
            
            self.cursor.execute(query, (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting videos for analysis: {e}")
            raise
            
    def update_setting(self, key, value):
        """
        Update or insert a setting value.
        
        Args:
            key (str): Setting key
            value: Setting value (will be converted to JSON string)
        """
        try:
            # Convert value to JSON string if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
                
            timestamp = datetime.datetime.now().isoformat()
            
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                """,
                (key, value, timestamp)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Error updating setting: {e}")
            raise
            
    def get_setting(self, key, default=None):
        """
        Get a setting value.
        
        Args:
            key (str): Setting key
            default: Default value if key doesn't exist
            
        Returns:
            The setting value (converted from JSON if applicable)
        """
        try:
            self.cursor.execute(
                "SELECT value FROM settings WHERE key = ?",
                (key,)
            )
            row = self.cursor.fetchone()
            
            if not row:
                return default
                
            value = row['value']
            
            # Try to parse as JSON, return raw string if fails
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except sqlite3.Error as e:
            self.logger.error(f"Error getting setting: {e}")
            return default
            
    def add_task(self, task_type, params=None):
        """
        Add a new task to the task queue.
        
        Args:
            task_type (str): Type of task (e.g., 'download', 'process', 'upload')
            params (dict, optional): Parameters for the task
            
        Returns:
            int: ID of the inserted task
        """
        try:
            # Convert params to JSON string
            if params:
                params = json.dumps(params)
                
            created_at = datetime.datetime.now().isoformat()
            
            self.cursor.execute(
                """
                INSERT INTO tasks (task_type, status, created_at, params)
                VALUES (?, ?, ?, ?)
                """,
                (task_type, 'pending', created_at, params)
            )
            self.conn.commit()
            
            task_id = self.cursor.lastrowid
            self.logger.debug(f"Added {task_type} task with ID: {task_id}")
            return task_id
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Error adding task: {e}")
            raise
            
    def update_task_status(self, task_id, status, result=None, error=None):
        """
        Update the status of a task.
        
        Args:
            task_id (int): ID of the task
            status (str): New status ('running', 'completed', 'failed')
            result (dict, optional): Result data
            error (str, optional): Error message
        """
        try:
            updates = {'status': status}
            
            if status == 'running':
                updates['started_at'] = datetime.datetime.now().isoformat()
            elif status in ('completed', 'failed'):
                updates['completed_at'] = datetime.datetime.now().isoformat()
                
            if result:
                updates['result'] = json.dumps(result)
                
            if error:
                updates['error'] = error
                
            # Build SET clause
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [task_id]
            
            self.cursor.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()
            
            self.logger.debug(f"Updated task {task_id} status to {status}")
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Error updating task status: {e}")
            raise
            
    def get_pending_tasks(self, task_type=None, limit=10):
        """
        Get pending tasks from the queue.
        
        Args:
            task_type (str, optional): Filter by task type
            limit (int): Maximum number of tasks to return
            
        Returns:
            list: List of task dictionaries
        """
        try:
            query = "SELECT * FROM tasks WHERE status = 'pending'"
            params = []
            
            if task_type:
                query += " AND task_type = ?"
                params.append(task_type)
                
            query += " ORDER BY created_at ASC LIMIT ?"
            params.append(limit)
            
            self.cursor.execute(query, params)
            tasks = [dict(row) for row in self.cursor.fetchall()]
            
            # Parse JSON fields
            for task in tasks:
                if task['params']:
                    try:
                        task['params'] = json.loads(task['params'])
                    except json.JSONDecodeError:
                        pass
                        
                if task['result']:
                    try:
                        task['result'] = json.loads(task['result'])
                    except json.JSONDecodeError:
                        pass
                        
            return tasks
        except sqlite3.Error as e:
            self.logger.error(f"Error getting pending tasks: {e}")
            raise
            
    def execute_query(self, query, params=None):
        """
        Execute a custom SQL query.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            list: List of query results as dictionaries
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
                
            if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                return [dict(row) for row in self.cursor.fetchall()]
            else:
                self.conn.commit()
                return None
        except sqlite3.Error as e:
            if not query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                self.conn.rollback()
            self.logger.error(f"Error executing query: {e}")
            raise
    
    def get_videos_ready_for_upload(self, limit=5):
        """
        Ottieni video pronti per l'upload automatico.
        
        Args:
            limit (int): Numero massimo di video da restituire
            
        Returns:
            list: Lista di video pronti per l'upload
        """
        try:
            query = """
            SELECT 
                pc.id,
                pc.title,
                pc.description, 
                pc.hashtags,
                pc.file_path,
                pc.viral_score,
                pc.created_at,
                sv.title as source_title,
                sv.channel as source_channel
            FROM processed_clips pc
            LEFT JOIN source_videos sv ON pc.source_id = sv.id
            LEFT JOIN uploaded_videos uv ON pc.id = uv.clip_id
            WHERE uv.id IS NULL  -- Non ancora uploadato
                AND pc.file_path IS NOT NULL  -- Ha file video
                AND pc.title IS NOT NULL  -- Ha titolo
                AND pc.created_at >= date('now', '-30 days')  -- Creato negli ultimi 30 giorni
            ORDER BY pc.viral_score DESC, pc.created_at DESC
            LIMIT ?
            """
            
            self.cursor.execute(query, (limit,))
            results = [dict(row) for row in self.cursor.fetchall()]
            
            self.logger.info(f"Found {len(results)} videos ready for upload")
            return results
            
        except sqlite3.Error as e:
            self.logger.error(f"Error getting videos ready for upload: {e}")
            return []
    
    def mark_video_as_uploaded(self, clip_id, youtube_id, upload_data=None):
        """
        Marca un video come caricato su YouTube.
        
        Args:
            clip_id (int): ID del clip processato
            youtube_id (str): ID del video su YouTube
            upload_data (dict, optional): Dati aggiuntivi dell'upload
            
        Returns:
            int: ID del record di upload creato
        """
        try:
            upload_info = {
                'clip_id': clip_id,
                'youtube_id': youtube_id,
                'upload_time': datetime.datetime.now().isoformat(),
                'visibility': 'public'
            }
            
            if upload_data:
                upload_info.update(upload_data)
            
            return self.add_uploaded_video(upload_info)
            
        except sqlite3.Error as e:
            self.logger.error(f"Error marking video as uploaded: {e}")
            raise
    
    def get_daily_upload_stats(self, date=None):
        """
        Ottieni statistiche di upload per una specifica data.
        
        Args:
            date (str, optional): Data in formato 'YYYY-MM-DD'. Default: oggi
            
        Returns:
            dict: Statistiche di upload del giorno
        """
        try:
            if date is None:
                date = datetime.datetime.now().strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                COUNT(*) as uploads_count,
                COUNT(CASE WHEN visibility = 'public' THEN 1 END) as public_uploads,
                MIN(upload_time) as first_upload,
                MAX(upload_time) as last_upload
            FROM uploaded_videos
            WHERE DATE(upload_time) = ?
            """
            
            self.cursor.execute(query, (date,))
            result = dict(self.cursor.fetchone())
            
            self.logger.debug(f"Daily upload stats for {date}: {result}")
            return result
            
        except sqlite3.Error as e:
            self.logger.error(f"Error getting daily upload stats: {e}")
            return {
                'uploads_count': 0,
                'public_uploads': 0,
                'first_upload': None,
                'last_upload': None
            }
