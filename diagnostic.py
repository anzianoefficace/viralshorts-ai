#!/usr/bin/env python3
"""
ViralShortsAI - Diagnostic Launcher
Questo script avvia l'applicazione in modalità diagnostica, 
eseguendo controlli preliminari e fornendo informazioni dettagliate 
per risolvere eventuali problemi di inizializzazione.
"""

import os
import sys
import json
import time
import traceback
import importlib
import platform
import subprocess
from pathlib import Path

# Configurazione colori ANSI per output console
COLORS = {
    'INFO': '\033[92m',     # Green
    'WARNING': '\033[93m',  # Yellow
    'ERROR': '\033[91m',    # Red
    'HEADER': '\033[95m',   # Purple
    'BOLD': '\033[1m',      # Bold
    'RESET': '\033[0m'      # Reset
}

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

def check_python_version():
    """Verifica la versione di Python."""
    print_section("Verifica della versione di Python")
    version_info = sys.version_info
    print(f"Python {version_info.major}.{version_info.minor}.{version_info.micro}")
    
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 10):
        print_colored("ATTENZIONE: Questa applicazione è stata sviluppata per Python 3.10 o superiore.", 'WARNING')
    else:
        print_colored("Versione di Python compatibile.", 'INFO')

def check_dependencies():
    """Verifica la presenza delle dipendenze necessarie."""
    print_section("Verifica delle dipendenze")
    required_packages = [
        'PyQt5',
        'apscheduler',
        'python-dotenv',
        'openai',
        'moviepy',
        'matplotlib',
        'pandas',
        'google-auth',
        'google-auth-oauthlib',
        'google-api-python-client'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Gestisce il caso di pacchetti con sottopacchetti (come google-auth)
            package_name = package.split('-')[0]
            module = importlib.__import__(package_name)
            version = getattr(module, '__version__', 'Unknown')
            print(f"✓ {package} - Versione: {version}")
        except ImportError:
            print_colored(f"✗ {package} - Non installato", 'ERROR')
            missing_packages.append(package)
    
    if missing_packages:
        print("\nPacchetti mancanti rilevati. Installali con il seguente comando:")
        cmd = f"{sys.executable} -m pip install {' '.join(missing_packages)}"
        print_colored(f"\n{cmd}\n", 'BOLD')
        
        choice = input("Vuoi installare i pacchetti mancanti ora? (s/n): ").lower()
        if choice == 's' or choice == 'y':
            try:
                print("Installazione dei pacchetti in corso...")
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print_colored("Installazione completata con successo!", 'INFO')
            except subprocess.CalledProcessError as e:
                print_colored(f"Errore durante l'installazione: {e}", 'ERROR')
        
def check_directory_structure():
    """Verifica la struttura delle directory dell'applicazione."""
    print_section("Verifica della struttura delle directory")
    required_dirs = [
        'data',
        'data/downloads',
        'data/processed',
        'data/uploads',
        'data/reports',
        'data/temp',
        'logs'
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✓ {directory}")
        else:
            print_colored(f"✗ {directory} - Mancante", 'WARNING')
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                print_colored(f"  Directory {directory} creata", 'INFO')
            except Exception as e:
                print_colored(f"  Impossibile creare la directory {directory}: {e}", 'ERROR')

def check_configuration_files():
    """Verifica la presenza e la validità dei file di configurazione."""
    print_section("Verifica dei file di configurazione")
    
    # Controlla config.json
    config_path = 'config.json'
    if os.path.exists(config_path):
        print(f"✓ {config_path} trovato")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Verifica che la configurazione contenga le sezioni necessarie
            required_sections = ['paths', 'app_settings', 'youtube_search', 
                               'video_processing', 'upload', 'analytics']
            for section in required_sections:
                if section not in config:
                    print_colored(f"  Sezione '{section}' mancante in config.json", 'WARNING')
            
            # Verifica la sezione paths
            if 'paths' in config:
                required_paths = ['data', 'downloads', 'processed', 'uploads', 
                                'reports', 'logs', 'database', 'temp', 'credentials']
                for path in required_paths:
                    if path not in config['paths']:
                        print_colored(f"  Percorso '{path}' mancante nella sezione paths", 'WARNING')
        except json.JSONDecodeError:
            print_colored(f"  Il file {config_path} non è un JSON valido", 'ERROR')
    else:
        print_colored(f"✗ {config_path} non trovato", 'ERROR')
    
    # Controlla .env
    env_path = '.env'
    if os.path.exists(env_path):
        print(f"✓ {env_path} trovato")
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        required_vars = ['OPENAI_API_KEY', 'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET']
        for var in required_vars:
            if var not in env_content:
                print_colored(f"  Variabile '{var}' mancante nel file .env", 'WARNING')
    else:
        print_colored(f"✗ {env_path} non trovato", 'WARNING')
        print_colored("  Crea un file .env con le tue chiavi API", 'INFO')
    
    # Controlla youtube_credentials.json
    yt_creds_path = 'data/youtube_credentials.json'
    if os.path.exists(yt_creds_path):
        print(f"✓ {yt_creds_path} trovato")
        try:
            with open(yt_creds_path, 'r') as f:
                creds = json.load(f)
            if 'token' not in creds:
                print_colored(f"  Il file {yt_creds_path} non contiene un token OAuth valido", 'WARNING')
        except json.JSONDecodeError:
            print_colored(f"  Il file {yt_creds_path} non è un JSON valido", 'ERROR')
    else:
        print_colored(f"✗ {yt_creds_path} non trovato", 'WARNING')
        print_colored("  Dovrai eseguire l'autenticazione di YouTube al primo avvio", 'INFO')

def check_database():
    """Verifica lo stato del database."""
    print_section("Verifica del database")
    db_path = 'data/viral_shorts.db'
    
    if os.path.exists(db_path):
        print(f"✓ Database trovato: {db_path}")
        
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Conta le tabelle
            cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            if table_count > 0:
                print(f"  Il database contiene {table_count} tabelle")
                
                # Elenca le tabelle
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print("  Tabelle trovate:")
                for table in tables:
                    print(f"    - {table[0]}")
            else:
                print_colored("  Il database esiste ma non contiene tabelle", 'WARNING')
                print("  Il database verrà inizializzato al primo avvio dell'applicazione")
                
            conn.close()
        except Exception as e:
            print_colored(f"  Errore nell'accesso al database: {e}", 'ERROR')
    else:
        print_colored(f"✗ Database non trovato: {db_path}", 'WARNING')
        print("  Il database verrà creato al primo avvio dell'applicazione")

def launch_application():
    """Avvia l'applicazione principale."""
    print_section("Avvio dell'applicazione")
    print("Avvio di ViralShortsAI in modalità diagnostica...")
    
    try:
        print_colored("\nRedirezione log sulla console...", 'INFO')
        time.sleep(1)
        
        # Imposta variabile d'ambiente per modalità diagnostica
        os.environ['VIRAL_SHORTS_DEBUG'] = '1'
        
        # Crea log file
        log_file = os.path.join('logs', 'diagnostic.log')
        Path('logs').mkdir(parents=True, exist_ok=True)
        
        # Importa ed esegui l'applicazione principale
        print_colored("\nAvvio dell'applicazione principale...", 'INFO')
        
        # Rimuovi eventuale file pickle delle credenziali per forzare la riautenticazione
        token_pickle = os.path.join('data', 'token.pickle')
        if os.path.exists(token_pickle):
            os.remove(token_pickle)
            print_colored("File token.pickle rimosso per forzare una nuova autenticazione", 'INFO')
        
        # Avvia l'applicazione
        import main
        main.main()
        
    except ImportError as e:
        print_colored(f"\nErrore nell'importazione del modulo principale: {e}", 'ERROR')
        print("Controlla che tutti i file dell'applicazione siano presenti e che le dipendenze siano installate.")
    except Exception as e:
        print_colored(f"\nErrore nell'avvio dell'applicazione: {e}", 'ERROR')
        traceback.print_exc()

def main():
    """Funzione principale."""
    print_header("ViralShortsAI - Diagnostic Launcher")
    print("Questo strumento ti aiuterà a diagnosticare e risolvere problemi di avvio.")
    print_colored("Esecuzione di controlli preliminari...\n", 'INFO')
    
    # Esegui i controlli
    check_python_version()
    check_dependencies()
    check_directory_structure()
    check_configuration_files()
    check_database()
    
    print_header("Riepilogo della diagnostica")
    print("I controlli diagnostici sono stati completati.")
    print("Se sono stati rilevati problemi, risolvi gli errori segnalati prima di avviare l'applicazione.")
    
    # Chiedi all'utente se vuole avviare l'applicazione
    choice = input("\nVuoi avviare l'applicazione ora? (s/n): ").lower()
    if choice == 's' or choice == 'y':
        launch_application()
    else:
        print_colored("\nAvvio annullato. Risolvi eventuali problemi e riavvia questo script.", 'INFO')

if __name__ == "__main__":
    main()
