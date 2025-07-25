"""
Video processing module for ViralShortsAI.
Handles video editing, clip extraction, and adding visual elements.
"""

import os
import json
import math
import random
import tempfile
from pathlib import Path

import numpy as np

# Configura ImageMagick prima di importare MoviePy
try:
    from moviepy_config import configure_imagemagick
    configure_imagemagick()
except:
    pass

try:
    # Tenta di importare moviepy correttamente
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, ImageClip
    from moviepy.video.fx.resize import resize
    from moviepy.video.fx.fadeout import fadeout
    from moviepy.video.fx.fadein import fadein
    from moviepy.editor import concatenate_videoclips
    # Verifica se SubtitlesClip esiste
    try:
        from moviepy.video.tools.subtitles import SubtitlesClip
    except ImportError:
        # Fallback se SubtitlesClip non è disponibile
        SubtitlesClip = None
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    # Log dell'errore
    import logging
    logging.error(f"Errore nell'importare moviepy: {e}")
    MOVIEPY_AVAILABLE = False
    # Crea stub per consentire l'avvio dell'applicazione
    class VideoFileClip:
        def __init__(self, *args, **kwargs): 
            self.duration = 0
            self.fps = 30
        def subclip(self, *args, **kwargs): return self
        def write_videofile(self, *args, **kwargs): pass
        def get_frame(self, *args, **kwargs): return None
        def close(self): pass
    class TextClip:
        def __init__(self, *args, **kwargs): pass
    class CompositeVideoClip:
        def __init__(self, *args, **kwargs): pass
    class ColorClip:
        def __init__(self, *args, **kwargs): pass
    class ImageClip:
        def __init__(self, *args, **kwargs): pass
        def save_frame(self, *args, **kwargs): pass
    def concatenate_videoclips(*args, **kwargs): return None
    def resize(*args, **kwargs): pass
    def fadeout(*args, **kwargs): pass
    def fadein(*args, **kwargs): pass
    SubtitlesClip = None

import ffmpeg

from utils import app_logger

