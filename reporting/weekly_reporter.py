"""
📊 Weekly Reporter per ViralShortsAI
Sistema di generazione report settimanali avanzati con grafici e analytics
"""

import os
import json
import logging
import datetime
import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from jinja2 import Template
import pandas as pd

class WeeklyReporter:
    """
    Generatore di report settimanali con analytics e visualizzazioni
    """
    
    def __init__(self, db_path: str = "data/viral_shorts.db"):
        self.db_path = db_path
        self.logger = logging.getLogger('ViralShortsAI.WeeklyReporter')
        self.reports_dir = Path("data/reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Setup matplotlib per background
        plt.switch_backend('Agg')
        plt.style.use('default')
    
    def generate_report(self, week_offset: int = 0) -> str:
        """
        Genera report settimanale completo
        
        Args:
            week_offset: Offset settimane (0 = settimana corrente, -1 = settimana scorsa)
        
        Returns:
            str: Path del report generato
        """
        try:
            # Calcola periodo settimana
            end_date = datetime.datetime.now() + datetime.timedelta(weeks=week_offset)
            start_date = end_date - datetime.timedelta(days=7)
            
            self.logger.info(f"📊 Generating weekly report for {start_date.date()} to {end_date.date()}")
            
            # Raccogli dati
            data = self._collect_weekly_data(start_date, end_date)
            
            # Genera grafici
            charts = self._generate_charts(data, start_date, end_date)
            
            # Genera report HTML
            report_path = self._generate_html_report(data, charts, start_date, end_date)
            
            self.logger.info(f"✅ Weekly report generated: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate weekly report: {e}")
            return ""
    
    def _collect_weekly_data(self, start_date: datetime.datetime, end_date: datetime.datetime) -> Dict[str, Any]:
        """Raccoglie dati per il report settimanale"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Query per dati video della settimana
            video_data = pd.read_sql_query("""
                SELECT 
                    u.id,
                    u.title,
                    u.youtube_video_id,
                    u.upload_date,
                    a.views,
                    a.likes,
                    a.comments,
                    a.shares,
                    a.engagement_rate,
                    a.viral_score
                FROM uploaded_videos u
                LEFT JOIN analytics a ON u.id = a.video_id
                WHERE u.upload_date >= ? AND u.upload_date < ?
                ORDER BY u.upload_date DESC
            """, conn, params=(start_date.isoformat(), end_date.isoformat()))
            
            # Query per dati precedenti (confronto)
            prev_start = start_date - datetime.timedelta(days=7)
            prev_end = start_date
            
            prev_data = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as video_count,
                    COALESCE(SUM(a.views), 0) as total_views,
                    COALESCE(SUM(a.likes), 0) as total_likes,
                    COALESCE(SUM(a.comments), 0) as total_comments,
                    COALESCE(AVG(a.engagement_rate), 0) as avg_engagement,
                    COALESCE(AVG(a.viral_score), 0) as avg_viral_score
                FROM uploaded_videos u
                LEFT JOIN analytics a ON u.id = a.video_id
                WHERE u.upload_date >= ? AND u.upload_date < ?
            """, conn, params=(prev_start.isoformat(), prev_end.isoformat()))
            
            conn.close()
            
            # Processa dati
            if not video_data.empty:
                video_data['upload_date'] = pd.to_datetime(video_data['upload_date'])
                video_data = video_data.fillna(0)
            
            # Statistiche aggregate
            current_stats = {
                'video_count': len(video_data),
                'total_views': int(video_data['views'].sum()) if not video_data.empty else 0,
                'total_likes': int(video_data['likes'].sum()) if not video_data.empty else 0,
                'total_comments': int(video_data['comments'].sum()) if not video_data.empty else 0,
                'avg_engagement': float(video_data['engagement_rate'].mean()) if not video_data.empty else 0.0,
                'avg_viral_score': float(video_data['viral_score'].mean()) if not video_data.empty else 0.0,
            }
            
            # Calcola variazioni rispetto settimana precedente
            if not prev_data.empty:
                prev_stats = prev_data.iloc[0].to_dict()
                changes = {}
                for key in current_stats.keys():
                    if key in prev_stats and prev_stats[key] > 0:
                        change_pct = ((current_stats[key] - prev_stats[key]) / prev_stats[key]) * 100
                        changes[f'{key}_change'] = round(change_pct, 1)
                    else:
                        changes[f'{key}_change'] = 0.0
            else:
                changes = {f'{key}_change': 0.0 for key in current_stats.keys()}
            
            # Top performers
            top_videos = []
            if not video_data.empty:
                top_videos = video_data.nlargest(5, 'viral_score')[
                    ['title', 'views', 'likes', 'comments', 'viral_score', 'youtube_video_id']
                ].to_dict('records')
            
            # Performance giornaliera
            daily_performance = []
            if not video_data.empty:
                daily_stats = video_data.groupby(video_data['upload_date'].dt.date).agg({
                    'views': 'sum',
                    'likes': 'sum',
                    'comments': 'sum',
                    'viral_score': 'mean'
                }).reset_index()
                daily_performance = daily_stats.to_dict('records')
            
            return {
                'period': {'start': start_date, 'end': end_date},
                'current_stats': current_stats,
                'changes': changes,
                'top_videos': top_videos,
                'daily_performance': daily_performance,
                'video_data': video_data,
                'generated_at': datetime.datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting weekly data: {e}")
            return {}
    
    def _generate_charts(self, data: Dict[str, Any], start_date: datetime.datetime, end_date: datetime.datetime) -> Dict[str, str]:
        """Genera grafici per il report"""
        charts = {}
        
        try:
            charts_dir = self.reports_dir / "charts"
            charts_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 1. Grafico performance giornaliera
            if data.get('daily_performance'):
                chart_path = self._create_daily_performance_chart(
                    data['daily_performance'], charts_dir, timestamp
                )
                charts['daily_performance'] = chart_path
            
            # 2. Grafico top video
            if data.get('top_videos'):
                chart_path = self._create_top_videos_chart(
                    data['top_videos'], charts_dir, timestamp
                )
                charts['top_videos'] = chart_path
            
            # 3. Grafico engagement vs views
            if not data.get('video_data', pd.DataFrame()).empty:
                chart_path = self._create_engagement_scatter_chart(
                    data['video_data'], charts_dir, timestamp
                )
                charts['engagement_scatter'] = chart_path
            
            # 4. Grafico distribuzione viral score
            if not data.get('video_data', pd.DataFrame()).empty:
                chart_path = self._create_viral_score_distribution(
                    data['video_data'], charts_dir, timestamp
                )
                charts['viral_distribution'] = chart_path
            
        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")
        
        return charts
    
    def _create_daily_performance_chart(self, daily_data: List[Dict], charts_dir: Path, timestamp: str) -> str:
        """Crea grafico performance giornaliera"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            dates = [item['upload_date'] for item in daily_data]
            views = [item['views'] for item in daily_data]
            viral_scores = [item['viral_score'] for item in daily_data]
            
            # Views per giorno
            ax1.plot(dates, views, marker='o', linewidth=2, markersize=6, color='#1f77b4')
            ax1.set_title('Views Giornaliere', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Views', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # Viral score medio per giorno
            ax2.bar(dates, viral_scores, color='#ff7f0e', alpha=0.7)
            ax2.set_title('Viral Score Medio Giornaliero', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Viral Score', fontsize=12)
            ax2.set_xlabel('Data', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            chart_path = charts_dir / f"daily_performance_{timestamp}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path.name)
            
        except Exception as e:
            self.logger.error(f"Error creating daily performance chart: {e}")
            return ""
    
    def _create_top_videos_chart(self, top_videos: List[Dict], charts_dir: Path, timestamp: str) -> str:
        """Crea grafico top video"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            titles = [video['title'][:30] + '...' if len(video['title']) > 30 else video['title'] 
                     for video in top_videos]
            viral_scores = [video['viral_score'] for video in top_videos]
            
            bars = ax.barh(titles, viral_scores, color='#2ca02c', alpha=0.7)
            ax.set_title('Top 5 Video per Viral Score', fontsize=14, fontweight='bold')
            ax.set_xlabel('Viral Score', fontsize=12)
            ax.grid(True, alpha=0.3, axis='x')
            
            # Aggiungi valori sulle barre
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                       f'{width:.1f}', ha='left', va='center', fontweight='bold')
            
            plt.tight_layout()
            
            chart_path = charts_dir / f"top_videos_{timestamp}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path.name)
            
        except Exception as e:
            self.logger.error(f"Error creating top videos chart: {e}")
            return ""
    
    def _create_engagement_scatter_chart(self, video_data: pd.DataFrame, charts_dir: Path, timestamp: str) -> str:
        """Crea scatter plot engagement vs views"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            scatter = ax.scatter(video_data['views'], video_data['engagement_rate'], 
                               c=video_data['viral_score'], cmap='viridis', 
                               alpha=0.7, s=60)
            
            ax.set_title('Engagement Rate vs Views', fontsize=14, fontweight='bold')
            ax.set_xlabel('Views', fontsize=12)
            ax.set_ylabel('Engagement Rate (%)', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Colorbar per viral score
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Viral Score', fontsize=12)
            
            plt.tight_layout()
            
            chart_path = charts_dir / f"engagement_scatter_{timestamp}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path.name)
            
        except Exception as e:
            self.logger.error(f"Error creating engagement scatter chart: {e}")
            return ""
    
    def _create_viral_score_distribution(self, video_data: pd.DataFrame, charts_dir: Path, timestamp: str) -> str:
        """Crea istogramma distribuzione viral score"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.hist(video_data['viral_score'], bins=20, color='#d62728', alpha=0.7, edgecolor='black')
            ax.set_title('Distribuzione Viral Score', fontsize=14, fontweight='bold')
            ax.set_xlabel('Viral Score', fontsize=12)
            ax.set_ylabel('Numero di Video', fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Aggiungi linea media
            mean_score = video_data['viral_score'].mean()
            ax.axvline(mean_score, color='red', linestyle='--', linewidth=2, 
                      label=f'Media: {mean_score:.1f}')
            ax.legend()
            
            plt.tight_layout()
            
            chart_path = charts_dir / f"viral_distribution_{timestamp}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path.name)
            
        except Exception as e:
            self.logger.error(f"Error creating viral score distribution: {e}")
            return ""
    
    def _generate_html_report(self, data: Dict[str, Any], charts: Dict[str, str], 
                            start_date: datetime.datetime, end_date: datetime.datetime) -> Path:
        """Genera report HTML"""
        try:
            template_str = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 ViralShortsAI - Report Settimanale</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; margin: 0 auto; 
            background: white; border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; text-align: center; 
        }
        .header h1 { margin: 0; font-size: 2.5rem; }
        .header p { margin: 10px 0 0 0; font-size: 1.2rem; opacity: 0.9; }
        .content { padding: 30px; }
        .stats-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; margin-bottom: 30px; 
        }
        .stat-card { 
            background: #f8f9fa; border-radius: 10px; padding: 25px;
            text-align: center; border-left: 5px solid #667eea;
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 2.5rem; font-weight: bold; color: #667eea; margin: 0; }
        .stat-label { color: #6c757d; margin: 5px 0; }
        .stat-change { 
            font-size: 0.9rem; padding: 5px 10px; border-radius: 20px; 
            display: inline-block; margin-top: 10px;
        }
        .stat-change.positive { background: #d4edda; color: #155724; }
        .stat-change.negative { background: #f8d7da; color: #721c24; }
        .stat-change.neutral { background: #e2e3e5; color: #383d41; }
        .section { margin: 40px 0; }
        .section h2 { 
            color: #343a40; border-bottom: 3px solid #667eea; 
            padding-bottom: 10px; margin-bottom: 20px; 
        }
        .chart-container { text-align: center; margin: 20px 0; }
        .chart-container img { max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .video-table { 
            width: 100%; border-collapse: collapse; 
            background: white; border-radius: 10px; overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .video-table th { 
            background: #667eea; color: white; padding: 15px; 
            text-align: left; font-weight: 600; 
        }
        .video-table td { padding: 15px; border-bottom: 1px solid #dee2e6; }
        .video-table tr:hover { background: #f8f9fa; }
        .video-title { 
            font-weight: 600; color: #343a40; 
            max-width: 300px; overflow: hidden; 
            text-overflow: ellipsis; white-space: nowrap; 
        }
        .metric-badge { 
            background: #e9ecef; padding: 4px 8px; 
            border-radius: 15px; font-size: 0.85rem; 
            font-weight: 600; color: #495057; 
        }
        .footer { 
            background: #f8f9fa; padding: 20px; text-align: center; 
            color: #6c757d; border-top: 1px solid #dee2e6; 
        }
        .no-data { 
            text-align: center; padding: 40px; color: #6c757d; 
            background: #f8f9fa; border-radius: 10px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ViralShortsAI</h1>
            <p>Report Settimanale: {{ start_date.strftime('%d/%m/%Y') }} - {{ end_date.strftime('%d/%m/%Y') }}</p>
        </div>
        
        <div class="content">
            <!-- Statistiche Principali -->
            <div class="section">
                <h2>📈 Statistiche Settimanali</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <p class="stat-number">{{ data.current_stats.video_count }}</p>
                        <p class="stat-label">Video Pubblicati</p>
                        <span class="stat-change {{ 'positive' if data.changes.video_count_change > 0 else 'negative' if data.changes.video_count_change < 0 else 'neutral' }}">
                            {{ '+' if data.changes.video_count_change > 0 else '' }}{{ data.changes.video_count_change }}%
                        </span>
                    </div>
                    <div class="stat-card">
                        <p class="stat-number">{{ "{:,}".format(data.current_stats.total_views) }}</p>
                        <p class="stat-label">Visualizzazioni Totali</p>
                        <span class="stat-change {{ 'positive' if data.changes.total_views_change > 0 else 'negative' if data.changes.total_views_change < 0 else 'neutral' }}">
                            {{ '+' if data.changes.total_views_change > 0 else '' }}{{ data.changes.total_views_change }}%
                        </span>
                    </div>
                    <div class="stat-card">
                        <p class="stat-number">{{ "{:,}".format(data.current_stats.total_likes) }}</p>
                        <p class="stat-label">Like Totali</p>
                        <span class="stat-change {{ 'positive' if data.changes.total_likes_change > 0 else 'negative' if data.changes.total_likes_change < 0 else 'neutral' }}">
                            {{ '+' if data.changes.total_likes_change > 0 else '' }}{{ data.changes.total_likes_change }}%
                        </span>
                    </div>
                    <div class="stat-card">
                        <p class="stat-number">{{ data.current_stats.avg_engagement|round(1) }}%</p>
                        <p class="stat-label">Engagement Medio</p>
                        <span class="stat-change {{ 'positive' if data.changes.avg_engagement_change > 0 else 'negative' if data.changes.avg_engagement_change < 0 else 'neutral' }}">
                            {{ '+' if data.changes.avg_engagement_change > 0 else '' }}{{ data.changes.avg_engagement_change }}%
                        </span>
                    </div>
                    <div class="stat-card">
                        <p class="stat-number">{{ data.current_stats.avg_viral_score|round(1) }}</p>
                        <p class="stat-label">Viral Score Medio</p>
                        <span class="stat-change {{ 'positive' if data.changes.avg_viral_score_change > 0 else 'negative' if data.changes.avg_viral_score_change < 0 else 'neutral' }}">
                            {{ '+' if data.changes.avg_viral_score_change > 0 else '' }}{{ data.changes.avg_viral_score_change }}%
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- Grafici -->
            {% if charts %}
            <div class="section">
                <h2>📊 Grafici Performance</h2>
                {% if charts.daily_performance %}
                <div class="chart-container">
                    <img src="charts/{{ charts.daily_performance }}" alt="Performance Giornaliera">
                </div>
                {% endif %}
                
                {% if charts.top_videos %}
                <div class="chart-container">
                    <img src="charts/{{ charts.top_videos }}" alt="Top Video">
                </div>
                {% endif %}
                
                {% if charts.engagement_scatter %}
                <div class="chart-container">
                    <img src="charts/{{ charts.engagement_scatter }}" alt="Engagement vs Views">
                </div>
                {% endif %}
                
                {% if charts.viral_distribution %}
                <div class="chart-container">
                    <img src="charts/{{ charts.viral_distribution }}" alt="Distribuzione Viral Score">
                </div>
                {% endif %}
            </div>
            {% endif %}
            
            <!-- Top Video -->
            {% if data.top_videos %}
            <div class="section">
                <h2>🏆 Top 5 Video della Settimana</h2>
                <table class="video-table">
                    <thead>
                        <tr>
                            <th>Titolo</th>
                            <th>Views</th>
                            <th>Likes</th>
                            <th>Commenti</th>
                            <th>Viral Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for video in data.top_videos %}
                        <tr>
                            <td class="video-title" title="{{ video.title }}">{{ video.title }}</td>
                            <td><span class="metric-badge">{{ "{:,}".format(video.views) }}</span></td>
                            <td><span class="metric-badge">{{ "{:,}".format(video.likes) }}</span></td>
                            <td><span class="metric-badge">{{ "{:,}".format(video.comments) }}</span></td>
                            <td><span class="metric-badge">{{ video.viral_score|round(1) }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="section">
                <div class="no-data">
                    <h3>🤷 Nessun video trovato</h3>
                    <p>Non ci sono video da mostrare per questo periodo.</p>
                </div>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>Report generato il {{ data.generated_at.strftime('%d/%m/%Y alle %H:%M') }} da ViralShortsAI</p>
        </div>
    </div>
</body>
</html>
"""
            
            template = Template(template_str)
            html_content = template.render(
                data=data,
                charts=charts,
                start_date=start_date,
                end_date=end_date
            )
            
            # Salva report
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = self.reports_dir / f"weekly_report_{timestamp}.html"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return Path("")

if __name__ == "__main__":
    # Test del reporter
    logging.basicConfig(level=logging.INFO)
    
    reporter = WeeklyReporter()
    report_path = reporter.generate_report()
    print(f"Report generated: {report_path}")
