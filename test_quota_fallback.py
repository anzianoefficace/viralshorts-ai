#!/usr/bin/env python3
"""
Test script to verify the quota exhaustion fallback mechanism.
"""

import sys
import json
import logging
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from data.downloader import YouTubeShortsFinder
from database import Database

def test_quota_fallback():
    """Test the quota exhaustion fallback mechanism."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        db_path = Path("data/viral_shorts.db")
        db = Database(str(db_path))
        logger.info("Database initialized successfully")
        
        # Load configuration
        config_path = Path("config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Initialize YouTubeShortsFinder
        finder = YouTubeShortsFinder(config, db)
        logger.info("YouTubeShortsFinder initialized successfully")
        
        # Test getting existing unprocessed videos
        logger.info("\n=== Testing Existing Unprocessed Videos ===")
        existing_videos = finder.get_existing_unprocessed_videos(max_results=5)
        
        if existing_videos:
            logger.info(f"Found {len(existing_videos)} existing unprocessed videos:")
            for i, video in enumerate(existing_videos, 1):
                logger.info(f"{i}. {video['title']}")
                logger.info(f"   - Views: {video['views']}")
                logger.info(f"   - Viral Score: {video['viral_score']}")
                logger.info(f"   - File Path: {video.get('file_path', 'N/A')}")
                logger.info(f"   - Source: {video.get('source', 'N/A')}")
                logger.info("")
        else:
            logger.warning("No existing unprocessed videos found")
            
        # Test download_video with existing video data
        if existing_videos:
            logger.info("\n=== Testing Download Video with Existing Data ===")
            test_video = existing_videos[0]
            
            logger.info(f"Testing with video: {test_video['title']}")
            result = finder.download_video(test_video)
            
            if result:
                logger.info("download_video successfully handled existing video data")
                logger.info(f"File path: {result.get('file_path')}")
                logger.info(f"Source: {result.get('source')}")
            else:
                logger.error("download_video failed to handle existing video data")
        
        # Test search_viral_shorts with quota exhaustion simulation
        logger.info("\n=== Testing Search Viral Shorts (May Hit Quota) ===")
        try:
            videos = finder.search_viral_shorts(max_results=3)
            
            if videos:
                logger.info(f"Found {len(videos)} videos:")
                for i, video in enumerate(videos, 1):
                    source = video.get('source', 'new_api')
                    logger.info(f"{i}. {video['title']} (Source: {source})")
            else:
                logger.warning("No videos found")
        except Exception as e:
            logger.error(f"Error in search_viral_shorts: {e}")
        
        logger.info("\n=== Test Complete ===")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quota_fallback()
