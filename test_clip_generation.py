#!/usr/bin/env python3
"""
Test specifico per la generazione delle clip con le nuove funzionalità di fallback
"""

import json
import os
from processing.editor import VideoEditor
from database import Database

def test_clip_generation():
    """Test la generazione di clip con fallback"""
    print("🎬 Test generazione clip con fallback...")
    
    # Carica configurazione
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Inizializza database e editor
    db_path = config.get('paths', {}).get('database', 'data/viral_shorts.db')
    db = Database(db_path)
    editor = VideoEditor(config, db)
    
    # Test 1: Video normale con key moments
    print("\n=== Test 1: Video normale ===")
    video_duration = 60
    key_moments = [
        {'start': 10, 'end': 15, 'text': 'Momento interessante'},
        {'start': 30, 'end': 35, 'text': 'Altro momento'}
    ]
    segments = editor.find_optimal_clip_segments(video_duration, key_moments, 30)
    print(f"Segmenti generati: {segments}")
    
    # Test 2: Video senza key moments (should use fallback)
    print("\n=== Test 2: Video senza key moments ===")
    segments_no_moments = editor.find_optimal_clip_segments(video_duration, [], 30)
    print(f"Segmenti fallback: {segments_no_moments}")
    
    # Test 3: Video molto corto
    print("\n=== Test 3: Video molto corto ===")
    short_segments = editor.find_optimal_clip_segments(10, [], 30)
    print(f"Segmenti video corto: {short_segments}")
    
    # Test 4: Video con durata 0 (should return empty)
    print("\n=== Test 4: Video durata 0 ===")
    zero_segments = editor.find_optimal_clip_segments(0, [], 30)
    print(f"Segmenti video durata 0: {zero_segments}")
    
    print("\n✅ Test completati!")

if __name__ == "__main__":
    test_clip_generation()
