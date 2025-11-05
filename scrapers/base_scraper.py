"""Base scraper class with common functionality."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser
import logging

from config import SCREENSHOTS_DIR, DATA_DIR, BROWSER_CONFIG, RATE_LIMIT_DELAY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdData:
    """Represents scraped advertisement data."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.platform = kwargs.get('platform')
        self.advertiser = kwargs.get('advertiser')
        self.headline = kwargs.get('headline')
        self.body_text = kwargs.get('body_text')
        self.cta = kwargs.get('cta')
        self.image_url = kwargs.get('image_url')
        self.video_url = kwargs.get('video_url')
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')
        self.impressions = kwargs.get('impressions')
        self.spend_estimate = kwargs.get('spend_estimate')
        self.targeting = kwargs.get('targeting', {})
        self.page_url = kwargs.get('page_url')
        self.screenshot_path = kwargs.get('screenshot_path')
        self.scraped_at = datetime.now().isoformat()
        self.metadata = kwargs.get('metadata', {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert ad data to dictionary."""
        return {
            'id': self.id,
            'platform': self.platform,
            'advertiser': self.advertiser,
            'headline': self.headline,
            'body_text': self.body_text,
            'cta': self.cta,
            'image_url': self.image_url,
            'video_url': self.video_url,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'impressions': self.impressions,
            'spend_estimate': self.spend_estimate,
            'targeting': self.targeting,
            'page_url': self.page_url,
            'screenshot_path': self.screenshot_path,
            'scraped_at': self.scraped_at,
            'metadata': self.metadata
        }


class BaseScraper(ABC):
    """Base class for ad scrapers."""

    def __init__(self, headless: bool = True):
        """Initialize the scraper.

        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.scraped_ads: List[AdData] = []

    def __enter__(self):
        """Context manager entry."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_browser()

    def start_browser(self):
        """Start the Playwright browser."""
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        logger.info("Browser started successfully")

    def close_browser(self):
        """Close the browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")

    def create_page(self) -> Page:
        """Create a new browser page with anti-detection measures."""
        context = self.browser.new_context(
            viewport=BROWSER_CONFIG['viewport'],
            user_agent=BROWSER_CONFIG['user_agent']
        )
        page = context.new_page()

        # Add stealth measures
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        return page

    def save_screenshot(self, page: Page, ad_id: str) -> str:
        """Take a screenshot of the ad.

        Args:
            page: Playwright page object
            ad_id: Unique identifier for the ad

        Returns:
            Path to saved screenshot
        """
        screenshot_path = SCREENSHOTS_DIR / f"{self.get_platform_name()}_{ad_id}_{int(time.time())}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"Screenshot saved: {screenshot_path}")
        return str(screenshot_path)

    def save_ads_to_file(self, filename: Optional[str] = None) -> str:
        """Save scraped ads to JSON file.

        Args:
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.get_platform_name()}_ads_{timestamp}.json"

        filepath = DATA_DIR / filename

        ads_data = [ad.to_dict() for ad in self.scraped_ads]

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'platform': self.get_platform_name(),
                'total_ads': len(ads_data),
                'scraped_at': datetime.now().isoformat(),
                'ads': ads_data
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(ads_data)} ads to {filepath}")
        return str(filepath)

    def rate_limit_delay(self):
        """Apply rate limiting delay."""
        time.sleep(RATE_LIMIT_DELAY)

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name."""
        pass

    @abstractmethod
    def scrape(self, query: str, limit: int = 50, **kwargs) -> List[AdData]:
        """Scrape ads from the platform.

        Args:
            query: Search query
            limit: Maximum number of ads to scrape
            **kwargs: Additional platform-specific parameters

        Returns:
            List of scraped ad data
        """
        pass
