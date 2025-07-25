#!/usr/bin/env python3
"""
ViralShortsAI - YouTube Authentication Manager
Utility per gestire l'autenticazione con l'API YouTube.
Consente di visualizzare, rinnovare o ripristinare i token di autenticazione.
"""

import os
import sys
import json
import pickle
import datetime
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
except ImportError:
    print("Librerie Google necessarie non installate.")
    print("Installa le dipendenze con:")
    print("pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Colori ANSI per output console
COLORS = {
    'INFO': '\033[92m',     # Green
    'WARNING': '\033[93m',  # Yellow
    'ERROR': '\033[91m',    # Red
    'HEADER': '\033[95m',   # Purple
    'BOLD': '\033[1m',      # Bold
    'RESET': '\033[0m'      # Reset
}

# Percorsi dei file
CREDENTIALS_FILE = 'data/youtube_credentials.json'
TOKEN_FILE = 'data/token.pickle'
CONFIG_FILE = 'config.json'

# Scopes richiesti per l'API YouTube
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

def print_colored(message, color='INFO'):
    """Stampa un messaggio colorato sulla console."""
    color_code = COLORS.get(color, COLORS['INFO'])
    print(f"{color_code}{message}{COLORS['RESET']}")

def print_header(message):
    """Stampa un'intestazione formattata."""
    print("\n" + "="*80)
    print_colored(f" {message} ", 'HEADER')
    print("="*80)

def print_section(message):
    """Stampa un'intestazione di sezione."""
    print("\n" + "-"*60)
    print_colored(f" {message} ", 'BOLD')
    print("-"*60)

def create_directory_if_not_exists(dir_path):
    """Crea una directory se non esiste."""
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def load_token():
    """Carica il token salvato."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            return pickle.load(token)
    return None

def save_token(credentials):
    """Salva il token in un file pickle."""
    create_directory_if_not_exists(os.path.dirname(TOKEN_FILE))
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(credentials, token)
    print_colored("Token salvato con successo!", 'INFO')

def get_credentials_info():
    """Ottiene e mostra le informazioni sulle credenziali salvate."""
    print_section("Informazioni sulle credenziali YouTube")
    
    # Controlla il file delle credenziali client
    if not os.path.exists(CREDENTIALS_FILE):
        print_colored(f"Il file delle credenziali ({CREDENTIALS_FILE}) non esiste.", 'ERROR')
        return None
    
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
        
        if 'installed' in creds_data:
            client_id = creds_data['installed']['client_id']
            client_secret_masked = creds_data['installed']['client_secret'][:5] + "..." if creds_data['installed']['client_secret'] else "Non trovato"
            print(f"Client ID: {client_id}")
            print(f"Client Secret: {client_secret_masked}")
            print_colored("File delle credenziali valido.", 'INFO')
        else:
            print_colored("Il file delle credenziali non contiene la sezione 'installed'.", 'ERROR')
            return None
    except Exception as e:
        print_colored(f"Errore nella lettura del file delle credenziali: {e}", 'ERROR')
        return None
    
    # Controlla il token salvato
    credentials = load_token()
    if credentials:
        print("\nToken OAuth:")
        if credentials.expired:
            print_colored("Stato: Scaduto", 'WARNING')
        else:
            print_colored("Stato: Valido", 'INFO')
        
        # Mostra la scadenza se disponibile
        if hasattr(credentials, 'expiry'):
            expiry = credentials.expiry
            now = datetime.datetime.now()
            if expiry:
                print(f"Scadenza: {expiry}")
                if expiry > now:
                    diff = expiry - now
                    print(f"Tempo rimanente: {diff.days} giorni, {diff.seconds//3600} ore")
                else:
                    print_colored("Il token è scaduto e deve essere rinnovato.", 'WARNING')
    else:
        print_colored("\nNessun token salvato trovato.", 'WARNING')
    
    return credentials

def refresh_token():
    """Tenta di aggiornare il token esistente."""
    print_section("Aggiornamento del token")
    
    credentials = load_token()
    if not credentials:
        print_colored("Nessun token trovato da aggiornare.", 'ERROR')
        return False
    
    if not credentials.refresh_token:
        print_colored("Il token non contiene un refresh_token valido e non può essere aggiornato.", 'ERROR')
        return False
    
    try:
        print("Tentativo di aggiornamento del token...")
        credentials.refresh(Request())
        save_token(credentials)
        print_colored("Token aggiornato con successo!", 'INFO')
        return True
    except Exception as e:
        print_colored(f"Errore nell'aggiornamento del token: {e}", 'ERROR')
        return False

def force_new_authentication():
    """Forza una nuova autenticazione rimuovendo il token esistente."""
    print_section("Nuova autenticazione")
    
    # Rimuovi il token esistente
    if os.path.exists(TOKEN_FILE):
        try:
            os.remove(TOKEN_FILE)
            print_colored("Token esistente rimosso.", 'INFO')
        except Exception as e:
            print_colored(f"Errore nella rimozione del token esistente: {e}", 'ERROR')
            return False
    
    # Verifica file delle credenziali
    if not os.path.exists(CREDENTIALS_FILE):
        print_colored(f"Il file delle credenziali ({CREDENTIALS_FILE}) non esiste.", 'ERROR')
        print("Assicurati di aver scaricato il file delle credenziali dalla console sviluppatori Google.")
        return False
    
    try:
        # Crea il flow di autenticazione
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES)
        
        # Esegui l'autenticazione locale
        print_colored("Avvio del processo di autenticazione. Si aprirà una finestra del browser.", 'INFO')
        print("Segui le istruzioni nel browser per autenticarti e autorizzare l'applicazione.")
        
        credentials = flow.run_local_server(
            port=8080,
            prompt='consent',
            authorization_prompt_message='Vai sul browser per autorizzare',
            success_message='Autenticazione completata! Puoi chiudere questa finestra.',
        )
        
        # Salva il nuovo token
        save_token(credentials)
        
        # Verifica la validità del token
        youtube = build('youtube', 'v3', credentials=credentials)
        request = youtube.channels().list(part='snippet', mine=True)
        response = request.execute()
        
        channel_name = response['items'][0]['snippet']['title']
        print_colored(f"Autenticato con successo al canale: {channel_name}", 'INFO')
        
        return True
    except Exception as e:
        print_colored(f"Errore nel processo di autenticazione: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        return False

def test_token():
    """Testa il token esistente."""
    print_section("Test del token")
    
    credentials = load_token()
    if not credentials:
        print_colored("Nessun token trovato da testare.", 'ERROR')
        return False
    
    try:
        youtube = build('youtube', 'v3', credentials=credentials)
        request = youtube.channels().list(part='snippet', mine=True)
        response = request.execute()
        
        channel_name = response['items'][0]['snippet']['title']
        channel_id = response['items'][0]['id']
        
        print_colored("Token valido e funzionante!", 'INFO')
        print(f"Canale: {channel_name}")
        print(f"ID canale: {channel_id}")
        
        return True
    except Exception as e:
        print_colored(f"Il token non è valido o è scaduto: {e}", 'ERROR')
        return False

def show_menu():
    """Mostra il menu principale."""
    print_header("YouTube Authentication Manager")
    print("1. Visualizza informazioni sulle credenziali")
    print("2. Testa il token esistente")
    print("3. Aggiorna il token esistente")
    print("4. Forza una nuova autenticazione")
    print("5. Esci")
    
    choice = input("\nScegli un'opzione (1-5): ")
    return choice

def main():
    """Funzione principale."""
    # Assicurati che la directory data esista
    create_directory_if_not_exists('data')
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            get_credentials_info()
        elif choice == '2':
            test_token()
        elif choice == '3':
            refresh_token()
        elif choice == '4':
            force_new_authentication()
        elif choice == '5':
            print_colored("Arrivederci!", 'INFO')
            break
        else:
            print_colored("Opzione non valida. Riprova.", 'ERROR')
        
        input("\nPremi Enter per continuare...")

if __name__ == "__main__":
    main()
