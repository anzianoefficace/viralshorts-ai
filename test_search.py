#!/usr/bin/env python3
"""
Test del download di video virali - esempio pratico
"""

import json
from data.downloader import YouTubeShortsFinder
from database import Database

def test_viral_search():
    """Test ricerca video virali"""
    print("🔍 Ricerca video virali...")
    
    # Carica configurazione
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Inizializza database e finder
    db_path = config.get('paths', {}).get('database', 'data/viral_shorts.db')
    db = Database(db_path)
    finder = YouTubeShortsFinder(config, db)
    
    # Cerca 5 video virali
    print("Ricerca in corso...")
    viral_videos = finder.search_viral_shorts(max_results=5)
    
    if viral_videos:
        print(f"\n🎬 Trovati {len(viral_videos)} video virali:")
        for i, video in enumerate(viral_videos, 1):
            print(f"\n{i}. {video['title']}")
            print(f"   📺 Canale: {video['channel']}")
            print(f"   👀 Views: {video['views']:,}")
            print(f"   👍 Likes: {video['likes']:,}")
            print(f"   💬 Commenti: {video['comments']:,}")
            print(f"   ⭐ Viral Score: {video['viral_score']}")
            print(f"   🔗 URL: {video['url']}")
    else:
        print("❌ Nessun video virale trovato")

if __name__ == "__main__":
    test_viral_search()
