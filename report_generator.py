"""
Modulo per la generazione di report sulle tendenze dei video virali.
"""

import os
import datetime
from pathlib import Path

def generate_trend_report(videos_by_category):
    """
    Generate a basic text report of trends by category
    
    Args:
        videos_by_category (dict): Dictionary of videos grouped by category
        
    Returns:
        str: Text report of trends
    """
    report = "📊 REPORT DELLE TENDENZE PER CATEGORIA 📊\n"
    report += f"Generato il: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n"
    
    # Overall stats
    total_videos = sum(len(videos) for videos in videos_by_category.values())
    report += f"Video totali analizzati: {total_videos}\n"
    report += f"Categorie analizzate: {len(videos_by_category)}\n\n"
    
    # Per category stats
    for category, videos in videos_by_category.items():
        report += f"\n📊 Categoria: {category} ({len(videos)} videos)\n"
        
        if not videos:
            report += "  Nessun video trovato in questa categoria.\n"
            continue
            
        # Get top videos by viral score
        top = sorted(videos, key=lambda x: x.get("viral_score", 0), reverse=True)[:3]
        
        # Calculate average stats
        avg_views = sum(v.get('views', 0) for v in videos) / len(videos)
        avg_likes = sum(v.get('likes', 0) for v in videos) / len(videos)
        avg_viral_score = sum(v.get('viral_score', 0) for v in videos) / len(videos)
        
        report += f"  Media visualizzazioni: {avg_views:.0f}\n"
        report += f"  Media likes: {avg_likes:.0f}\n"
        report += f"  Media viral score: {avg_viral_score:.2f}\n"
        
        report += "\n  Top 3 video per viral score:\n"
        for i, v in enumerate(top, 1):
            report += f"   {i}. {v['title'][:50]}{'...' if len(v['title']) > 50 else ''}\n"
            report += f"      👁️ {v.get('views', 0):,} views | 👍 {v.get('likes', 0):,} likes | 💯 Score: {v.get('viral_score', 0):.2f}\n"
            report += f"      🔗 https://youtube.com/watch?v={v.get('youtube_id')}\n"
    
    return report


def save_trend_report(report, filename=None, report_dir="data/reports"):
    """
    Save a trend report to a file
    
    Args:
        report (str): The text report to save
        filename (str, optional): The filename to save to
        report_dir (str, optional): The directory to save to
        
    Returns:
        str: Path to the saved report
    """
    # Create reports directory if it doesn't exist
    os.makedirs(report_dir, exist_ok=True)
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trend_report_{timestamp}.txt"
    
    # Complete path
    report_path = os.path.join(report_dir, filename)
    
    # Save report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report_path
