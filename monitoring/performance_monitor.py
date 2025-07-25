"""
📈 Performance Monitor per ViralShortsAI
Sistema di monitoraggio avanzato per tracking performance video
"""

import os
import json
import logging
import datetime
import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path
import requests
import time

class PerformanceMonitor:
    """
    Sistema di monitoraggio performance video con analytics avanzati
    """
    
    def __init__(self, db_path: str = "data/viral_shorts.db"):
        self.db_path = db_path
        self.logger = logging.getLogger('ViralShortsAI.PerformanceMonitor')
        self.youtube_service = None
        self._setup_youtube_api()
    
    def _setup_youtube_api(self):
        """Setup YouTube API client"""
        try:
            from upload.youtube_uploader import YouTubeUploader
            uploader = YouTubeUploader()
            self.youtube_service = uploader.youtube_service
            self.youtube_api_available = True
            self.logger.info("✅ YouTube API client initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ YouTube API not available: {e}")
            self.youtube_service = None
            self.youtube_api_available = False
    
    def update_all_video_metrics(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Aggiorna metriche per tutti i video pubblicati negli ultimi X giorni
        """
        return self.update_video_metrics(days_back)
    
    def update_video_metrics(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Aggiorna metriche per video pubblicati negli ultimi X giorni
        """
        try:
            # Ottieni video da monitorare
            videos_to_monitor = self._get_videos_to_monitor(days_back)
            
            updated_count = 0
            failed_count = 0
            
            for video in videos_to_monitor:
                try:
                    # Ottieni metriche aggiornate
                    metrics = self._fetch_video_metrics(video['youtube_video_id'])
                    
                    if metrics:
                        # Aggiorna database
                        self._update_video_analytics(video['id'], metrics)
                        updated_count += 1
                        self.logger.debug(f"Updated metrics for video {video['youtube_video_id']}")
                    else:
                        failed_count += 1
                        
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Error updating metrics for video {video.get('youtube_video_id', 'unknown')}: {e}")
                    failed_count += 1
            
            # Genera report di monitoraggio
            self._generate_monitoring_report(updated_count, failed_count)
            
            result = {
                "updated_videos": updated_count,
                "failed_videos": failed_count,
                "total_monitored": len(videos_to_monitor),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.logger.info(f"📈 Performance monitoring completed: {updated_count}/{len(videos_to_monitor)} videos updated")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Performance monitoring failed: {e}")
            return {"error": str(e)}
    
    def _get_videos_to_monitor(self, days_back: int) -> List[Dict[str, Any]]:
        """Ottieni video da monitorare dal database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query per video pubblicati negli ultimi X giorni
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
            
            cursor.execute("""
                SELECT id, youtube_video_id, title, upload_date
                FROM uploaded_videos 
                WHERE upload_date >= ? 
                AND youtube_video_id IS NOT NULL
                AND youtube_video_id != ''
                ORDER BY upload_date DESC
            """, (cutoff_date.isoformat(),))
            
            videos = []
            for row in cursor.fetchall():
                videos.append({
                    "id": row[0],
                    "youtube_video_id": row[1],
                    "title": row[2],
                    "upload_date": row[3]
                })
            
            conn.close()
            return videos
            
        except Exception as e:
            self.logger.error(f"Error fetching videos to monitor: {e}")
            return []
    
    def _fetch_video_metrics(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Fetch metriche da YouTube API"""
        if not self.youtube_service:
            return self._get_fallback_metrics(video_id)
        
        try:
            # Request per statistics del video
            request = self.youtube_service.videos().list(
                part="statistics,snippet",
                id=video_id
            )
            response = request.execute()
            
            if response['items']:
                item = response['items'][0]
                stats = item['statistics']
                snippet = item['snippet']
                
                # Estrai metriche
                metrics = {
                    "views": int(stats.get('viewCount', 0)),
                    "likes": int(stats.get('likeCount', 0)),
                    "comments": int(stats.get('commentCount', 0)),
                    "shares": int(stats.get('shareCount', 0)) if 'shareCount' in stats else 0,
                    "duration": snippet.get('duration', ''),
                    "tags": snippet.get('tags', []),
                    "category_id": snippet.get('categoryId', ''),
                    "published_at": snippet.get('publishedAt', ''),
                    "last_updated": datetime.datetime.now().isoformat()
                }
                
                # Calcola metriche derivate
                metrics["engagement_rate"] = self._calculate_engagement_rate(metrics)
                metrics["viral_score"] = self._calculate_viral_score(metrics)
                
                return metrics
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching metrics from YouTube API: {e}")
            return self._get_fallback_metrics(video_id)
    
    def _get_fallback_metrics(self, video_id: str) -> Dict[str, Any]:
        """Metriche di fallback quando API non disponibile"""
        return {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "engagement_rate": 0.0,
            "viral_score": 0.0,
            "last_updated": datetime.datetime.now().isoformat(),
            "source": "fallback"
        }
    
    def _calculate_engagement_rate(self, metrics: Dict[str, Any]) -> float:
        """Calcola engagement rate"""
        views = metrics.get('views', 0)
        if views == 0:
            return 0.0
        
        engagements = (
            metrics.get('likes', 0) + 
            metrics.get('comments', 0) + 
            metrics.get('shares', 0)
        )
        
        return round((engagements / views) * 100, 2)
    
    def _calculate_viral_score(self, metrics: Dict[str, Any]) -> float:
        """Calcola punteggio virale basato su metriche"""
        views = metrics.get('views', 0)
        likes = metrics.get('likes', 0)
        comments = metrics.get('comments', 0)
        engagement_rate = metrics.get('engagement_rate', 0)
        
        # Formula punteggio virale (personalizzabile)
        viral_score = (
            (views / 1000) * 0.4 +  # Peso visualizzazioni
            (likes / 100) * 0.3 +   # Peso likes
            (comments / 10) * 0.2 + # Peso commenti
            engagement_rate * 0.1   # Peso engagement rate
        )
        
        return min(round(viral_score, 2), 100.0)  # Max 100
    
    def _update_video_analytics(self, video_id: int, metrics: Dict[str, Any]):
        """Aggiorna analytics nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert o update nella tabella analytics
            cursor.execute("""
                INSERT OR REPLACE INTO analytics 
                (video_id, views, likes, comments, shares, engagement_rate, viral_score, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_id,
                metrics.get('views', 0),
                metrics.get('likes', 0),
                metrics.get('comments', 0),
                metrics.get('shares', 0),
                metrics.get('engagement_rate', 0.0),
                metrics.get('viral_score', 0.0),
                metrics.get('last_updated', datetime.datetime.now().isoformat())
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating analytics in database: {e}")
    
    def _generate_monitoring_report(self, updated_count: int, failed_count: int):
        """Genera report di monitoraggio"""
        try:
            report_dir = Path("data/reports")
            report_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now()
            report_data = {
                "timestamp": timestamp.isoformat(),
                "updated_videos": updated_count,
                "failed_videos": failed_count,
                "total_monitored": updated_count + failed_count,
                "success_rate": round((updated_count / (updated_count + failed_count)) * 100, 2) if (updated_count + failed_count) > 0 else 0
            }
            
            # Salva report JSON
            report_file = report_dir / f"monitoring_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📊 Monitoring report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating monitoring report: {e}")
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Ottieni riassunto performance degli ultimi X giorni"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            # Query per statistiche aggregate
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_videos,
                    SUM(a.views) as total_views,
                    SUM(a.likes) as total_likes,
                    SUM(a.comments) as total_comments,
                    AVG(a.engagement_rate) as avg_engagement,
                    AVG(a.viral_score) as avg_viral_score,
                    MAX(a.views) as max_views,
                    MAX(a.viral_score) as max_viral_score
                FROM analytics a
                JOIN uploaded_videos u ON a.video_id = u.id
                WHERE u.upload_date >= ?
            """, (cutoff_date.isoformat(),))
            
            row = cursor.fetchone()
            
            summary = {
                "period_days": days,
                "total_videos": row[0] if row[0] else 0,
                "total_views": row[1] if row[1] else 0,
                "total_likes": row[2] if row[2] else 0,
                "total_comments": row[3] if row[3] else 0,
                "avg_engagement_rate": round(row[4], 2) if row[4] else 0.0,
                "avg_viral_score": round(row[5], 2) if row[5] else 0.0,
                "max_views": row[6] if row[6] else 0,
                "max_viral_score": round(row[7], 2) if row[7] else 0.0,
                "generated_at": datetime.datetime.now().isoformat()
            }
            
            conn.close()
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating performance summary: {e}")
            return {"error": str(e)}
    
    def get_top_performing_videos(self, limit: int = 10, metric: str = 'viral_score') -> List[Dict[str, Any]]:
        """Ottieni top video per una metrica specifica"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            valid_metrics = ['views', 'likes', 'comments', 'engagement_rate', 'viral_score']
            if metric not in valid_metrics:
                metric = 'viral_score'
            
            cursor.execute(f"""
                SELECT 
                    u.title,
                    u.youtube_video_id,
                    a.views,
                    a.likes,
                    a.comments,
                    a.engagement_rate,
                    a.viral_score,
                    u.upload_date
                FROM analytics a
                JOIN uploaded_videos u ON a.video_id = u.id
                ORDER BY a.{metric} DESC
                LIMIT ?
            """, (limit,))
            
            videos = []
            for row in cursor.fetchall():
                videos.append({
                    "title": row[0],
                    "youtube_video_id": row[1],
                    "views": row[2],
                    "likes": row[3],
                    "comments": row[4],
                    "engagement_rate": row[5],
                    "viral_score": row[6],
                    "upload_date": row[7]
                })
            
            conn.close()
            return videos
            
        except Exception as e:
            self.logger.error(f"Error getting top performing videos: {e}")
            return []

if __name__ == "__main__":
    # Test del monitor
    logging.basicConfig(level=logging.INFO)
    
    monitor = PerformanceMonitor()
    
    # Test aggiornamento metriche
    result = monitor.update_video_metrics(days_back=7)
    print("Update result:", result)
    
    # Test summary
    summary = monitor.get_performance_summary(days=7)
    print("Performance summary:", summary)
