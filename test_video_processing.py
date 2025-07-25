#!/usr/bin/env python3
"""
Test script per processare video esistenti senza fare nuove ricerche
"""

import os
import sys
import json
from pathlib import Path

# Aggiungi la directory root al Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_existing_videos():
    """Test processamento video esistenti nel database"""
    print("🔧 Test processamento video esistenti...")
    
    try:
        from database import Database
        from ai.whisper_transcriber import WhisperTranscriber
        from ai.gpt_captioner import GPTCaptioner
        from processing.editor import VideoEditor
        
        # Carica configurazione
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        # Inizializza database
        db = Database('data/viral_shorts.db')
        
        # Prendi un video esistente
        result = db.execute_query(
            "SELECT * FROM source_videos WHERE id = ? LIMIT 1", 
            (9,)  # ID video più recente
        )
        
        if not result:
            print("❌ Nessun video trovato nel database")
            return False
            
        video = result[0]
        print(f"✅ Video trovato: {video['title'][:50]}...")
        print(f"   File: {video['file_path']}")
        print(f"   Views: {video['views']}")
        
        # Controlla se il file esiste
        video_path = video['file_path']
        if not os.path.exists(video_path):
            print(f"❌ File video non trovato: {video_path}")
            return False
        
        print(f"✅ File video esiste: {os.path.basename(video_path)}")
        
        # Test inizializzazione componenti AI
        print("🔧 Inizializzazione componenti AI...")
        
        whisper = WhisperTranscriber(config)
        print("✅ Whisper transcriber inizializzato")
        
        gpt = GPTCaptioner(config)
        print("✅ GPT captioner inizializzato")
        
        editor = VideoEditor(config, db)
        print("✅ Video editor inizializzato")
        
        # Test trascrizione se non esiste
        srt_path = video_path.replace('.mp4', '.srt')
        if not os.path.exists(srt_path):
            print(f"🔧 Trascrizione non trovata, avvio trascrizione...")
            try:
                transcription = whisper.transcribe_video(video_path)
                if transcription:
                    print(f"✅ Trascrizione completata: {len(transcription.get('segments', []))} segmenti")
                else:
                    print("❌ Trascrizione fallita")
            except Exception as e:
                print(f"❌ Errore trascrizione: {e}")
        else:
            print(f"✅ File trascrizione esiste: {os.path.basename(srt_path)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Errore test video esistenti: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_workflow():
    """Test completo del workflow senza ricerca API"""
    print("🔧 Test workflow completo (senza ricerca API)...")
    
    try:
        from database import Database
        from data.downloader import YouTubeShortsFinder
        from ai.whisper_transcriber import WhisperTranscriber
        from ai.gpt_captioner import GPTCaptioner
        from processing.editor import VideoEditor
        
        # Carica configurazione
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        print(f"   Min views: {config['youtube_search']['min_views']}")
        print(f"   Viral threshold: {config['analytics']['viral_score_threshold']}")
        
        # Inizializza database
        db = Database('data/viral_shorts.db')
        
        # Trova video che non sono stati processati
        result = db.execute_query("""
            SELECT sv.* FROM source_videos sv 
            LEFT JOIN processed_clips pc ON sv.id = pc.source_id 
            WHERE pc.id IS NULL 
            ORDER BY sv.views DESC 
            LIMIT 1
        """)
        
        if not result:
            print("❌ Nessun video non processato trovato")
            return False
            
        video = result[0]
        print(f"✅ Video da processare: {video['title'][:50]}...")
        print(f"   Views: {video['views']}, ID: {video['id']}")
        
        # Inizializza componenti
        whisper = WhisperTranscriber(config)
        gpt = GPTCaptioner(config)
        editor = VideoEditor(config, db)
        
        # Simula workflow completo
        video_id = video['id']
        video_path = video['file_path']
        
        # Step 1: Trascrizione
        print("🔧 Step 1: Trascrizione...")
        transcription = whisper.transcribe_video(video_path)
        if transcription:
            print(f"✅ Trascrizione OK: {len(transcription.get('text', ''))} caratteri")
        else:
            print("❌ Trascrizione fallita")
            return False
            
        # Step 2: Analisi virale con GPT
        print("🔧 Step 2: Analisi virale...")
        viral_analysis = gpt.analyze_viral_potential(
            transcription.get('text', ''), 
            video['category']
        )
        if viral_analysis:
            print(f"✅ Analisi virale OK")
        else:
            print("❌ Analisi virale fallita")
            
        # Step 3: Elaborazione clip
        print("🔧 Step 3: Elaborazione clip...")
        try:
            clips = editor.process_source_video(video_id, transcription, viral_analysis)
            if clips:
                print(f"✅ Clip generate: {len(clips)}")
            else:
                print("❌ Nessuna clip generata")
        except Exception as e:
            print(f"❌ Errore elaborazione clip: {e}")
            import traceback
            traceback.print_exc()
            
        return True
        
    except Exception as e:
        print(f"❌ Errore workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Funzione principale del test"""
    print("=" * 70)
    print("    🎬 Test Processamento Video Esistenti")
    print("=" * 70)
    
    # Vai nella directory dell'applicazione
    os.chdir(Path(__file__).parent)
    
    tests = [
        test_existing_videos,
        test_process_workflow
    ]
    
    results = []
    
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print("-" * 70)
        except Exception as e:
            print(f"❌ Errore nel test {test_func.__name__}: {e}")
            results.append(False)
            print("-" * 70)
    
    # Riepilogo
    passed = sum(results)
    total = len(results)
    
    print("=" * 70)
    print("                    📊 RIEPILOGO TEST")
    print("=" * 70)
    print(f"✅ Test passati: {passed}/{total}")
    print(f"❌ Test falliti: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 Tutti i test sono passati!")
    else:
        print("⚠️  Alcuni test sono falliti. Controlla gli errori sopra.")
    
    return passed == total

if __name__ == "__main__":
    main()
