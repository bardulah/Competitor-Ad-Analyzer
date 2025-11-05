"""Data storage and persistence utilities."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import DATA_DIR, REPORTS_DIR

logger = logging.getLogger(__name__)


class DataStorage:
    """Handles data persistence and retrieval."""

    def __init__(self):
        """Initialize data storage."""
        self.data_dir = DATA_DIR
        self.reports_dir = REPORTS_DIR

    def save_scraped_data(self, data: List[Dict[str, Any]], platform: str) -> str:
        """Save scraped ad data.

        Args:
            data: List of ad data dictionaries
            platform: Platform name

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{platform}_ads_{timestamp}.json"
        filepath = self.data_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'platform': platform,
                'total_ads': len(data),
                'scraped_at': datetime.now().isoformat(),
                'ads': data
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(data)} ads to {filepath}")
        return str(filepath)

    def load_scraped_data(self, filepath: str) -> Dict[str, Any]:
        """Load scraped ad data from file.

        Args:
            filepath: Path to data file

        Returns:
            Dictionary containing ad data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Loaded {data.get('total_ads', 0)} ads from {filepath}")
        return data

    def save_analysis_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Save analysis report.

        Args:
            report_data: Report data dictionary
            report_type: Type of report (e.g., 'visual', 'messaging', 'patterns')

        Returns:
            Path to saved report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_report_{timestamp}.json"
        filepath = self.reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {report_type} report to {filepath}")
        return str(filepath)

    def save_recommendations(self, recommendations: Dict[str, Any]) -> str:
        """Save campaign recommendations.

        Args:
            recommendations: Recommendations dictionary

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"recommendations_{timestamp}.json"
        filepath = self.reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved recommendations to {filepath}")
        return str(filepath)

    def list_scraped_files(self, platform: Optional[str] = None) -> List[str]:
        """List all scraped data files.

        Args:
            platform: Optional platform filter

        Returns:
            List of file paths
        """
        pattern = f"{platform}_ads_*.json" if platform else "*_ads_*.json"
        files = list(self.data_dir.glob(pattern))
        return [str(f) for f in sorted(files, reverse=True)]

    def list_reports(self, report_type: Optional[str] = None) -> List[str]:
        """List all analysis reports.

        Args:
            report_type: Optional report type filter

        Returns:
            List of file paths
        """
        pattern = f"{report_type}_report_*.json" if report_type else "*_report_*.json"
        files = list(self.reports_dir.glob(pattern))
        return [str(f) for f in sorted(files, reverse=True)]

    def get_latest_scraped_file(self, platform: Optional[str] = None) -> Optional[str]:
        """Get the most recent scraped data file.

        Args:
            platform: Optional platform filter

        Returns:
            Path to latest file or None
        """
        files = self.list_scraped_files(platform)
        return files[0] if files else None

    def create_html_report(self, report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Create an HTML report from analysis data.

        Args:
            report_data: Report data dictionary
            output_path: Optional custom output path

        Returns:
            Path to HTML report
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = str(self.reports_dir / f"report_{timestamp}.html")

        html_content = self._generate_html_report(report_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Created HTML report: {output_path}")
        return output_path

    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content for report.

        Args:
            report_data: Report data dictionary

        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Competitor Ad Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        h1 {{ margin: 0; }}
        .date {{ opacity: 0.9; margin-top: 10px; }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stat {{
            display: inline-block;
            background: #f0f4ff;
            padding: 15px 25px;
            margin: 10px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-label {{
            font-size: 0.9em;
            color: #666;
            display: block;
        }}
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }}
        .recommendation {{
            background: #f9fafb;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #10b981;
            border-radius: 4px;
        }}
        .priority-high {{ border-left-color: #ef4444; }}
        .priority-medium {{ border-left-color: #f59e0b; }}
        .priority-low {{ border-left-color: #10b981; }}
        pre {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Competitor Ad Analysis Report</h1>
        <div class="date">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div>
            <div class="stat">
                <span class="stat-label">Total Ads Analyzed</span>
                <span class="stat-value">{report_data.get('total_ads', 0)}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Platforms</span>
                <span class="stat-value">{report_data.get('platforms', 'N/A')}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Patterns Detected</span>
                <span class="stat-value">{report_data.get('patterns_count', 'N/A')}</span>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Key Findings</h2>
        <pre>{json.dumps(report_data.get('findings', {}), indent=2)}</pre>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        {self._format_recommendations_html(report_data.get('recommendations', []))}
    </div>

    <div class="section">
        <h2>Full Analysis</h2>
        <pre>{json.dumps(report_data, indent=2)}</pre>
    </div>
</body>
</html>
"""
        return html

    def _format_recommendations_html(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations as HTML.

        Args:
            recommendations: List of recommendations

        Returns:
            HTML string
        """
        if not recommendations:
            return "<p>No recommendations available.</p>"

        html_parts = []
        for rec in recommendations:
            priority = rec.get('priority', 'medium')
            html_parts.append(f"""
            <div class="recommendation priority-{priority}">
                <strong>{rec.get('title', rec.get('recommendation', 'N/A'))}</strong>
                <p>{rec.get('description', rec.get('rationale', 'N/A'))}</p>
            </div>
            """)

        return '\n'.join(html_parts)
