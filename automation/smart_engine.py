"""
🤖 ViralShortsAI - Smart Automation Engine
Advanced automation system with AI-powered decision making
"""

import os
import json
import time
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import redis
from celery import Celery
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from utils import app_logger

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class SmartTask:
    """Enhanced task structure with AI capabilities"""
    id: str
    task_type: str
    priority: TaskPriority
    params: Dict[str, Any]
    scheduled_time: datetime
    created_at: datetime
    estimated_duration: int  # seconds
    resource_requirements: Dict[str, float]
    dependencies: List[str]
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_history: List[Dict] = None
    
    def __post_init__(self):
        if self.execution_history is None:
            self.execution_history = []

class SmartAutomationEngine:
    """
    🧠 AI-Powered Smart Automation Engine
    
    Features:
    - Predictive scheduling based on audience behavior
    - Resource optimization and conflict resolution
    - Failure recovery with intelligent retry logic
    - Performance-based task prioritization
    - Multi-timezone optimization
    - Content queue management with viral prediction
    """
    
    def __init__(self, config: Dict, db):
        self.config = config
        self.db = db
        self.logger = app_logger
        
        # Initialize Redis for caching and queue management
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            decode_responses=True
        )
        
        # Initialize Celery for distributed task processing
        self.celery_app = Celery(
            'viral_shorts_automation',
            broker=f"redis://{config.get('redis_host', 'localhost')}:6379/0",
            backend=f"redis://{config.get('redis_host', 'localhost')}:6379/0"
        )
        
        # Task queues by priority
        self.task_queues = {
            TaskPriority.EMERGENCY: [],
            TaskPriority.CRITICAL: [],
            TaskPriority.HIGH: [],
            TaskPriority.NORMAL: [],
            TaskPriority.LOW: []
        }
        
        # Resource tracking
        self.available_resources = {
            'cpu_cores': config.get('max_cpu_cores', 4),
            'memory_gb': config.get('max_memory_gb', 8),
            'api_quota_youtube': config.get('youtube_quota_limit', 10000),
            'api_quota_openai': config.get('openai_quota_limit', 1000000),
            'storage_gb': config.get('max_storage_gb', 100)
        }
        
        self.used_resources = {key: 0 for key in self.available_resources}
        
        # AI Models for optimization
        self.scheduling_model = None
        self.viral_prediction_model = None
        self.load_ai_models()
        
        # Audience behavior patterns
        self.audience_patterns = self._load_audience_patterns()
        
        # Automation rules
        self.automation_rules = self._initialize_automation_rules()
        
        # Performance tracking
        self.performance_metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_execution_time': 0,
            'resource_utilization': 0,
            'optimization_score': 0
        }
        
        self.logger.info("🤖 Smart Automation Engine initialized")
    
    def load_ai_models(self):
        """Load or train AI models for optimization"""
        try:
            # Try to load existing models
            models_path = 'data/ai_models'
            os.makedirs(models_path, exist_ok=True)
            
            scheduling_model_path = f"{models_path}/scheduling_model.pkl"
            viral_model_path = f"{models_path}/viral_prediction_model.pkl"
            
            if os.path.exists(scheduling_model_path):
                with open(scheduling_model_path, 'rb') as f:
                    self.scheduling_model = pickle.load(f)
                self.logger.info("Loaded existing scheduling model")
            else:
                self.train_scheduling_model()
                
            if os.path.exists(viral_model_path):
                with open(viral_model_path, 'rb') as f:
                    self.viral_prediction_model = pickle.load(f)
                self.logger.info("Loaded existing viral prediction model")
            else:
                self.train_viral_prediction_model()
                
        except Exception as e:
            self.logger.error(f"Error loading AI models: {e}")
            self.train_scheduling_model()
            self.train_viral_prediction_model()
    
    def train_scheduling_model(self):
        """Train ML model for optimal scheduling"""
        try:
            # Get historical performance data
            query = """
            SELECT 
                CAST(strftime('%H', uv.upload_time) AS INTEGER) as hour,
                CAST(strftime('%w', uv.upload_time) AS INTEGER) as day_of_week,
                sv.category,
                pc.clip_duration,
                a.views,
                a.likes,
                a.viral_score
            FROM uploaded_videos uv
            JOIN processed_clips pc ON uv.clip_id = pc.id
            JOIN source_videos sv ON pc.source_id = sv.id
            JOIN analytics a ON uv.id = a.upload_id
            WHERE uv.upload_time > date('now', '-60 days')
            """
            
            data = self.db.execute_query(query)
            
            if len(data) < 10:
                # Not enough data, use default model
                self.scheduling_model = RandomForestRegressor(n_estimators=50, random_state=42)
                self.logger.warning("Not enough data for training, using default model")
                return
            
            # Prepare features and target
            features = []
            targets = []
            
            for row in data:
                # Features: hour, day_of_week, category_encoded, duration
                category_encoded = hash(row['category']) % 100  # Simple encoding
                features.append([
                    row['hour'],
                    row['day_of_week'], 
                    category_encoded,
                    row['clip_duration']
                ])
                
                # Target: viral_score (what we want to optimize)
                targets.append(row['viral_score'])
            
            X = np.array(features)
            y = np.array(targets)
            
            # Train model
            self.scheduling_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.scheduling_model.fit(X, y)
            
            # Save model
            models_path = 'data/ai_models'
            os.makedirs(models_path, exist_ok=True)
            with open(f"{models_path}/scheduling_model.pkl", 'wb') as f:
                pickle.dump(self.scheduling_model, f)
            
            self.logger.info(f"Trained scheduling model with {len(data)} samples")
            
        except Exception as e:
            self.logger.error(f"Error training scheduling model: {e}")
            self.scheduling_model = RandomForestRegressor(n_estimators=50, random_state=42)
    
    def train_viral_prediction_model(self):
        """Train ML model for viral potential prediction"""
        try:
            # Get video data with viral scores
            query = """
            SELECT 
                sv.views as source_views,
                sv.likes as source_likes,
                sv.duration as source_duration,
                sv.category,
                pc.viral_score as clip_viral_score,
                pc.clip_duration,
                pc.start_time,
                a.viral_score as final_viral_score
            FROM source_videos sv
            JOIN processed_clips pc ON sv.id = pc.source_id
            JOIN uploaded_videos uv ON pc.id = uv.clip_id
            JOIN analytics a ON uv.id = a.upload_id
            WHERE a.viral_score IS NOT NULL
            """
            
            data = self.db.execute_query(query)
            
            if len(data) < 5:
                self.viral_prediction_model = RandomForestRegressor(n_estimators=50, random_state=42)
                self.logger.warning("Not enough data for viral prediction model")
                return
            
            features = []
            targets = []
            
            for row in data:
                # Calculate engagement rate of source
                engagement_rate = 0
                if row['source_views'] > 0:
                    engagement_rate = row['source_likes'] / row['source_views']
                
                category_encoded = hash(row['category']) % 100
                
                features.append([
                    row['source_views'],
                    engagement_rate,
                    row['source_duration'],
                    category_encoded,
                    row['clip_duration'],
                    row['start_time'],
                    row['clip_viral_score']
                ])
                
                targets.append(row['final_viral_score'])
            
            X = np.array(features)
            y = np.array(targets)
            
            self.viral_prediction_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=12,
                random_state=42
            )
            self.viral_prediction_model.fit(X, y)
            
            # Save model
            models_path = 'data/ai_models'
            with open(f"{models_path}/viral_prediction_model.pkl", 'wb') as f:
                pickle.dump(self.viral_prediction_model, f)
            
            self.logger.info(f"Trained viral prediction model with {len(data)} samples")
            
        except Exception as e:
            self.logger.error(f"Error training viral prediction model: {e}")
            self.viral_prediction_model = RandomForestRegressor(n_estimators=50, random_state=42)
    
    def predict_optimal_upload_time(self, content_data: Dict) -> datetime:
        """🎯 AI-powered optimal upload time prediction"""
        try:
            if not self.scheduling_model:
                # Fallback to config times
                return self._get_next_config_time()
            
            # Test different time slots for next 7 days
            now = datetime.now()
            best_time = now + timedelta(hours=1)
            best_score = 0
            
            for day_offset in range(7):
                test_date = now + timedelta(days=day_offset)
                
                for hour in range(6, 24):  # 6 AM to 11 PM
                    test_time = test_date.replace(
                        hour=hour, 
                        minute=0, 
                        second=0, 
                        microsecond=0
                    )
                    
                    if test_time <= now:
                        continue
                    
                    # Predict performance for this time
                    category_encoded = hash(content_data.get('category', 'unknown')) % 100
                    features = [[
                        hour,
                        test_date.weekday(),
                        category_encoded,
                        content_data.get('duration', 30)
                    ]]
                    
                    predicted_score = self.scheduling_model.predict(features)[0]
                    
                    # Apply audience pattern multiplier
                    pattern_multiplier = self._get_audience_activity_multiplier(test_time)
                    final_score = predicted_score * pattern_multiplier
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_time = test_time
            
            self.logger.info(f"Predicted optimal upload time: {best_time} (score: {best_score:.2f})")
            return best_time
            
        except Exception as e:
            self.logger.error(f"Error predicting optimal upload time: {e}")
            return self._get_next_config_time()
    
    def _get_audience_activity_multiplier(self, upload_time: datetime) -> float:
        """Get audience activity multiplier for given time"""
        hour = upload_time.hour
        day_of_week = upload_time.weekday()
        
        # Base activity patterns (can be learned from analytics)
        weekday_pattern = {
            6: 0.3, 7: 0.5, 8: 0.7, 9: 0.8, 10: 0.9, 11: 1.0,
            12: 1.2, 13: 1.1, 14: 0.9, 15: 0.8, 16: 0.9, 17: 1.1,
            18: 1.3, 19: 1.4, 20: 1.5, 21: 1.4, 22: 1.2, 23: 0.8
        }
        
        weekend_pattern = {
            9: 0.4, 10: 0.6, 11: 0.8, 12: 1.0, 13: 1.1, 14: 1.2,
            15: 1.3, 16: 1.4, 17: 1.3, 18: 1.2, 19: 1.4, 20: 1.5,
            21: 1.4, 22: 1.1, 23: 0.9
        }
        
        if day_of_week >= 5:  # Weekend
            return weekend_pattern.get(hour, 0.5)
        else:  # Weekday
            return weekday_pattern.get(hour, 0.5)
    
    def create_smart_task(self, 
                         task_type: str,
                         params: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.NORMAL,
                         scheduled_time: Optional[datetime] = None,
                         dependencies: List[str] = None) -> SmartTask:
        """🧠 Create intelligent task with resource estimation"""
        
        if scheduled_time is None:
            if task_type == 'upload_video':
                # Use AI prediction for upload timing
                scheduled_time = self.predict_optimal_upload_time(params)
            else:
                scheduled_time = datetime.now()
        
        if dependencies is None:
            dependencies = []
        
        # Estimate task duration and resources
        estimated_duration = self._estimate_task_duration(task_type, params)
        resource_requirements = self._estimate_resource_requirements(task_type, params)
        
        task = SmartTask(
            id=f"{task_type}_{int(time.time())}_{hash(str(params)) % 10000}",
            task_type=task_type,
            priority=priority,
            params=params,
            scheduled_time=scheduled_time,
            created_at=datetime.now(),
            estimated_duration=estimated_duration,
            resource_requirements=resource_requirements,
            dependencies=dependencies
        )
        
        # Add to appropriate queue
        self.task_queues[priority].append(task)
        
        # Cache in Redis
        self.redis_client.hset(
            'smart_tasks',
            task.id,
            json.dumps(asdict(task), default=str)
        )
        
        self.logger.info(f"Created smart task {task.id} scheduled for {scheduled_time}")
        return task
    
    def _estimate_task_duration(self, task_type: str, params: Dict) -> int:
        """Estimate task duration in seconds"""
        base_durations = {
            'search_videos': 120,  # 2 minutes
            'download_video': 300,  # 5 minutes
            'transcribe_video': 180,  # 3 minutes
            'analyze_viral_potential': 60,  # 1 minute
            'create_clips': 240,  # 4 minutes
            'generate_metadata': 90,  # 1.5 minutes
            'upload_video': 600,  # 10 minutes
            'collect_analytics': 30,  # 30 seconds
            'generate_report': 120  # 2 minutes
        }
        
        base_duration = base_durations.get(task_type, 300)
        
        # Adjust based on parameters
        if task_type == 'create_clips':
            video_duration = params.get('video_duration', 60)
            base_duration += video_duration * 2  # 2 seconds processing per second of video
        
        elif task_type == 'upload_video':
            file_size_mb = params.get('file_size_mb', 50)
            base_duration += file_size_mb * 2  # 2 seconds per MB
        
        return base_duration
    
    def _estimate_resource_requirements(self, task_type: str, params: Dict) -> Dict[str, float]:
        """Estimate resource requirements for task"""
        base_requirements = {
            'search_videos': {'cpu_cores': 0.5, 'memory_gb': 1, 'api_quota_youtube': 100},
            'download_video': {'cpu_cores': 1, 'memory_gb': 2, 'storage_gb': 0.5},
            'transcribe_video': {'cpu_cores': 2, 'memory_gb': 4, 'storage_gb': 0.1},
            'analyze_viral_potential': {'cpu_cores': 0.5, 'memory_gb': 1, 'api_quota_openai': 1000},
            'create_clips': {'cpu_cores': 2, 'memory_gb': 3, 'storage_gb': 1},
            'generate_metadata': {'cpu_cores': 0.5, 'memory_gb': 1, 'api_quota_openai': 500},
            'upload_video': {'cpu_cores': 1, 'memory_gb': 2, 'api_quota_youtube': 50},
            'collect_analytics': {'cpu_cores': 0.2, 'memory_gb': 0.5, 'api_quota_youtube': 10},
            'generate_report': {'cpu_cores': 1, 'memory_gb': 2, 'storage_gb': 0.1}
        }
        
        return base_requirements.get(task_type, {'cpu_cores': 1, 'memory_gb': 1})
    
    async def execute_smart_pipeline(self, max_parallel_tasks: int = 3):
        """🚀 Execute smart pipeline with optimal resource utilization"""
        self.logger.info("Starting smart automation pipeline")
        
        while True:
            try:
                # Get ready tasks
                ready_tasks = self._get_ready_tasks()
                
                if not ready_tasks:
                    await asyncio.sleep(30)  # Wait 30 seconds before checking again
                    continue
                
                # Select optimal task combination
                selected_tasks = self._select_optimal_task_combination(
                    ready_tasks, 
                    max_parallel_tasks
                )
                
                if not selected_tasks:
                    await asyncio.sleep(60)  # Wait longer if no tasks can run
                    continue
                
                # Execute tasks in parallel
                execution_tasks = []
                for task in selected_tasks:
                    execution_tasks.append(self._execute_task_async(task))
                
                # Wait for all tasks to complete
                results = await asyncio.gather(*execution_tasks, return_exceptions=True)
                
                # Process results
                for task, result in zip(selected_tasks, results):
                    self._process_task_result(task, result)
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Brief pause before next iteration
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in smart pipeline execution: {e}")
                await asyncio.sleep(60)
    
    def _get_ready_tasks(self) -> List[SmartTask]:
        """Get tasks that are ready to execute"""
        ready_tasks = []
        now = datetime.now()
        
        for priority in TaskPriority:
            for task in self.task_queues[priority][:]:
                if (task.status == TaskStatus.PENDING and 
                    task.scheduled_time <= now and
                    self._are_dependencies_satisfied(task)):
                    ready_tasks.append(task)
        
        return ready_tasks
    
    def _are_dependencies_satisfied(self, task: SmartTask) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            # Check if dependency task is completed
            dep_data = self.redis_client.hget('smart_tasks', dep_id)
            if dep_data:
                dep_task = json.loads(dep_data)
                if dep_task.get('status') != TaskStatus.COMPLETED.value:
                    return False
            else:
                # Dependency not found, assume it's satisfied
                continue
        return True
    
    def _select_optimal_task_combination(self, 
                                       ready_tasks: List[SmartTask], 
                                       max_tasks: int) -> List[SmartTask]:
        """🧠 Select optimal combination of tasks to run in parallel"""
        if not ready_tasks:
            return []
        
        # Sort by priority and viral prediction score
        ready_tasks.sort(key=lambda t: (
            t.priority.value,
            self._predict_task_viral_potential(t)
        ), reverse=True)
        
        selected = []
        temp_resources = self.used_resources.copy()
        
        for task in ready_tasks:
            if len(selected) >= max_tasks:
                break
            
            # Check if we have enough resources
            can_run = True
            for resource, required in task.resource_requirements.items():
                if resource in temp_resources:
                    available = self.available_resources[resource] - temp_resources[resource]
                    if available < required:
                        can_run = False
                        break
            
            if can_run:
                selected.append(task)
                # Reserve resources
                for resource, required in task.resource_requirements.items():
                    if resource in temp_resources:
                        temp_resources[resource] += required
        
        return selected
    
    def _predict_task_viral_potential(self, task: SmartTask) -> float:
        """Predict viral potential of task result"""
        if task.task_type != 'upload_video' or not self.viral_prediction_model:
            return 50.0  # Default score
        
        try:
            params = task.params
            category_encoded = hash(params.get('category', 'unknown')) % 100
            
            features = [[
                params.get('source_views', 10000),
                params.get('engagement_rate', 0.05),
                params.get('source_duration', 120),
                category_encoded,
                params.get('clip_duration', 30),
                params.get('start_time', 0),
                params.get('clip_viral_score', 50)
            ]]
            
            return float(self.viral_prediction_model.predict(features)[0])
            
        except Exception as e:
            self.logger.error(f"Error predicting viral potential: {e}")
            return 50.0
    
    async def _execute_task_async(self, task: SmartTask) -> Dict[str, Any]:
        """Execute single task asynchronously"""
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            self._update_task_in_redis(task)
            
            # Reserve resources
            self._reserve_resources(task)
            
            start_time = time.time()
            
            # Execute based on task type
            result = await self._dispatch_task_execution(task)
            
            execution_time = time.time() - start_time
            
            # Update task with result
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.execution_history.append({
                'start_time': start_time,
                'execution_time': execution_time,
                'result': result
            })
            
            self._release_resources(task)
            self._update_task_in_redis(task)
            
            self.logger.info(f"Task {task.id} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.retry_count += 1
            
            self._release_resources(task)
            self._update_task_in_redis(task)
            
            # Schedule retry if applicable
            if task.retry_count < task.max_retries:
                self._schedule_task_retry(task)
            
            self.logger.error(f"Task {task.id} failed: {e}")
            return {'error': str(e)}
    
    async def _dispatch_task_execution(self, task: SmartTask) -> Dict[str, Any]:
        """Dispatch task execution to appropriate handler"""
        handlers = {
            'search_videos': self._execute_search_videos,
            'download_video': self._execute_download_video,
            'transcribe_video': self._execute_transcribe_video,
            'analyze_viral_potential': self._execute_analyze_viral,
            'create_clips': self._execute_create_clips,
            'generate_metadata': self._execute_generate_metadata,
            'upload_video': self._execute_upload_video,
            'collect_analytics': self._execute_collect_analytics,
            'generate_report': self._execute_generate_report
        }
        
        handler = handlers.get(task.task_type)
        if not handler:
            raise ValueError(f"Unknown task type: {task.task_type}")
        
        return await handler(task)
    
    # Task execution methods would be implemented here
    # Each method would be an async wrapper around existing functionality
    
    async def _execute_search_videos(self, task: SmartTask) -> Dict[str, Any]:
        """Execute video search task"""
        # This would wrap the existing YouTubeShortsFinder.search_viral_shorts method
        pass
    
    async def _execute_upload_video(self, task: SmartTask) -> Dict[str, Any]:
        """Execute video upload task"""
        # This would wrap the existing YouTubeUploader.upload_video method
        pass
    
    # ... other execution methods
    
    def generate_automation_report(self) -> Dict[str, Any]:
        """📊 Generate comprehensive automation performance report"""
        return {
            'performance_metrics': self.performance_metrics,
            'resource_utilization': self._calculate_resource_utilization(),
            'task_statistics': self._get_task_statistics(),
            'optimization_recommendations': self._generate_optimization_recommendations(),
            'predicted_improvements': self._predict_performance_improvements()
        }
    
    def _load_audience_patterns(self) -> Dict:
        """Load learned audience behavior patterns"""
        # This would analyze historical data to learn when audience is most active
        return {}
    
    def _initialize_automation_rules(self) -> Dict:
        """Initialize automation business rules"""
        return {
            'max_videos_per_hour': 2,
            'min_time_between_uploads': 1800,  # 30 minutes
            'viral_threshold_for_priority': 70,
            'resource_usage_threshold': 0.8
        }
    
    # ... additional helper methods
