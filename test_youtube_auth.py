"""
Script per testare l'autenticazione con YouTube API.
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
print("Caricamento delle variabili d'ambiente dal file .env...")
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)

# Verifica che le variabili d'ambiente siano caricate correttamente
youtube_client_id = os.getenv('YOUTUBE_CLIENT_ID')
youtube_client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')

print(f"YOUTUBE_CLIENT_ID caricato: {'Sì' if youtube_client_id else 'No'}")
print(f"YOUTUBE_CLIENT_SECRET caricato: {'Sì' if youtube_client_secret else 'No'}")

sys.path.insert(0, '.')  # Permette di importare moduli dalla directory corrente

print("Importazione del modulo YouTubeUploader...")
from upload.youtube_uploader import YouTubeUploader

def test_youtube_auth():
    print("Test dell'autenticazione YouTube")
    
    # Carica il config
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Errore nel caricamento del config: {e}")
        return False
        
    # Crea un'istanza dell'uploader
    uploader = YouTubeUploader(config)
    
    # Verifica se c'è un token di refresh esistente
    refresh_token = uploader.get_refresh_token()
    
    if refresh_token:
        print(f"Token di refresh trovato: {refresh_token[:10]}...")
        
        # Prova ad autenticare con il token esistente
        print("Tentativo di autenticazione con token esistente...")
        success = uploader.authenticate()
        
        if success:
            print("✅ Autenticazione con token esistente riuscita!")
        else:
            print("❌ Autenticazione con token esistente fallita.")
            
            # Prova una ri-autenticazione forzata
            print("\nTentativo di ri-autenticazione forzata...")
            success = uploader.force_reauthenticate()
            
            if success:
                print("✅ Ri-autenticazione forzata riuscita!")
                new_token = uploader.get_refresh_token()
                print(f"Nuovo token di refresh: {new_token[:10]}...")
            else:
                print("❌ Anche la ri-autenticazione forzata è fallita.")
                return False
    else:
        print("Nessun token di refresh trovato.")
        
        # Prova una autenticazione da zero
        print("Tentativo di autenticazione da zero...")
        success = uploader.force_reauthenticate()
        
        if success:
            print("✅ Autenticazione iniziale riuscita!")
            new_token = uploader.get_refresh_token()
            print(f"Nuovo token di refresh: {new_token[:10]}...")
        else:
            print("❌ L'autenticazione iniziale è fallita.")
            return False
    
    return True

if __name__ == "__main__":
    success = test_youtube_auth()
    if success:
        print("\nTest di autenticazione YouTube completato con successo!")
    else:
        print("\nTest di autenticazione YouTube fallito.")
