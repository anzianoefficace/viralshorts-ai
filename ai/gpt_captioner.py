"""
GPT-4 integration module for ViralShortsAI.
Handles content generation for titles, descriptions, hashtags, and text overlays.
"""

import os
import json
import time
from dotenv import load_dotenv

import openai
from utils import app_logger

# Load environment variables
load_dotenv()

class GPTCaptioner:
    """
    Class to handle content generation using OpenAI's GPT-4 API.
    Generates titles, descriptions, hashtags, and text overlays for videos.
    """
    
    def __init__(self, config):
        """
        Initialize the GPT captioner.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.logger = app_logger
        
        # Set OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.logger.info("GPT captioner initialized")
        
        # Default model - Using GPT-3.5-turbo instead of GPT-4
        self.model = "gpt-3.5-turbo"
        
        # Rate limiting parameters
        self.request_count = 0
        self.rate_limit = 50  # requests per minute (adjust based on your tier)
        self.rate_limit_interval = 60  # seconds
        self.last_reset = time.time()
    
    def _rate_limit_check(self):
        """
        Check and enforce rate limits for API calls.
        Implements a simple token bucket algorithm.
        """
        current_time = time.time()
        time_passed = current_time - self.last_reset
        
        # Reset counter if interval has passed
        if time_passed > self.rate_limit_interval:
            self.request_count = 0
            self.last_reset = current_time
        
        # Check if we're at the rate limit
        if self.request_count >= self.rate_limit:
            sleep_time = self.rate_limit_interval - time_passed
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_reset = time.time()
        
        self.request_count += 1
    
    def generate_content(self, prompt, max_tokens=300, temperature=0.7):
        """
        Generate content using GPT-4.
        
        Args:
            prompt (str): The prompt for content generation
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Controls randomness (0.0-1.0)
            
        Returns:
            str: Generated text content
        """
        self._rate_limit_check()
        
        try:
            self.logger.info(f"Generating content with prompt: {prompt[:50]}...")
            print(f"[GPT] Invio richiesta a OpenAI con prompt: {prompt[:100]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a viral social media content creator specializing in short-form video content. Your goal is to create engaging, attention-grabbing titles, descriptions, and hashtags that will make videos go viral."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content.strip()
            print(f"[GPT Response] Risposta ricevuta: {content[:200]}...")
            
            self.logger.info("Content generation successful")
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            raise
    
    def generate_video_metadata(self, clip_info, transcription):
        """
        Generate title, description, and hashtags for a video clip.
        
        Args:
            clip_info (dict): Information about the video clip
            transcription (dict): Transcription of the clip
            
        Returns:
            dict: Generated metadata (title, description, hashtags)
        """
        # Extract transcript text
        transcript = ""
        for segment in transcription.get('segments', []):
            transcript += segment.get('text', '') + " "
        transcript = transcript.strip()
        
        # Create a prompt for GPT-4
        category = clip_info.get('category', 'Entertainment')
        duration = clip_info.get('clip_duration', 60)
        
        prompt = f"""
Create viral YouTube Shorts metadata for a {duration}-second video in the {category} category.

