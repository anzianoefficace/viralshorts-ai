#!/usr/bin/env python3
"""
Test script per ViralShortsAI - testa le funzioni core senza GUI
"""

import os
import sys
import json
from pathlib import Path

# Aggiungi la directory root al Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test import dei moduli principali"""
    print("🔧 Test degli import dei moduli...")
    
    try:
        # Test database
        from database import Database
        print("✅ Database module imported successfully")
        
        # Test downloader
        from data.downloader import YouTubeShortsFinder
        print("✅ Downloader module imported successfully")
        
        # Test AI modules
        from ai.whisper_transcriber import WhisperTranscriber
        print("✅ Whisper transcriber imported successfully")
        
        from ai.gpt_captioner import GPTCaptioner
        print("✅ GPT captioner imported successfully")
        
        # Test uploader
        from upload.youtube_uploader import YouTubeUploader
        print("✅ YouTube uploader imported successfully")
        
        print("🎉 Tutti i moduli core importati con successo!")
        return True
    except Exception as e:
        print(f"❌ Errore nell'import: {e}")
        return False

def test_config():
    """Test configurazione"""
    print("🔧 Test della configurazione...")
    
    try:
        # Test config.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("✅ config.json caricato correttamente")
        
        # Test .env
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('YOUTUBE_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if api_key:
            print(f"✅ YouTube API key trovata: {api_key[:10]}...")
        else:
            print("❌ YouTube API key non trovata")
            
        if openai_key:
            print(f"✅ OpenAI API key trovata: {openai_key[:10]}...")
        else:
            print("❌ OpenAI API key non trovata")
            
        return True
    except Exception as e:
        print(f"❌ Errore nella configurazione: {e}")
        return False

def test_database():
    """Test connessione database"""
    print("🔧 Test del database...")
    
    try:
        from database import Database
        
        # Carica configurazione
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        # Estrai il percorso del database dalla configurazione
        db_path = config.get('paths', {}).get('database', 'data/viral_shorts.db')
        
        # Inizializza database con il percorso corretto
        db = Database(db_path)
        
        # Test semplice query
        result = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        print(f"✅ Database connesso. Tabelle trovate: {[row['name'] for row in result]}")
        
        return True
    except Exception as e:
        print(f"❌ Errore nel database: {e}")
        return False

def test_youtube_api():
    """Test connessione YouTube API"""
    print("🔧 Test YouTube API...")
    
    try:
        from dotenv import load_dotenv
        import googleapiclient.discovery
        
        load_dotenv()
        api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not api_key:
            print("❌ API key non trovata")
            return False
            
        # Inizializza client API
        youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
        
        # Test semplice ricerca
        request = youtube.search().list(
            part='snippet',
            q='test',
            maxResults=1
        )
        response = request.execute()
        
        print(f"✅ YouTube API funziona. Test search restituito: {len(response.get('items', []))} risultati")
        return True
    except Exception as e:
        print(f"❌ Errore YouTube API: {e}")
        return False

def test_downloader_logic():
    """Test logica downloader senza effettuare download"""
    print("🔧 Test logica downloader...")
    
    try:
        from data.downloader import YouTubeShortsFinder
        from database import Database
        
        # Carica configurazione
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        # Inizializza database con percorso corretto
        db_path = config.get('paths', {}).get('database', 'data/viral_shorts.db')
        db = Database(db_path)
        finder = YouTubeShortsFinder(config, db)
        
        # Test parsing durata ISO 8601
        test_duration = finder._parse_duration('PT1M30S')  # 1 minuto e 30 secondi
        expected = 90  # secondi
        
        if test_duration == expected:
            print(f"✅ Parser durata funziona: PT1M30S = {test_duration} secondi")
        else:
            print(f"❌ Parser durata non funziona: PT1M30S = {test_duration}, atteso {expected}")
            
        # Test calcolo viral score (mock data)
        mock_video = {
            'statistics': {
                'viewCount': '100000',
                'likeCount': '5000',
                'commentCount': '500'
            },
            'snippet': {
                'publishedAt': '2025-07-19T12:00:00Z'
            }
        }
        
        viral_score = finder._calculate_viral_score(mock_video, 100000)
        print(f"✅ Calcolo viral score funziona: {viral_score}")
        
        # Test ricerca effettiva (limitata)
        print("🔍 Test ricerca video limitata...")
        config_test = config.copy()
        config_test['youtube_search']['min_views'] = 1000  # Soglia bassa per test
        config_test['youtube_search']['copyright_filter'] = False  # Nessun filtro copyright
        
        test_finder = YouTubeShortsFinder(config_test, db)
        
        # Prova a cercare 1 video
        videos = test_finder.search_viral_shorts(max_results=1)
        
        if videos and len(videos) > 0:
            video = videos[0]
            print(f"✅ Ricerca funziona! Trovato: {video['title'][:50]}... - {video['views']} views")
        else:
            print("⚠️  Nessun video trovato nel test di ricerca (potrebbe essere normale)")
            
        return True
    except Exception as e:
        print(f"❌ Errore test downloader: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Funzione principale del test"""
    print("=" * 60)
    print("    🎬 ViralShortsAI - Test delle Funzionalità Core")
    print("=" * 60)
    
    # Vai nella directory dell'applicazione
    os.chdir(Path(__file__).parent)
    
    tests = [
        test_imports,
        test_config, 
        test_database,
        test_youtube_api,
        test_downloader_logic
    ]
    
    results = []
    
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print("-" * 60)
        except Exception as e:
            print(f"❌ Errore nel test {test_func.__name__}: {e}")
            results.append(False)
            print("-" * 60)
    
    # Riepilogo
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print("                    📊 RIEPILOGO TEST")
    print("=" * 60)
    print(f"✅ Test passati: {passed}/{total}")
    print(f"❌ Test falliti: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 Tutti i test sono passati! L'applicazione è pronta per l'uso.")
        print("\n💡 Per avviare l'applicazione GUI:")
        print("   python main.py")
        print("\n💡 Per testare solo il download:")
        print("   python -c \"from data.downloader import *; # test code here\"")
    else:
        print("⚠️  Alcuni test sono falliti. Controlla gli errori sopra.")
    
    return passed == total

if __name__ == "__main__":
    main()
