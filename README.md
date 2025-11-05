# Competitor Ad Analyzer

An automated tool that scrapes competitor advertisements from ad libraries, extracts messaging, visuals, and engagement patterns, then provides actionable insights on how to adapt successful elements for your own campaigns.

## Features

- **Multi-Platform Scraping**: Scrapes ads from Facebook Ad Library and Google Ads Transparency Center
- **Automated Screenshot Capture**: Uses Playwright for reliable screenshot capture
- **AI-Powered Analysis**: Leverages Claude AI to analyze visual elements, messaging, and patterns
- **Engagement Pattern Detection**: Identifies successful ad characteristics and patterns
- **Campaign Recommendations**: Provides specific suggestions for adapting winning elements
- **Export Reports**: Generates comprehensive JSON and HTML reports

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Competitor-Ad-Analyzer
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

4. Configure your environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file with the following:

```
ANTHROPIC_API_KEY=your_claude_api_key_here
```

## Usage

### Basic Ad Scraping

```bash
# Scrape ads from Facebook Ad Library
python main.py scrape --platform facebook --query "Nike shoes" --limit 20

# Scrape ads from Google Ads Transparency
python main.py scrape --platform google --advertiser "Nike" --limit 20

# Scrape from multiple platforms
python main.py scrape --query "fitness app" --limit 50
```

### Analyze Scraped Ads

```bash
# Analyze all scraped ads
python main.py analyze --output-dir ./reports

# Analyze specific campaign
python main.py analyze --campaign-id abc123
```

### Generate Campaign Recommendations

```bash
# Get recommendations based on top-performing ads
python main.py recommend --top-n 10 --output ./recommendations.json
```

### Full Pipeline

```bash
# Scrape, analyze, and generate recommendations in one command
python main.py pipeline --query "eco-friendly products" --limit 30
```

## Project Structure

```
Competitor-Ad-Analyzer/
├── main.py                      # CLI entry point
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py         # Base scraper class
│   ├── facebook_scraper.py     # Facebook Ad Library scraper
│   └── google_scraper.py       # Google Ads scraper
├── analyzers/
│   ├── __init__.py
│   ├── visual_analyzer.py      # AI-powered visual analysis
│   ├── messaging_analyzer.py   # Text and messaging analysis
│   └── pattern_detector.py     # Engagement pattern detection
├── recommender/
│   ├── __init__.py
│   └── campaign_advisor.py     # Recommendation engine
├── utils/
│   ├── __init__.py
│   ├── screenshot.py           # Screenshot automation
│   └── storage.py              # Data persistence
└── data/                        # Scraped data and screenshots
    ├── ads/                    # Ad metadata
    └── screenshots/            # Ad screenshots
```

## Output Format

The tool generates comprehensive reports including:

- **Ad Metadata**: Platform, advertiser, date ranges, engagement metrics
- **Visual Analysis**: Colors, layout, imagery description, design patterns
- **Messaging Analysis**: Headlines, CTAs, emotional triggers, value propositions
- **Success Patterns**: Common elements in high-performing ads
- **Recommendations**: Specific suggestions for your campaigns

## Example Report

```json
{
  "analysis_date": "2025-11-05",
  "total_ads_analyzed": 50,
  "top_patterns": [
    {
      "pattern": "User-generated content style",
      "frequency": 15,
      "avg_engagement": "high"
    }
  ],
  "recommendations": [
    {
      "category": "visual",
      "suggestion": "Use authentic customer photos instead of stock imagery",
      "confidence": 0.85
    }
  ]
}
```

## Legal and Ethical Considerations

- This tool is for competitive research and educational purposes only
- Respect platform Terms of Service and rate limits
- Do not copy ads directly - use insights to inspire original creative
- Ensure compliance with advertising regulations in your jurisdiction
- Some ad libraries have usage restrictions - review before commercial use

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

## License

MIT License - See LICENSE file for details