class VideoEditor:
    """
    Class for video processing and editing.
    Handles clip extraction, text overlays, and subtitles.
    """
    
    def __init__(self, config, db):
        """
        Initialize the video editor.
        
        Args:
            config (dict): Configuration dictionary
            db: Database instance
        """
        self.config = config
        self.db = db
        self.logger = app_logger
        
        # Create output directory if it doesn't exist
        try:
            processed_path = self.config.get('paths', {}).get('processed', 'data/processed')
            self.logger.debug(f"[DEBUG] Percorso processed configurato: {processed_path}")
            
            self.processed_dir = Path(processed_path)
            self.processed_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Directory di output creata/verificata: {self.processed_dir}")
        except Exception as e:
            self.logger.error(f"Errore nella configurazione della directory di output: {e}")
            # Usa una directory predefinita in caso di errore
            self.processed_dir = Path("data/processed")
            self.processed_dir.mkdir(parents=True, exist_ok=True)
            self.logger.warning(f"Usando directory di fallback per l'output: {self.processed_dir}")
        
        # Set font for text overlays with safe access
        video_processing = self.config.get('video_processing', {})
        self.font = 'Arial'  # Default
        self.font_size = video_processing.get('font_size', 24)
        self.font_color = video_processing.get('font_color', '#FFFFFF')
        self.highlight_color = video_processing.get('highlight_color', '#FF0000')
        
        self.logger.debug(f"[DEBUG] Font configurato: {self.font}, Size: {self.font_size}")
        self.logger.debug(f"[DEBUG] Font color: {self.font_color}, Highlight: {self.highlight_color}")
        
        self.logger.info("Video editor initialized")
    
    def extract_clip(self, video_path, output_path, start_time=0, end_time=None, duration=None):
        """
        Extract a clip from a video file.
        
        Args:
            video_path (str): Path to the source video
            output_path (str): Path to save the output clip
            start_time (float): Start time in seconds
            end_time (float, optional): End time in seconds
            duration (float, optional): Duration in seconds (alternative to end_time)
            
        Returns:
            str: Path to the extracted clip
        """
        try:
            print(f"[DEBUG] Estrazione clip: {os.path.basename(video_path)}")
            print(f"[DEBUG] Start: {start_time}s, End: {end_time}s, Duration: {duration}s")
            
            if end_time is None and duration is not None:
                end_time = start_time + duration
            
            # Validate clip parameters
            if end_time is not None and end_time <= start_time:
                self.logger.error(f"Invalid clip parameters: start={start_time:.1f}s, end={end_time:.1f}s")
                print(f"[ERROR] Parametri clip non validi: start={start_time:.1f}s, end={end_time:.1f}s")
                raise ValueError("end_time must be greater than start_time")
            
            clip_duration = end_time - start_time if end_time is not None else None
            if clip_duration is not None and clip_duration <= 0:
                self.logger.error(f"Invalid clip duration: {clip_duration:.1f}s")
                print(f"[ERROR] Durata clip non valida: {clip_duration:.1f}s")
                raise ValueError("Clip duration must be positive")
            
            self.logger.info(f"Extracting clip from {start_time:.1f}s to {end_time:.1f}s")
            print(f"[DEBUG] Inizio estrazione clip da {start_time:.1f}s a {end_time:.1f}s")
            
            # Gestione errori MoviePy con try/except
            try:
                # Load the video clip
                video = VideoFileClip(video_path)
                try:
                    # Extract the clip
                    clip = video.subclip(start_time, end_time)
                    
                    # Write the clip to the output path
                    clip.write_videofile(
                        output_path,
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile='temp-audio.m4a',
                        remove_temp=True,
                        fps=clip.fps,
                        threads=4,
                        preset='faster'  # Use 'ultrafast' for even faster processing
                    )
                    
                    # Clean up clips to free memory
                    clip.close()
                finally:
                    video.close()
                
                print(f"[DEBUG] Clip estratta con successo: {os.path.basename(output_path)}")
                    
            except Exception as e:
                print(f"[ERROR] Errore nella creazione della clip: {e}")
                self.logger.error(f"Error in MoviePy clip creation: {e}")
                raise
            
            self.logger.info(f"Clip extracted successfully to {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error extracting clip: {e}")
            print(f"[ERROR] Errore generale estrazione clip: {e}")
            raise
    
    def _parse_srt(self, srt_path):
        """
        Parse SRT subtitle file into a list of subtitles.
        
        Args:
            srt_path (str): Path to the SRT file
            
        Returns:
            list: List of (start_time, end_time, text) tuples
        """
        subtitles = []
        
        try:
            with open(srt_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            blocks = content.strip().split('\n\n')
            
            for block in blocks:
                lines = block.split('\n')
                if len(lines) < 3:
                    continue
                
                # Parse timestamp line (format: 00:00:00,000 --> 00:00:00,000)
                timestamp_line = lines[1]
                start_str, end_str = timestamp_line.split(' --> ')
                
                start_time = self._srt_timestamp_to_seconds(start_str)
                end_time = self._srt_timestamp_to_seconds(end_str)
                
                # Combine all text lines
                text = ' '.join(lines[2:])
                
                subtitles.append((start_time, end_time, text))
            
            return subtitles
            
        except Exception as e:
            self.logger.error(f"Error parsing SRT file: {e}")
            raise
    
    def _srt_timestamp_to_seconds(self, timestamp):
        """
        Convert SRT timestamp to seconds.
        
        Args:
            timestamp (str): SRT timestamp (format: 00:00:00,000)
            
        Returns:
            float: Time in seconds
        """
        try:
            # Replace comma with dot for milliseconds
            timestamp = timestamp.replace(',', '.')
            # Split into time components
            time_parts = timestamp.split(':')
            if len(time_parts) != 3:
                raise ValueError(f"Invalid timestamp format: {timestamp}")
            
            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds = float(time_parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
            
        except Exception as e:
            self.logger.error(f"Error parsing timestamp '{timestamp}': {e}")
            return 0.0
    
    def add_subtitles(self, video_path, srt_path, output_path):
        """
        Add subtitles to a video.
        
        Args:
            video_path (str): Path to the video file
            srt_path (str): Path to the SRT subtitle file
            output_path (str): Path to save the output video
            
        Returns:
            str: Path to the output video
        """
        try:
            self.logger.info(f"Adding subtitles to {os.path.basename(video_path)}")
            
            # Check if MoviePy is available
            if not MOVIEPY_AVAILABLE:
                self.logger.warning("MoviePy not available, copying video without subtitles")
                import shutil
                shutil.copy2(video_path, output_path)
                return output_path
            
            # Load the video
            video = VideoFileClip(video_path)
            
            # Parse subtitles from SRT file
            subtitles = self._parse_srt(srt_path)
            
            # If SubtitlesClip is not available, create subtitles manually
            if SubtitlesClip is None:
                # Create individual subtitle clips manually
                subtitle_clips = []
                
                for start_time, end_time, text in subtitles:
                    # Create text clip
                    txt_clip = TextClip(
                        text, 
                        font=self.font, 
                        fontsize=self.font_size,
                        color=self.font_color,
                        stroke_color='black',
                        stroke_width=1,
                        method='caption',
                        size=(video.w * 0.9, None),  # 90% of video width
                        align='center'
                    ).set_duration(end_time - start_time).set_start(start_time)
                    
                    # Position at bottom of video
                    txt_clip = txt_clip.set_position(('center', video.h * 0.85))
                    subtitle_clips.append(txt_clip)
                
                # Combine video with all subtitle clips
                final_clip = CompositeVideoClip([video] + subtitle_clips)
            else:
                # Use SubtitlesClip if available
                def make_subtitle_clip(txt):
                    return TextClip(
                        txt, 
                        font=self.font, 
                        fontsize=self.font_size,
                        color=self.font_color,
                        stroke_color='black',
                        stroke_width=1,
                        method='caption',
                        size=(video.w * 0.9, None),  # 90% of video width
                        align='center'
                    )
                
                subtitles_clip = SubtitlesClip(
                    subtitles, make_subtitle_clip
                )
                
                # Position subtitles at the bottom of the video
                subtitles_clip = subtitles_clip.set_position(
                    ('center', video.h * 0.85)  # Position at 85% of video height
                )
                
                # Combine video and subtitles
                final_clip = CompositeVideoClip([video, subtitles_clip])
            
            # Write the final video
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video.fps
            )
            
            # Close clips
            final_clip.close()
            video.close()
            
            self.logger.info(f"Subtitles added successfully to {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error adding subtitles: {e}")
            # If subtitle addition fails, copy original video
            try:
                import shutil
                shutil.copy2(video_path, output_path)
                self.logger.info(f"Copied original video without subtitles to {output_path}")
                return output_path
            except Exception as copy_error:
                self.logger.error(f"Failed to copy original video: {copy_error}")
                return None
            raise
    
    def add_highlighted_text(self, video_path, text, output_path, 
                           start_time=None, end_time=None, position='center'):
        """
        Add highlighted text overlay to a video.
        
        Args:
            video_path (str): Path to the video file
            text (str): Text to display
            output_path (str): Path to save the output video
            start_time (float, optional): Start time for text display
            end_time (float, optional): End time for text display
            position (str): Position of text ('top', 'center', 'bottom')
            
        Returns:
            str: Path to the output video
        """
        try:
            self.logger.info(f"Adding highlighted text to {os.path.basename(video_path)}")
            
            # Load the video
            video = VideoFileClip(video_path)
            
            # Set default times if not provided
            if start_time is None:
                start_time = 0
            if end_time is None:
                end_time = video.duration
            
            # Create background for highlighted text
            text_clip = TextClip(
                text, 
                font=self.font, 
                fontsize=int(self.font_size * 1.5),  # Larger font for highlight
                color=self.font_color,
                stroke_color='black',
                stroke_width=1.5,
                method='caption',
                size=(video.w * 0.8, None),  # 80% of video width
                align='center'
            )
            
            # Create highlight background
            bg_color = self.highlight_color
            padding = 20
            bg_width = text_clip.w + padding * 2
            bg_height = text_clip.h + padding
            bg_clip = ColorClip(
                size=(bg_width, bg_height),
                color=bg_color
            )
            
            # Position text on background
            text_clip = text_clip.set_position('center')
            
            # Combine background and text
            highlight_clip = CompositeVideoClip(
                [bg_clip, text_clip],
                size=bg_clip.size
            )
            
            # Set position based on parameter
            if position == 'top':
                pos = ('center', video.h * 0.15)  # 15% from top
            elif position == 'bottom':
                pos = ('center', video.h * 0.7)  # 70% from top
            else:  # center
                pos = ('center', video.h * 0.4)  # 40% from top
                
            # Set timing for the highlight
            highlight_clip = (
                highlight_clip
                .set_position(pos)
                .set_start(start_time)
                .set_end(end_time)
            )
            
            # Add highlight to video
            final_clip = CompositeVideoClip([video, highlight_clip])
            
            # Write the final video
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video.fps
            )
            
            # Close clips
            final_clip.close()
            video.close()
            highlight_clip.close()
            
            self.logger.info(f"Highlighted text added successfully to {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error adding highlighted text: {e}")
            raise
    
    def find_optimal_clip_segments(self, video_duration, key_moments, desired_duration):
        """
        Find optimal segments for creating clips of desired duration.
        Prioritizes including key moments.
        
        Args:
            video_duration (float): Total video duration in seconds
            key_moments (list): List of key moments with start and end times
            desired_duration (int): Desired clip duration in seconds
            
        Returns:
            list: List of (start_time, end_time) tuples for clips
        """
        print(f"[DEBUG] Durata video: {video_duration}")
        print(f"[DEBUG] Key moments trovati: {len(key_moments) if key_moments else 0}")
        print(f"[DEBUG] Durata desiderata clip: {desired_duration}")
        
        # Check for invalid video duration
        if video_duration <= 0:
            self.logger.error(f"Invalid video duration: {video_duration}")
            print(f"[ERROR] Durata video non valida: {video_duration}")
            return []
        
        # If video is shorter than desired duration, return the whole video (with minimum 1 second)
        if video_duration <= desired_duration:
            if video_duration <= 1:  # Avoid very short or zero duration clips
                self.logger.warning(f"Video too short ({video_duration:.1f}s), skipping clip creation")
                print(f"[WARNING] Video troppo corto ({video_duration:.1f}s), salto creazione clip")
                return []
            print(f"[DEBUG] Video più corto della durata desiderata, ritorno video intero: (0, {video_duration})")
            return [(0, video_duration)]
        
        # If no key moments, create fallback segments
        if not key_moments:
            print("[ClipEngine] Nessun key moment trovato. Creo segmenti di fallback.")
            segments = []
            
            # Always create at least one clip from the beginning (fallback strategy)
            fallback_duration = min(desired_duration, video_duration)
            segments.append((0, fallback_duration))
            
            # Add more segments if video is long enough
            for start in range(desired_duration, int(video_duration - desired_duration) + 1, desired_duration):
                end = min(start + desired_duration, video_duration)
                segments.append((start, end))
            
            print(f"[DEBUG] Segmenti fallback generati: {segments}")
            return segments
        
        # Sort key moments by start time
        key_moments = sorted(key_moments, key=lambda x: x['start'])
        
        # Try to create clips centered around key moments
        segments = []
        for moment in key_moments:
            moment_center = (moment['start'] + moment['end']) / 2
            half_duration = desired_duration / 2
            
            # Calculate potential segment
            start = max(0, moment_center - half_duration)
            end = min(video_duration, start + desired_duration)
            
            # Adjust start if needed
            if end == video_duration and end - start < desired_duration:
                start = max(0, video_duration - desired_duration)
            
            # Check if this segment overlaps with existing segments
            overlap = False
            for existing_start, existing_end in segments:
                if (start < existing_end and end > existing_start):
                    overlap = True
                    break
            
            if not overlap:
                segments.append((start, end))
        
        # GESTIONE FALLBACK: Se non abbiamo trovato segmenti, crea clip dai primi 15 secondi
        if not segments:
            print("[ClipEngine] Nessuna clip virale trovata. Creo una clip fallback dai primi 15 secondi.")
            fallback_duration = min(15, video_duration)  # Prendi al massimo 15 secondi o meno se il video è più corto
            segments.append((0, fallback_duration))
        
        # If we don't have enough segments, add more from remaining parts
        elif len(segments) < 2:  # Relax: assicuriamoci di avere almeno 2 clip se possibile
            # Sort segments by start time
            segments.sort(key=lambda x: x[0])
            
            # Find gaps between segments
            gaps = []
            if len(segments) > 0:
                for i in range(len(segments) - 1):
                    gap_start = segments[i][1]
                    gap_end = segments[i + 1][0]
                    gap_duration = gap_end - gap_start
                    
                    if gap_duration >= desired_duration:
                        gaps.append((gap_start, gap_end))
                
                # Also check gap at the beginning and end
                if segments[0][0] > desired_duration:
                    gaps.append((0, segments[0][0]))
                
                if video_duration - segments[-1][1] > desired_duration:
                    gaps.append((segments[-1][1], video_duration))
                
                # Add segments from gaps
                for gap_start, gap_end in gaps:
                    # If gap is bigger than desired duration, take the middle
                    if gap_end - gap_start > desired_duration:
                        mid_point = (gap_start + gap_end) / 2
                        new_start = max(0, mid_point - desired_duration/2)
                        new_end = min(video_duration, new_start + desired_duration)
                        segments.append((new_start, new_end))
                    else:
                        segments.append((gap_start, gap_end))
        
        # FALLBACK FINALE: Se ancora non abbiamo segmenti, forza almeno una clip
        if not segments:
            print("[EMERGENCY FALLBACK] Nessun segmento trovato, forzo creazione clip di emergenza")
            emergency_duration = min(desired_duration, video_duration)
            segments = [(0, emergency_duration)]
        
        # Sort segments by start time
        segments.sort(key=lambda x: x[0])
        
        print(f"[DEBUG] Segmenti finali generati: {segments}")
        
        return segments
    
    def process_source_video(self, video_id, transcription, viral_analysis):
        """
        Process a source video into multiple clips with subtitles and highlights.
        
        Args:
            video_id (int): ID of the source video in the database
            transcription (dict): Transcription data with segments
            viral_analysis (dict): Viral potential analysis
            
        Returns:
            list: List of processed clip IDs
        """
        try:
            # Get source video from database
            source_video = self.db.execute_query(
                "SELECT * FROM source_videos WHERE id = ?", 
                (video_id,)
            )[0]
            
            video_path = source_video['file_path']
            srt_path = transcription.get('srt_path')
            
            if not os.path.exists(video_path):
                self.logger.error(f"Source video file not found: {video_path}")
                return []
                
            if not os.path.exists(srt_path):
                self.logger.error(f"Subtitle file not found: {srt_path}")
                return []
            
            # Load video to get duration
            video = VideoFileClip(video_path)
            try:
                video_duration = video.duration
                print(f"[DEBUG] Video caricato: {os.path.basename(video_path)}")
                print(f"[DEBUG] Durata video rilevata: {video_duration}s")
                
                # CONTROLLO CRITICO: Se la durata è 0 o None, qualcosa è andato storto
                if not video_duration or video_duration <= 0:
                    self.logger.error(f"Video duration is invalid: {video_duration}")
                    print(f"[CRITICAL ERROR] Durata video non valida: {video_duration}")
                    print("[Fallback] Nessuna clip virale trovata. Creo una clip di backup da 0 a 15 secondi.")
                    
                    # Prova comunque a creare una clip di fallback assumendo una durata minima
                    video_duration = 15  # Assumiamo che il video abbia almeno 15 secondi
                    print(f"[FALLBACK] Assumo durata video di {video_duration}s per il fallback")
                    
            finally:
                video.close()
            
            # Get key moments from transcription
            key_moments = transcription.get('key_moments', [])
            if not key_moments and 'segments' in transcription:
                # Create key moments from segments if not provided
                segments = transcription['segments']
                # Use top 3 segments with highest words/second as key moments
                segments_with_density = []
                for segment in segments:
                    duration = segment['end'] - segment['start']
                    word_count = len(segment['text'].split())
                    if duration > 0:
                        word_density = word_count / duration
                        segments_with_density.append((segment, word_density))
                
                # Sort by word density
                segments_with_density.sort(key=lambda x: x[1], reverse=True)
                
                # Take top 3
                key_moments = [
                    {
                        'start': s['start'],
                        'end': s['end'],
                        'text': s['text']
                    }
                    for s, _ in segments_with_density[:3]
                ]
            
            # Get enabled clip durations
            clip_durations = [
                int(dur) for dur, enabled 
                in self.config['video_processing']['clip_durations'].items()
                if enabled
            ]
            
            if not clip_durations:
                self.logger.warning("No clip durations enabled, using 30 seconds")
                clip_durations = [30]
            
            self.logger.info(f"Processing source video {video_id} into clips with durations: {clip_durations}")
            
            processed_clip_ids = []
            
            # Create clips for each duration
            for duration in clip_durations:
                print(f"[DEBUG] === Processando durata: {duration}s ===")
                # Find optimal segments for this duration
                segments = self.find_optimal_clip_segments(
                    video_duration, key_moments, duration
                )
                
                if not segments:
                    print("[Fallback] Nessuna clip virale trovata. Creo una clip di backup da 0 a 15 secondi.")
                    segments = [(0, 15)]
                
                self.logger.info(f"Creating {len(segments)} clips of {duration}s duration")
                
                # Process each segment
                for i, (start_time, end_time) in enumerate(segments):
                    print(f"[DEBUG] --- Processando clip {i+1}/{len(segments)} ---")
                    print(f"[DEBUG] Segmento: {start_time:.1f}s - {end_time:.1f}s")
                    
                    try:
                        # Generate filenames
                        base_name = f"{os.path.splitext(os.path.basename(video_path))[0]}"
                        clip_filename = f"{base_name}_clip_{duration}s_{i+1}.mp4"
                        clip_path = os.path.join(self.processed_dir, clip_filename)
                        
                        print(f"[DEBUG] File output: {clip_filename}")
                        
                        # Extract the clip
                        self.extract_clip(
                            video_path, clip_path, 
                            start_time=start_time, 
                            end_time=end_time
                        )
                        
                        # Adjust SRT timings for the clip
                        clip_srt_filename = f"{base_name}_clip_{duration}s_{i+1}.srt"
                        clip_srt_path = os.path.join(self.processed_dir, clip_srt_filename)
                        self._adjust_srt_timing(
                            srt_path, clip_srt_path, 
                            -start_time, end_time - start_time
                        )
                        
                        # Add subtitles to the clip
                        subtitled_filename = f"{base_name}_clip_{duration}s_{i+1}_sub.mp4"
                        subtitled_path = os.path.join(self.processed_dir, subtitled_filename)
                        
                        self.add_subtitles(
                            clip_path, clip_srt_path, subtitled_path
                        )
                        
                        # Add highlighted text for key moments in this clip
                        final_path = subtitled_path
                        
                        if self.config['video_processing']['add_highlighted_text']:
                            for moment in key_moments:
                                # Check if key moment is in this clip
                                moment_start = moment['start']
                                moment_end = moment['end']
                                
                                if (moment_start >= start_time and moment_start < end_time) or \
                                   (moment_end > start_time and moment_end <= end_time):
                                    
                                    # Adjust times relative to clip
                                    relative_start = max(0, moment_start - start_time)
                                    relative_end = min(end_time - start_time, moment_end - start_time)
                                    
                                    # Add highlighted text
                                    highlighted_filename = (
                                        f"{base_name}_clip_{duration}s_{i+1}_sub_hl.mp4"
                                    )
                                    highlighted_path = os.path.join(
                                        self.processed_dir, highlighted_filename
                                    )
                                    
                                    self.add_highlighted_text(
                                        final_path,
                                        moment['text'],
                                        highlighted_path,
                                        start_time=relative_start,
                                        end_time=relative_end,
                                        position='center'
                                    )
                                    
                                    # Update final path
                                    final_path = highlighted_path
                        
                        # Calculate viral score for this clip
                        # Base score on the viral analysis
                        base_score = viral_analysis.get('viral_score', 50)
                        
                        # Adjust score based on clip position
                        # (beginning of video often has higher retention)
                        position_factor = 1 - (start_time / video_duration) * 0.3
                        
                        # Adjust score based on inclusion of key moments
                        key_moment_count = sum(
                            1 for moment in key_moments
                            if moment['start'] >= start_time and moment['end'] <= end_time
                        )
                        key_moment_factor = 1 + (key_moment_count * 0.1)
                        
                        # Calculate final score (capped at 100)
                        viral_score = min(100, base_score * position_factor * key_moment_factor)
                        
                        # Add processed clip to database
                        clip_data = {
                            'source_id': video_id,
                            'clip_duration': duration,
                            'start_time': int(start_time),
                            'end_time': int(end_time),
                            'file_path': final_path,
                            'subtitle_path': clip_srt_path,
                            'created_at': None,  # Will be set by database
                            'viral_score': viral_score,
                            # Title, description, hashtags will be added later by GPT
                        }
                        
                        clip_id = self.db.add_processed_clip(clip_data)
                        
                        processed_clip_ids.append(clip_id)
                        
                        self.logger.info(f"Created processed clip {clip_id} with viral score {viral_score:.1f}")
                        print(f"[SUCCESS] Clip {i+1} creata con successo! ID: {clip_id}, Score: {viral_score:.1f}")
                        
                    except Exception as e:
                        self.logger.error(f"Error processing clip {i+1}: {e}")
                        print(f"[ERROR] Errore processando clip {i+1}: {e}")
                        # Non fermiamo il processo, continuiamo con le altre clip
            
            print(f"[FINAL] Processamento completato. {len(processed_clip_ids)} clip create totali.")
            return processed_clip_ids
            
        except Exception as e:
            self.logger.error(f"Error processing source video {video_id}: {e}")
            raise
    
    def _adjust_srt_timing(self, input_srt, output_srt, offset, max_duration=None):
        """
        Adjust SRT subtitle timing with an offset and optionally clip to max duration.
        
        Args:
            input_srt (str): Path to input SRT file
            output_srt (str): Path to output SRT file
            offset (float): Time offset in seconds (can be negative)
            max_duration (float, optional): Maximum duration to include
        """
        try:
            # Parse input SRT
            subtitles = self._parse_srt(input_srt)
            
            # Apply offset and filter by max_duration
            adjusted_subtitles = []
            for i, (start_time, end_time, text) in enumerate(subtitles):
                new_start = max(0, start_time + offset)
                new_end = end_time + offset
                
                # Skip if entirely before 0
                if new_end <= 0:
                    continue
                
                # Skip if after max_duration
                if max_duration is not None and new_start >= max_duration:
                    continue
                
                # Clip to max_duration if needed
                if max_duration is not None and new_end > max_duration:
                    new_end = max_duration
                
                adjusted_subtitles.append((new_start, new_end, text))
            
            # Write adjusted SRT
            with open(output_srt, 'w', encoding='utf-8') as file:
                for i, (start_time, end_time, text) in enumerate(adjusted_subtitles, 1):
                    # Format timestamps
                    start_str = self._seconds_to_srt_timestamp(start_time)
                    end_str = self._seconds_to_srt_timestamp(end_time)
                    
                    # Write SRT entry
                    file.write(f"{i}\n")
                    file.write(f"{start_str} --> {end_str}\n")
                    file.write(f"{text}\n\n")
            
            self.logger.debug(f"Adjusted SRT timing in {os.path.basename(output_srt)}")
            
        except Exception as e:
            self.logger.error(f"Error adjusting SRT timing: {e}")
            raise
    
    def _seconds_to_srt_timestamp(self, seconds):
        """
        Convert seconds to SRT timestamp format (HH:MM:SS,mmm).
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Formatted timestamp
        """
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        seconds_remainder = seconds % 60
        milliseconds = int((seconds_remainder - int(seconds_remainder)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds_remainder):02d},{milliseconds:03d}"
    
    def generate_thumbnail(self, video_path, output_path=None):
        """
        Generate a thumbnail from a video.
        
        Args:
            video_path (str): Path to the video file
            output_path (str, optional): Path to save the thumbnail
            
        Returns:
            str: Path to the generated thumbnail
        """
        try:
            # If output path not provided, create one
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_path = os.path.join(
                    os.path.dirname(video_path), 
                    f"{base_name}_thumbnail.jpg"
                )
            
            self.logger.info(f"Generating thumbnail for {os.path.basename(video_path)}")
            
            # Load the video
            video = VideoFileClip(video_path)
            try:
                # Get duration
                duration = video.duration
                
                # Take frame from middle of the video
                middle_time = duration / 2
                
                # Extract the frame
                thumbnail = video.get_frame(middle_time)
                
                # Save as image
                image_clip = ImageClip(thumbnail)
                image_clip.save_frame(output_path)
            finally:
                video.close()
                
            self.logger.info(f"Thumbnail generated at {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating thumbnail: {e}")
            raise
