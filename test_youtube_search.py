#!/usr/bin/env python3
"""
Script di test per la funzionalità di ricerca di YouTube Shorts.
Esegue una ricerca di shorts virali e mostra i risultati.
"""

import os
import json
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configura logging di base
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger("YouTubeSearchTest")

# Carica le variabili d'ambiente
load_dotenv()

# Importa i moduli necessari
try:
    logger.info("Importazione dei moduli necessari...")
    from data.downloader import YouTubeShortsFinder
    from database import Database
except Exception as e:
    logger.error(f"Errore nell'importazione dei moduli: {e}")
    sys.exit(1)

def main():
    """Funzione principale del test."""
    logger.info("Avvio del test di ricerca di YouTube Shorts")
    
    # Carica la configurazione
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        logger.info("Configurazione caricata con successo")
    except Exception as e:
        logger.error(f"Errore nel caricamento della configurazione: {e}")
        sys.exit(1)
    
    # Assicura che le directory necessarie esistano
    for path_name in ['data', 'data/downloads', 'logs']:
        Path(path_name).mkdir(parents=True, exist_ok=True)
    
    # Connessione al database
    db_path = config.get('paths', {}).get('database', 'data/viral_shorts.db')
    try:
        db = Database(db_path)
        logger.info(f"Connesso al database: {db_path}")
    except Exception as e:
        logger.error(f"Errore nella connessione al database: {e}")
        sys.exit(1)
        
    # Aggiorna la configurazione con i valori da .env
    try:
        # Leggi i valori da .env
        search_config = {
            'min_views': int(os.getenv('SEARCH_MIN_VIEWS', '50000')),
            'published_within_hours': int(os.getenv('SEARCH_PUBLISHED_WITHIN_HOURS', '48')),
            'max_duration': int(os.getenv('SEARCH_MAX_DURATION', '60')),
            'copyright_filter': os.getenv('COPYRIGHT_FILTER', 'false').lower() == 'true'
        }
        
        # Aggiorna la configurazione
        if 'youtube_search' not in config:
            config['youtube_search'] = {}
        
        config['youtube_search'].update({
            'min_views': search_config['min_views'],
            'published_within_hours': search_config['published_within_hours'],
            'max_duration': search_config['max_duration'],
            'copyright_filter': search_config['copyright_filter']
        })
        
        logger.info(f"Configurazione di ricerca: {json.dumps(search_config)}")
    except Exception as e:
        logger.warning(f"Errore nell'aggiornamento della configurazione: {e}")
    
    # Crea l'istanza di YouTubeShortsFinder
    try:
        finder = YouTubeShortsFinder(config, db)
        logger.info("YouTubeShortsFinder inizializzato con successo")
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione di YouTubeShortsFinder: {e}")
        sys.exit(1)
    
    # Esegui la ricerca
    try:
        logger.info("Avvio della ricerca di shorts virali...")
        shorts = finder.search_viral_shorts(max_results=10)
        
        # Mostra i risultati
        logger.info(f"Trovati {len(shorts)} shorts virali")
        
        if shorts:
            logger.info("\n=== RISULTATI DELLA RICERCA ===")
            for i, video in enumerate(shorts, 1):
                logger.info(f"\n--- Video {i} ---")
                logger.info(f"ID: {video['youtube_id']}")
                logger.info(f"Titolo: {video['title']}")
                logger.info(f"Canale: {video['channel']}")
                logger.info(f"Visualizzazioni: {video['views']}")
                logger.info(f"Like: {video['likes']}")
                logger.info(f"Durata: {video['duration']} secondi")
                logger.info(f"Categoria: {video['category']}")
                logger.info(f"Query di ricerca: {video.get('search_query', 'N/A')}")
                logger.info(f"URL: {video['url']}")
                logger.info(f"Stato copyright: {video['copyright_status']}")
        else:
            logger.warning("Nessun video trovato che corrisponda ai criteri")
            
    except Exception as e:
        logger.error(f"Errore durante la ricerca: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("Test completato")

if __name__ == "__main__":
    main()
