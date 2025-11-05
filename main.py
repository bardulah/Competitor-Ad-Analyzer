#!/usr/bin/env python3
"""Main CLI interface for the Competitor Ad Analyzer."""

import click
import logging
import sys
from pathlib import Path
from typing import Optional

from scrapers import FacebookAdScraper, GoogleAdScraper
from analyzers import VisualAnalyzer, MessagingAnalyzer, PatternDetector
from recommender import CampaignAdvisor
from utils import DataStorage
from config import ANTHROPIC_API_KEY

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Competitor Ad Analyzer - Scrape, analyze, and get insights from competitor ads."""
    # Check for API key
    if not ANTHROPIC_API_KEY:
        click.echo(click.style(
            "Warning: ANTHROPIC_API_KEY not found. Analysis features will not work.",
            fg='yellow'
        ))


@cli.command()
@click.option('--platform', type=click.Choice(['facebook', 'google', 'all']), default='all',
              help='Platform to scrape ads from')
@click.option('--query', required=True, help='Search query (advertiser name or keyword)')
@click.option('--limit', default=50, help='Maximum number of ads to scrape')
@click.option('--country', default='US', help='Country code for Facebook (default: US)')
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
def scrape(platform: str, query: str, limit: int, country: str, headless: bool):
    """Scrape ads from ad libraries."""
    click.echo(click.style(f"\n🔍 Starting ad scraping for: {query}", fg='blue', bold=True))

    storage = DataStorage()
    scraped_files = []

    try:
        # Facebook scraping
        if platform in ['facebook', 'all']:
            click.echo("\n📱 Scraping Facebook Ad Library...")
            with FacebookAdScraper(headless=headless) as scraper:
                ads = scraper.scrape(query=query, limit=limit, country=country)
                if ads:
                    filepath = scraper.save_ads_to_file()
                    scraped_files.append(filepath)
                    click.echo(click.style(
                        f"✓ Scraped {len(ads)} ads from Facebook",
                        fg='green'
                    ))

        # Google scraping
        if platform in ['google', 'all']:
            click.echo("\n🌐 Scraping Google Ads Transparency Center...")
            with GoogleAdScraper(headless=headless) as scraper:
                ads = scraper.scrape(query=query, limit=limit)
                if ads:
                    filepath = scraper.save_ads_to_file()
                    scraped_files.append(filepath)
                    click.echo(click.style(
                        f"✓ Scraped {len(ads)} ads from Google",
                        fg='green'
                    ))

        # Summary
        click.echo(click.style(f"\n✅ Scraping complete!", fg='green', bold=True))
        click.echo(f"Saved data to:")
        for filepath in scraped_files:
            click.echo(f"  - {filepath}")

    except Exception as e:
        click.echo(click.style(f"\n❌ Error during scraping: {str(e)}", fg='red'))
        logger.exception("Scraping error")
        sys.exit(1)


@cli.command()
@click.option('--input-file', help='Path to scraped data file (latest if not specified)')
@click.option('--analyze-visuals/--no-visuals', default=True, help='Perform visual analysis')
@click.option('--analyze-messaging/--no-messaging', default=True, help='Perform messaging analysis')
@click.option('--detect-patterns/--no-patterns', default=True, help='Detect patterns')
@click.option('--output', help='Output file path')
def analyze(input_file: Optional[str], analyze_visuals: bool, analyze_messaging: bool,
            detect_patterns: bool, output: Optional[str]):
    """Analyze scraped ads."""
    click.echo(click.style("\n🔬 Starting ad analysis...", fg='blue', bold=True))

    storage = DataStorage()

    try:
        # Load data
        if not input_file:
            input_file = storage.get_latest_scraped_file()
            if not input_file:
                click.echo(click.style("❌ No scraped data found. Run 'scrape' first.", fg='red'))
                sys.exit(1)

        click.echo(f"Loading data from: {input_file}")
        data = storage.load_scraped_data(input_file)
        ads = data.get('ads', [])

        if not ads:
            click.echo(click.style("❌ No ads found in data file.", fg='red'))
            sys.exit(1)

        results = {
            'total_ads': len(ads),
            'platform': data.get('platform'),
            'analyzed_at': storage.get_latest_scraped_file()
        }

        # Visual analysis
        if analyze_visuals:
            click.echo("\n👁️  Analyzing visual elements...")
            visual_analyzer = VisualAnalyzer()

            # Get ads with screenshots
            ads_with_screenshots = [ad for ad in ads if ad.get('screenshot_path')]
            click.echo(f"Found {len(ads_with_screenshots)} ads with screenshots")

            if ads_with_screenshots:
                # Analyze first few ads (can be expensive)
                sample_size = min(5, len(ads_with_screenshots))
                visual_analyses = []

                with click.progressbar(ads_with_screenshots[:sample_size],
                                      label='Analyzing visuals') as bar:
                    for ad in bar:
                        analysis = visual_analyzer.analyze_image(ad['screenshot_path'])
                        visual_analyses.append(analysis)

                results['visual_analyses'] = visual_analyses
                click.echo(click.style(f"✓ Analyzed {len(visual_analyses)} ad visuals", fg='green'))

        # Messaging analysis
        if analyze_messaging:
            click.echo("\n📝 Analyzing messaging and copy...")
            messaging_analyzer = MessagingAnalyzer()

            messaging_analyses = []
            with click.progressbar(ads, label='Analyzing messaging') as bar:
                for ad in bar:
                    analysis = messaging_analyzer.analyze_ad_copy(ad)
                    messaging_analyses.append(analysis)

            # Get patterns
            patterns = messaging_analyzer.analyze_multiple_ads(ads)
            results['messaging_analyses'] = messaging_analyses
            results['messaging_patterns'] = patterns

            click.echo(click.style(f"✓ Analyzed {len(messaging_analyses)} ad messages", fg='green'))

        # Pattern detection
        if detect_patterns:
            click.echo("\n🔍 Detecting patterns...")
            pattern_detector = PatternDetector()

            patterns = pattern_detector.detect_patterns(
                ads,
                visual_analyses=results.get('visual_analyses'),
                messaging_analyses=results.get('messaging_analyses')
            )

            results['patterns'] = patterns
            click.echo(click.style("✓ Pattern detection complete", fg='green'))

        # Save results
        report_path = storage.save_analysis_report(results, 'comprehensive')
        click.echo(click.style(f"\n✅ Analysis complete!", fg='green', bold=True))
        click.echo(f"Report saved to: {report_path}")

        # Create HTML report
        html_path = storage.create_html_report(results)
        click.echo(f"HTML report: {html_path}")

    except Exception as e:
        click.echo(click.style(f"\n❌ Error during analysis: {str(e)}", fg='red'))
        logger.exception("Analysis error")
        sys.exit(1)


@cli.command()
@click.option('--input-file', help='Path to analysis report (latest if not specified)')
@click.option('--goal', help='Campaign goal (e.g., "increase conversions", "brand awareness")')
@click.option('--output', help='Output file path')
def recommend(input_file: Optional[str], goal: Optional[str], output: Optional[str]):
    """Generate campaign recommendations."""
    click.echo(click.style("\n💡 Generating recommendations...", fg='blue', bold=True))

    storage = DataStorage()

    try:
        # Load analysis data
        if not input_file:
            reports = storage.list_reports('comprehensive')
            if not reports:
                click.echo(click.style("❌ No analysis reports found. Run 'analyze' first.", fg='red'))
                sys.exit(1)
            input_file = reports[0]

        click.echo(f"Loading analysis from: {input_file}")
        with open(input_file, 'r') as f:
            import json
            analysis_data = json.load(f)

        # Generate recommendations
        advisor = CampaignAdvisor()

        # Load original ads data
        scraped_file = storage.get_latest_scraped_file()
        if scraped_file:
            scraped_data = storage.load_scraped_data(scraped_file)
            ads = scraped_data.get('ads', [])
        else:
            ads = []

        recommendations = advisor.generate_recommendations(
            ads_data=ads,
            patterns=analysis_data.get('patterns'),
            visual_analyses=analysis_data.get('visual_analyses'),
            messaging_analyses=analysis_data.get('messaging_analyses'),
            campaign_goal=goal
        )

        # Save recommendations
        rec_path = storage.save_recommendations(recommendations)

        click.echo(click.style(f"\n✅ Recommendations generated!", fg='green', bold=True))
        click.echo(f"Saved to: {rec_path}")

        # Display summary
        click.echo(click.style("\n📋 Summary:", fg='blue'))
        click.echo(f"Visual recommendations: {len(recommendations.get('visual_recommendations', []))}")
        click.echo(f"Messaging recommendations: {len(recommendations.get('messaging_recommendations', []))}")
        click.echo(f"Tactical actions: {len(recommendations.get('tactical_actions', []))}")

    except Exception as e:
        click.echo(click.style(f"\n❌ Error generating recommendations: {str(e)}", fg='red'))
        logger.exception("Recommendation error")
        sys.exit(1)


@cli.command()
@click.option('--query', required=True, help='Search query (advertiser name or keyword)')
@click.option('--limit', default=30, help='Maximum number of ads to scrape')
@click.option('--goal', help='Campaign goal')
@click.option('--platform', type=click.Choice(['facebook', 'google', 'all']), default='all')
def pipeline(query: str, limit: int, goal: Optional[str], platform: str):
    """Run the full pipeline: scrape, analyze, and generate recommendations."""
    click.echo(click.style("\n🚀 Running full analysis pipeline...", fg='blue', bold=True))

    # Step 1: Scrape
    click.echo(click.style("\n[1/3] Scraping ads...", fg='cyan'))
    ctx = click.get_current_context()
    ctx.invoke(scrape, platform=platform, query=query, limit=limit, country='US', headless=True)

    # Step 2: Analyze
    click.echo(click.style("\n[2/3] Analyzing ads...", fg='cyan'))
    ctx.invoke(analyze, input_file=None, analyze_visuals=True,
               analyze_messaging=True, detect_patterns=True, output=None)

    # Step 3: Recommend
    click.echo(click.style("\n[3/3] Generating recommendations...", fg='cyan'))
    ctx.invoke(recommend, input_file=None, goal=goal, output=None)

    click.echo(click.style("\n✅ Pipeline complete!", fg='green', bold=True))


@cli.command()
def list_data():
    """List all scraped data and reports."""
    storage = DataStorage()

    click.echo(click.style("\n📦 Scraped Data Files:", fg='blue', bold=True))
    scraped_files = storage.list_scraped_files()
    if scraped_files:
        for f in scraped_files[:10]:  # Show latest 10
            click.echo(f"  - {f}")
    else:
        click.echo("  No data files found")

    click.echo(click.style("\n📊 Analysis Reports:", fg='blue', bold=True))
    reports = storage.list_reports()
    if reports:
        for f in reports[:10]:  # Show latest 10
            click.echo(f"  - {f}")
    else:
        click.echo("  No reports found")


if __name__ == '__main__':
    cli()
