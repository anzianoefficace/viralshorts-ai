"""
Whisper transcription module for ViralShortsAI.
Handles audio transcription and speech-to-text conversion using OpenAI's Whisper model.
"""

import os
import ssl
import time
import json
import tempfile
from pathlib import Path

import whisper
import ffmpeg
import numpy as np
from dotenv import load_dotenv

from utils import app_logger

# Load environment variables
load_dotenv()

class WhisperTranscriber:
    """
    Class to handle audio transcription using OpenAI's Whisper model.
    Supports local processing with the whisper library.
    """
    
    def __init__(self, config):
        """
        Initialize the Whisper transcriber.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.logger = app_logger
        self.model_size = "base"  # Options: tiny, base, small, medium, large
        self.model = None
        self.logger.info(f"Initializing Whisper transcriber with {self.model_size} model")
    
    def load_model(self):
        """
        Load the Whisper model if not already loaded.
        """
        if self.model is None:
            self.logger.info(f"Loading Whisper {self.model_size} model...")
            try:
                # Configure SSL context to avoid certificate verification issues
                ssl._create_default_https_context = ssl._create_unverified_context
                self.model = whisper.load_model(self.model_size)
                self.logger.info("Whisper model loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading Whisper model: {e}")
                raise
    
    def extract_audio(self, video_path, output_path=None):
        """
        Extract audio from video file using ffmpeg.
        
        Args:
            video_path (str): Path to the video file
            output_path (str, optional): Path to save the audio file
            
        Returns:
            str: Path to the extracted audio file
        """
        if output_path is None:
            # Create a temporary file with .wav extension
            fd, output_path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
        
        try:
            self.logger.info(f"Extracting audio from {os.path.basename(video_path)}")
            
            # Use ffmpeg to extract audio
            (
                ffmpeg
                .input(video_path)
                .output(output_path, acodec='pcm_s16le', ac=1, ar='16k')
                .global_args('-loglevel', 'error')
                .run(quiet=True, overwrite_output=True)
            )
            
            self.logger.info(f"Audio extracted successfully to {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error extracting audio: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise
    
    def transcribe_audio(self, audio_path, language=None):
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_path (str): Path to the audio file
            language (str, optional): Language code (e.g., 'en', 'es')
            
        Returns:
            dict: Transcription result with segments
        """
        self.load_model()  # Make sure model is loaded
        
        if language is None:
            language = self.config['app_settings']['selected_language']
        
        try:
            self.logger.info(f"Transcribing audio in {language}...")
            
            # Transcribe audio
            options = {
                'language': language,
                'task': 'transcribe',
                'verbose': False
            }
            
            result = self.model.transcribe(audio_path, **options)
            
            self.logger.info("Audio transcription completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            raise
    
    def transcribe_video(self, video_path, language=None, save_srt=True, output_dir=None):
        """
        Transcribe a video file using Whisper.
        
        Args:
            video_path (str): Path to the video file
            language (str, optional): Language code
            save_srt (bool): Whether to save SRT subtitle file
            output_dir (str, optional): Directory to save SRT file
            
        Returns:
            dict: Transcription result with segments and subtitle path
        """
        try:
            # Extract audio from video
            audio_path = self.extract_audio(video_path)
            
            # Transcribe the audio
            result = self.transcribe_audio(audio_path, language)
            
            # Clean up temporary audio file
            os.remove(audio_path)
            
            # Save as SRT if requested
            srt_path = None
            if save_srt:
                if output_dir is None:
                    output_dir = os.path.dirname(video_path)
                
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                srt_path = os.path.join(output_dir, f"{base_name}.srt")
                
                self.save_as_srt(result, srt_path)
                result['srt_path'] = srt_path
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error transcribing video: {e}")
            raise
    
    def save_as_srt(self, result, output_path):
        """
        Save transcription result as SRT subtitle file.
        
        Args:
            result (dict): Transcription result from Whisper
            output_path (str): Path to save the SRT file
        """
        try:
            self.logger.info(f"Saving subtitles to {os.path.basename(output_path)}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(result['segments'], start=1):
                    # Format start and end time
                    start_time = self._format_timestamp(segment['start'])
                    end_time = self._format_timestamp(segment['end'])
                    
                    # Write SRT entry
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text'].strip()}\n\n")
            
            self.logger.info("Subtitles saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving SRT file: {e}")
            raise
    
    def _format_timestamp(self, seconds):
        """
        Format seconds as SRT timestamp (HH:MM:SS,mmm).
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Formatted timestamp
        """
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"
    
    def get_word_level_timestamps(self, audio_path, language=None):
        """
        Get word-level timestamps for precise alignment.
        
        Args:
            audio_path (str): Path to the audio file
            language (str, optional): Language code
            
        Returns:
            list: List of words with timestamps
        """
        self.load_model()  # Make sure model is loaded
        
        if language is None:
            language = self.config['app_settings']['selected_language']
        
        try:
            self.logger.info(f"Getting word-level timestamps for {os.path.basename(audio_path)}...")
            
            # Use faster model for alignment
            options = {
                'language': language,
                'task': 'transcribe',
                'verbose': False,
                'word_timestamps': True,  # Enable word timestamps
            }
            
            result = self.model.transcribe(audio_path, **options)
            
            # Extract words with timestamps
            words = []
            for segment in result.get('segments', []):
                for word in segment.get('words', []):
                    words.append({
                        'word': word.get('word', '').strip(),
                        'start': word.get('start', 0),
                        'end': word.get('end', 0),
                        'confidence': word.get('confidence', 0)
                    })
            
            self.logger.info(f"Found timestamps for {len(words)} words")
            return words
            
        except Exception as e:
            self.logger.error(f"Error getting word timestamps: {e}")
            raise
    
    def find_key_moments(self, transcription, top_n=3):
        """
        Find key moments in the video based on transcript.
        Uses a simple heuristic based on sentence length and keywords.
        
        Args:
            transcription (dict): Transcription result from Whisper
            top_n (int): Number of key moments to find
            
        Returns:
            list: List of key moments with timestamps
        """
        # Keywords that might indicate important moments
        highlight_keywords = [
            "amazing", "incredible", "shocking", "must see", "wait for it",
            "watch this", "look at", "best", "worst", "never", "ever",
            "insane", "viral", "trending", "wow", "omg", "awesome"
        ]
        
        segments = transcription.get('segments', [])
        
        # Score each segment
        scored_segments = []
        for segment in segments:
            text = segment.get('text', '').lower()
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            
            # Skip very short segments
            if end - start < 1.5:
                continue
            
            # Base score on segment length (longer often more important)
            score = len(text.split()) * 0.2
            
            # Check for highlight keywords
            for keyword in highlight_keywords:
                if keyword in text:
                    score += 2
            
            # Check for question marks (often indicate key points)
            if '?' in text:
                score += 2
                
            # Check for exclamation marks
            if '!' in text:
                score += 2
            
            scored_segments.append({
                'start': start,
                'end': end,
                'text': segment.get('text', '').strip(),
                'score': score
            })
        
        # Sort by score and get top N
        scored_segments.sort(key=lambda x: x['score'], reverse=True)
        key_moments = scored_segments[:top_n]
        
        # Sort by timestamp for better usability
        key_moments.sort(key=lambda x: x['start'])
        
        self.logger.info(f"Found {len(key_moments)} key moments in transcription")
        return key_moments