VIDEO TRANSCRIPT:
"{transcript}"

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
TITLE: [attention-grabbing title, max 100 characters]
DESCRIPTION: [1-2 compelling sentences about the content]
HASHTAGS: [8-10 relevant hashtags separated by commas, starting with #]

Make the title catchy, emotional, and curiosity-inducing. Use powerful action words, numbers, or questions when appropriate.
The hashtags should include a mix of trending and specific terms related to the video content.
"""

        # Add custom hashtags if available
        custom_hashtags = self.config['upload'].get('custom_hashtags', [])
        if custom_hashtags:
            hashtags_str = ', '.join(custom_hashtags)
            prompt += f"\nInclude these custom hashtags: {hashtags_str}"
        
        # Generate content
        content = self.generate_content(prompt, max_tokens=500)
        
        # Parse the response
        title = ""
        description = ""
        hashtags = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('TITLE:'):
                title = line[6:].strip()
            elif line.startswith('DESCRIPTION:'):
                description = line[12:].strip()
            elif line.startswith('HASHTAGS:'):
                hashtags_text = line[9:].strip()
                # Clean and parse hashtags
                hashtags = [
                    tag.strip() 
                    for tag in hashtags_text.replace(' ', '').split(',')
                    if tag.strip()
                ]
                # Add # if missing
                hashtags = [
                    tag if tag.startswith('#') else f"#{tag}" 
                    for tag in hashtags
                ]
        
        # Ensure title isn't too long
        if len(title) > 100:
            title = title[:97] + '...'
        
        self.logger.info(f"Generated metadata: {title}")
        
        return {
            'title': title,
            'description': description,
            'hashtags': hashtags
        }
    
    def generate_text_overlay(self, segment_text, max_length=70):
        """
        Generate a shorter, punchier text overlay from transcript segment.
        
        Args:
            segment_text (str): Original transcript segment text
            max_length (int): Maximum length of overlay text
            
        Returns:
            str: Text overlay content
        """
        if len(segment_text) <= max_length:
            return segment_text
            
        prompt = f"""
Convert this transcript segment into a short, punchy text overlay for a viral video.
Make it attention-grabbing, clear, and concise (maximum {max_length} characters).
Maintain the key message but make it more impactful.

ORIGINAL TEXT:
"{segment_text}"

TEXT OVERLAY:
"""
        
        try:
            overlay_text = self.generate_content(
                prompt, max_tokens=100, temperature=0.5
            )
            
            # Clean up the response and ensure it's not too long
            overlay_text = overlay_text.strip()
            if overlay_text.startswith('"') and overlay_text.endswith('"'):
                overlay_text = overlay_text[1:-1]
            
            if len(overlay_text) > max_length:
                overlay_text = overlay_text[:max_length-3] + '...'
                
            return overlay_text
            
        except Exception as e:
            self.logger.warning(f"Failed to generate overlay text: {e}")
            # Fall back to truncated original text
            return segment_text[:max_length-3] + '...'
    
    def analyze_viral_potential(self, transcription, category):
        """
        Analyze the viral potential of a video based on its transcription.
        
        Args:
            transcription (dict): Transcription of the video
            category (str): Video category
            
        Returns:
            dict: Analysis results with scores and insights
        """
        # Extract transcript text
        transcript = ""
        for segment in transcription.get('segments', []):
            transcript += segment.get('text', '') + " "
        transcript = transcript.strip()
        
        # Limit transcript length for API efficiency
        if len(transcript) > 3000:
            transcript = transcript[:3000] + "..."
        
        prompt = f"""
Analyze this {category} video transcript for viral potential on short-form platforms.

TRANSCRIPT:
"{transcript}"

Rate on a scale of 1-100 for each category and provide brief reasoning:
1. Hook Strength: How well does it grab attention in first 3 seconds?
2. Emotional Appeal: How emotionally engaging is the content?
3. Curiosity Factor: How much does it make viewers want to keep watching?
4. Relevance: How relevant is it to current trends?
5. Shareability: How likely would viewers share this?
6. Overall Viral Score: Weighted average of above scores

FORMAT YOUR RESPONSE EXACTLY AS:
HOOK_SCORE: [1-100]
HOOK_REASON: [brief explanation]
EMOTIONAL_SCORE: [1-100]
EMOTIONAL_REASON: [brief explanation]
CURIOSITY_SCORE: [1-100]
CURIOSITY_REASON: [brief explanation]
RELEVANCE_SCORE: [1-100]
RELEVANCE_REASON: [brief explanation]
SHAREABILITY_SCORE: [1-100]
SHAREABILITY_REASON: [brief explanation]
VIRAL_SCORE: [1-100]
KEY_INSIGHT: [one key suggestion to improve viral potential]
"""
        
        try:
            analysis = self.generate_content(prompt, max_tokens=800)
            print(f"[GPT Response] Analisi virale ricevuta: {analysis}")
            
            # Parse the response
            result = {}
            current_key = None
            
            for line in analysis.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    # Convert scores to integers
                    if key.endswith('_score'):
                        try:
                            value = int(value)
                        except ValueError:
                            # Try to extract the number if there's text
                            import re
                            match = re.search(r'\d+', value)
                            if match:
                                value = int(match.group())
                            else:
                                value = 50  # Default if parsing fails
                    
                    result[key] = value
            
            # RELAX ALGORITMO: Se tutti i punteggi sono bassi, aumenta il viral_score
            viral_score = result.get('viral_score', 50)
            if viral_score < 30:  # Soglia relax abbassata
                print(f"[RELAX] Punteggio virale troppo basso ({viral_score}), aumento a 35")
                result['viral_score'] = 35
                
            print(f"[DEBUG] Punteggi analisi virale: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing viral potential: {e}")
            print(f"[ERROR] Errore nell'analisi virale: {e}")
            # Return default values if analysis fails (FALLBACK COMPLETO)
            fallback_result = {
                'hook_score': 60,        # Valori più ottimistici per fallback
                'emotional_score': 55,
                'curiosity_score': 50,
                'relevance_score': 45,
                'shareability_score': 50,
                'viral_score': 52,       # Punteggio medio-alto di fallback
                'key_insight': "Analysis failed due to error - using fallback scoring"
            }
            print(f"[FALLBACK] Usando punteggi di fallback: {fallback_result}")
            return fallback_result
