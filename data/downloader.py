"""
YouTube Shorts downloader module for ViralShortsAI.
Handles searching for viral shorts, checking copyright status, and downloading videos.
"""

import os
import json
import time
import datetime
import re
import random
from pathlib import Path

import googleapiclient.discovery
from googleapiclient.errors import HttpError
import yt_dlp
import requests
from dotenv import load_dotenv

from utils import app_logger

# Load environment variables
load_dotenv()

class YouTubeShortsFinder:
    """
    Class to search for and download viral YouTube Shorts.
    Uses YouTube Data API v3 to find trending shorts and yt-dlp to download them.
    """
    
    # Lista di query di ricerca categorizzate per diversificare i risultati
    SEARCH_QUERIES = {
        "Entertainment": [
            "funny fails", "tiktok compilation", "comedy shorts", "satisfying videos", 
            "amazing talent", "magic tricks", "pranks", "stand up comedy",
            "funny moments", "bloopers", "celebrities", "reaction videos"
        ],
        "News": [
            "viral moments", "daily facts", "trending topics", "interviews", 
            "current events", "news updates", "tech news", "sports highlights",
            "celebrity news", "breaking stories", "viral news", "world updates"
        ],
        "Sports": [
            "gaming highlights", "fitness motivation", "sports moments", "workout tips", 
            "exercise routines", "athletic feats", "extreme sports", "football skills",
            "basketball tricks", "soccer goals", "sports fails", "gaming moments"
        ],
        "Curiosity": [
            "life hacks", "tech tips", "ai memes", "science facts", 
            "how to", "did you know", "fun facts", "learning hacks",
            "mind blowing", "psychology facts", "historical moments", "space facts"
        ],
        "Lifestyle": [
            "beauty hacks", "fashion trends", "cute animals", "cooking tips", 
            "travel moments", "dance challenge", "food hacks", "DIY crafts",
            "home decor", "outfit ideas", "makeup tutorials", "relationship advice"
        ]
    }
    
    def __init__(self, config, db):
        """
        Initialize the YouTube Shorts finder.
        
        Args:
            config (dict): Configuration dictionary
            db: Database instance
        """
        self.config = config
        self.db = db
        self.logger = app_logger
        
        # API client setup
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            self.logger.error("YouTube API key not found in environment variables")
            raise ValueError("YouTube API key is required")
        
        self.youtube = googleapiclient.discovery.build(
            'youtube', 'v3', developerKey=api_key
        )
        
        # Create download directory if it doesn't exist
        try:
            downloads_path = self.config.get('paths', {}).get('downloads', 'data/downloads')
            self.logger.debug(f"[DEBUG] Percorso downloads configurato: {downloads_path}")
            
            self.download_dir = Path(downloads_path)
            self.download_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Directory di download creata/verificata: {self.download_dir}")
        except Exception as e:
            self.logger.error(f"Errore nella configurazione della directory di download: {e}")
            # Usa una directory predefinita in caso di errore
            self.download_dir = Path("data/downloads")
            self.download_dir.mkdir(parents=True, exist_ok=True)
            self.logger.warning(f"Usando directory di fallback per i download: {self.download_dir}")
        
        self.logger.info("YouTube Shorts finder initialized")
    
    def search_viral_shorts(self, max_results=50):
        """
        Search for viral YouTube Shorts based on configuration criteria.
        
        Args:
            max_results (int): Maximum number of shorts to find
            
        Returns:
            list: List of video IDs and metadata
        """
        self.logger.info(f"Searching for viral YouTube Shorts (max: {max_results})")
        
        # Get active categories from config
        categories = [
            cat for cat, active in self.config['youtube_search']['categories'].items()
            if active
        ]
        
        if not categories:
            self.logger.warning("No categories selected, using all categories")
            categories = list(self.config['youtube_search']['categories'].keys())
            
        self.logger.info(f"Searching in categories: {', '.join(categories)}")
        
        # Calculate published after date
        hours = self.config['youtube_search']['published_within_hours']
        published_after = datetime.datetime.now() - datetime.timedelta(hours=hours)
        published_after_rfc3339 = published_after.isoformat("T") + "Z"
        
        min_views = self.config['youtube_search']['min_views']
        self.logger.info(f"Filtering for shorts with at least {min_views} views, " +
                      f"published in the last {hours} hours")
        
        all_videos = []
        
        # Search in each category
        for category in categories:
            try:
                # Seleziona alcune query specifiche per questa categoria o query generiche
                category_specific_queries = self.SEARCH_QUERIES.get(category, [])
                
                # Se non ci sono query specifiche per questa categoria, usa quelle generiche
                if not category_specific_queries:
                    # Crea una lista di tutte le query da tutte le categorie
                    all_queries = []
                    for cat_queries in self.SEARCH_QUERIES.values():
                        all_queries.extend(cat_queries)
                    search_queries = random.sample(all_queries, min(3, len(all_queries)))
                else:
                    # Usa le query specifiche per questa categoria
                    search_queries = random.sample(category_specific_queries, min(3, len(category_specific_queries)))
                
                category_videos = []
                
                for query in search_queries:
                    full_query = f"{category} {query} shorts"
                    self.logger.debug(f"Searching with query: '{full_query}'")
                    
                    # First search for shorts
                    search_response = self.youtube.search().list(
                        q=full_query,
                        type='video',
                        part='id,snippet',
                        maxResults=50,
                        videoDefinition='high',
                        videoDuration='short',  # Less than 4 minutes
                        publishedAfter=published_after_rfc3339,
                        regionCode='US',  # Can be customized based on target audience
                        relevanceLanguage=self.config['app_settings']['selected_language'],
                        order='viewCount'  # Sort by view count
                    ).execute()
                    
                    # Log the response for debugging
                    if not search_response.get('items'):
                        self.logger.debug(f"No results for query '{full_query}'. API Response: {json.dumps(search_response, indent=2)}")
                        continue
                        
                    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                    
                    if not video_ids:
                        self.logger.warning(f"No shorts found for query: {full_query}")
                        continue
                        
                    # Get detailed video information including statistics
                    videos_response = self.youtube.videos().list(
                        part='snippet,contentDetails,statistics,status',
                        id=','.join(video_ids)
                    ).execute()
                    
                    # Filter for vertical shorts with enough views
                    for video in videos_response.get('items', []):
                        try:
                            # Extract view count
                            view_count = int(video['statistics'].get('viewCount', 0))
                            
                            # Check if it has enough views
                            if view_count < min_views:
                                continue
                                
                            # Extract duration
                            duration = self._parse_duration(video['contentDetails']['duration'])
                            
                            # Check if it's a short (duration <= max_duration)
                            max_duration = self.config['youtube_search']['max_duration']
                            if duration > max_duration:
                                continue
                                
                            # Algoritmo migliorato per il rilevamento degli Shorts
                            description = video['snippet'].get('description', '').lower()
                            title = video['snippet'].get('title', '').lower()
                            tags = video['snippet'].get('tags', [])
                            
                            # Sistema di punteggio per determinare se è uno Short
                            shorts_score = 0
                            
                            # Indicatori nei metadati del video
                            shorts_indicators = ['#shorts', '#short', '#youtubeshorts', '#shortvideo', '#shortsvideo', 'shorts', 'short video']
                            
                            # Verifica presenza di indicatori nel titolo (peso maggiore)
                            for indicator in shorts_indicators:
                                if indicator in title:
                                    shorts_score += 3
                                    break
                            
                            # Verifica presenza di indicatori nella descrizione
                            for indicator in shorts_indicators:
                                if indicator in description:
                                    shorts_score += 2
                                    break
                                    
                            # Verifica presenza di indicatori nei tag
                            for tag in tags:
                                if any(indicator in tag.lower() for indicator in shorts_indicators):
                                    shorts_score += 1
                                    break
                            
                            # Verifica la durata (forte indicatore di Shorts)
                            if duration <= 60:
                                shorts_score += 4
                            elif duration <= 90:
                                shorts_score += 2
                                
                            # Verifica del formato verticale (se disponibile)
                            if 'height' in video.get('contentDetails', {}) and 'width' in video.get('contentDetails', {}):
                                height = int(video['contentDetails']['height'])
                                width = int(video['contentDetails']['width'])
                                if height > width:  # Formato verticale
                                    shorts_score += 3
                                    
                            # Decidi se è uno Short in base al punteggio totale
                            is_shorts = shorts_score >= 4  # Soglia minima
                            
                            if not is_shorts:
                                self.logger.debug(f"Video {video['id']} doesn't appear to be a Short (score: {shorts_score})")
                                continue
                                
                            self.logger.debug(f"Video {video['id']} is a Short with detection score: {shorts_score}")
                                
                            # Initialize license_type
                            license_type = video['status'].get('license', '')
                            
                            # Check license and copyright status
                            if self.config['youtube_search']['copyright_filter']:
                                # The standard YouTube license doesn't allow reuse
                                can_reuse = (license_type == 'creativeCommon')
                                
                                if not can_reuse:
                                    self.logger.debug(f"Video {video['id']} has copyright restrictions")
                                    continue
                            
                            # Calcola il punteggio virale del video
                            engagement_score = self._calculate_viral_score(video, view_count)
                            
                            # Format video data
                            video_data = {
                                'youtube_id': video['id'],
                                'title': video['snippet']['title'],
                                'channel': video['snippet']['channelTitle'],
                                'url': f"https://www.youtube.com/shorts/{video['id']}",
                                'views': view_count,
                                'likes': int(video['statistics'].get('likeCount', 0)),
                                'comments': int(video['statistics'].get('commentCount', 0)),
                                'duration': duration,
                                'category': category,
                                'search_query': query,
                                'copyright_status': 'creative_commons' if license_type == 'creativeCommon' else 'standard',
                                'viral_score': engagement_score,
                                'metadata': {
                                    'description': video['snippet'].get('description', ''),
                                    'tags': video['snippet'].get('tags', []),
                                    'published_at': video['snippet']['publishedAt'],
                                    'thumbnail': video['snippet']['thumbnails'].get('high', {}).get('url', '')
                                }
                            }
                            
                            # Stampa informazioni sul video trovato
                            self.logger.info(f"Found video: {video['id']} - {video['snippet']['title']} - {view_count} views")
                            category_videos.append(video_data)
                        except Exception as e:
                            self.logger.warning(f"Error processing video {video.get('id', 'unknown')}: {e}")
                    
                    # Avoid API rate limits
                    time.sleep(1)
                
                # Aggiungi tutti i video trovati per questa categoria
                all_videos.extend(category_videos)
                self.logger.info(f"Found {len(category_videos)} suitable shorts for category: {category}")
                
            except HttpError as e:
                self.logger.error(f"YouTube API error: {e}")
                if "quotaExceeded" in str(e):
                    self.logger.critical("YouTube API quota exceeded!")
                    # Se la quota è esaurita e non abbiamo trovato video, prova con video esistenti
                    if not all_videos:
                        self.logger.info("Falling back to existing unprocessed videos...")
                        existing_videos = self.get_existing_unprocessed_videos(max_results)
                        if existing_videos:
                            self.logger.info(f"Found {len(existing_videos)} existing videos to process")
                            return existing_videos
                    break
            except Exception as e:
                self.logger.error(f"Error searching category {category}: {e}")
        
        # Ordina i video per punteggio virale e limita ai risultati massimi
        all_videos.sort(key=lambda v: v['viral_score'], reverse=True)
        
        # Garantisci diversità tra categorie - prendi almeno 1 video da ciascuna categoria se disponibile
        diversified_results = []
        categories_used = set()
        remaining_videos = []
        
        # Assicurati che ogni categoria sia rappresentata
        for video in all_videos:
            category = video['category']
            if category not in categories_used and len(diversified_results) < max_results:
                diversified_results.append(video)
                categories_used.add(category)
            else:
                remaining_videos.append(video)
        
        # Riempi con i migliori video rimanenti
        remaining_slots = max_results - len(diversified_results)
        if remaining_slots > 0:
            # Ordina i rimanenti per punteggio virale
            remaining_videos.sort(key=lambda v: v['viral_score'], reverse=True)
            diversified_results.extend(remaining_videos[:remaining_slots])
        
        # Riordina il risultato finale per punteggio virale
        result = sorted(diversified_results, key=lambda v: v['viral_score'], reverse=True)
        
        self.logger.info(f"Found {len(result)} viral shorts in total")
        
        # Se abbiamo trovato almeno un video valido, stampa alcune informazioni
        if result:
            self.logger.info("Top viral shorts found:")
            for i, video in enumerate(result[:5], 1):
                self.logger.info(f"{i}. {video['title']} (ID: {video['youtube_id']}) - {video['views']} views - Viral Score: {video['viral_score']}")
        else:
            self.logger.warning("No viral shorts matching criteria found")
            # Fallback finale: se non sono stati trovati video nuovi, prova con quelli esistenti
            self.logger.info("Attempting fallback to existing unprocessed videos...")
            existing_videos = self.get_existing_unprocessed_videos(max_results)
            if existing_videos:
                self.logger.info(f"Using {len(existing_videos)} existing videos for processing")
                return existing_videos
            
        return result
    
    def get_existing_unprocessed_videos(self, max_results=50):
        """
        Get existing downloaded videos that haven't been processed yet.
        This is a fallback when API quota is exhausted.
        
        Args:
            max_results (int): Maximum number of videos to return
            
        Returns:
            list: List of video data from database
        """
        self.logger.info("Searching for existing unprocessed videos...")
        
        try:
            min_views = self.config['youtube_search']['min_views']
            viral_threshold = self.config['analytics']['viral_score_threshold']
            
            # Query per video non processati dal database
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT sv.id, sv.youtube_id, sv.title, sv.channel, sv.url, sv.views, 
                       sv.likes, sv.duration, sv.category, sv.downloaded_at, sv.file_path,
                       sv.copyright_status, sv.metadata
                FROM source_videos sv
                LEFT JOIN processed_clips pc ON sv.id = pc.source_id
                WHERE sv.views >= ? AND pc.source_id IS NULL
                ORDER BY sv.views DESC
                LIMIT ?
            """, (min_views, max_results))
            
            rows = cursor.fetchall()
            
            # Converti i risultati del database nel formato atteso
            existing_videos = []
            for row in rows:
                # Deserializza i metadati se esistono
                metadata = {}
                if row[12]:  # metadata field
                    try:
                        metadata = json.loads(row[12])
                    except:
                        metadata = {}
                
                # Calcola un punteggio virale basico dai dati esistenti
                view_count = row[5] or 0
                likes = row[6] or 0
                
                # Punteggio semplificato basato sui dati disponibili
                viral_score = 0
                if view_count > 0:
                    like_ratio = (likes / view_count) * 1000 if likes > 0 else 0
                    viral_score = min(100, like_ratio * 10)
                    
                    # Bonus per video con molte visualizzazioni
                    if view_count > 100000:
                        viral_score += 20
                    elif view_count > 50000:
                        viral_score += 15
                    elif view_count > 10000:
                        viral_score += 10
                
                # Verifica che il file video esista ancora
                file_path = row[10]
                if file_path and os.path.exists(file_path):
                    video_data = {
                        'database_id': row[0],
                        'youtube_id': row[1],
                        'title': row[2],
                        'channel': row[3],
                        'url': row[4],
                        'views': view_count,
                        'likes': likes,
                        'duration': row[7] or 0,
                        'category': row[8] or 'Unknown',
                        'copyright_status': row[11] or 'standard',
                        'viral_score': viral_score,
                        'file_path': file_path,
                        'metadata': metadata,
                        'source': 'existing_database'  # Indica che proviene dal database
                    }
                    
                    # Filtra per soglia virale se configurata
                    if viral_score >= viral_threshold:
                        existing_videos.append(video_data)
            
            self.logger.info(f"Found {len(existing_videos)} existing unprocessed videos meeting criteria")
            
            if existing_videos:
                self.logger.info("Existing videos ready for processing:")
                for i, video in enumerate(existing_videos[:5], 1):
                    self.logger.info(f"{i}. {video['title']} - {video['views']} views - Score: {video['viral_score']}")
            
            return existing_videos
            
        except Exception as e:
            self.logger.error(f"Error getting existing unprocessed videos: {e}")
            return []
    
    def _calculate_viral_score(self, video, view_count):
        """
        Calculate a viral score based on views, likes, comments, and publish date.
        
        Args:
            video (dict): Video data from YouTube API
            view_count (int): Number of views
            
        Returns:
            float: Viral score between 0-100
        """
        try:
            # Get basic metrics
            likes = int(video['statistics'].get('likeCount', 0))
            comments = int(video['statistics'].get('commentCount', 0))
            
            # Calculate engagement rate (likes + comments) / views
            engagement_rate = 0
            if view_count > 0:
                engagement_rate = (likes + comments) / view_count
                
            # Calculate recency (newer videos get higher score)
            published_at = video['snippet']['publishedAt']
            publish_date = datetime.datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            days_since_publish = (datetime.datetime.now() - publish_date).days
            
            # Adjust for very recent videos (avoid division by zero)
            days_factor = max(days_since_publish, 0.5)
            recency_score = min(100, 10 / days_factor * 10)
            
            # Calculate like-to-view ratio score (0-40 points)
            like_view_ratio = 0
            if view_count > 0:
                like_view_ratio = min(40, (likes / view_count) * 1000)
                
            # Calculate comment-to-view ratio score (0-20 points)
            comment_view_ratio = 0
            if view_count > 0:
                comment_view_ratio = min(20, (comments / view_count) * 1000)
                
            # Calculate view velocity score (0-30 points)
            # Higher score for more views in less time
            view_velocity = min(30, (view_count / max(days_factor, 1)) / 1000)
            
            # Calculate final viral score
            viral_score = min(100, like_view_ratio + comment_view_ratio + view_velocity + recency_score * 0.1)
            
            return round(viral_score, 2)
        except Exception as e:
            self.logger.warning(f"Error calculating viral score: {e}")
            return 0
    
    def _parse_duration(self, duration_str):
        """
        Parse ISO 8601 duration string to seconds.
        
        Args:
            duration_str (str): ISO 8601 duration string (e.g. 'PT1M30S')
            
        Returns:
            int: Duration in seconds
        """
        match = re.match(
            r'P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?',
            duration_str
        )
        
        if not match:
            return 0
            
        parts = match.groupdict()
        time_params = {}
        
        for name, param in parts.items():
            if param:
                time_params[name] = int(param)
                
        return (
            time_params.get('days', 0) * 86400 +
            time_params.get('hours', 0) * 3600 +
            time_params.get('minutes', 0) * 60 +
            time_params.get('seconds', 0)
        )
    
    def download_video(self, video_data):
        """
        Download a YouTube video using yt-dlp.
        
        Args:
            video_data (dict): Video information including YouTube ID
            
        Returns:
            dict: Updated video_data with download info
        """
        # Check if this video is from existing database and already downloaded
        if video_data.get('source') == 'existing_database':
            self.logger.info(f"Using existing video file: {video_data['title']}")
            # Verifica che il file esista ancora
            if video_data.get('file_path') and os.path.exists(video_data['file_path']):
                return video_data
            else:
                self.logger.warning(f"Existing video file not found: {video_data.get('file_path')}")
                # Il file non esiste più, proviamo a riscaricarlo
        
        video_id = video_data['youtube_id']
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create filename with video ID (to avoid duplicates and special chars issues)
        filename = f"{video_id}.mp4"
        output_path = self.download_dir / filename
        
        self.logger.info(f"Downloading video {video_id}: {video_data['title']}")
        
        # yt-dlp options
        ydl_opts = {
            'format': 'best[height<=1080]',  # Best quality up to 1080p
            'outtmpl': str(output_path),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'windowsfilenames': True,  # Use safe filenames
            'writethumbnail': True,  # Also download thumbnail
            'writesubtitles': True,  # Download subtitles if available
            'writeautomaticsub': True,  # Download auto-generated subtitles
            'subtitleslangs': [self.config['app_settings']['selected_language']],
        }
        
        # Check if file already exists and skip download if it does
        if output_path.exists():
            self.logger.info(f"Video already exists: {output_path}")
            video_data.update({
                'file_path': str(output_path),
                'download_status': 'existing',
                'downloaded_at': datetime.datetime.now().isoformat()
            })
            # Check for subtitle and thumbnail files too
            subtitle_files = list(self.download_dir.glob(f"{video_id}*.vtt")) + list(self.download_dir.glob(f"{video_id}*.srt"))
            if subtitle_files:
                video_data['subtitle_path'] = str(subtitle_files[0])
            thumbnail_files = list(self.download_dir.glob(f"{video_id}*.webp")) + list(self.download_dir.glob(f"{video_id}*.jpg"))
            if thumbnail_files:
                video_data['thumbnail_path'] = str(thumbnail_files[0])
            return video_data
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                
                # Update video_data with download info
                video_data['downloaded_at'] = datetime.datetime.now().isoformat()
                video_data['file_path'] = str(output_path)
                
                # Add extra metadata if available
                if info_dict:
                    video_data['metadata'].update({
                        'height': info_dict.get('height'),
                        'width': info_dict.get('width'),
                        'fps': info_dict.get('fps'),
                        'format': info_dict.get('format')
                    })
                
                self.logger.info(f"Successfully downloaded video {video_id}")
                return video_data
                
        except Exception as e:
            self.logger.error(f"Error downloading video {video_id}: {e}")
            raise
    
    def download_video_direct(self, video_id, force=False):
        """
        Download a YouTube video directly by ID, bypassing search.
        Used for test mode.
        
        Args:
            video_id (str): YouTube video ID
            force (bool): Force download even if video exists
            
        Returns:
            dict: Video data dictionary with download info
        """
        try:
            # First get video info from YouTube API
            self.logger.info(f"Fetching info for video ID: {video_id}")
            
            request = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id
            )
            response = request.execute()
            
            if not response['items']:
                raise Exception(f"Video not found: {video_id}")
            
            video_info = response['items'][0]
            snippet = video_info['snippet']
            statistics = video_info['statistics']
            content_details = video_info['contentDetails']
            
            # Parse duration
            duration = self._parse_duration(content_details.get('duration', 'PT0S'))
            
            # Create video data structure
            video_data = {
                'youtube_id': video_id,
                'title': snippet['title'],
                'channel_title': snippet['channelTitle'],
                'published_at': snippet['publishedAt'],
                'duration': duration,
                'views': int(statistics.get('viewCount', 0)),
                'likes': int(statistics.get('likeCount', 0)),
                'comments': int(statistics.get('commentCount', 0)),
                'category': snippet.get('categoryId', 'Entertainment'),
                'description': snippet.get('description', ''),
                'tags': snippet.get('tags', []),
                'metadata': {
                    'channel_id': snippet['channelId'],
                    'language': snippet.get('defaultLanguage', 'en'),
                    'category_id': snippet.get('categoryId')
                },
                'source': 'test_mode'
            }
            
            self.logger.info(f"Video info fetched: {video_data['title']} - {video_data['views']} views")
            
            # Download the video
            downloaded_video = self.download_video(video_data)
            
            # Add to database
            video_id_db = self.db.add_source_video(downloaded_video)
            downloaded_video['id'] = video_id_db
            
            self.logger.info(f"Test video processed successfully: {downloaded_video['title']}")
            return downloaded_video
            
        except Exception as e:
            self.logger.error(f"Error in direct video download for {video_id}: {e}")
            raise
    
    def process_viral_shorts(self, max_videos=10):
        """
        Find viral shorts, download them, and add to the database.
        
        Args:
            max_videos (int): Maximum number of videos to process
            
        Returns:
            list: List of IDs of downloaded videos
        """
        # Search for viral shorts
        viral_shorts = self.search_viral_shorts(max_videos * 2)  # Get extra to account for filtering
        
        # Check if any videos found
        if not viral_shorts:
            self.logger.warning("No viral shorts found")
            return []
        
        # Check if these are existing videos from fallback
        existing_fallback_videos = []
        new_shorts = []
        
        # Separate existing videos (from fallback) from new videos
        for video in viral_shorts:
            if video.get('source') == 'existing_database':
                existing_fallback_videos.append(video)
            else:
                new_shorts.append(video)
        
        # Filter out NEW videos that are already in the database
        if new_shorts:
            existing_ids = set()
            try:
                result = self.db.execute_query(
                    "SELECT youtube_id FROM source_videos"
                )
                existing_ids = {row['youtube_id'] for row in result}
            except Exception as e:
                self.logger.error(f"Error checking existing videos: {e}")
                
            new_shorts = [v for v in new_shorts if v['youtube_id'] not in existing_ids]
        
        # Process new videos
        downloaded_ids = []
        if new_shorts:
            self.logger.info(f"Found {len(new_shorts)} new viral shorts")
            
            # Limit to max_videos
            new_shorts = new_shorts[:max_videos]
            
            # Download each video and add to database
            for video_data in new_shorts:
                try:
                    # Download the video
                    video_data = self.download_video(video_data)
                    
                    # Add to database
                    video_id = self.db.add_source_video(video_data)
                    downloaded_ids.append(video_id)
                    
                    self.logger.info(f"Added video to database with ID: {video_id}")
                    
                    # Small delay between downloads
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error processing video {video_data['youtube_id']}: {e}")
        
        # Process existing videos from fallback
        if existing_fallback_videos and not new_shorts:
            self.logger.info(f"Processing {len(existing_fallback_videos)} existing videos from fallback")
            
            # Get database IDs for existing videos
            for video_data in existing_fallback_videos[:max_videos]:
                try:
                    result = self.db.execute_query(
                        "SELECT id FROM source_videos WHERE youtube_id = ?",
                        (video_data['youtube_id'],)
                    )
                    if result:
                        downloaded_ids.append(result[0]['id'])
                        self.logger.info(f"Selected existing video for processing: {video_data['title']}")
                        
                except Exception as e:
                    self.logger.error(f"Error getting database ID for video {video_data['youtube_id']}: {e}")
        
        if downloaded_ids:
            if new_shorts:
                self.logger.info(f"Downloaded and added {len(downloaded_ids)} new videos to database")
            else:
                self.logger.info(f"Selected {len(downloaded_ids)} existing videos for processing")
        else:
            self.logger.warning("No videos available for processing")
        
        return downloaded_ids
    
    def analyze_trends(self, videos):
        """
        Analyze trends in the viral shorts found.
        
        Args:
            videos (list): List of video data dictionaries
            
        Returns:
            dict: Trend analysis results
        """
        if not videos:
            return {}
            
        self.logger.info("Analyzing trends in viral shorts...")
        
        # Initialize analysis dict
        analysis = {
            'total_videos': len(videos),
            'categories': {},
            'queries': {},
            'top_channels': {},
            'avg_views': 0,
            'avg_likes': 0,
            'avg_comments': 0,
            'avg_duration': 0,
            'avg_viral_score': 0,
        }
        
        # Populate analysis data
        total_views = 0
        total_likes = 0
        total_comments = 0
        total_duration = 0
        total_viral_score = 0
        
        for video in videos:
            # Category stats
            category = video['category']
            if category not in analysis['categories']:
                analysis['categories'][category] = {
                    'count': 0,
                    'views': 0,
                    'viral_score': 0
                }
            analysis['categories'][category]['count'] += 1
            analysis['categories'][category]['views'] += video['views']
            analysis['categories'][category]['viral_score'] += video['viral_score']
            
            # Query stats
            query = video['search_query']
            if query not in analysis['queries']:
                analysis['queries'][query] = {
                    'count': 0,
                    'videos': []
                }
            analysis['queries'][query]['count'] += 1
            analysis['queries'][query]['videos'].append({
                'id': video['youtube_id'],
                'title': video['title'],
                'views': video['views'],
                'viral_score': video['viral_score']
            })
            
            # Channel stats
            channel = video['channel']
            if channel not in analysis['top_channels']:
                analysis['top_channels'][channel] = 0
            analysis['top_channels'][channel] += 1
            
            # Aggregates for averages
            total_views += video['views']
            total_likes += video['likes']
            total_comments += video['comments']
            total_duration += video['duration']
            total_viral_score += video['viral_score']
        
        # Calculate averages
        video_count = max(1, len(videos))
        analysis['avg_views'] = total_views / video_count
        analysis['avg_likes'] = total_likes / video_count
        analysis['avg_comments'] = total_comments / video_count
        analysis['avg_duration'] = total_duration / video_count
        analysis['avg_viral_score'] = total_viral_score / video_count
        
        # Sort top channels
        analysis['top_channels'] = dict(sorted(
            analysis['top_channels'].items(), 
            key=lambda item: item[1], 
            reverse=True
        )[:5])  # Top 5 channels
        
        # Find most effective categories
        for category, data in analysis['categories'].items():
            if data['count'] > 0:
                data['avg_viral_score'] = data['viral_score'] / data['count']
                data['avg_views'] = data['views'] / data['count']
        
        # Sort categories by average viral score
        analysis['categories'] = dict(sorted(
            analysis['categories'].items(),
            key=lambda item: item[1]['avg_viral_score'],
            reverse=True
        ))
        
        # Find most effective queries
        analysis['queries'] = dict(sorted(
            analysis['queries'].items(),
            key=lambda item: item[1]['count'],
            reverse=True
        ))
        
        # Log some insights
        self.logger.info(f"Trend analysis complete. Found {analysis['total_videos']} videos across {len(analysis['categories'])} categories")
        
        # Log top categories
        self.logger.info("Top performing categories by viral score:")
        for i, (category, data) in enumerate(list(analysis['categories'].items())[:3], 1):
            self.logger.info(f"{i}. {category}: {data['avg_viral_score']:.2f} avg viral score, {data['count']} videos")
            
        return analysis
