#!/usr/bin/env python3
"""
Test della modalità test single video URL con pipeline completo.
Testa il bypass della ricerca e l'elaborazione completa di un singolo video.
"""

import os
import sys
import json
import traceback
import re
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from data.downloader import YouTubeShortsFinder
from ai.whisper_transcriber import WhisperTranscriber
from ai.gpt_captioner import GPTCaptioner
from processing.editor import VideoEditor
from monitoring.analyzer import PerformanceAnalyzer
from utils import app_logger

def test_single_video_mode():
    """Test della modalità test con singolo video URL."""
    
    print("=" * 60)
    print("🧪 TEST MODALITÀ SINGLE VIDEO URL")
    print("=" * 60)
    
    # URL di test (video breve esistente)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - video noto
    
    try:
        # Step 1: Estrai Video ID dall'URL
        print(f"📋 Test URL: {test_url}")
        video_id_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)', test_url)
        
        if not video_id_match:
            raise Exception("URL non valido - impossibile estrarre video ID")
        
        video_id = video_id_match.group(1)
        print(f"✅ Video ID estratto: {video_id}")
        
        # Step 2: Carica configurazione
        print("📋 Caricamento configurazione...")
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("✅ Configurazione caricata")
        
        # Step 3: Inizializza componenti
        print("📋 Inizializzazione componenti...")
        
        db_path = config['paths']['database']
        db = Database(db_path)
        print("✅ Database connesso")
        
        finder = YouTubeShortsFinder(config, db)
        print("✅ YouTube Finder inizializzato")
        
        transcriber = WhisperTranscriber(config)
        print("✅ Whisper Transcriber inizializzato")
        
        captioner = GPTCaptioner(config)
        print("✅ GPT Captioner inizializzato")
        
        editor = VideoEditor(config, db)
        print("✅ Video Editor inizializzato")
        
        analyzer = PerformanceAnalyzer(config, db)
        print("✅ Performance Analyzer inizializzato")
        
        # Step 4: Download diretto del video (modalità test)
        print("\n" + "="*50)
        print("🔄 FASE 1: DOWNLOAD DIRETTO VIDEO")
        print("="*50)
        
        print(f"📋 Scaricamento video {video_id}...")
        video_data = finder.download_video_direct(video_id, force=True)
        print(f"✅ Video scaricato: {video_data['title']}")
        print(f"   📊 Views: {video_data.get('views', 'N/A')}")
        print(f"   ⏱️  Durata: {video_data.get('duration', 'N/A')} secondi")
        print(f"   📁 File: {video_data.get('file_path', 'N/A')}")
        
        # Step 5: Trascrizione
        print("\n" + "="*50)
        print("🔄 FASE 2: TRASCRIZIONE VIDEO")
        print("="*50)
        
        language = config['app_settings']['selected_language']
        print(f"📋 Trascrizione in linguaggio: {language}")
        
        transcription = transcriber.transcribe_video(
            video_data['file_path'],
            language=language,
            save_srt=True
        )
        
        # Find key moments
        key_moments = transcriber.find_key_moments(transcription)
        transcription['key_moments'] = key_moments
        
        print(f"✅ Trascrizione completata")
        print(f"   📝 Segmenti: {len(transcription.get('segments', []))}")
        print(f"   ⭐ Key moments: {len(key_moments)}")
        
        # Step 6: Analisi potenziale virale
        print("\n" + "="*50)
        print("🔄 FASE 3: ANALISI VIRALE")
        print("="*50)
        
        print("📋 Analisi potenziale virale...")
        viral_analysis = captioner.analyze_viral_potential(
            transcription, 
            video_data.get('category', 'Entertainment')
        )
        
        print("✅ Analisi virale completata")
        if viral_analysis:
            print(f"   🎯 Score virale: {viral_analysis.get('viral_score', 'N/A')}")
            print(f"   📊 Segmenti virali: {len(viral_analysis.get('viral_segments', []))}")
        
        # Step 7: Elaborazione in clip (con sistema di fallback)
        print("\n" + "="*50)
        print("🔄 FASE 4: GENERAZIONE CLIP")
        print("="*50)
        
        print("📋 Elaborazione in clip con sistema fallback...")
        clip_ids = editor.process_source_video(
            video_data['id'], 
            transcription,
            viral_analysis
        )
        
        if not clip_ids:
            print("⚠️  ATTENZIONE: Nessuna clip creata (fallback non attivato)")
        else:
            print(f"✅ Create {len(clip_ids)} clip")
            
        # Step 8: Generazione metadata
        print("\n" + "="*50)
        print("🔄 FASE 5: METADATA GENERATION")
        print("="*50)
        
        processed_clips = []
        for i, clip_id in enumerate(clip_ids):
            print(f"📋 Elaborazione metadata clip {i+1}/{len(clip_ids)}")
            
            clip = db.execute_query(
                "SELECT * FROM processed_clips WHERE id = ?", 
                (clip_id,)
            )[0]
            
            # Extract clip transcription segment
            clip_start = clip['start_time']
            clip_end = clip['end_time']
            
            clip_segments = []
            for segment in transcription['segments']:
                if segment['start'] >= clip_start and segment['end'] <= clip_end:
                    clip_segments.append(segment)
                    
            clip_transcription = {
                'segments': clip_segments
            }
            
            # Generate metadata
            metadata = captioner.generate_video_metadata(clip, clip_transcription)
            
            # Update clip with metadata
            db.execute_query(
                """
                UPDATE processed_clips
                SET title = ?, description = ?, hashtags = ?
                WHERE id = ?
                """,
                (
                    metadata['title'],
                    metadata['description'],
                    ','.join(metadata['hashtags']),
                    clip_id
                )
            )
            
            processed_clips.append(clip_id)
            print(f"   ✅ Clip {clip_id}: {metadata['title']}")
        
        # Step 9: Genera report
        print("\n" + "="*50)
        print("🔄 FASE 6: GENERAZIONE REPORT")
        print("="*50)
        
        print("📋 Generazione report di performance...")
        report = analyzer.generate_performance_report()
        
        if report:
            print("✅ Report generato con successo")
        else:
            print("⚠️  Report non generato (normale per modalità test)")
        
        # Cleanup
        db.close()
        
        # Final results
        print("\n" + "="*60)
        print("🎉 TEST MODALITÀ SINGLE VIDEO COMPLETATO!")
        print("="*60)
        print(f"📺 Video: {video_data['title']}")
        print(f"🎬 Clip generate: {len(processed_clips)}")
        print(f"📊 Trascrizione: {len(transcription.get('segments', []))} segmenti")
        print(f"⭐ Key moments: {len(key_moments)}")
        print(f"🎯 Modalità: TEST (bypass ricerca)")
        print(f"✅ Sistema fallback: ATTIVO")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRORE nel test: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configura logging
    app_logger.info("Avvio test modalità single video")
    
    # Esegui il test
    success = test_single_video_mode()
    
    if success:
        print("\n🟢 Test completato con successo!")
        sys.exit(0)
    else:
        print("\n🔴 Test fallito!")
        sys.exit(1)
