"""
🔄 ViralShortsAI - Advanced Task Queue Manager
Intelligent task scheduling and resource optimization
"""

import json
import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from queue import PriorityQueue
import heapq

from utils import app_logger

class TaskExecutor:
    """
    🚀 Advanced Task Executor with intelligent resource management
    
    This integrates with your existing ViralShortsWorker but adds:
    - Intelligent prioritization
    - Resource-aware scheduling
    - Failure recovery
    - Performance optimization
    """
    
    def __init__(self, config: Dict, db, existing_components: Dict):
        self.config = config
        self.db = db
        self.logger = app_logger
        
        # Reference to existing components
        self.finder = existing_components.get('finder')
        self.transcriber = existing_components.get('transcriber')
        self.captioner = existing_components.get('captioner')
        self.editor = existing_components.get('editor')
        self.uploader = existing_components.get('uploader')
        self.analyzer = existing_components.get('analyzer')
        
        # Task queues
        self.high_priority_queue = PriorityQueue()
        self.normal_priority_queue = PriorityQueue()
        self.low_priority_queue = PriorityQueue()
        
        # Execution tracking
        self.running_tasks = {}
        self.completed_tasks = []
        self.failed_tasks = []
        
        # Resource monitoring
        self.max_concurrent_tasks = config.get('max_concurrent_tasks', 3)
        self.current_resource_usage = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'api_calls': 0
        }
        
        # Performance tracking
        self.performance_stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_execution_time': 0,
            'viral_success_rate': 0
        }
        
        self.logger.info("🔄 Advanced Task Executor initialized")
    
    def create_smart_content_pipeline(self, max_videos: int) -> List[Dict]:
        """
        🧠 Create intelligent content creation pipeline
        
        This replaces the linear processing in your main.py with smart automation
        """
        pipeline_tasks = []
        
        # 1. Smart Video Discovery Task
        discovery_task = {
            'id': f"discovery_{int(time.time())}",
            'type': 'smart_video_discovery',
            'priority': 3,
            'params': {
                'max_videos': max_videos,
                'use_ai_selection': True,
                'viral_threshold': 60
            },
            'estimated_duration': 120,
            'dependencies': []
        }
        pipeline_tasks.append(discovery_task)
        
        # 2. Batch Processing Tasks (will be created after discovery)
        batch_task = {
            'id': f"batch_processing_{int(time.time())}",
            'type': 'intelligent_batch_processing',
            'priority': 2,
            'params': {
                'optimize_for_viral': True,
                'parallel_processing': True
            },
            'estimated_duration': 600,
            'dependencies': [discovery_task['id']]
        }
        pipeline_tasks.append(batch_task)
        
        # 3. Smart Upload Scheduling
        upload_task = {
            'id': f"smart_upload_{int(time.time())}",
            'type': 'ai_powered_upload_scheduling',
            'priority': 1,
            'params': {
                'use_audience_insights': True,
                'optimize_timing': True,
                'multi_timezone': True
            },
            'estimated_duration': 300,
            'dependencies': [batch_task['id']]
        }
        pipeline_tasks.append(upload_task)
        
        # 4. Performance Analysis & Learning
        analysis_task = {
            'id': f"analysis_{int(time.time())}",
            'type': 'performance_analysis_and_learning',
            'priority': 1,
            'params': {
                'update_ai_models': True,
                'generate_insights': True
            },
            'estimated_duration': 180,
            'dependencies': [upload_task['id']]
        }
        pipeline_tasks.append(analysis_task)
        
        # Add tasks to appropriate queues
        for task in pipeline_tasks:
            self.add_task_to_queue(task)
        
        return pipeline_tasks
    
    def add_task_to_queue(self, task: Dict):
        """Add task to appropriate priority queue"""
        priority = task['priority']
        # Use negative priority for max-heap behavior
        queue_item = (-priority, time.time(), task)
        
        if priority >= 3:
            self.high_priority_queue.put(queue_item)
        elif priority >= 2:
            self.normal_priority_queue.put(queue_item)
        else:
            self.low_priority_queue.put(queue_item)
        
        self.logger.info(f"Added task {task['id']} to queue (priority: {priority})")
    
    async def execute_smart_pipeline(self):
        """
        🚀 Execute the smart automation pipeline
        
        This is the main execution loop that replaces your current run() method
        """
        self.logger.info("🚀 Starting Smart Automation Pipeline")
        
        while True:
            try:
                # Get next batch of tasks to execute
                executable_tasks = self._get_ready_tasks()
                
                if not executable_tasks:
                    await asyncio.sleep(10)
                    continue
                
                # Execute tasks with intelligent resource management
                execution_coroutines = []
                for task in executable_tasks:
                    if len(self.running_tasks) < self.max_concurrent_tasks:
                        coroutine = self._execute_task_with_monitoring(task)
                        execution_coroutines.append(coroutine)
                
                if execution_coroutines:
                    # Execute tasks in parallel
                    await asyncio.gather(*execution_coroutines, return_exceptions=True)
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Brief pause
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in smart pipeline: {e}")
                await asyncio.sleep(30)
    
    def _get_ready_tasks(self) -> List[Dict]:
        """Get tasks that are ready to execute"""
        ready_tasks = []
        
        # Check high priority queue first
        if not self.high_priority_queue.empty():
            _, _, task = self.high_priority_queue.get()
            if self._are_dependencies_satisfied(task):
                ready_tasks.append(task)
            else:
                # Put back if dependencies not satisfied
                self.high_priority_queue.put((-task['priority'], time.time(), task))
        
        # Then normal priority
        elif not self.normal_priority_queue.empty():
            _, _, task = self.normal_priority_queue.get()
            if self._are_dependencies_satisfied(task):
                ready_tasks.append(task)
            else:
                self.normal_priority_queue.put((-task['priority'], time.time(), task))
        
        # Finally low priority
        elif not self.low_priority_queue.empty():
            _, _, task = self.low_priority_queue.get()
            if self._are_dependencies_satisfied(task):
                ready_tasks.append(task)
            else:
                self.low_priority_queue.put((-task['priority'], time.time(), task))
        
        return ready_tasks
    
    def _are_dependencies_satisfied(self, task: Dict) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.get('dependencies', []):
            if dep_id not in [t['id'] for t in self.completed_tasks]:
                return False
        return True
    
    async def _execute_task_with_monitoring(self, task: Dict):
        """Execute task with comprehensive monitoring"""
        task_id = task['id']
        task_type = task['type']
        
        try:
            self.running_tasks[task_id] = {
                'task': task,
                'start_time': time.time(),
                'status': 'running'
            }
            
            self.logger.info(f"🔄 Executing task: {task_id} ({task_type})")
            
            # Execute based on task type
            result = await self._dispatch_task_execution(task)
            
            # Calculate execution time
            execution_time = time.time() - self.running_tasks[task_id]['start_time']
            
            # Update task completion
            completed_task = task.copy()
            completed_task['result'] = result
            completed_task['execution_time'] = execution_time
            completed_task['status'] = 'completed'
            
            self.completed_tasks.append(completed_task)
            del self.running_tasks[task_id]
            
            self.performance_stats['successful_tasks'] += 1
            self._update_average_execution_time(execution_time)
            
            self.logger.info(f"✅ Task completed: {task_id} in {execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Task failed: {task_id} - {e}")
            
            failed_task = task.copy()
            failed_task['error'] = str(e)
            failed_task['status'] = 'failed'
            
            self.failed_tasks.append(failed_task)
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            self.performance_stats['failed_tasks'] += 1
            
            # Intelligent retry logic
            await self._handle_task_failure(task, str(e))
    
    async def _dispatch_task_execution(self, task: Dict) -> Dict[str, Any]:
        """Dispatch task to appropriate execution method"""
        task_type = task['type']
        params = task['params']
        
        handlers = {
            'smart_video_discovery': self._execute_smart_video_discovery,
            'intelligent_batch_processing': self._execute_intelligent_batch_processing,
            'ai_powered_upload_scheduling': self._execute_ai_powered_upload_scheduling,
            'performance_analysis_and_learning': self._execute_performance_analysis_and_learning,
            'emergency_content_generation': self._execute_emergency_content_generation,
            'viral_optimization': self._execute_viral_optimization
        }
        
        handler = handlers.get(task_type)
        if not handler:
            raise ValueError(f"Unknown task type: {task_type}")
        
        return await handler(task)
    
    async def _execute_smart_video_discovery(self, task: Dict) -> Dict[str, Any]:
        """
        🔍 Smart Video Discovery with AI-powered selection
        
        Enhanced version of your existing video search
        """
        params = task['params']
        max_videos = params.get('max_videos', 5)
        viral_threshold = params.get('viral_threshold', 60)
        
        # Use your existing finder but with AI enhancement
        categories = self.config['youtube_search']['categories']
        enabled_categories = [cat for cat, enabled in categories.items() if enabled]
        
        all_videos = []
        
        for category in enabled_categories:
            try:
                # Search for more videos than needed to allow AI selection
                videos = self.finder.search_viral_shorts(
                    category=category, 
                    max_results=max_videos * 2
                )
                
                # AI-powered filtering based on viral potential
                high_potential_videos = []
                for video in videos:
                    if video.get('viral_score', 0) >= viral_threshold:
                        # Additional AI scoring could be added here
                        enhanced_score = self._calculate_enhanced_viral_score(video)
                        video['enhanced_viral_score'] = enhanced_score
                        high_potential_videos.append(video)
                
                all_videos.extend(high_potential_videos)
                
            except Exception as e:
                self.logger.error(f"Error searching category {category}: {e}")
        
        # Sort by enhanced viral score and select top videos
        all_videos.sort(key=lambda x: x.get('enhanced_viral_score', 0), reverse=True)
        selected_videos = all_videos[:max_videos]
        
        # Store selected videos for next task
        video_ids = []
        for video in selected_videos:
            video_id = self.db.add_source_video(video)
            video_ids.append(video_id)
        
        return {
            'video_ids': video_ids,
            'total_videos_found': len(all_videos),
            'selected_videos': len(selected_videos),
            'average_viral_score': sum(v.get('enhanced_viral_score', 0) for v in selected_videos) / len(selected_videos) if selected_videos else 0
        }
    
    def _calculate_enhanced_viral_score(self, video: Dict) -> float:
        """Calculate enhanced viral score using additional factors"""
        base_score = video.get('viral_score', 0)
        
        # Additional factors
        recency_boost = 0
        publish_date = video.get('publish_date')
        if publish_date:
            days_old = (datetime.now() - publish_date).days
            if days_old <= 7:
                recency_boost = 10 * (7 - days_old) / 7
        
        # Channel credibility boost
        channel_boost = 0
        views = video.get('views', 0)
        if views > 100000:
            channel_boost = 5
        elif views > 50000:
            channel_boost = 3
        
        # Duration optimization
        duration_score = 0
        duration = video.get('duration', 0)
        if 15 <= duration <= 60:  # Optimal for shorts
            duration_score = 5
        
        enhanced_score = base_score + recency_boost + channel_boost + duration_score
        return min(100, enhanced_score)
    
    async def _execute_intelligent_batch_processing(self, task: Dict) -> Dict[str, Any]:
        """
        ⚡ Intelligent Batch Processing
        
        Process multiple videos in parallel with smart resource management
        """
        # Get video IDs from previous task
        discovery_result = self._get_dependency_result(task, 'smart_video_discovery')
        video_ids = discovery_result.get('video_ids', [])
        
        processed_clips = []
        processing_stats = {
            'total_videos': len(video_ids),
            'successful_processing': 0,
            'failed_processing': 0,
            'total_clips_created': 0
        }
        
        # Process videos with intelligent parallel execution
        semaphore = asyncio.Semaphore(2)  # Limit concurrent video processing
        
        async def process_single_video(video_id):
            async with semaphore:
                try:
                    result = await self._process_video_with_ai_optimization(video_id)
                    processing_stats['successful_processing'] += 1
                    processing_stats['total_clips_created'] += len(result.get('clip_ids', []))
                    processed_clips.extend(result.get('clip_ids', []))
                    return result
                except Exception as e:
                    self.logger.error(f"Failed to process video {video_id}: {e}")
                    processing_stats['failed_processing'] += 1
                    return None
        
        # Execute all video processing in parallel
        processing_tasks = [process_single_video(vid_id) for vid_id in video_ids]
        await asyncio.gather(*processing_tasks, return_exceptions=True)
        
        return {
            'processed_clip_ids': processed_clips,
            'processing_stats': processing_stats
        }
    
    async def _process_video_with_ai_optimization(self, video_id: int) -> Dict[str, Any]:
        """Process single video with AI optimization"""
        # Get video data
        video = self.db.execute_query(
            "SELECT * FROM source_videos WHERE id = ?", 
            (video_id,)
        )[0]
        
        # Transcribe with optimized settings
        language = self.config['app_settings']['selected_language']
        transcription = self.transcriber.transcribe_video(
            video['file_path'],
            language=language,
            save_srt=True
        )
        
        # Find key moments with AI enhancement
        key_moments = self.transcriber.find_key_moments(transcription)
        transcription['key_moments'] = key_moments
        
        # Analyze viral potential with enhanced AI
        viral_analysis = self.captioner.analyze_viral_potential(
            transcription, 
            video['category']
        )
        
        # Create clips with intelligent selection
        clip_ids = self.editor.process_source_video(
            video_id, 
            transcription,
            viral_analysis
        )
        
        # Generate enhanced metadata for each clip
        for clip_id in clip_ids:
            await self._generate_enhanced_metadata(clip_id, transcription)
        
        return {
            'video_id': video_id,
            'clip_ids': clip_ids,
            'viral_analysis': viral_analysis
        }
    
    async def _generate_enhanced_metadata(self, clip_id: int, transcription: Dict):
        """Generate enhanced metadata with AI optimization"""
        clip = self.db.execute_query(
            "SELECT * FROM processed_clips WHERE id = ?", 
            (clip_id,)
        )[0]
        
        # Extract clip transcription segment
        clip_start = clip['start_time']
        clip_end = clip['end_time']
        
        clip_segments = []
        for segment in transcription['segments']:
            if segment['start'] >= clip_start and segment['end'] <= clip_end:
                clip_segments.append(segment)
        
        clip_transcription = {'segments': clip_segments}
        
        # Generate metadata with AI enhancement
        metadata = self.captioner.generate_video_metadata(
            clip, clip_transcription
        )
        
        # Enhance with trending hashtags (placeholder for hashtag AI)
        enhanced_hashtags = await self._get_trending_hashtags(metadata['hashtags'])
        metadata['hashtags'] = enhanced_hashtags
        
        # Update clip with enhanced metadata
        self.db.execute_query(
            """
            UPDATE processed_clips
            SET title = ?, description = ?, hashtags = ?
            WHERE id = ?
            """,
            (
                metadata['title'],
                metadata['description'],
                ','.join(metadata['hashtags']),
                clip_id
            )
        )
    
    async def _get_trending_hashtags(self, base_hashtags: List[str]) -> List[str]:
        """Get trending hashtags (placeholder for future hashtag AI)"""
        # This would integrate with hashtag trending analysis
        # For now, return enhanced base hashtags
        enhanced = base_hashtags.copy()
        
        # Add some trending hashtags based on current trends
        trending_additions = ['#viral', '#trending', '#fyp', '#shorts']
        for tag in trending_additions:
            if tag not in enhanced:
                enhanced.append(tag)
        
        return enhanced[:10]  # Limit to 10 hashtags
    
    async def _execute_ai_powered_upload_scheduling(self, task: Dict) -> Dict[str, Any]:
        """
        📤 AI-Powered Upload Scheduling
        
        Intelligent upload timing based on audience behavior analysis
        """
        # Get processed clips from previous task
        batch_result = self._get_dependency_result(task, 'intelligent_batch_processing')
        clip_ids = batch_result.get('processed_clip_ids', [])
        
        if not clip_ids:
            return {'uploaded_videos': 0, 'scheduled_videos': 0}
        
        # Authenticate YouTube uploader
        if not self.uploader.authenticate():
            raise Exception("YouTube authentication failed")
        
        # Get clips and sort by viral potential
        clips = []
        for clip_id in clip_ids:
            clip = self.db.execute_query(
                "SELECT * FROM processed_clips WHERE id = ?", 
                (clip_id,)
            )[0]
            clips.append(clip)
        
        # Sort by viral score (descending)
        clips.sort(key=lambda x: x['viral_score'], reverse=True)
        
        # Limit to max uploads per day
        max_uploads = self.config['app_settings']['max_videos_per_day']
        clips = clips[:max_uploads]
        
        upload_results = []
        scheduled_count = 0
        immediate_count = 0
        
        for i, clip in enumerate(clips):
            try:
                # Calculate optimal upload time using AI
                optimal_time = self._calculate_optimal_upload_time(clip, i)
                
                # Schedule the upload
                result = self.uploader.schedule_upload(clip, optimal_time)
                
                if result:
                    # Add to uploaded_videos table
                    upload_data = {
                        'clip_id': clip['id'],
                        'youtube_id': result.get('youtube_id'),
                        'title': result['title'],
                        'description': result['description'],
                        'hashtags': ','.join(result['hashtags']) if isinstance(result['hashtags'], list) else result['hashtags'],
                        'upload_time': result.get('upload_time'),
                        'scheduled_time': result.get('scheduled_time', optimal_time.isoformat()),
                        'visibility': result['visibility'],
                        'url': result.get('url')
                    }
                    
                    self.db.add_uploaded_video(upload_data)
                    upload_results.append(result)
                    
                    if result.get('youtube_id'):
                        immediate_count += 1
                    else:
                        scheduled_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to schedule upload for clip {clip['id']}: {e}")
        
        return {
            'uploaded_videos': immediate_count,
            'scheduled_videos': scheduled_count,
            'total_processed': len(clips),
            'upload_results': upload_results
        }
    
    def _calculate_optimal_upload_time(self, clip: Dict, sequence_index: int) -> datetime:
        """Calculate optimal upload time using AI and audience analysis"""
        now = datetime.now()
        
        # Base upload times from config
        upload_times = self.config['upload']['upload_times']
        
        if sequence_index < len(upload_times):
            # Parse time string (e.g. "12:00")
            time_str = upload_times[sequence_index]
            hour, minute = map(int, time_str.split(':'))
            
            upload_time = datetime.combine(
                now.date(), 
                datetime.min.time().replace(hour=hour, minute=minute)
            )
            
            # If time is in the past, schedule for tomorrow
            if upload_time < now:
                upload_time += timedelta(days=1)
            
            # Apply AI optimization (audience behavior analysis)
            optimized_time = self._optimize_upload_time_with_ai(upload_time, clip)
            
            return optimized_time
        else:
            # Default to 3 hours from now for extra videos
            return now + timedelta(hours=3)
    
    def _optimize_upload_time_with_ai(self, base_time: datetime, clip: Dict) -> datetime:
        """Optimize upload time based on AI analysis"""
        # This would use ML models to predict best timing
        # For now, apply heuristic optimization
        
        # Weekend vs weekday optimization
        if base_time.weekday() >= 5:  # Weekend
            # Slightly later posting on weekends
            optimized_time = base_time + timedelta(hours=1)
        else:
            # Peak engagement times on weekdays
            hour = base_time.hour
            if hour < 12:
                # Morning posts - slight delay
                optimized_time = base_time + timedelta(minutes=30)
            elif hour > 20:
                # Evening posts - slight advancement
                optimized_time = base_time - timedelta(minutes=30)
            else:
                optimized_time = base_time
        
        return optimized_time
    
    async def _execute_performance_analysis_and_learning(self, task: Dict) -> Dict[str, Any]:
        """
        📊 Performance Analysis and Learning
        
        Analyze results and update AI models
        """
        # Collect metrics for recently uploaded videos
        updated_count = self.analyzer.collect_metrics(self.uploader)
        
        # Generate comprehensive performance report
        report = self.analyzer.generate_performance_report(days=7)
        
        # Update content strategy based on performance
        strategy_updates = None
        if self.config['analytics']['auto_learning']:
            strategy_updates = self.analyzer.update_content_strategy()
        
        # Update performance statistics
        self._update_viral_success_rate(report)
        
        return {
            'metrics_updated': updated_count,
            'performance_report': report,
            'strategy_updates': strategy_updates,
            'viral_success_rate': self.performance_stats['viral_success_rate']
        }
    
    def _get_dependency_result(self, task: Dict, dependency_type: str) -> Dict[str, Any]:
        """Get result from dependency task"""
        for dep_id in task.get('dependencies', []):
            for completed_task in self.completed_tasks:
                if (completed_task['id'] == dep_id and 
                    completed_task['type'] == dependency_type):
                    return completed_task.get('result', {})
        return {}
    
    def _update_performance_metrics(self):
        """Update performance tracking metrics"""
        total_tasks = self.performance_stats['successful_tasks'] + self.performance_stats['failed_tasks']
        self.performance_stats['total_tasks'] = total_tasks
        
        if total_tasks > 0:
            success_rate = self.performance_stats['successful_tasks'] / total_tasks
            self.performance_stats['success_rate'] = success_rate
    
    def _update_average_execution_time(self, execution_time: float):
        """Update average execution time"""
        current_avg = self.performance_stats['average_execution_time']
        total_successful = self.performance_stats['successful_tasks']
        
        if total_successful == 1:
            self.performance_stats['average_execution_time'] = execution_time
        else:
            # Running average
            new_avg = ((current_avg * (total_successful - 1)) + execution_time) / total_successful
            self.performance_stats['average_execution_time'] = new_avg
    
    def _update_viral_success_rate(self, report: Dict):
        """Update viral success rate based on performance report"""
        if report and 'avg_viral_score' in report:
            # Consider videos with score > 70 as viral successes
            viral_threshold = 70
            avg_score = report['avg_viral_score']
            
            if avg_score >= viral_threshold:
                self.performance_stats['viral_success_rate'] = min(100, avg_score)
            else:
                # Calculate percentage of videos above threshold
                self.performance_stats['viral_success_rate'] = (avg_score / viral_threshold) * 100
    
    async def _handle_task_failure(self, task: Dict, error: str):
        """Handle task failure with intelligent retry logic"""
        retry_count = task.get('retry_count', 0)
        max_retries = task.get('max_retries', 3)
        
        if retry_count < max_retries:
            # Calculate retry delay (exponential backoff)
            delay = min(300, 30 * (2 ** retry_count))  # Max 5 minutes
            
            # Update task for retry
            retry_task = task.copy()
            retry_task['retry_count'] = retry_count + 1
            retry_task['priority'] = max(1, task['priority'] - 1)  # Lower priority
            
            self.logger.info(f"Scheduling retry for task {task['id']} in {delay} seconds")
            
            # Schedule retry
            await asyncio.sleep(delay)
            self.add_task_to_queue(retry_task)
        else:
            self.logger.error(f"Task {task['id']} exhausted all retries")
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        return {
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'queue_sizes': {
                'high_priority': self.high_priority_queue.qsize(),
                'normal_priority': self.normal_priority_queue.qsize(),
                'low_priority': self.low_priority_queue.qsize()
            },
            'performance_stats': self.performance_stats,
            'resource_usage': self.current_resource_usage
        }
    
    async def _execute_emergency_content_generation(self, task: Dict) -> Dict[str, Any]:
        """Emergency content generation when queue is empty"""
        # This would trigger when no content is in pipeline
        self.logger.info("🚨 Executing emergency content generation")
        
        # Quick video discovery and processing
        emergency_pipeline = self.create_smart_content_pipeline(max_videos=2)
        
        # Execute with high priority
        for emergency_task in emergency_pipeline:
            emergency_task['priority'] = 5  # Maximum priority
            self.add_task_to_queue(emergency_task)
        
        return {'emergency_tasks_created': len(emergency_pipeline)}
    
    async def _execute_viral_optimization(self, task: Dict) -> Dict[str, Any]:
        """Optimize existing content for viral potential"""
        # This would re-analyze and re-optimize existing clips
        self.logger.info("🔥 Executing viral optimization")
        
        # Get recent clips with low viral scores
        low_performing = self.db.execute_query("""
            SELECT pc.* FROM processed_clips pc
            JOIN uploaded_videos uv ON pc.id = uv.clip_id
            LEFT JOIN analytics a ON uv.id = a.upload_id
            WHERE a.viral_score < 50 OR a.viral_score IS NULL
            ORDER BY pc.created_at DESC
            LIMIT 5
        """)
        
        optimization_results = []
        
        for clip in low_performing:
            try:
                # Re-generate metadata with current AI models
                enhanced_metadata = await self._regenerate_optimized_metadata(clip)
                optimization_results.append(enhanced_metadata)
            except Exception as e:
                self.logger.error(f"Failed to optimize clip {clip['id']}: {e}")
        
        return {'optimized_clips': len(optimization_results)}
    
    async def _regenerate_optimized_metadata(self, clip: Dict) -> Dict[str, Any]:
        """Regenerate metadata with latest AI optimizations"""
        # This would use the latest AI models and trending data
        # to regenerate titles, descriptions, and hashtags
        
        # Get source video for context
        source_video = self.db.execute_query(
            "SELECT * FROM source_videos WHERE id = ?",
            (clip['source_id'],)
        )[0]
        
        # Get latest trending hashtags
        trending_hashtags = await self._get_trending_hashtags([])
        
        # Generate optimized metadata
        optimized_metadata = {
            'title': f"🔥 {clip['title'][:50]}... #Viral",
            'description': f"{clip['description']}\n\n{' '.join(trending_hashtags[:5])}",
            'hashtags': trending_hashtags
        }
        
        # Update in database
        self.db.execute_query("""
            UPDATE processed_clips 
            SET title = ?, description = ?, hashtags = ?
            WHERE id = ?
        """, (
            optimized_metadata['title'],
            optimized_metadata['description'], 
            ','.join(optimized_metadata['hashtags']),
            clip['id']
        ))
        
        return optimized_metadata
