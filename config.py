"""Configuration management for the Competitor Ad Analyzer."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv('DATA_DIR', BASE_DIR / 'data'))
SCREENSHOTS_DIR = Path(os.getenv('SCREENSHOTS_DIR', DATA_DIR / 'screenshots'))
REPORTS_DIR = Path(os.getenv('REPORTS_DIR', BASE_DIR / 'reports'))

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# API Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Scraping Configuration
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 3))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
RATE_LIMIT_DELAY = int(os.getenv('RATE_LIMIT_DELAY', 2))

# Analysis Configuration
MIN_AD_QUALITY_SCORE = float(os.getenv('MIN_AD_QUALITY_SCORE', 0.5))
ENABLE_VISUAL_ANALYSIS = os.getenv('ENABLE_VISUAL_ANALYSIS', 'true').lower() == 'true'
ENABLE_PATTERN_DETECTION = os.getenv('ENABLE_PATTERN_DETECTION', 'true').lower() == 'true'

# Ad Library URLs
FACEBOOK_AD_LIBRARY_URL = 'https://www.facebook.com/ads/library/'
GOOGLE_ADS_TRANSPARENCY_URL = 'https://adstransparency.google.com/'

# Browser settings for Playwright
BROWSER_CONFIG = {
    'headless': True,
    'viewport': {'width': 1920, 'height': 1080},
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
