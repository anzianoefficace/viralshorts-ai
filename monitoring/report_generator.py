import os
import json
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path
import logging

class TrendReportGenerator:
    """
    Generate visual and textual reports from trend analysis data
    """
    
    def __init__(self, report_dir=None):
        """
        Initialize the report generator
        
        Args:
            report_dir (str): Directory to save reports (default: data/reports)
        """
        self.logger = logging.getLogger('viral_shorts')
        
        if report_dir:
            self.report_dir = Path(report_dir)
        else:
            self.report_dir = Path('data/reports')
            
        # Create directory if it doesn't exist
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Set up style for plots
        sns.set(style="whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        
    def generate_report(self, trend_analysis, filename_prefix=None):
        """
        Generate a complete report from trend analysis data
        
        Args:
            trend_analysis (dict): The trend analysis data
            filename_prefix (str): Optional prefix for report filenames
            
        Returns:
            dict: Paths to the generated reports
        """
        if not trend_analysis or not isinstance(trend_analysis, dict):
            self.logger.error("Invalid trend analysis data provided")
            return {}
            
        # Generate timestamp for filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{filename_prefix}_" if filename_prefix else ""
        
        # Create report paths
        report_paths = {
            'json': self.report_dir / f"{prefix}trend_report_{timestamp}.json",
            'html': self.report_dir / f"{prefix}trend_report_{timestamp}.html",
            'charts_dir': self.report_dir / f"{prefix}charts_{timestamp}"
        }
        
        # Create charts directory
        os.makedirs(report_paths['charts_dir'], exist_ok=True)
        
        # Save JSON report
        with open(report_paths['json'], 'w') as f:
            json.dump(trend_analysis, f, indent=2)
            
        # Generate charts
        chart_paths = self._generate_charts(trend_analysis, report_paths['charts_dir'])
        report_paths['charts'] = chart_paths
        
        # Generate HTML report
        html_content = self._generate_html_report(trend_analysis, chart_paths)
        with open(report_paths['html'], 'w') as f:
            f.write(html_content)
            
        self.logger.info(f"Generated reports at {self.report_dir}")
        return report_paths
        
    def _generate_charts(self, analysis, charts_dir):
        """
        Generate charts from the trend analysis
        
        Args:
            analysis (dict): The trend analysis data
            charts_dir (Path): Directory to save charts
            
        Returns:
            dict: Paths to the generated charts
        """
        chart_paths = {}
        
        # 1. Category Distribution
        if analysis.get('categories'):
            plt.figure(figsize=(12, 6))
            categories = list(analysis['categories'].keys())
            counts = [data['count'] for data in analysis['categories'].values()]
            
            plt.bar(categories, counts, color=sns.color_palette("viridis", len(categories)))
            plt.title('Video Distribution by Category', fontsize=15)
            plt.xlabel('Category', fontsize=12)
            plt.ylabel('Number of Videos', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            chart_path = charts_dir / 'category_distribution.png'
            plt.savefig(chart_path)
            plt.close()
            chart_paths['category_distribution'] = chart_path
            
        # 2. Viral Score by Category
        if analysis.get('categories'):
            plt.figure(figsize=(12, 6))
            categories = list(analysis['categories'].keys())
            viral_scores = [data['avg_viral_score'] for data in analysis['categories'].values()]
            
            plt.bar(categories, viral_scores, color=sns.color_palette("magma", len(categories)))
            plt.title('Average Viral Score by Category', fontsize=15)
            plt.xlabel('Category', fontsize=12)
            plt.ylabel('Average Viral Score', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            chart_path = charts_dir / 'viral_score_by_category.png'
            plt.savefig(chart_path)
            plt.close()
            chart_paths['viral_score_by_category'] = chart_path
            
        # 3. Top Channels
        if analysis.get('top_channels'):
            plt.figure(figsize=(12, 6))
            channels = list(analysis['top_channels'].keys())
            video_counts = list(analysis['top_channels'].values())
            
            plt.barh(channels, video_counts, color=sns.color_palette("coolwarm", len(channels)))
            plt.title('Top Channels by Video Count', fontsize=15)
            plt.xlabel('Number of Videos', fontsize=12)
            plt.ylabel('Channel', fontsize=12)
            plt.tight_layout()
            
            chart_path = charts_dir / 'top_channels.png'
            plt.savefig(chart_path)
            plt.close()
            chart_paths['top_channels'] = chart_path
            
        # 4. Key Metrics
        if all(key in analysis for key in ['avg_views', 'avg_likes', 'avg_comments', 'avg_viral_score']):
            plt.figure(figsize=(10, 6))
            metrics = ['avg_views', 'avg_likes', 'avg_comments', 'avg_viral_score']
            values = [analysis[metric] for metric in metrics]
            
            # Normalize for better visualization
            normalized_values = []
            for i, val in enumerate(values):
                if i == 0:  # views are usually much higher
                    normalized_values.append(val / 1000)  # show in thousands
                elif i == 3:  # viral score might need scaling
                    normalized_values.append(val * 10)
                else:
                    normalized_values.append(val)
                    
            labels = ['Views (thousands)', 'Likes', 'Comments', 'Viral Score (x10)']
            
            plt.bar(labels, normalized_values, color=sns.color_palette("Set2", 4))
            plt.title('Average Performance Metrics', fontsize=15)
            plt.ylabel('Value', fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            chart_path = charts_dir / 'key_metrics.png'
            plt.savefig(chart_path)
            plt.close()
            chart_paths['key_metrics'] = chart_path
            
        return chart_paths
        
    def _generate_html_report(self, analysis, chart_paths):
        """
        Generate an HTML report from the trend analysis
        
        Args:
            analysis (dict): The trend analysis data
            chart_paths (dict): Paths to the generated charts
            
        Returns:
            str: HTML content
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Viral Shorts Trend Report</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    border-radius: 8px;
                }}
                h1, h2, h3 {{
                    color: #2C3E50;
                }}
                h1 {{
                    border-bottom: 2px solid #3498DB;
                    padding-bottom: 10px;
                    margin-bottom: 30px;
                }}
                .section {{
                    margin-bottom: 40px;
                }}
                .chart-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #3498DB;
                    color: white;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .highlight {{
                    font-weight: bold;
                    color: #3498DB;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 0.9em;
                    color: #7f8c8d;
                }}
                .metric-card {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #3498DB;
                    padding: 15px;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .metric-value {{
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #2C3E50;
                }}
                .metric-label {{
                    font-size: 0.9em;
                    color: #7f8c8d;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Viral Shorts Trend Analysis Report</h1>
                <p>Generated on: {timestamp}</p>
                
                <div class="section">
                    <h2>Overview</h2>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{analysis.get('total_videos', 0)}</div>
                            <div class="metric-label">Total Videos Analyzed</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{len(analysis.get('categories', {}))}</div>
                            <div class="metric-label">Categories</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{analysis.get('avg_views', 0):,.0f}</div>
                            <div class="metric-label">Average Views</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{analysis.get('avg_viral_score', 0):.2f}</div>
                            <div class="metric-label">Average Viral Score</div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Key Performance Metrics</h3>
        """
        
        # Add key metrics chart if available
        if 'key_metrics' in chart_paths:
            rel_path = os.path.relpath(chart_paths['key_metrics'], self.report_dir)
            html += f'<img src="{rel_path}" alt="Key Metrics Chart">\n'
        
        html += """
                    </div>
                </div>
                
                <div class="section">
                    <h2>Category Analysis</h2>
        """
        
        # Add category distribution chart if available
        if 'category_distribution' in chart_paths:
            rel_path = os.path.relpath(chart_paths['category_distribution'], self.report_dir)
            html += f"""
                    <div class="chart-container">
                        <h3>Video Distribution by Category</h3>
                        <img src="{rel_path}" alt="Category Distribution Chart">
                    </div>
            """
            
        # Add viral score by category chart if available
        if 'viral_score_by_category' in chart_paths:
            rel_path = os.path.relpath(chart_paths['viral_score_by_category'], self.report_dir)
            html += f"""
                    <div class="chart-container">
                        <h3>Average Viral Score by Category</h3>
                        <img src="{rel_path}" alt="Viral Score by Category Chart">
                    </div>
            """
        
        # Add category details table
        if analysis.get('categories'):
            html += """
                    <h3>Category Details</h3>
                    <table>
                        <tr>
                            <th>Category</th>
                            <th>Videos</th>
                            <th>Avg. Views</th>
                            <th>Avg. Viral Score</th>
                        </tr>
            """
            
            for category, data in analysis['categories'].items():
                html += f"""
                        <tr>
                            <td>{category}</td>
                            <td>{data.get('count', 0)}</td>
                            <td>{data.get('avg_views', 0):,.0f}</td>
                            <td>{data.get('avg_viral_score', 0):.2f}</td>
                        </tr>
                """
                
            html += """
                    </table>
            """
        
        html += """
                </div>
                
                <div class="section">
                    <h2>Channel Analysis</h2>
        """
        
        # Add top channels chart if available
        if 'top_channels' in chart_paths:
            rel_path = os.path.relpath(chart_paths['top_channels'], self.report_dir)
            html += f"""
                    <div class="chart-container">
                        <h3>Top Channels by Video Count</h3>
                        <img src="{rel_path}" alt="Top Channels Chart">
                    </div>
            """
            
        html += """
                </div>
                
                <div class="section">
                    <h2>Query Analysis</h2>
        """
        
        # Add query details
        if analysis.get('queries'):
            html += """
                    <h3>Most Effective Search Queries</h3>
                    <table>
                        <tr>
                            <th>Query</th>
                            <th>Videos Found</th>
                        </tr>
            """
            
            for query, data in list(analysis['queries'].items())[:10]:  # Show top 10
                html += f"""
                        <tr>
                            <td>{query}</td>
                            <td>{data.get('count', 0)}</td>
                        </tr>
                """
                
            html += """
                    </table>
            """
            
        html += """
                </div>
                
                <div class="footer">
                    <p>Generated by ViralShortsAI Trend Report Generator</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def generate_csv_export(self, trend_analysis, filename=None):
        """
        Export trend analysis data to CSV format
        
        Args:
            trend_analysis (dict): The trend analysis data
            filename (str): Optional filename for the CSV file
            
        Returns:
            str: Path to the CSV file
        """
        if not trend_analysis or not isinstance(trend_analysis, dict):
            self.logger.error("Invalid trend analysis data provided")
            return None
            
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.report_dir / f"trend_analysis_{timestamp}.csv"
        else:
            filename = self.report_dir / filename
            
        # Create DataFrames from the analysis data
        
        # Categories DataFrame
        if trend_analysis.get('categories'):
            categories_data = []
            for category, data in trend_analysis['categories'].items():
                categories_data.append({
                    'category': category,
                    'video_count': data.get('count', 0),
                    'total_views': data.get('views', 0),
                    'avg_views': data.get('avg_views', 0),
                    'avg_viral_score': data.get('avg_viral_score', 0)
                })
                
            df_categories = pd.DataFrame(categories_data)
            df_categories.to_csv(self.report_dir / f"{filename.stem}_categories.csv", index=False)
            
        # Queries DataFrame
        if trend_analysis.get('queries'):
            queries_data = []
            for query, data in trend_analysis['queries'].items():
                queries_data.append({
                    'query': query,
                    'video_count': data.get('count', 0)
                })
                
            df_queries = pd.DataFrame(queries_data)
            df_queries.to_csv(self.report_dir / f"{filename.stem}_queries.csv", index=False)
            
        # Overall metrics
        overall_data = {
            'metric': ['total_videos', 'avg_views', 'avg_likes', 'avg_comments', 'avg_viral_score'],
            'value': [
                trend_analysis.get('total_videos', 0),
                trend_analysis.get('avg_views', 0),
                trend_analysis.get('avg_likes', 0),
                trend_analysis.get('avg_comments', 0),
                trend_analysis.get('avg_viral_score', 0)
            ]
        }
        df_overall = pd.DataFrame(overall_data)
        df_overall.to_csv(self.report_dir / f"{filename.stem}_overall.csv", index=False)
        
        self.logger.info(f"Exported trend analysis data to CSV at {self.report_dir}")
        return filename
