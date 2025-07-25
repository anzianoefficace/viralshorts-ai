#!/usr/bin/env python3
"""
YouTube Analytics Real-time Updater
Aggiorna automaticamente le views e metriche dei video caricati
"""

import sqlite3
import os
import json
import time
from datetime import datetime
import logging

class YouTubeAnalyticsUpdater:
    """Classe per aggiornare automaticamente le analytics da YouTube"""
    
    def __init__(self):
        self.db_path = os.path.join('data', 'viral_shorts.db')
        self.logger = logging.getLogger('ViralShortsAI.Analytics')
        
    def get_uploaded_videos(self):
        """Ottieni lista video caricati dal database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, youtube_id, title, upload_time 
                FROM uploaded_videos 
                WHERE youtube_id IS NOT NULL
            ''')
            
            videos = cursor.fetchall()
            conn.close()
            return videos
            
        except Exception as e:
            self.logger.error(f"Errore ottenimento video: {e}")
            return []
    
    def update_views_manual(self, youtube_id, current_views):
        """Aggiorna manualmente le views per un video"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Controlla se esiste già un record analytics
            cursor.execute('''
                SELECT id FROM analytics 
                WHERE upload_id = (
                    SELECT id FROM uploaded_videos WHERE youtube_id = ?
                )
                ORDER BY timestamp DESC LIMIT 1
            ''', (youtube_id,))
            
            existing = cursor.fetchone()
            
            # Ottieni upload_id
            cursor.execute('SELECT id FROM uploaded_videos WHERE youtube_id = ?', (youtube_id,))
            upload_result = cursor.fetchone()
            
            if not upload_result:
                self.logger.error(f"Video {youtube_id} non trovato nel database")
                conn.close()
                return False
            
            upload_id = upload_result[0]
            
            if existing:
                # Aggiorna record esistente
                cursor.execute('''
                    UPDATE analytics 
                    SET views = ?, timestamp = ?
                    WHERE id = ?
                ''', (current_views, datetime.now().isoformat(), existing[0]))
            else:
                # Crea nuovo record
                cursor.execute('''
                    INSERT INTO analytics (upload_id, timestamp, views, likes, comments, retention_rate, ctr, viral_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (upload_id, datetime.now().isoformat(), current_views, 0, 0, 0.0, 0.0, current_views))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Views aggiornate per {youtube_id}: {current_views}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore aggiornamento views: {e}")
            return False
    
    def get_current_analytics(self):
        """Ottieni analytics attuali dal database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    uv.youtube_id,
                    uv.title,
                    COALESCE(a.views, 0) as views,
                    COALESCE(a.likes, 0) as likes,
                    COALESCE(a.comments, 0) as comments,
                    a.timestamp
                FROM uploaded_videos uv
                LEFT JOIN analytics a ON uv.id = a.upload_id
                ORDER BY a.timestamp DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Errore ottenimento analytics: {e}")
            return []
    
    def update_real_analytics(self):
        """Aggiorna analytics con dati reali (manuale per ora)"""
        print("🔄 Aggiornamento Analytics...")
        
        videos = self.get_uploaded_videos()
        
        for video in videos:
            video_id, youtube_id, title, upload_time = video
            
            print(f"📹 Video: {title[:50]}...")
            print(f"   YouTube ID: {youtube_id}")
            
            # Per ora aggiorniamo manualmente con le 6 views
            if youtube_id == "1tuQcuFKecA":
                self.update_views_manual(youtube_id, 6)
                print("   ✅ Views aggiornate: 6")
            
        print("✅ Aggiornamento completato!")

def main():
    """Script principale per aggiornare analytics"""
    print("🚀 YouTube Analytics Updater")
    print("=" * 40)
    
    updater = YouTubeAnalyticsUpdater()
    
    # Mostra analytics attuali
    print("\n📊 Analytics Attuali:")
    analytics = updater.get_current_analytics()
    
    for record in analytics:
        youtube_id, title, views, likes, comments, timestamp = record
        print(f"   📹 {title[:40]}...")
        print(f"       Views: {views}, Likes: {likes}, Comments: {comments}")
        print(f"       Ultimo aggiornamento: {timestamp}")
    
    # Aggiorna dati
    print("\n🔄 Aggiornamento in corso...")
    updater.update_real_analytics()
    
    # Mostra analytics aggiornati
    print("\n📊 Analytics Aggiornati:")
    analytics = updater.get_current_analytics()
    
    for record in analytics:
        youtube_id, title, views, likes, comments, timestamp = record
        print(f"   📹 {title[:40]}...")
        print(f"       Views: {views}, Likes: {likes}, Comments: {comments}")
        print(f"       Ultimo aggiornamento: {timestamp}")

if __name__ == "__main__":
    main()
