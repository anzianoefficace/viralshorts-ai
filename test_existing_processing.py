#!/usr/bin/env python3
"""
Test di processing per video esistenti - bypassa la ricerca YouTube
"""

import json
import os
import sys

# Aggiungi la directory del progetto al path
project_root = "/Volumes/RoG Marco 1/Whashing Machine/ViralShortsAI"
sys.path.insert(0, project_root)
os.chdir(project_root)

from database import Database
from ai.whisper_transcriber import WhisperTranscriber
from ai.gpt_captioner import GPTCaptioner
from processing.editor import VideoEditor

def test_process_existing_videos():
    """Test del processing di video già scaricati"""
    print("=== TEST PROCESSING VIDEO ESISTENTI ===")
    
    # Carica configurazione aggiornata
    with open("config.json", "r") as f:
        config = json.load(f)
    
    print(f"Min views configurati: {config['youtube_search']['min_views']}")
    print(f"Viral score threshold: {config['analytics']['viral_score_threshold']}")
    
    # Inizializza database
    db = Database(config["paths"]["database"])
    
    # Trova video nel database con visualizzazioni sufficienti
    min_views = config['youtube_search']['min_views']
    
    # Query per video non processati
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT sv.id, sv.title, sv.views, sv.youtube_id
        FROM source_videos sv
        LEFT JOIN processed_clips pc ON sv.id = pc.source_id
        WHERE sv.views >= ? AND pc.source_id IS NULL
        ORDER BY sv.views DESC
    """, (min_views,))
    
    unprocessed_videos = [
        {"id": row[0], "title": row[1], "view_count": row[2], "youtube_id": row[3]}
        for row in cursor.fetchall()
    ]
    
    print(f"\nVideo non processati con >= {min_views} views: {len(unprocessed_videos)}")
    
    if not unprocessed_videos:
        print("Nessun video da processare trovato!")
        # Mostra tutti i video per debug
        cursor.execute("SELECT id, title, views FROM source_videos ORDER BY views DESC")
        all_videos = [{"id": row[0], "title": row[1], "view_count": row[2]} for row in cursor.fetchall()]
        print(f"Tutti i video nel database: {len(all_videos)}")
        for video in all_videos:
            print(f"- {video['title']}: {video['view_count']} views")
        return False
    
    # Prendi il primo video non processato
    video = unprocessed_videos[0]
    print(f"\nProcessing video: {video['title']}")
    print(f"Views: {video['view_count']}")
    print(f"Video ID: {video['id']}")
    
    # Trova il file video
    video_path = os.path.join(config["paths"]["downloads"], f"{video['youtube_id']}.mp4")
    if not os.path.exists(video_path):
        print(f"File video non trovato: {video_path}")
        return False
    
    print(f"File video trovato: {video_path}")
    
    # Inizializza componenti di processing
    try:
        print("Inizializzazione Whisper...")
        transcriber = WhisperTranscriber(config)
        
        print("Inizializzazione GPT Captioner...")
        captioner = GPTCaptioner(config)
        
        print("Inizializzazione Video Editor...")
        editor = VideoEditor(config, db)
        
        print("Tutti i componenti inizializzati con successo!")
        
        # Test trascrizione
        print("\nTest trascrizione...")
        transcript_result = transcriber.transcribe_video(video_path)
        print(f"Transcript result type: {type(transcript_result)}")
        print(f"Transcript result keys: {transcript_result.keys() if isinstance(transcript_result, dict) else 'Non è un dict'}")
        
        if transcript_result and transcript_result.get('text'):
            transcript = transcript_result['text']
            print(f"Trascrizione completata: {len(transcript)} caratteri")
            print(f"Primi 100 caratteri: {transcript[:100]}...")
        elif isinstance(transcript_result, str):
            transcript = transcript_result
            print(f"Trascrizione completata (stringa): {len(transcript)} caratteri")
            print(f"Primi 100 caratteri: {transcript[:100]}...")
            # Creiamo un oggetto transcript_result fittizio per il GPT
            transcript_result = {'text': transcript, 'segments': []}
        else:
            print("Trascrizione fallita!")
            print(f"Trascrizione ricevuta: {transcript_result}")
            return False
        
        # Test generazione caption - temporaneamente saltato per quota GPT
        print("\nTest generazione caption...")
        print("⚠️  Saltando la generazione GPT per quota superata")
        caption = "Test Caption - GPT Quote Exceeded"
        print(f"Caption di test: {caption}")
        
        # Procediamo direttamente al test del video editor
        
        # Test creazione clips
        print("\nTest creazione clips...")
        # Creiamo un singolo clip di prova di 30 secondi
        clip_output_path = os.path.join(config["paths"]["processed"], f"{video['youtube_id']}_clip_30s.mp4")
        try:
            editor.extract_clip(video_path, clip_output_path, start_time=0, duration=30)
            if os.path.exists(clip_output_path):
                clips = [clip_output_path]
                print(f"Creati {len(clips)} clips")
                for i, clip in enumerate(clips):
                    print(f"  Clip {i+1}: {clip}")
            else:
                print("File clip non creato!")
                return False
        except Exception as e:
            print(f"Errore nella creazione del clip: {e}")
            return False
        
        print("\n✅ Test completato con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_process_existing_videos()
    print(f"\nTest {'SUPERATO' if success else 'FALLITO'}")
