#!/usr/bin/env python3
"""
Test script per verificare l'inizializzazione dei componenti
"""

import os
import sys
import json
from pathlib import Path

# Aggiungi la directory root al Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_component_initialization():
    """Test inizializzazione componenti come nel main.py"""
    print("🔧 Test dell'inizializzazione dei componenti...")
    
    try:
        # Import moduli necessari
        from database import Database
        from data.downloader import YouTubeShortsFinder
        from ai.whisper_transcriber import WhisperTranscriber
        from ai.gpt_captioner import GPTCaptioner
        from processing.editor import VideoEditor
        from upload.youtube_uploader import YouTubeUploader
        from monitoring.analyzer import PerformanceAnalyzer
        from dotenv import load_dotenv
        
        # Carica configurazione
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        load_dotenv()
        
        # Test inizializzazione nell'ordine corretto (come nel main.py)
        print("  📂 Inizializzazione Database...")
        db_path = config.get('paths', {}).get('database', 'data/viral_shorts.db')
        db = Database(db_path)
        print("  ✅ Database inizializzato")
        
        print("  🔍 Inizializzazione YouTubeShortsFinder...")
        finder = YouTubeShortsFinder(config, db)
        print("  ✅ YouTubeShortsFinder inizializzato")
        
        print("  🎤 Inizializzazione WhisperTranscriber...")
        transcriber = WhisperTranscriber(config)
        print("  ✅ WhisperTranscriber inizializzato")
        
        print("  💬 Inizializzazione GPTCaptioner...")
        captioner = GPTCaptioner(config)
        print("  ✅ GPTCaptioner inizializzato")
        
        print("  ✂️ Inizializzazione VideoEditor...")
        editor = VideoEditor(config, db)
        print("  ✅ VideoEditor inizializzato")
        
        print("  📤 Inizializzazione YouTubeUploader...")
        uploader = YouTubeUploader(config)
        print("  ✅ YouTubeUploader inizializzato")
        
        print("  📊 Inizializzazione PerformanceAnalyzer...")
        analyzer = PerformanceAnalyzer(config, db)
        print("  ✅ PerformanceAnalyzer inizializzato")
        
        print("🎉 Tutti i componenti inizializzati correttamente!")
        return True
        
    except Exception as e:
        print(f"❌ Errore nell'inizializzazione: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_worker_simulation():
    """Simula l'avvio del worker thread"""
    print("🔧 Test simulazione worker thread...")
    
    try:
        from database import Database
        from data.downloader import YouTubeShortsFinder
        from ai.whisper_transcriber import WhisperTranscriber
        from ai.gpt_captioner import GPTCaptioner
        from processing.editor import VideoEditor
        from upload.youtube_uploader import YouTubeUploader
        from monitoring.analyzer import PerformanceAnalyzer
        
        # Carica configurazione
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Simula l'inizializzazione del worker
        print("  🧵 Simulazione ViralShortsWorker...")
        
        # Mock worker class attributes
        class MockWorker:
            def __init__(self, config):
                self.config = config
                self.db = None
                self.finder = None
                self.transcriber = None
                self.captioner = None
                self.editor = None
                self.uploader = None
                self.analyzer = None
                
            def initialize_components(self):
                """Inizializza tutti i componenti come nel worker reale"""
                # Database path
                db_path = self.config.get('paths', {}).get('database', 'data/viral_shorts.db')
                
                # Initialize components in order
                self.db = Database(db_path)
                self.finder = YouTubeShortsFinder(self.config, self.db)
                self.transcriber = WhisperTranscriber(self.config)
                self.captioner = GPTCaptioner(self.config)
                self.editor = VideoEditor(self.config, self.db)
                self.uploader = YouTubeUploader(self.config)
                self.analyzer = PerformanceAnalyzer(self.config, self.db)
                
                return True
        
        worker = MockWorker(config)
        result = worker.initialize_components()
        
        if result:
            print("  ✅ Worker simulation successful")
            return True
        else:
            print("  ❌ Worker simulation failed")
            return False
            
    except Exception as e:
        print(f"❌ Errore nella simulazione worker: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Funzione principale del test"""
    print("=" * 60)
    print("    🔧 Test Inizializzazione Componenti ViralShortsAI")
    print("=" * 60)
    
    # Vai nella directory dell'applicazione
    os.chdir(Path(__file__).parent)
    
    tests = [
        test_component_initialization,
        test_worker_simulation
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
        print("🎉 Inizializzazione componenti funziona correttamente!")
        print("   L'errore precedente dovrebbe essere risolto.")
    else:
        print("⚠️  Alcuni test sono falliti.")
    
    return passed == total

if __name__ == "__main__":
    main()
