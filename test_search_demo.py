#!/usr/bin/env python3
"""
Test del download di video virali - SENZA filtro copyright per demo
"""

import json
from data.downloader import YouTubeShortsFinder
from database import Database

def test_viral_search_no_copyright():
    """Test ricerca video virali senza filtro copyright"""
    print("🔍 Ricerca video virali (SENZA filtro copyright)...")
    
    # Carica configurazione
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Disabilita temporaneamente il filtro copyright
    original_filter = config['youtube_search']['copyright_filter']
    config['youtube_search']['copyright_filter'] = False
    
    # Riduci views minime per avere più risultati
    original_views = config['youtube_search']['min_views']
    config['youtube_search']['min_views'] = 10000
    
    print(f"🔧 Filtro copyright: {config['youtube_search']['copyright_filter']}")
    print(f"🔧 Views minime: {config['youtube_search']['min_views']:,}")
    
    # Inizializza database e finder
    db_path = config.get('paths', {}).get('database', 'data/viral_shorts.db')
    db = Database(db_path)
    finder = YouTubeShortsFinder(config, db)
    
    # Cerca 3 video virali
    print("\nRicerca in corso...")
    viral_videos = finder.search_viral_shorts(max_results=3)
    
    if viral_videos:
        print(f"\n🎬 Trovati {len(viral_videos)} video virali:")
        for i, video in enumerate(viral_videos, 1):
            print(f"\n{i}. {video['title']}")
            print(f"   📺 Canale: {video['channel']}")
            print(f"   👀 Views: {video['views']:,}")
            print(f"   👍 Likes: {video['likes']:,}")
            print(f"   💬 Commenti: {video['comments']:,}")
            print(f"   ⭐ Viral Score: {video['viral_score']}")
            print(f"   📂 Categoria: {video['category']}")
            print(f"   ⏱️ Durata: {video['duration']} secondi")
            print(f"   📄 Copyright: {video['copyright_status']}")
            print(f"   🔗 URL: {video['url']}")
    else:
        print("❌ Nessun video virale trovato")
    
    # Ripristina configurazione originale
    config['youtube_search']['copyright_filter'] = original_filter
    config['youtube_search']['min_views'] = original_views

if __name__ == "__main__":
    test_viral_search_no_copyright()
