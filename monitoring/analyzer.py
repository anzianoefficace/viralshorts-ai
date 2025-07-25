"""
Analytics and performance monitoring module for ViralShortsAI.
Handles tracking video performance and adapting content strategy.
"""

import os
import json
import datetime
import time
from pathlib import Path
import math
import logging

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from utils import app_logger
from database import Database
from data.downloader import YouTubeShortsFinder
from monitoring.report_generator import TrendReportGenerator

class PerformanceAnalyzer:
    """
    Class to analyze video performance and refine content strategy.
    Tracks metrics, identifies patterns, and adapts strategy over time.
    """
    
    def __init__(self, config, db):
        """
        Initialize the performance analyzer.
        
        Args:
            config (dict): Configuration dictionary
            db: Database instance
        """
        self.config = config
        self.db = db
        self.shorts_finder = YouTubeShortsFinder(config, db)
        self.report_generator = TrendReportGenerator()
        self.logger = app_logger
        
        try:
            # Ottieni la base directory dai percorsi configurati o usa un valore predefinito
            base_dir = self.config.get('paths', {}).get('data')
            
            # Se 'data' non è definito nel config, lo deduci dal percorso del database
            if not base_dir:
                db_path = self.config.get('paths', {}).get('database', 'data/viral_shorts.db')
                self.logger.debug(f"[DEBUG] Percorso database: {db_path}")
                # Estrai la directory di base dal percorso del database (di solito 'data')
                base_dir = os.path.dirname(db_path)
                self.logger.info(f"Directory di base dedotta dal database: {base_dir}")
            
            # Assicurati che la directory esista
            Path(base_dir).mkdir(parents=True, exist_ok=True)
            
            # Crea la directory dei report
            reports_dir = Path(base_dir) / 'reports'
            reports_dir.mkdir(parents=True, exist_ok=True)
            self.reports_dir = reports_dir
            
            self.logger.info(f"Directory dei report creata/verificata: {reports_dir}")
        except Exception as e:
            self.logger.error(f"Errore nella configurazione dell'analizzatore: {e}")
            # Usa una directory predefinita in caso di errore
            reports_dir = Path("data/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            self.reports_dir = reports_dir
            self.logger.warning(f"Usando directory di fallback per i report: {reports_dir}")
        
        self.logger.info("Performance analyzer initialized")
    
    def collect_metrics(self, uploader):
        """
        Collect performance metrics for videos without analytics.
        
        Args:
            uploader: YouTubeUploader instance
            
        Returns:
            int: Number of videos updated
        """
        try:
            # Check how many hours ago videos should have metrics collected
            hours_ago = self.config['analytics']['measure_after_hours']
            min_time = (datetime.datetime.now() - 
                      datetime.timedelta(hours=hours_ago)).isoformat()
            
            # Get uploaded videos without analytics
            query = """
            SELECT uv.* FROM uploaded_videos uv
            LEFT JOIN analytics a ON uv.id = a.upload_id
            WHERE a.id IS NULL 
            AND uv.youtube_id IS NOT NULL
            AND uv.upload_time < ?
            """
            
            videos = self.db.execute_query(query, (min_time,))
            
            if not videos:
                self.logger.info("No videos need metrics collection")
                return 0
                
            self.logger.info(f"Collecting metrics for {len(videos)} videos")
            
            updated_count = 0
            
            for video in videos:
                try:
                    # Get analytics from YouTube
                    youtube_id = video['youtube_id']
                    analytics = uploader.get_video_analytics(youtube_id)
                    
                    if not analytics:
                        self.logger.warning(f"No analytics available for {youtube_id}")
                        continue
                    
                    # Get clip data
                    clip = self.db.execute_query(
                        "SELECT * FROM processed_clips WHERE id = ?", 
                        (video['clip_id'],)
                    )
                    
                    if not clip:
                        self.logger.error(f"Clip not found for video {youtube_id}")
                        continue
                        
                    clip = clip[0]
                    
                    # Enhance with additional metrics
                    # For metrics that aren't available via the API, we'll estimate
                    views = analytics.get('views', 0)
                    
                    # Estimate retention rate (better would be from YouTube Analytics API)
                    retention_rate = min(100, 50 + analytics.get('viral_score', 0) / 3)
                    
                    # Estimate CTR (click-through rate)
                    ctr = min(20, 5 + analytics.get('viral_score', 0) / 10)
                    
                    # Calculate overall viral score
                    # - Weighted average of various factors
                    likes = analytics.get('likes', 0)
                    comments = analytics.get('comments', 0)
                    
                    # Engagement rate per view
                    engagement_per_view = 0
                    if views > 0:
                        engagement_per_view = (likes * 1.0 + comments * 2.0) / views
                    
                    # Normalize the engagement (typical range is 0-0.2)
                    normalized_engagement = min(1.0, engagement_per_view * 5)
                    
                    # Calculate viral score (0-100)
                    viral_score = min(100, (
                        (views / max(1, clip['clip_duration'])) * 0.05 +  # Views per second
                        (normalized_engagement * 50) +                    # Engagement
                        (retention_rate * 0.3) +                         # Retention
                        (ctr * 2.0)                                      # CTR
                    ))
                    
                    # Add analytics to database
                    analytics_data = {
                        'upload_id': video['id'],
                        'timestamp': analytics.get('timestamp'),
                        'views': views,
                        'likes': likes,
                        'comments': comments,
                        'retention_rate': retention_rate,
                        'ctr': ctr,
                        'viral_score': viral_score
                    }
                    
                    self.db.add_analytics(analytics_data)
                    
                    self.logger.info(
                        f"Added analytics for {youtube_id}: {views} views, " +
                        f"score {viral_score:.1f}"
                    )
                    
                    updated_count += 1
                    
                    # Prevent too many API calls in a short time
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error collecting metrics for {video['youtube_id']}: {e}")
            
            return updated_count
            
        except Exception as e:
            self.logger.error(f"Error in collect_metrics: {e}")
            return 0
    
    def generate_performance_report(self, days=7):
        """
        Generate a performance report for recent videos.
        
        Args:
            days (int): Number of days to include in report
            
        Returns:
            dict: Report data
        """
        try:
            self.logger.info(f"Generating performance report for the last {days} days")
            
            # Get date range
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days)
            
            # Query for performance data
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
            WHERE uv.upload_time BETWEEN ? AND ?
            ORDER BY uv.upload_time DESC
            """
            
            videos = self.db.execute_query(
                query, 
                (start_date.isoformat(), end_date.isoformat())
            )
            
            if not videos:
                self.logger.info("No videos found for performance report")
                return {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'total_videos': 0,
                    'total_views': 0,
                    'categories': [],
                    'durations': [],
                    'top_videos': [],
                    'recommendations': []
                }
            
            # Convert to DataFrame for analysis
            videos_df = pd.DataFrame(videos)
            
            # Basic metrics
            total_videos = len(videos_df)
            total_views = videos_df['views'].sum()
            total_likes = videos_df['likes'].sum()
            total_comments = videos_df['comments'].sum()
            avg_viral_score = videos_df['viral_score'].mean()
            
            # Performance by category
            category_perf = videos_df.groupby('category').agg({
                'views': 'sum',
                'viral_score': 'mean',
                'upload_id': 'count'
            }).reset_index()
            category_perf = category_perf.rename(columns={'upload_id': 'count'})
            category_perf = category_perf.sort_values('viral_score', ascending=False)
            
            # Performance by duration
            duration_perf = videos_df.groupby('clip_duration').agg({
                'views': 'sum',
                'viral_score': 'mean',
                'upload_id': 'count'
            }).reset_index()
            duration_perf = duration_perf.rename(columns={'upload_id': 'count'})
            duration_perf = duration_perf.sort_values('viral_score', ascending=False)
            
            # Top performing videos
            top_videos = videos_df.sort_values('viral_score', ascending=False).head(5)
            
            # Generate recommendations
            recommendations = []
            
            # Check if we have enough data
            if total_videos >= 5:
                # Recommend best category
                if not category_perf.empty and len(category_perf) > 1:
                    best_category = category_perf.iloc[0]['category']
                    worst_category = category_perf.iloc[-1]['category']
                    
                    if category_perf.iloc[0]['viral_score'] > category_perf.iloc[-1]['viral_score'] * 1.5:
                        recommendations.append(
                            f"Focus more on {best_category} content which outperforms {worst_category} "
                            f"({category_perf.iloc[0]['viral_score']:.1f} vs {category_perf.iloc[-1]['viral_score']:.1f} viral score)"
                        )
                
                # Recommend best duration
                if not duration_perf.empty and len(duration_perf) > 1:
                    best_duration = int(duration_perf.iloc[0]['clip_duration'])
                    
                    recommendations.append(
                        f"{best_duration}-second clips have the best performance with "
                        f"{duration_perf.iloc[0]['viral_score']:.1f} average viral score"
                    )
                
                # Check if shorter or longer videos perform better
                if not duration_perf.empty and len(duration_perf) > 1:
                    # Add clip_duration as numeric column and sort
                    duration_perf = duration_perf.sort_values('clip_duration')
                    
                    # Check for trend
                    if duration_perf.iloc[-1]['viral_score'] > duration_perf.iloc[0]['viral_score'] * 1.3:
                        recommendations.append(
                            "Longer videos are performing significantly better. Consider increasing clip duration."
                        )
                    elif duration_perf.iloc[0]['viral_score'] > duration_perf.iloc[-1]['viral_score'] * 1.3:
                        recommendations.append(
                            "Shorter videos are performing significantly better. Consider decreasing clip duration."
                        )
            else:
                recommendations.append(
                    "Need more data for reliable recommendations (at least 5 videos)"
                )
            
            # Save report data
            report = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_videos': total_videos,
                'total_views': int(total_views),
                'total_likes': int(total_likes),
                'total_comments': int(total_comments),
                'avg_viral_score': float(avg_viral_score),
                'categories': category_perf.to_dict('records'),
                'durations': duration_perf.to_dict('records'),
                'top_videos': top_videos.to_dict('records'),
                'recommendations': recommendations
            }
            
            # Save report to file
            report_file = self.reports_dir / f"report_{end_date.strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Performance report saved to {report_file}")
            
            # Generate charts
            self._generate_performance_charts(videos_df, end_date)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {
                'error': str(e),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'recommendations': ['Error generating report']
            }
    
    def _generate_performance_charts(self, df, date):
        """
        Generate performance charts from video data.
        
        Args:
            df (DataFrame): Video performance data
            date (datetime): Date for the report
        """
        try:
            date_str = date.strftime('%Y%m%d')
            
            # 1. Category Performance Chart
            if 'category' in df.columns and len(df) > 0:
                fig = Figure(figsize=(10, 6))
                canvas = FigureCanvas(fig)
                ax = fig.add_subplot(111)
                
                category_data = df.groupby('category').agg({
                    'viral_score': 'mean',
                    'views': 'sum'
                }).reset_index()
                
                category_data = category_data.sort_values('viral_score', ascending=False)
                
                # Create bar chart
                bars = ax.bar(category_data['category'], category_data['viral_score'])
                
                # Add data labels
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width()/2.,
                        height + 1,
                        f'{height:.1f}',
                        ha='center', va='bottom',
                        rotation=0
                    )
                
                ax.set_title('Average Viral Score by Category')
                ax.set_xlabel('Category')
                ax.set_ylabel('Viral Score')
                ax.set_ylim(0, max(100, category_data['viral_score'].max() * 1.2))
                fig.tight_layout()
                
                # Save chart
                chart_path = self.reports_dir / f"category_chart_{date_str}.png"
                fig.savefig(chart_path)
                self.logger.debug(f"Category chart saved to {chart_path}")
            
            # 2. Duration Performance Chart
            if 'clip_duration' in df.columns and len(df) > 0:
                fig = Figure(figsize=(10, 6))
                canvas = FigureCanvas(fig)
                ax = fig.add_subplot(111)
                
                duration_data = df.groupby('clip_duration').agg({
                    'viral_score': 'mean'
                }).reset_index()
                
                duration_data = duration_data.sort_values('clip_duration')
                
                # Create bar chart
                bars = ax.bar(duration_data['clip_duration'], duration_data['viral_score'])
                
                # Add data labels
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width()/2.,
                        height + 1,
                        f'{height:.1f}',
                        ha='center', va='bottom',
                        rotation=0
                    )
                
                ax.set_title('Average Viral Score by Clip Duration')
                ax.set_xlabel('Duration (seconds)')
                ax.set_ylabel('Viral Score')
                ax.set_ylim(0, max(100, duration_data['viral_score'].max() * 1.2))
                fig.tight_layout()
                
                # Save chart
                chart_path = self.reports_dir / f"duration_chart_{date_str}.png"
                fig.savefig(chart_path)
                self.logger.debug(f"Duration chart saved to {chart_path}")
            
            # 3. Daily Performance Chart
            if 'upload_time' in df.columns and len(df) > 0:
                fig = Figure(figsize=(12, 6))
                canvas = FigureCanvas(fig)
                ax = fig.add_subplot(111)
                
                # Convert upload_time to datetime
                df['upload_date'] = pd.to_datetime(df['upload_time']).dt.date
                
                daily_data = df.groupby('upload_date').agg({
                    'viral_score': 'mean',
                    'views': 'sum',
                    'upload_id': 'count'
                }).reset_index()
                daily_data = daily_data.rename(columns={'upload_id': 'videos'})
                
                # Plot data
                ax.plot(
                    daily_data['upload_date'], 
                    daily_data['viral_score'], 
                    marker='o',
                    linewidth=2,
                    label='Viral Score'
                )
                
                # Add right y-axis for views
                ax2 = ax.twinx()
                ax2.plot(
                    daily_data['upload_date'],
                    daily_data['views'],
                    marker='s',
                    color='red',
                    linewidth=2,
                    label='Views'
                )
                
                # Add annotations
                for i, row in daily_data.iterrows():
                    ax.annotate(
                        f"{row['videos']}",
                        (row['upload_date'], row['viral_score']),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center'
                    )
                
                ax.set_title('Daily Performance Metrics')
                ax.set_xlabel('Date')
                ax.set_ylabel('Viral Score')
                ax2.set_ylabel('Views')
                
                # Add legends
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                # Format x-axis dates
                fig.autofmt_xdate()
                fig.tight_layout()
                
                # Save chart
                chart_path = self.reports_dir / f"daily_chart_{date_str}.png"
                fig.savefig(chart_path)
                self.logger.debug(f"Daily performance chart saved to {chart_path}")
                
        except Exception as e:
            self.logger.error(f"Error generating performance charts: {e}")
    
    def update_content_strategy(self):
        """
        Update content strategy based on performance data.
        
        Returns:
            dict: Updated strategy parameters
        """
        try:
            # Generate a performance report for the last 30 days
            report = self.generate_performance_report(days=30)
            
            if report.get('total_videos', 0) < 5:
                self.logger.info("Not enough videos to update content strategy")
                return None
                
            strategy_updates = {}
            
            # Update category priorities
            categories = report.get('categories', [])
            if categories:
                # Sort by viral score
                categories.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
                
                # Update category priorities in config
                for category in categories:
                    cat_name = category.get('category')
                    if cat_name in self.config['youtube_search']['categories']:
                        # Enable high-performing categories, disable low-performing ones
                        threshold = report.get('avg_viral_score', 50) * 0.8
                        should_enable = category.get('viral_score', 0) >= threshold
                        
                        self.config['youtube_search']['categories'][cat_name] = should_enable
                        
                        status = "enabled" if should_enable else "disabled"
                        self.logger.info(
                            f"Category '{cat_name}' {status} with score {category.get('viral_score'):.1f}"
                        )
                        
                strategy_updates['categories'] = self.config['youtube_search']['categories']
            
            # Update clip duration priorities
            durations = report.get('durations', [])
            if durations:
                # Sort by viral score
                durations.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
                
                # Update duration priorities in config
                for duration in durations:
                    dur_val = str(int(duration.get('clip_duration', 0)))
                    if dur_val in self.config['video_processing']['clip_durations']:
                        # Enable high-performing durations, disable low-performing ones
                        threshold = report.get('avg_viral_score', 50) * 0.8
                        should_enable = duration.get('viral_score', 0) >= threshold
                        
                        self.config['video_processing']['clip_durations'][dur_val] = should_enable
                        
                        status = "enabled" if should_enable else "disabled"
                        self.logger.info(
                            f"Duration '{dur_val}s' {status} with score {duration.get('viral_score'):.1f}"
                        )
                        
                strategy_updates['durations'] = self.config['video_processing']['clip_durations']
            
            # Update upload times based on best performing times
            # This would require more detailed analytics from YouTube API
            # For now, we'll use a placeholder
            
            # Save updated config
            if strategy_updates:
                self.logger.info("Content strategy updated based on performance data")
                return strategy_updates
            else:
                self.logger.info("No changes made to content strategy")
                return None
                
        except Exception as e:
            self.logger.error(f"Error updating content strategy: {e}")
            return None
    
    def export_data_to_csv(self, days=90, output_path=None):
        """
        Export performance data to CSV for external analysis.
        
        Args:
            days (int): Number of days of data to export
            output_path (str, optional): Path to save the CSV file
            
        Returns:
            str: Path to the exported CSV file
        """
        try:
            # Set default output path if not provided
            if output_path is None:
                date_str = datetime.datetime.now().strftime('%Y%m%d')
                output_path = self.reports_dir / f"performance_data_{date_str}.csv"
            
            # Get date range
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days)
            
            # Query for performance data
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
                a.viral_score,
                a.timestamp as analytics_timestamp
            FROM uploaded_videos uv
            JOIN processed_clips pc ON uv.clip_id = pc.id
            JOIN source_videos sv ON pc.source_id = sv.id
            JOIN analytics a ON uv.id = a.upload_id
            WHERE uv.upload_time BETWEEN ? AND ?
            ORDER BY uv.upload_time DESC
            """
            
            videos = self.db.execute_query(
                query, 
                (start_date.isoformat(), end_date.isoformat())
            )
            
            if not videos:
                self.logger.info(f"No videos found for export in the last {days} days")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(videos)
            
            # Save to CSV
            df.to_csv(output_path, index=False)
            
            self.logger.info(f"Exported {len(df)} videos to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error exporting data to CSV: {e}")
            return None
    
    def analyze_recent_trends(self, days=7, min_videos=20, generate_report=True):
        """
        Analyze recent viral shorts trends and optionally generate reports
        
        Args:
            days (int): Number of recent days to analyze
            min_videos (int): Minimum number of videos to analyze or search for more
            generate_report (bool): Whether to generate a report
            
        Returns:
            dict: Trend analysis results
        """
        self.logger.info(f"Analyzing viral shorts trends for the past {days} days")
        
        # Get recent videos from database
        recent_videos = self._get_recent_videos(days)
        
        # If not enough videos, search for more
        if len(recent_videos) < min_videos:
            self.logger.info(f"Only found {len(recent_videos)} videos in database, searching for more...")
            additional_videos = self._search_additional_videos(min_videos - len(recent_videos))
            # Add found videos to the database and the list
            for video in additional_videos:
                self.db.insert_video_data(video)
            recent_videos.extend(additional_videos)
            
        if not recent_videos:
            self.logger.warning("No videos found for trend analysis")
            return {}
            
        # Analyze trends
        trend_analysis = self.shorts_finder.analyze_trends(recent_videos)
        
        # Generate report if requested
        if generate_report and trend_analysis:
            today = datetime.datetime.now().strftime("%Y%m%d")
            report_paths = self.report_generator.generate_report(
                trend_analysis, 
                filename_prefix=f"viral_trends_{today}"
            )
            
            # Export CSV data
            csv_path = self.report_generator.generate_csv_export(
                trend_analysis, 
                filename=f"viral_trends_{today}.csv"
            )
            
            # Add paths to the analysis results
            trend_analysis['report_paths'] = {
                'html': str(report_paths.get('html')),
                'json': str(report_paths.get('json')),
                'csv': str(csv_path)
            }
            
        return trend_analysis
        
    def _get_recent_videos(self, days):
        """
        Get videos from the database added in the last N days
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            list: List of video data dictionaries
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_timestamp = cutoff_date.timestamp()
        
        query = "SELECT * FROM videos WHERE date_added > ? AND is_short = 1"
        results = self.db.execute_query(query, (cutoff_timestamp,))
        
        videos = []
        for result in results:
            # Convert database row to video dictionary
            video = {
                'youtube_id': result[1],
                'title': result[2],
                'channel': result[3],
                'duration': result[4],
                'views': result[5],
                'likes': result[6],
                'comments': result[7],
                'thumbnail_url': result[8],
                'publish_date': result[9],
                'category': result[10],
                'viral_score': result[11] if len(result) > 11 else 0,
                'search_query': result[12] if len(result) > 12 else "unknown"
            }
            videos.append(video)
            
        self.logger.info(f"Found {len(videos)} recent videos in database")
        return videos
        
    def _search_additional_videos(self, count):
        """
        Search for additional viral shorts to augment analysis
        
        Args:
            count (int): Minimum number of videos to find
            
        Returns:
            list: List of video data dictionaries
        """
        self.logger.info(f"Searching for {count} additional viral shorts...")
        
        # Get videos with balanced categories
        max_per_category = max(3, count // 5)  # At least 3 per category, but try to balance
        
        videos = []
        categories = self.shorts_finder.SEARCH_QUERIES.keys()
        
        for category in categories:
            if len(videos) >= count:
                break
                
            category_videos = self.shorts_finder.search_viral_shorts(
                category=category,
                max_results=max_per_category
            )
            
            videos.extend(category_videos)
            
        return videos[:count]  # Return only up to the requested count
        
    def generate_category_report(self, category, days=30, min_videos=10):
        """
        Generate a report for a specific category
        
        Args:
            category (str): Category to analyze
            days (int): Number of recent days to analyze
            min_videos (int): Minimum number of videos to analyze or search for more
            
        Returns:
            dict: Report paths
        """
        self.logger.info(f"Generating report for category: {category}")
        
        # Get videos for this category
        query = """
            SELECT * FROM videos 
            WHERE category = ? AND date_added > ? AND is_short = 1
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_timestamp = cutoff_date.timestamp()
        
        results = self.db.execute_query(query, (category, cutoff_timestamp))
        
        videos = []
        for result in results:
            # Convert database row to video dictionary
            video = {
                'youtube_id': result[1],
                'title': result[2],
                'channel': result[3],
                'duration': result[4],
                'views': result[5],
                'likes': result[6],
                'comments': result[7],
                'thumbnail_url': result[8],
                'publish_date': result[9],
                'category': result[10],
                'viral_score': result[11] if len(result) > 11 else 0,
                'search_query': result[12] if len(result) > 12 else "unknown"
            }
            videos.append(video)
            
        # If not enough videos, search for more in this category
        if len(videos) < min_videos:
            additional_videos = self.shorts_finder.search_viral_shorts(
                category=category,
                max_results=min_videos - len(videos)
            )
            
            # Add found videos to the database and the list
            for video in additional_videos:
                self.db.insert_video_data(video)
            videos.extend(additional_videos)
            
        if not videos:
            self.logger.warning(f"No videos found for category: {category}")
            return {}
            
        # Analyze trends
        trend_analysis = self.shorts_finder.analyze_trends(videos)
        
        # Generate report
        today = datetime.datetime.now().strftime("%Y%m%d")
        report_paths = self.report_generator.generate_report(
            trend_analysis, 
            filename_prefix=f"category_{category}_{today}"
        )
        
        return report_paths
