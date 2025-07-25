"""
🔧 OpenAI Fallback System per ViralShortsAI
Sistema di fallback intelligente quando l'API OpenAI non è disponibile
"""

import logging
import json
from typing import Dict, Any, Optional
import re

app_logger = logging.getLogger('ViralShortsAI')

class OpenAIFallbackEngine:
    """
    Sistema di fallback intelligente per sostituire OpenAI quando non disponibile
    """
    
    def __init__(self):
        self.viral_keywords = {
            'sports': ['goal', 'score', 'win', 'champion', 'incredible', 'amazing', 'best', 'unbelievable'],
            'entertainment': ['funny', 'hilarious', 'crazy', 'epic', 'viral', 'trending', 'must watch'],
            'news': ['breaking', 'urgent', 'exclusive', 'shocking', 'revealed', 'exposed'],
            'lifestyle': ['life hack', 'secret', 'tips', 'tricks', 'genius', 'game changer'],
            'general': ['wow', 'omg', 'insane', 'mind blown', 'you won\'t believe', 'this will shock you']
        }
        
        self.viral_patterns = {
            'question_hook': ['What happens when', 'Can you believe', 'Did you know', 'Have you seen'],
            'emotional_hook': ['This made me cry', 'I can\'t stop laughing', 'This is heartbreaking', 'So inspiring'],
            'urgency_hook': ['Don\'t miss this', 'Watch before it\'s deleted', 'Going viral right now'],
            'curiosity_hook': ['The ending will surprise you', 'Plot twist', 'Wait for it', 'You have to see this']
        }
    
    def analyze_viral_potential(self, transcript: str, title: str = "", category: str = "general") -> Dict[str, Any]:
        """
        Analizza il potenziale virale usando algoritmi locali
        """
        try:
            # Analisi lunghezza e struttura
            word_count = len(transcript.split())
            hook_score = self._analyze_hook_strength(transcript, title)
            emotional_score = self._analyze_emotional_appeal(transcript)
            curiosity_score = self._analyze_curiosity_factor(transcript)
            relevance_score = self._analyze_relevance(transcript, category)
            shareability_score = self._analyze_shareability(transcript)
            
            # Calcolo punteggio virale ponderato
            viral_score = int(
                hook_score * 0.25 +
                emotional_score * 0.20 +
                curiosity_score * 0.20 +
                relevance_score * 0.15 +
                shareability_score * 0.20
            )
            
            # Genera insight miglioramento
            key_insight = self._generate_improvement_insight(
                hook_score, emotional_score, curiosity_score, relevance_score, shareability_score
            )
            
            result = {
                'hook_score': hook_score,
                'hook_reason': f'Content opening analyzed for attention-grabbing potential',
                'emotional_score': emotional_score,
                'emotional_reason': f'Emotional engagement assessment based on content analysis',
                'curiosity_score': curiosity_score,
                'curiosity_reason': f'Curiosity factor evaluated through content structure',
                'relevance_score': relevance_score,
                'relevance_reason': f'Relevance to {category} category and current trends',
                'shareability_score': shareability_score,
                'shareability_reason': f'Shareability potential based on viral indicators',
                'viral_score': viral_score,
                'key_insight': key_insight
            }
            
            app_logger.info(f"✅ Fallback viral analysis completed: score {viral_score}/100")
            return result
            
        except Exception as e:
            app_logger.error(f"Error in fallback viral analysis: {e}")
            return self._get_default_scores()
    
    def _analyze_hook_strength(self, transcript: str, title: str) -> int:
        """Analizza la forza dell'hook iniziale"""
        text = (title + " " + transcript).lower()
        score = 40  # Base score
        
        # Check for question hooks
        if any(pattern.lower() in text for pattern in self.viral_patterns['question_hook']):
            score += 20
        
        # Check for emotional hooks
        if any(pattern.lower() in text for pattern in self.viral_patterns['emotional_hook']):
            score += 15
        
        # Check for urgency
        if any(pattern.lower() in text for pattern in self.viral_patterns['urgency_hook']):
            score += 15
        
        # Check for numbers (statistics hook)
        if re.search(r'\d+%|\d+ million|\d+ billion', text):
            score += 10
        
        return min(score, 95)
    
    def _analyze_emotional_appeal(self, transcript: str) -> int:
        """Analizza l'appeal emotivo del contenuto"""
        text = transcript.lower()
        score = 45  # Base score
        
        # Positive emotions
        positive_words = ['amazing', 'incredible', 'beautiful', 'awesome', 'fantastic', 'wonderful']
        positive_count = sum(1 for word in positive_words if word in text)
        score += min(positive_count * 8, 25)
        
        # Emotional intensity
        intense_words = ['shocking', 'unbelievable', 'insane', 'crazy', 'mind-blowing']
        intense_count = sum(1 for word in intense_words if word in text)
        score += min(intense_count * 10, 20)
        
        # Personal pronouns (relatability)
        personal_count = text.count('you') + text.count('your') + text.count('we') + text.count('us')
        score += min(personal_count * 2, 10)
        
        return min(score, 95)
    
    def _analyze_curiosity_factor(self, transcript: str) -> int:
        """Analizza il fattore curiosità"""
        text = transcript.lower()
        score = 40  # Base score
        
        # Mystery words
        mystery_words = ['secret', 'hidden', 'reveal', 'discover', 'mystery', 'unknown']
        mystery_count = sum(1 for word in mystery_words if word in text)
        score += min(mystery_count * 12, 30)
        
        # Curiosity patterns
        if any(pattern.lower() in text for pattern in self.viral_patterns['curiosity_hook']):
            score += 20
        
        # Question marks (engagement)
        question_count = text.count('?')
        score += min(question_count * 5, 15)
        
        return min(score, 95)
    
    def _analyze_relevance(self, transcript: str, category: str) -> int:
        """Analizza la rilevanza rispetto alla categoria e trend"""
        text = transcript.lower()
        score = 50  # Base score
        
        # Category-specific keywords
        if category.lower() in self.viral_keywords:
            category_words = self.viral_keywords[category.lower()]
            category_count = sum(1 for word in category_words if word in text)
            score += min(category_count * 8, 25)
        
        # General viral keywords
        general_words = self.viral_keywords['general']
        general_count = sum(1 for word in general_words if word in text)
        score += min(general_count * 5, 15)
        
        # Hashtag potential
        if '#' in transcript or any(word in text for word in ['trending', 'viral', 'popular']):
            score += 10
        
        return min(score, 95)
    
    def _analyze_shareability(self, transcript: str) -> int:
        """Analizza la probabilità di condivisione"""
        text = transcript.lower()
        score = 45  # Base score
        
        # Call to action
        cta_words = ['share', 'like', 'comment', 'subscribe', 'follow', 'tag']
        cta_count = sum(1 for word in cta_words if word in text)
        score += min(cta_count * 8, 20)
        
        # Social proof indicators
        social_words = ['everyone', 'millions', 'thousands', 'viral', 'trending']
        social_count = sum(1 for word in social_words if word in text)
        score += min(social_count * 6, 18)
        
        # Memorable phrases
        if len(text.split()) < 10:  # Short and punchy
            score += 12
        elif len(text.split()) < 20:  # Medium length
            score += 8
        
        return min(score, 95)
    
    def _generate_improvement_insight(self, hook: int, emotional: int, curiosity: int, relevance: int, shareability: int) -> str:
        """Genera suggerimenti per migliorare il potenziale virale"""
        scores = {
            'hook': hook,
            'emotional': emotional,
            'curiosity': curiosity,
            'relevance': relevance,
            'shareability': shareability
        }
        
        # Trova il punteggio più basso
        lowest_score = min(scores.values())
        lowest_category = min(scores, key=scores.get)
        
        insights = {
            'hook': 'Strengthen the opening with a compelling question or surprising statement',
            'emotional': 'Add more emotional words and personal pronouns to increase relatability',
            'curiosity': 'Include mystery elements or "wait for it" moments to boost curiosity',
            'relevance': 'Add trending keywords and category-specific terms for better relevance',
            'shareability': 'Include clear call-to-actions and social proof elements'
        }
        
        if lowest_score < 60:
            return insights[lowest_category]
        else:
            return 'Content shows good viral potential across all metrics - consider A/B testing different titles'
    
    def _get_default_scores(self) -> Dict[str, Any]:
        """Punteggi di fallback di default"""
        return {
            'hook_score': 55,
            'hook_reason': 'Default scoring due to analysis error',
            'emotional_score': 50,
            'emotional_reason': 'Default scoring due to analysis error',
            'curiosity_score': 45,
            'curiosity_reason': 'Default scoring due to analysis error',
            'relevance_score': 50,
            'relevance_reason': 'Default scoring due to analysis error',
            'shareability_score': 48,
            'shareability_reason': 'Default scoring due to analysis error',
            'viral_score': 50,
            'key_insight': 'Unable to analyze - consider manual review'
        }
    
    def generate_optimized_content(self, transcript: str, category: str = "general") -> Dict[str, str]:
        """
        Genera titoli e descrizioni ottimizzati usando algoritmi locali
        """
        try:
            # Estrai parole chiave dal transcript
            words = transcript.lower().split()
            keywords = [word for word in words if len(word) > 3 and word.isalpha()]
            
            # Template titoli virali
            title_templates = [
                f"🔥 {keywords[0].title()} That Will Blow Your Mind!",
                f"You Won't Believe This {category.title()} Video!",
                f"SHOCKING: {keywords[0].title() if keywords else 'This'} Goes Viral!",
                f"This {category.title()} Video Has Everyone Talking",
                f"MUST WATCH: {keywords[0].title() if keywords else 'Amazing'} Content!"
            ]
            
            # Scegli template basato sulla lunghezza del transcript
            if len(words) < 5:
                title = title_templates[0]
            elif 'shocking' in transcript.lower() or 'unbelievable' in transcript.lower():
                title = title_templates[2]
            else:
                title = title_templates[1]
            
            # Genera descrizione
            description_parts = [
                f"🎯 {transcript[:100]}..." if len(transcript) > 100 else transcript,
                "",
                "🔥 Don't forget to LIKE & SHARE if this amazed you!",
                "💬 Comment below with your thoughts!",
                "🔔 Subscribe for more viral content!",
                "",
                f"#{category} #viral #trending #shorts #fyp #amazing"
            ]
            
            description = "\n".join(description_parts)
            
            # Genera hashtags
            base_hashtags = ["#viral", "#trending", "#shorts", "#fyp"]
            category_hashtags = [f"#{category}", f"#{category}videos"]
            
            if keywords:
                keyword_hashtags = [f"#{word}" for word in keywords[:3]]
                all_hashtags = base_hashtags + category_hashtags + keyword_hashtags
            else:
                all_hashtags = base_hashtags + category_hashtags
            
            hashtags = " ".join(all_hashtags[:10])  # Limit to 10 hashtags
            
            app_logger.info("✅ Fallback content generation completed")
            
            return {
                'title': title,
                'description': description,
                'hashtags': hashtags
            }
            
        except Exception as e:
            app_logger.error(f"Error in fallback content generation: {e}")
            return {
                'title': f"Amazing {category.title()} Content!",
                'description': f"{transcript}\n\n🔥 Like & Share for more!\n#viral #trending #shorts",
                'hashtags': "#viral #trending #shorts #fyp"
            }

# Funzione di utilità per integrazione
def get_fallback_analysis(transcript: str, title: str = "", category: str = "general") -> Dict[str, Any]:
    """
    Funzione wrapper per l'analisi di fallback
    """
    engine = OpenAIFallbackEngine()
    return engine.analyze_viral_potential(transcript, title, category)

def get_fallback_content(transcript: str, category: str = "general") -> Dict[str, str]:
    """
    Funzione wrapper per la generazione di contenuto di fallback
    """
    engine = OpenAIFallbackEngine()
    return engine.generate_optimized_content(transcript, category)

if __name__ == "__main__":
    # Test del sistema
    test_transcript = "one handed baller to the league nba basketball shorts"
    
    engine = OpenAIFallbackEngine()
    
    # Test analisi virale
    analysis = engine.analyze_viral_potential(test_transcript, category="sports")
    print("🧪 Viral Analysis Test:")
    print(f"Viral Score: {analysis['viral_score']}/100")
    print(f"Key Insight: {analysis['key_insight']}")
    
    # Test generazione contenuto
    content = engine.generate_optimized_content(test_transcript, "sports")
    print(f"\n📝 Content Generation Test:")
    print(f"Title: {content['title']}")
    print(f"Hashtags: {content['hashtags']}")
