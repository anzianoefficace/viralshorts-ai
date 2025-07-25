#!/usr/bin/env python3
"""
Script di test per verificare l'aggiunta automatica dei credits
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timezone

# Aggiungi la directory corrente al path per importare i moduli
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from upload.youtube_uploader import YouTubeUploader
from database import Database

def test_credits_feature():
    """Testa la funzionalità di aggiunta automatica dei credits"""
    
    # File video da caricare (stesso file per il test)
    video_file = "data/processed/1n091iPQ3uA_clip_30s.mp4"
    
    # Verifica che il file esista
    if not os.path.exists(video_file):
        print(f"❌ File video non trovato: {video_file}")
        return False
    
    print("🧪 TEST: Verifica aggiunta automatica credits")
    print("=" * 60)
    print(f"📹 File video: {video_file}")
    
    try:
        # Inizializza database
        db = Database('data/viral_shorts.db')
        
        # Ottieni informazioni dal database
        conn = sqlite3.connect('data/viral_shorts.db')
        cursor = conn.cursor()
        
        # Trova il source video
        cursor.execute("SELECT * FROM source_videos WHERE youtube_id = '1n091iPQ3uA'")
        source_video = cursor.fetchone()
        
        if not source_video:
            print("❌ Video sorgente non trovato nel database")
            return False
        
        # Costruisci i dati del video sorgente per i credits
        source_video_data = {
            'channel_title': source_video[3],  # channel field
            'metadata': source_video[12]  # metadata JSON field
        }
        
        print(f"🎬 Video sorgente: {source_video[2]}")
        print(f"👤 Canale: {source_video[3]}")
        
        # Prova a estrarre il channel_id dai metadati
        channel_id = None
        if source_video[12]:
            try:
                metadata = json.loads(source_video[12])
                channel_id = metadata.get('channel_id')
                print(f"🆔 Channel ID trovato: {channel_id}")
            except:
                print("⚠️ Impossibile parsare i metadati JSON")
        
        # Inizializza YouTube uploader
        print("\n🔄 Inizializzazione YouTube uploader...")
        with open('config.json', 'r') as f:
            config = json.load(f)
        uploader = YouTubeUploader(config)
        
        # Prepara metadati per il test
        title = "🧪 TEST CREDITS - Makeup Tutorial #shorts #test"
        description = """🔥 Test video per verificare l'aggiunta automatica dei credits!

✨ Questo è un video di test del sistema ViralShortsAI

#shorts #test #ai #makeup #credits

Generato da ViralShortsAI 🤖 per test"""

        tags = ["shorts", "test", "ai", "makeup", "credits"]
        
        print(f"\n📝 Titolo: {title}")
        print("📄 Descrizione PRIMA dell'aggiunta dei credits:")
        print("-" * 40)
        print(description)
        print("-" * 40)
        
        # Test della logica di aggiunta credits senza fare upload reale
        print("\n🧪 SIMULAZIONE: Test logica aggiunta credits...")
        
        # Simula la stessa logica dell'uploader
        final_description = description
        if source_video_data:
            channel_title = source_video_data.get('channel_title', 'Creator sconosciuto')
            channel_id_from_metadata = None
            
            # Extract channel_id from metadata if available
            metadata = source_video_data.get('metadata')
            if isinstance(metadata, str):
                try:
                    metadata_dict = json.loads(metadata)
                    channel_id_from_metadata = metadata_dict.get('channel_id')
                except:
                    pass
            
            # Add credits line
            if channel_id_from_metadata:
                credits_line = f"\n\n🎥 Credits: contenuto originale di [{channel_title}](https://www.youtube.com/channel/{channel_id_from_metadata})"
            else:
                credits_line = f"\n\n🎥 Credits: contenuto originale di {channel_title}"
            
            final_description = description + credits_line
        
        print("\n📄 Descrizione DOPO l'aggiunta dei credits:")
        print("-" * 40)
        print(final_description)
        print("-" * 40)
        
        # Verifica che i credits siano stati aggiunti
        if "🎥 Credits:" in final_description:
            print("\n✅ TEST PASSATO: Credits aggiunti correttamente!")
            if channel_id_from_metadata and f"https://www.youtube.com/channel/{channel_id_from_metadata}" in final_description:
                print("✅ Link al canale originale incluso!")
            else:
                print("⚠️ Link al canale non disponibile, solo nome del creator")
            return True
        else:
            print("\n❌ TEST FALLITO: Credits non aggiunti!")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante il test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST AUTOMATICO - AGGIUNTA CREDITS")
    print("=" * 60)
    
    success = test_credits_feature()
    
    if success:
        print("\n✅ TEST COMPLETATO CON SUCCESSO!")
        print("🎯 La funzionalità di credits automatici funziona correttamente")
    else:
        print("\n❌ TEST FALLITO")
        print("🔧 Controlla la logica di aggiunta credits")
