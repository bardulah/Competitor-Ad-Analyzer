#!/usr/bin/env python3
"""Example usage of the Competitor Ad Analyzer programmatically."""

import sys
sys.path.append('..')

from scrapers import FacebookAdScraper, GoogleAdScraper
from analyzers import VisualAnalyzer, MessagingAnalyzer, PatternDetector
from recommender import CampaignAdvisor
from utils import DataStorage


def example_scrape_and_analyze():
    """Example: Scrape ads and perform full analysis."""

    # Initialize storage
    storage = DataStorage()

    # Step 1: Scrape Facebook ads
    print("Step 1: Scraping Facebook ads...")
    with FacebookAdScraper(headless=True) as scraper:
        ads = scraper.scrape(query="Nike shoes", limit=10, country="US")
        print(f"Scraped {len(ads)} ads")

        # Save data
        filepath = scraper.save_ads_to_file()
        print(f"Saved to: {filepath}")

    # Step 2: Analyze visuals
    print("\nStep 2: Analyzing visuals...")
    visual_analyzer = VisualAnalyzer()

    ads_with_screenshots = [ad for ad in ads if ad.screenshot_path]
    visual_analyses = []

    for ad in ads_with_screenshots[:3]:  # Analyze first 3
        print(f"Analyzing {ad.id}...")
        analysis = visual_analyzer.analyze_image(ad.screenshot_path)
        visual_analyses.append(analysis)

    # Step 3: Analyze messaging
    print("\nStep 3: Analyzing messaging...")
    messaging_analyzer = MessagingAnalyzer()

    messaging_analyses = []
    for ad in ads:
        analysis = messaging_analyzer.analyze_ad_copy(ad.to_dict())
        messaging_analyses.append(analysis)

    # Get messaging patterns
    patterns = messaging_analyzer.analyze_multiple_ads([ad.to_dict() for ad in ads])
    print(f"Found patterns in {len(ads)} ads")

    # Step 4: Detect overall patterns
    print("\nStep 4: Detecting patterns...")
    pattern_detector = PatternDetector()

    all_patterns = pattern_detector.detect_patterns(
        [ad.to_dict() for ad in ads],
        visual_analyses=visual_analyses,
        messaging_analyses=messaging_analyses
    )

    print(f"Pattern summary: {all_patterns.get('summary', {})}")

    # Step 5: Generate recommendations
    print("\nStep 5: Generating recommendations...")
    advisor = CampaignAdvisor()

    recommendations = advisor.generate_recommendations(
        ads_data=[ad.to_dict() for ad in ads],
        patterns=all_patterns,
        visual_analyses=visual_analyses,
        messaging_analyses=messaging_analyses,
        campaign_goal="increase conversions"
    )

    # Save recommendations
    rec_path = storage.save_recommendations(recommendations)
    print(f"Recommendations saved to: {rec_path}")

    # Display some recommendations
    print("\n=== Visual Recommendations ===")
    for rec in recommendations.get('visual_recommendations', [])[:3]:
        print(f"\n- {rec.get('recommendation', 'N/A')}")
        print(f"  Priority: {rec.get('priority', 'N/A')}")

    print("\n=== Messaging Recommendations ===")
    for rec in recommendations.get('messaging_recommendations', [])[:3]:
        print(f"\n- {rec.get('strategy', 'N/A')}")
        print(f"  Priority: {rec.get('priority', 'N/A')}")


def example_compare_ads():
    """Example: Compare multiple ad visuals."""

    visual_analyzer = VisualAnalyzer()

    # Assume we have some screenshot paths
    screenshot_paths = [
        './data/screenshots/ad1.png',
        './data/screenshots/ad2.png',
        './data/screenshots/ad3.png'
    ]

    print("Comparing multiple ads...")
    comparison = visual_analyzer.compare_ads(screenshot_paths)

    print(f"\nComparison Analysis:")
    print(comparison.get('analysis', 'No analysis available'))


def example_messaging_themes():
    """Example: Identify messaging themes across ads."""

    messaging_analyzer = MessagingAnalyzer()

    # Sample ad data
    ads = [
        {
            'id': '1',
            'headline': 'Save 50% on Premium Running Shoes',
            'body_text': 'Get the best deals on Nike running shoes. Limited time offer!',
            'cta': 'Shop Now'
        },
        {
            'id': '2',
            'headline': 'Free Shipping on All Orders',
            'body_text': 'Discover our latest collection of athletic footwear.',
            'cta': 'Browse Collection'
        },
        {
            'id': '3',
            'headline': 'New Arrivals - Spring Collection',
            'body_text': 'Be the first to own our exclusive spring designs.',
            'cta': 'Shop New Arrivals'
        }
    ]

    print("Analyzing messaging patterns...")
    patterns = messaging_analyzer.analyze_multiple_ads(ads)

    print(f"\nMost common power words: {patterns.get('most_common_power_words', [])}")
    print(f"CTA patterns: {patterns.get('cta_patterns', {})}")
    print(f"Messaging themes: {patterns.get('messaging_themes', [])}")


if __name__ == '__main__':
    print("=== Competitor Ad Analyzer - Example Usage ===\n")

    # Run the main example
    try:
        example_scrape_and_analyze()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have set ANTHROPIC_API_KEY in your .env file")

    # Uncomment to run other examples:
    # example_compare_ads()
    # example_messaging_themes()
