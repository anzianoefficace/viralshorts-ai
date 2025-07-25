#!/usr/bin/env python3
"""
ViralShortsAI - Database Utility
Utility per gestire il database dell'applicazione.
Consente di visualizzare, riparare e ripulire il database.
"""

import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path

# Colori ANSI per output console
COLORS = {
    'INFO': '\033[92m',     # Green
    'WARNING': '\033[93m',  # Yellow
    'ERROR': '\033[91m',    # Red
    'HEADER': '\033[95m',   # Purple
    'BOLD': '\033[1m',      # Bold
    'RESET': '\033[0m'      # Reset
}

# Percorso del database
DEFAULT_DB_PATH = 'data/viral_shorts.db'
CONFIG_FILE = 'config.json'

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

def get_db_path():
    """Ottiene il percorso del database dalla configurazione."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            if 'paths' in config and 'database' in config['paths']:
                return config['paths']['database']
        except Exception:
            pass
    
    return DEFAULT_DB_PATH

def create_directory_if_not_exists(dir_path):
    """Crea una directory se non esiste."""
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def connect_to_database(db_path):
    """Connette al database e restituisce la connessione."""
    try:
        # Assicurati che la directory esista
        create_directory_if_not_exists(os.path.dirname(db_path))
        
        # Connetti al database
        conn = sqlite3.connect(db_path)
        print_colored(f"Connesso al database: {db_path}", 'INFO')
        return conn
    except Exception as e:
        print_colored(f"Errore nella connessione al database: {e}", 'ERROR')
        return None

def check_database_structure(conn):
    """Controlla la struttura del database."""
    print_section("Struttura del database")
    
    try:
        cursor = conn.cursor()
        
        # Ottieni la lista delle tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print_colored("Il database non contiene tabelle.", 'WARNING')
            return False
        
        print(f"Tabelle trovate: {len(tables)}")
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            print(f"{i}. {table_name}")
            
            # Ottieni la struttura della tabella
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print(f"   Colonne: {len(columns)}")
            
            # Conta le righe nella tabella
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            print(f"   Righe: {row_count}")
            print()
        
        return True
    except Exception as e:
        print_colored(f"Errore nell'analisi della struttura del database: {e}", 'ERROR')
        return False

def vacuum_database(conn):
    """Esegue VACUUM per ottimizzare il database."""
    print_section("Ottimizzazione del database")
    
    try:
        print("Esecuzione di VACUUM per ottimizzare il database...")
        conn.execute("VACUUM;")
        print_colored("Database ottimizzato con successo!", 'INFO')
        return True
    except Exception as e:
        print_colored(f"Errore nell'ottimizzazione del database: {e}", 'ERROR')
        return False

def repair_database(db_path):
    """Tenta di riparare il database."""
    print_section("Riparazione del database")
    
    # Crea un backup prima di tentare la riparazione
    backup_path = f"{db_path}.bak"
    try:
        if os.path.exists(db_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            print_colored(f"Backup del database creato: {backup_path}", 'INFO')
    except Exception as e:
        print_colored(f"Errore nella creazione del backup: {e}", 'WARNING')
    
    try:
        # Tenta di aprire il database in modalità recovery
        recovery_conn = sqlite3.connect(db_path)
        recovery_conn.execute("PRAGMA integrity_check;")
        recovery_conn.commit()
        recovery_conn.close()
        
        # Riconnetti e ottimizza
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA integrity_check;")
        conn.execute("VACUUM;")
        conn.close()
        
        print_colored("Riparazione completata con successo!", 'INFO')
        return True
    except Exception as e:
        print_colored(f"Errore nella riparazione del database: {e}", 'ERROR')
        print("Ripristino dal backup...")
        
        try:
            if os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, db_path)
                print_colored("Database ripristinato dal backup.", 'INFO')
        except Exception as backup_e:
            print_colored(f"Errore nel ripristino del backup: {backup_e}", 'ERROR')
        
        return False

def purge_old_records(conn):
    """Elimina i record obsoleti dal database."""
    print_section("Pulizia dei record obsoleti")
    
    try:
        cursor = conn.cursor()
        
        # Controlla se esiste la tabella videos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos';")
        if not cursor.fetchone():
            print_colored("Tabella 'videos' non trovata.", 'WARNING')
            return False
        
        # Ottieni la data di 90 giorni fa
        days_to_keep = 90
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Conta i record da eliminare
        cursor.execute(f"SELECT COUNT(*) FROM videos WHERE created_at < ?;", (cutoff_str,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print_colored(f"Nessun record più vecchio di {days_to_keep} giorni da eliminare.", 'INFO')
            return True
        
        # Chiedi conferma
        print_colored(f"Trovati {count} record più vecchi di {days_to_keep} giorni.", 'WARNING')
        confirm = input(f"Vuoi eliminare questi {count} record? (s/n): ").lower()
        
        if confirm == 's' or confirm == 'y':
            # Elimina i record
            cursor.execute(f"DELETE FROM videos WHERE created_at < ?;", (cutoff_str,))
            conn.commit()
            print_colored(f"{count} record eliminati con successo!", 'INFO')
            return True
        else:
            print_colored("Operazione annullata.", 'INFO')
            return False
        
    except Exception as e:
        print_colored(f"Errore nella pulizia dei record obsoleti: {e}", 'ERROR')
        return False

def rebuild_database(db_path):
    """Ricostruisce il database da zero."""
    print_section("Ricostruzione del database")
    
    # Crea un backup prima di procedere
    backup_path = f"{db_path}.bak"
    try:
        if os.path.exists(db_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            print_colored(f"Backup del database creato: {backup_path}", 'INFO')
    except Exception as e:
        print_colored(f"Errore nella creazione del backup: {e}", 'WARNING')
    
    # Elimina il database esistente
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print_colored("Database esistente rimosso.", 'INFO')
    except Exception as e:
        print_colored(f"Errore nella rimozione del database esistente: {e}", 'ERROR')
        return False
    
    # Crea un nuovo database con la struttura corretta
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crea la tabella videos
        cursor.execute('''
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            category TEXT,
            duration INTEGER,
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            viral_score REAL,
            retention_rate REAL,
            thumbnail_url TEXT,
            processed BOOLEAN DEFAULT 0,
            uploaded BOOLEAN DEFAULT 0,
            upload_id TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        ''')
        
        # Crea la tabella settings
        cursor.execute('''
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        ''')
        
        conn.commit()
        print_colored("Nuovo database creato con successo!", 'INFO')
        return True
    except Exception as e:
        print_colored(f"Errore nella creazione del nuovo database: {e}", 'ERROR')
        
        # Ripristina dal backup
        try:
            if os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, db_path)
                print_colored("Database ripristinato dal backup.", 'INFO')
        except Exception as backup_e:
            print_colored(f"Errore nel ripristino del backup: {backup_e}", 'ERROR')
        
        return False

def show_menu():
    """Mostra il menu principale."""
    print_header("Database Utility")
    print("1. Visualizza struttura del database")
    print("2. Ottimizza database (VACUUM)")
    print("3. Tenta riparazione del database")
    print("4. Elimina record obsoleti")
    print("5. Ricostruisci database da zero")
    print("6. Esci")
    
    choice = input("\nScegli un'opzione (1-6): ")
    return choice

def main():
    """Funzione principale."""
    db_path = get_db_path()
    
    # Assicurati che la directory del database esista
    create_directory_if_not_exists(os.path.dirname(db_path))
    
    print_colored(f"Utilizzo database: {db_path}", 'INFO')
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            conn = connect_to_database(db_path)
            if conn:
                check_database_structure(conn)
                conn.close()
        elif choice == '2':
            conn = connect_to_database(db_path)
            if conn:
                vacuum_database(conn)
                conn.close()
        elif choice == '3':
            repair_database(db_path)
        elif choice == '4':
            conn = connect_to_database(db_path)
            if conn:
                purge_old_records(conn)
                conn.close()
        elif choice == '5':
            confirm = input("Questa operazione eliminerà tutti i dati. Sei sicuro? (s/n): ").lower()
            if confirm == 's' or confirm == 'y':
                rebuild_database(db_path)
        elif choice == '6':
            print_colored("Arrivederci!", 'INFO')
            break
        else:
            print_colored("Opzione non valida. Riprova.", 'ERROR')
        
        input("\nPremi Enter per continuare...")

if __name__ == "__main__":
    main()
