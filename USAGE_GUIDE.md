# Competitor Ad Analyzer - Usage Guide

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd Competitor-Ad-Analyzer

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

Get your API key from: https://console.anthropic.com/

### 3. Basic Usage

#### Scrape Competitor Ads

```bash
# Scrape ads from Facebook Ad Library
python main.py scrape --platform facebook --query "Nike" --limit 20

# Scrape from all platforms
python main.py scrape --query "eco-friendly products" --limit 50

# See the browser while scraping (useful for debugging)
python main.py scrape --query "Nike" --no-headless
```

#### Analyze Scraped Ads

```bash
# Analyze the most recently scraped data
python main.py analyze

# Analyze a specific file
python main.py analyze --input-file ./data/facebook_ads_20250105_120000.json

# Skip visual analysis (faster)
python main.py analyze --no-visuals
```

#### Generate Recommendations

```bash
# Generate recommendations from latest analysis
python main.py recommend

# Specify a campaign goal
python main.py recommend --goal "increase conversions"
python main.py recommend --goal "brand awareness"
```

#### Run Full Pipeline

```bash
# Scrape, analyze, and get recommendations in one command
python main.py pipeline --query "fitness apps" --limit 30 --goal "increase app downloads"
```

#### List Data

```bash
# See all scraped data and reports
python main.py list-data
```

## Advanced Usage

### Programmatic Usage

You can use the tool as a Python library:

```python
from scrapers import FacebookAdScraper
from analyzers import VisualAnalyzer, MessagingAnalyzer
from recommender import CampaignAdvisor

# Scrape ads
with FacebookAdScraper() as scraper:
    ads = scraper.scrape(query="Nike", limit=10)

# Analyze visuals
analyzer = VisualAnalyzer()
for ad in ads:
    if ad.screenshot_path:
        analysis = analyzer.analyze_image(ad.screenshot_path)
        print(analysis)

# Get recommendations
advisor = CampaignAdvisor()
recommendations = advisor.generate_recommendations(
    ads_data=[ad.to_dict() for ad in ads],
    campaign_goal="increase conversions"
)
```

See `examples/example_usage.py` for more examples.

### Custom Analysis

#### Compare Specific Ads

```python
from analyzers import VisualAnalyzer

analyzer = VisualAnalyzer()
comparison = analyzer.compare_ads([
    './data/screenshots/ad1.png',
    './data/screenshots/ad2.png',
    './data/screenshots/ad3.png'
])
print(comparison['analysis'])
```

#### Detect Patterns

```python
from analyzers import PatternDetector

detector = PatternDetector()
patterns = detector.detect_patterns(
    ads_data=ads,
    visual_analyses=visual_results,
    messaging_analyses=messaging_results
)

# Export patterns
detector.export_patterns(patterns, './my_patterns.json')
```

## Common Use Cases

### 1. Competitor Research

```bash
# Research a specific competitor
python main.py pipeline --query "CompetitorName" --limit 50

# Research multiple competitors
python main.py scrape --query "Competitor1" --limit 30
python main.py scrape --query "Competitor2" --limit 30
python main.py scrape --query "Competitor3" --limit 30
python main.py analyze
python main.py recommend --goal "competitive differentiation"
```

### 2. Campaign Planning

```bash
# Research successful ads in your industry
python main.py scrape --query "sustainable fashion" --limit 50
python main.py analyze
python main.py recommend --goal "launch new product line"
```

### 3. A/B Testing Insights

```bash
# Analyze messaging patterns
python main.py scrape --query "fitness supplements" --limit 100
python main.py analyze --no-visuals  # Focus on messaging
python main.py recommend --goal "improve ad copy performance"
```

### 4. Visual Design Research

```bash
# Focus on visual analysis
python main.py scrape --query "mobile apps" --limit 30
python main.py analyze --no-messaging  # Focus on visuals
```

## Output Files

### Data Files

- **Scraped data**: `./data/[platform]_ads_[timestamp].json`
- **Screenshots**: `./data/screenshots/[platform]_[id]_[timestamp].png`

### Reports

- **Analysis reports**: `./reports/comprehensive_report_[timestamp].json`
- **HTML reports**: `./reports/report_[timestamp].html`
- **Recommendations**: `./reports/recommendations_[timestamp].json`

### Report Structure

JSON reports include:

```json
{
  "total_ads": 50,
  "platform": "facebook",
  "visual_analyses": [...],
  "messaging_analyses": [...],
  "patterns": {
    "metadata_patterns": {...},
    "visual_patterns": {...},
    "messaging_patterns": {...}
  }
}
```

## Tips & Best Practices

### 1. Rate Limiting

- Start with smaller limits (10-20 ads) to test
- Use `--no-headless` to see what's happening
- If you encounter issues, increase `RATE_LIMIT_DELAY` in `.env`

### 2. API Costs

- Visual analysis uses Claude's vision API (costs per image)
- Start with a few ads to estimate costs
- Use `--no-visuals` to skip visual analysis if needed

### 3. Data Quality

- Provide specific advertiser names for better results
- Facebook Ad Library has the most complete data
- Google Ads Transparency can be limited for some advertisers

### 4. Analysis Depth

- Visual analysis is most valuable for 5-10 representative ads
- Messaging analysis can handle 50+ ads efficiently
- Pattern detection improves with more data

### 5. Recommendations

- Provide specific campaign goals for better recommendations
- Review multiple competitors for broader insights
- Export recommendations as JSON for team sharing

## Troubleshooting

### "No ads found"

- Try a different query (advertiser name vs. keyword)
- Check if the advertiser has active ads on that platform
- Try different country codes for Facebook

### "API key not found"

- Make sure `.env` file exists in project root
- Verify `ANTHROPIC_API_KEY` is set correctly
- Restart your terminal after setting environment variables

### Browser/Scraping Issues

- Run with `--no-headless` to see browser behavior
- Check your internet connection
- Some advertisers may not have public ad data
- Ad library structure may change (scrapers may need updates)

### Performance Issues

- Reduce the number of ads to scrape
- Skip visual analysis for faster processing
- Close other applications to free up memory

## Support

For issues or questions:
- Check the troubleshooting guide above
- Review example usage in `examples/`
- Open an issue on GitHub with details about your problem

## Legal Notes

- This tool is for research and educational purposes
- Respect platform Terms of Service and rate limits
- Do not copy ads directly - use insights for inspiration
- Review advertising regulations in your jurisdiction
- Some ad libraries have commercial use restrictions
