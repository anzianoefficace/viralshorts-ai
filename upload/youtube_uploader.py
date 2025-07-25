"""
YouTube uploader module for ViralShortsAI.
Handles authentication and uploading videos to YouTube.
"""

import os
import time
import random
import datetime
import http.client
import httplib2
import json
from pathlib import Path

import google.oauth2.credentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from utils import app_logger

class YouTubeUploader:
    """
    Class to handle YouTube API authentication and video uploads.
    Manages OAuth2 flow and handles video metadata.
    """
    
    # YouTube API scopes needed
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube'
    ]
    
    # YouTube API service name and version
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    
    def __init__(self, config):
        """
        Initialize the YouTube uploader.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.logger = app_logger
        
        # Directory for storing credentials
        # Use the parent directory of the database as the data directory
        self.credentials_dir = Path(os.path.dirname(self.config['paths'].get('database', 'data/viral_shorts.db')))
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_path = self.credentials_dir / 'youtube_credentials.json'
        
        # Upload directory
        self.uploads_dir = Path(self.config['paths'].get('uploads', 'data/uploads'))
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize YouTube API client
        self.youtube = None
        self.logger.info("YouTube uploader initialized")
    
    def authenticate(self):
        """
        Authenticate with YouTube API using OAuth2.
        Handles token refresh and initial setup.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            credentials = None
            
            # Controlla prima se esiste un token di refresh nell'ambiente
            env_refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
            
            # Controlla se il file delle credenziali esiste
            if self.credentials_path.exists():
                try:
                    # Carica credenziali dal file
                    with open(self.credentials_path, 'r') as f:
                        creds_data = json.load(f)
                        credentials = Credentials.from_authorized_user_info(
                            creds_data, self.SCOPES
                        )
                        self.logger.info("Credenziali caricate dal file")
                        
                        # Se esiste un token nell'ambiente ed è diverso da quello nel file, usa quello dell'ambiente
                        if env_refresh_token and env_refresh_token != credentials.refresh_token:
                            self.logger.info("Token di refresh nell'ambiente diverso dal file, uso quello dell'ambiente")
                            credentials.refresh_token = env_refresh_token
                except Exception as e:
                    self.logger.error(f"Errore nel caricamento delle credenziali: {e}")
            
            # Se non ci sono credenziali ma c'è un token di refresh nell'ambiente, crea le credenziali
            if not credentials and env_refresh_token:
                self.logger.info("Creazione credenziali dal token di refresh nell'ambiente")
                client_id = os.getenv('YOUTUBE_CLIENT_ID')
                client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
                
                if not client_id or not client_secret:
                    self.logger.error(
                        "Client ID o Secret YouTube non trovati nelle variabili d'ambiente"
                    )
                    return False
                    
                credentials = Credentials(
                    None,  # Nessun access token
                    refresh_token=env_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=self.SCOPES
                )
            
            # Verifica se le credenziali sono valide
            if credentials and credentials.valid:
                self.logger.info("Uso credenziali YouTube esistenti e valide")
            elif credentials and credentials.expired and credentials.refresh_token:
                try:
                    # Refresh del token
                    self.logger.info("Aggiornamento credenziali YouTube scadute")
                    credentials.refresh(Request())
                    self.logger.info("Credenziali aggiornate con successo")
                except Exception as e:
                    self.logger.error(f"Errore nell'aggiornamento delle credenziali: {e}")
                    credentials = None
            
            # Se ancora non abbiamo credenziali valide, serve autenticazione da zero
            if not credentials:
                # Ottieni client secrets dalle variabili d'ambiente
                client_id = os.getenv('YOUTUBE_CLIENT_ID')
                client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
                
                if not client_id or not client_secret:
                    self.logger.error(
                        "Client ID o Secret YouTube non trovati nelle variabili d'ambiente"
                    )
                    return False
                
                # Crea dizionario di configurazione client
                client_config = {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["http://localhost"]
                    }
                }
                
                # Esegui il flusso OAuth
                self.logger.warning(
                    "Nessuna credenziale YouTube valida trovata, avvio del processo di autenticazione"
                )
                
                # Uso porta fissa 8080 per evitare problemi con redirect_uri dinamici
                flow = InstalledAppFlow.from_client_config(
                    client_config, self.SCOPES
                )
                credentials = flow.run_local_server(
                    port=8080,
                    prompt='consent',  # Force re-consent
                    authorization_prompt_message="Per favore, completa l'autenticazione nel browser",
                    success_message="Autenticazione completata! Puoi chiudere questa finestra."
                )
                self.logger.info("Autenticazione completata con successo")
            
            # Save credentials for next run
            if credentials:
                try:
                    # Assicura che la directory esista
                    self.credentials_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Imposta permessi di sola lettura per l'utente corrente
                    with open(self.credentials_path, 'w') as f:
                        creds_dict = {
                            'token': credentials.token,
                            'refresh_token': credentials.refresh_token,
                            'token_uri': credentials.token_uri,
                            'client_id': credentials.client_id,
                            'client_secret': credentials.client_secret,
                            'scopes': credentials.scopes
                        }
                        json.dump(creds_dict, f)
                    
                    # Imposta permessi di sola lettura per l'utente corrente (solo su sistemi Unix)
                    if os.name != 'nt':  # Non Windows
                        os.chmod(self.credentials_path, 0o600)
                        
                    # Aggiorna la variabile d'ambiente YOUTUBE_REFRESH_TOKEN se è cambiata
                    if os.getenv('YOUTUBE_REFRESH_TOKEN') != credentials.refresh_token:
                        os.environ['YOUTUBE_REFRESH_TOKEN'] = credentials.refresh_token
                        self.logger.info("Aggiornato token di refresh nelle variabili d'ambiente")
                    
                    self.logger.info(f"Credenziali salvate in {self.credentials_path}")
                except Exception as e:
                    self.logger.warning(f"Errore nel salvataggio delle credenziali su disco: {e}")
                
                # Costruisci il client API YouTube
                self.youtube = build(
                    self.API_SERVICE_NAME, 
                    self.API_VERSION, 
                    credentials=credentials
                )
                
                self.logger.info("Client API YouTube creato con successo")
                return True
            else:
                self.logger.error("Impossibile ottenere credenziali YouTube")
                return False
                
        except Exception as e:
            self.logger.error(f"Errore di autenticazione: {e}")
            return False
    
    def upload_video(self, video_path, title, description, tags=None, 
                   thumbnail_path=None, visibility='public', 
                   category_id='22', source_video_data=None):  # 22 is 'People & Blogs'
        """
        Upload a video to YouTube.
        
        Args:
            video_path (str): Path to the video file
            title (str): Video title
            description (str): Video description
            tags (list, optional): List of tags/keywords
            thumbnail_path (str, optional): Path to thumbnail image
            visibility (str): Privacy status ('public', 'private', 'unlisted')
            category_id (str): YouTube video category ID
            source_video_data (dict, optional): Original video data for credits
            
        Returns:
            dict: Upload result with video ID and URL
        """
        if not self.youtube:
            if not self.authenticate():
                self.logger.error("YouTube authentication failed, cannot upload")
                return None
        
        if not os.path.exists(video_path):
            self.logger.error(f"Video file not found: {video_path}")
            return None
        
        # Ensure tags is a list
        if tags is None:
            tags = []
        elif isinstance(tags, str):
            tags = [tags]
            
        # Remove # from hashtags
        tags = [tag[1:] if tag.startswith('#') else tag for tag in tags]
        
        # Add credits to description if source video data is provided
        final_description = description
        if source_video_data:
            channel_title = source_video_data.get('channel_title')
            
            # If channel_title is None or empty, try to get it from metadata
            if not channel_title:
                metadata = source_video_data.get('metadata')
                if isinstance(metadata, str):
                    try:
                        import json
                        metadata_dict = json.loads(metadata)
                        # YouTube API doesn't always provide channelTitle in metadata
                        # Use a default fallback
                        channel_title = "Creator originale"
                    except:
                        channel_title = "Creator originale"
                else:
                    channel_title = "Creator originale"
            
            channel_id = None
            
            # Extract channel_id from metadata if available
            metadata = source_video_data.get('metadata')
            if isinstance(metadata, dict):
                channel_id = metadata.get('channel_id')
            elif isinstance(metadata, str):
                try:
                    import json
                    metadata_dict = json.loads(metadata)
                    channel_id = metadata_dict.get('channel_id')
                except:
                    pass
            
            # Add credits line
            if channel_id:
                credits_line = f"\n\n🎥 Credits: contenuto originale di [{channel_title}](https://www.youtube.com/channel/{channel_id})"
            else:
                credits_line = f"\n\n🎥 Credits: contenuto originale di {channel_title}"
            
            final_description = description + credits_line
            self.logger.info(f"Added credits for channel: {channel_title}")
        
        self.logger.info(f"Uploading video: {title}")
        
        # Set up request body
        body = {
            'snippet': {
                'title': title,
                'description': final_description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': visibility,
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Execute upload
        try:
            # Insert video with resumable upload
            media = MediaFileUpload(
                video_path, 
                mimetype='video/*', 
                resumable=True,
                chunksize=1024*1024  # 1MB chunk size
            )
            
            insert_request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media,
                notifySubscribers=True
            )
            
            # Upload with progress tracking
            response = None
            last_progress = 0
            retry_count = 0
            max_retries = 10
            
            while response is None:
                try:
                    status, response = insert_request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        if progress - last_progress >= 10:
                            self.logger.info(f"Upload progress: {progress}%")
                            last_progress = progress
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504] and retry_count < max_retries:
                        retry_count += 1
                        sleep_time = 2 ** retry_count
                        self.logger.warning(
                            f"YouTube API error {e.resp.status}, retrying in {sleep_time} seconds"
                        )
                        time.sleep(sleep_time)
                    else:
                        self.logger.error(f"Upload failed: {e}")
                        return None
                except Exception as e:
                    self.logger.error(f"Upload error: {e}")
                    return None
            
            video_id = response['id']
            self.logger.info(f"Video uploaded successfully with ID: {video_id}")
            
            # Upload thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    self.youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    self.logger.info(f"Thumbnail uploaded for video {video_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to upload thumbnail: {e}")
            
            # Return video information
            result = {
                'youtube_id': video_id,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'title': title,
                'description': final_description,
                'tags': tags,
                'visibility': visibility,
                'upload_time': datetime.datetime.now().isoformat()
            }
            
            return result
            
        except HttpError as e:
            self.logger.error(f"YouTube API error: {e}")
            if "quotaExceeded" in str(e):
                self.logger.critical("YouTube API quota exceeded!")
            return None
        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            return None
    
    def schedule_upload(self, clip_data, scheduled_time=None):
        """
        Schedule a video upload at the specified time or using default upload times.
        
        Args:
            clip_data (dict): Clip information including file path and metadata
            scheduled_time (datetime, optional): When to upload the video
            
        Returns:
            dict: Scheduling result
        """
        # Check if the video file exists
        video_path = clip_data.get('file_path')
        if not video_path or not os.path.exists(video_path):
            self.logger.error(f"Video file not found: {video_path}")
            return None
        
        # Get source video data for credits if available
        source_video_data = None
        if 'source_id' in clip_data or 'source_video_id' in clip_data:
            try:
                import sqlite3
                conn = sqlite3.connect(self.config['paths']['database'])
                cursor = conn.cursor()
                
                source_id = clip_data.get('source_id') or clip_data.get('source_video_id')
                cursor.execute("SELECT * FROM source_videos WHERE id = ?", (source_id,))
                source_row = cursor.fetchone()
                
                if source_row:
                    source_video_data = {
                        'channel_title': source_row[3],  # channel field
                        'metadata': source_row[12]  # metadata JSON field
                    }
                    self.logger.info(f"Found source video data for credits: {source_row[3]}")
                
                conn.close()
            except Exception as e:
                self.logger.warning(f"Could not retrieve source video data: {e}")
        
        # Get title, description, and hashtags
        title = clip_data.get('title', 'Viral Short Video')
        description = clip_data.get('description', '')
        hashtags = clip_data.get('hashtags', [])
        
        # If hashtags is a string, convert to list
        if isinstance(hashtags, str):
            hashtags = hashtags.split(',')
            
        # Add hashtags to the end of the description
        if hashtags:
            # Make sure all hashtags start with #
            hashtags = [tag if tag.startswith('#') else f"#{tag}" for tag in hashtags]
            hashtags_text = ' '.join(hashtags)
            
            if description:
                description = f"{description}\n\n{hashtags_text}"
            else:
                description = hashtags_text
        
        # Determine upload time if not specified
        if scheduled_time is None:
            upload_times = self.config['upload']['upload_times']
            
            if not upload_times:
                # Default to current time + 5 minutes
                scheduled_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
            else:
                # Choose the next available time
                now = datetime.datetime.now()
                today = now.date()
                
                # Parse upload times
                today_times = []
                for time_str in upload_times:
                    try:
                        hour, minute = map(int, time_str.split(':'))
                        time_obj = datetime.datetime.combine(
                            today, datetime.time(hour=hour, minute=minute)
                        )
                        today_times.append(time_obj)
                    except Exception as e:
                        self.logger.warning(f"Invalid upload time format: {time_str} - {e}")
                
                # Add tomorrow's times too
                tomorrow = today + datetime.timedelta(days=1)
                tomorrow_times = []
                for time_obj in today_times:
                    tomorrow_time = datetime.datetime.combine(
                        tomorrow, time_obj.time()
                    )
                    tomorrow_times.append(tomorrow_time)
                
                all_times = sorted(today_times + tomorrow_times)
                
                # Find the next available time
                future_times = [t for t in all_times if t > now]
                
                if future_times:
                    scheduled_time = future_times[0]
                else:
                    # Default to tomorrow if no future times today
                    scheduled_time = datetime.datetime.combine(
                        tomorrow, datetime.time(hour=12, minute=0)
                    )
        
        # Determine whether to upload now or schedule
        now = datetime.datetime.now()
        wait_seconds = (scheduled_time - now).total_seconds()
        
        # If scheduled within 5 minutes, upload now
        if wait_seconds < 300:
            self.logger.info(f"Uploading video now: {title}")
            return self.upload_video(
                video_path, 
                title, 
                description, 
                tags=hashtags,
                visibility=self.config['upload']['visibility'],
                source_video_data=source_video_data
            )
        else:
            # Return scheduling information (actual upload will happen later)
            self.logger.info(f"Scheduled upload for {scheduled_time.isoformat()}: {title}")
            
            return {
                'clip_id': clip_data.get('id'),
                'title': title,
                'description': description,
                'hashtags': hashtags,
                'file_path': video_path,
                'scheduled_time': scheduled_time.isoformat(),
                'visibility': self.config['upload']['visibility'],
                'status': 'scheduled'
            }
    
    def check_scheduled_uploads(self, db):
        """
        Check for videos that are scheduled to be uploaded and execute if it's time.
        
        Args:
            db: Database instance
            
        Returns:
            list: List of uploaded video IDs
        """
        try:
            # Query database for scheduled uploads
            now = datetime.datetime.now()
            scheduled = db.execute_query(
                """
                SELECT * FROM uploaded_videos 
                WHERE youtube_id IS NULL 
                AND scheduled_time <= ?
                """,
                (now.isoformat(),)
            )
            
            if not scheduled:
                return []
                
            self.logger.info(f"Found {len(scheduled)} videos scheduled for upload")
            
            uploaded_ids = []
            
            # Process each scheduled upload
            for video in scheduled:
                try:
                    # Get clip information
                    clip_id = video['clip_id']
                    clip = db.execute_query(
                        "SELECT * FROM processed_clips WHERE id = ?", 
                        (clip_id,)
                    )
                    
                    if not clip:
                        self.logger.error(f"Clip not found for scheduled upload: {clip_id}")
                        continue
                    
                    clip = clip[0]
                    
                    # Check if file exists
                    file_path = clip['file_path']
                    if not os.path.exists(file_path):
                        self.logger.error(f"Video file not found: {file_path}")
                        continue
                    
                    # Upload video
                    upload_result = self.upload_video(
                        file_path,
                        video['title'],
                        video['description'],
                        tags=video['hashtags'].split(',') if video['hashtags'] else [],
                        visibility=video['visibility']
                    )
                    
                    if upload_result:
                        # Update database
                        db.execute_query(
                            """
                            UPDATE uploaded_videos 
                            SET youtube_id = ?, url = ?, upload_time = ? 
                            WHERE id = ?
                            """,
                            (
                                upload_result['youtube_id'],
                                upload_result['url'],
                                upload_result['upload_time'],
                                video['id']
                            )
                        )
                        
                        self.logger.info(
                            f"Successfully uploaded scheduled video: {upload_result['youtube_id']}"
                        )
                        uploaded_ids.append(video['id'])
                        
                except Exception as e:
                    self.logger.error(f"Error processing scheduled upload {video['id']}: {e}")
            
            return uploaded_ids
            
        except Exception as e:
            self.logger.error(f"Error checking scheduled uploads: {e}")
            return []
    
    def get_video_analytics(self, youtube_id):
        """
        Get analytics for a YouTube video.
        
        Args:
            youtube_id (str): YouTube video ID
            
        Returns:
            dict: Analytics data
        """
        if not self.youtube:
            if not self.authenticate():
                self.logger.error("YouTube authentication failed, cannot get analytics")
                return None
        
        try:
            # Get video statistics
            response = self.youtube.videos().list(
                part='statistics',
                id=youtube_id
            ).execute()
            
            if not response.get('items'):
                self.logger.warning(f"No statistics found for video {youtube_id}")
                return None
                
            stats = response['items'][0]['statistics']
            
            # Convert string values to integers
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))
            
            # Calculate engagement rate
            engagement_rate = 0
            if views > 0:
                engagement_rate = (likes + comments) / views * 100
            
            # Calculate viral score (simplified)
            # This is a basic formula - for a real app, this would be much more sophisticated
            viral_score = min(100, (
                (views * 0.5) +
                (likes * 2) +
                (comments * 3)
            ) / 100)
            
            # Return analytics data
            analytics = {
                'youtube_id': youtube_id,
                'views': views,
                'likes': likes,
                'comments': comments,
                'engagement_rate': engagement_rate,
                'viral_score': viral_score,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            self.logger.info(f"Retrieved analytics for video {youtube_id}: {views} views")
            return analytics
            
        except HttpError as e:
            self.logger.error(f"YouTube API error getting analytics: {e}")
            if "quotaExceeded" in str(e):
                self.logger.critical("YouTube API quota exceeded!")
            return None
        except Exception as e:
            self.logger.error(f"Error getting video analytics: {e}")
            return None
    
    def force_reauthenticate(self):
        """
        Force reauthentication with YouTube API, ignoring any existing credentials.
        Used when refresh tokens expire or are invalid.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            # Get client secrets from environment variables
            client_id = os.getenv('YOUTUBE_CLIENT_ID')
            client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                self.logger.error(
                    "Client ID o Secret YouTube non trovati nelle variabili d'ambiente"
                )
                return False
            
            # Create client config dict
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"]
                }
            }
            
            # Run OAuth flow with fixed port
            self.logger.info("Avvio di un nuovo flusso di autenticazione forzata")
            flow = InstalledAppFlow.from_client_config(
                client_config, self.SCOPES
            )
            credentials = flow.run_local_server(
                port=8080,
                prompt='consent',  # Force re-consent
                authorization_prompt_message="Per favore, completa l'autenticazione YouTube nel browser",
                success_message="Autenticazione completata con successo! Puoi chiudere questa finestra."
            )
            self.logger.info("Autenticazione forzata completata con successo")
            
            # Save credentials for next run
            if credentials:
                try:
                    # Assicura che la directory esista
                    self.credentials_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Salva le credenziali in formato JSON
                    with open(self.credentials_path, 'w') as f:
                        creds_dict = {
                            'token': credentials.token,
                            'refresh_token': credentials.refresh_token,
                            'token_uri': credentials.token_uri,
                            'client_id': credentials.client_id,
                            'client_secret': credentials.client_secret,
                            'scopes': credentials.scopes
                        }
                        json.dump(creds_dict, f)
                    
                    # Imposta permessi di sola lettura per l'utente corrente (solo su sistemi Unix)
                    if os.name != 'nt':  # Non Windows
                        os.chmod(self.credentials_path, 0o600)
                    
                    # Salva il refresh token nella variabile d'ambiente
                    os.environ['YOUTUBE_REFRESH_TOKEN'] = credentials.refresh_token
                    self.logger.info(f"Nuovo token di refresh generato: {credentials.refresh_token[:10]}...")
                    
                    self.logger.info(f"Credenziali salvate in {self.credentials_path}")
                except Exception as e:
                    self.logger.warning(f"Errore nel salvataggio delle credenziali: {e}")
                
                # Costruisci il client API YouTube
                self.youtube = build(
                    self.API_SERVICE_NAME, 
                    self.API_VERSION, 
                    credentials=credentials
                )
                
                self.logger.info("Client API YouTube creato con successo")
                return True
            else:
                self.logger.error("Impossibile ottenere credenziali YouTube")
                return False
                
        except Exception as e:
            self.logger.error(f"Errore di autenticazione: {e}")
            return False
    
    def get_refresh_token(self):
        """
        Get the current refresh token.
        
        Returns:
            str: The current refresh token or None if not available
        """
        if self.credentials_path.exists():
            try:
                with open(self.credentials_path, 'r') as f:
                    creds_data = json.load(f)
                    return creds_data.get('refresh_token')
            except Exception as e:
                self.logger.error(f"Error loading credentials: {e}")
        
        return None
