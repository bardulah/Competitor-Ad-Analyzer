"""Google Ads Transparency Center scraper."""

import logging
import time
from typing import List, Dict, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from .base_scraper import BaseScraper, AdData
from config import GOOGLE_ADS_TRANSPARENCY_URL

logger = logging.getLogger(__name__)


class GoogleAdScraper(BaseScraper):
    """Scraper for Google Ads Transparency Center."""

    def get_platform_name(self) -> str:
        return "google"

    def scrape(self, query: str, limit: int = 50, region: str = "US", **kwargs) -> List[AdData]:
        """Scrape ads from Google Ads Transparency Center.

        Args:
            query: Search query (advertiser name)
            limit: Maximum number of ads to scrape
            region: Region code (default: US)
            **kwargs: Additional parameters

        Returns:
            List of scraped ad data
        """
        logger.info(f"Starting Google Ads Transparency scrape for query: '{query}'")

        page = self.create_page()

        try:
            # Navigate to Google Ads Transparency Center
            logger.info(f"Navigating to: {GOOGLE_ADS_TRANSPARENCY_URL}")

            page.goto(GOOGLE_ADS_TRANSPARENCY_URL, wait_until="networkidle", timeout=60000)
            time.sleep(2)

            # Search for advertiser
            self._perform_search(page, query)

            # Click on advertiser if results found
            self._select_advertiser(page)

            # Scroll to load more ads
            self._scroll_to_load_ads(page, limit)

            # Extract ad data
            ads = self._extract_ads_from_page(page, limit)

            logger.info(f"Successfully scraped {len(ads)} ads from Google")
            self.scraped_ads.extend(ads)

            return ads

        except Exception as e:
            logger.error(f"Error scraping Google ads: {e}")
            raise
        finally:
            page.close()

    def _perform_search(self, page: Page, query: str):
        """Perform search for advertiser.

        Args:
            page: Playwright page object
            query: Search query
        """
        try:
            # Look for search input
            search_selectors = [
                'input[type="text"]',
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
                'material-input input'
            ]

            for selector in search_selectors:
                try:
                    search_input = page.locator(selector).first
                    if search_input.is_visible(timeout=5000):
                        logger.info(f"Found search input with selector: {selector}")
                        search_input.fill(query)
                        time.sleep(1)

                        # Try to submit
                        page.keyboard.press('Enter')
                        time.sleep(3)

                        logger.info("Search performed successfully")
                        return
                except:
                    continue

            logger.warning("Could not find search input")

        except Exception as e:
            logger.error(f"Error performing search: {e}")

    def _select_advertiser(self, page: Page):
        """Select the first advertiser from search results.

        Args:
            page: Playwright page object
        """
        try:
            # Wait for search results
            time.sleep(2)

            # Look for advertiser links/cards
            result_selectors = [
                'a[href*="advertiser"]',
                '[role="button"]',
                '.advertiser-card',
                'material-list-item'
            ]

            for selector in result_selectors:
                try:
                    results = page.locator(selector).all()
                    if results:
                        logger.info(f"Found {len(results)} results with selector: {selector}")
                        results[0].click()
                        time.sleep(3)
                        logger.info("Selected advertiser")
                        return
                except:
                    continue

            logger.warning("Could not find advertiser results to click")

        except Exception as e:
            logger.error(f"Error selecting advertiser: {e}")

    def _scroll_to_load_ads(self, page: Page, target_count: int):
        """Scroll page to load more ads.

        Args:
            page: Playwright page object
            target_count: Target number of ads to load
        """
        logger.info("Scrolling to load ads...")

        last_height = page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 15

        while scroll_attempts < max_attempts:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            new_height = page.evaluate("document.body.scrollHeight")

            # Count loaded ads
            ad_count = page.locator('[class*="creative"], [class*="ad-creative"]').count()
            logger.info(f"Loaded {ad_count} ads so far...")

            if ad_count >= target_count or new_height == last_height:
                break

            last_height = new_height
            scroll_attempts += 1
            self.rate_limit_delay()

    def _extract_ads_from_page(self, page: Page, limit: int) -> List[AdData]:
        """Extract ad data from the page.

        Args:
            page: Playwright page object
            limit: Maximum number of ads to extract

        Returns:
            List of AdData objects
        """
        ads = []

        try:
            # Google's structure varies, try multiple selectors
            ad_selectors = [
                '[class*="creative"]',
                '[class*="ad-creative"]',
                '[role="listitem"]',
                'material-card'
            ]

            ad_cards = []
            for selector in ad_selectors:
                try:
                    cards = page.locator(selector).all()
                    if cards:
                        ad_cards = cards
                        logger.info(f"Found {len(cards)} ad cards with selector: {selector}")
                        break
                except:
                    continue

            if not ad_cards:
                logger.warning("No ad cards found")
                return ads

            for idx, card in enumerate(ad_cards[:limit]):
                if idx >= limit:
                    break

                try:
                    ad_data = self._extract_single_ad(page, card, idx)
                    if ad_data:
                        ads.append(ad_data)
                        logger.info(f"Extracted ad {idx + 1}/{min(limit, len(ad_cards))}")

                    self.rate_limit_delay()

                except Exception as e:
                    logger.warning(f"Error extracting ad {idx}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting ads: {e}")

        return ads

    def _extract_single_ad(self, page: Page, card, idx: int) -> AdData:
        """Extract data from a single ad card.

        Args:
            page: Playwright page object
            card: Ad card element
            idx: Index of the ad

        Returns:
            AdData object or None
        """
        try:
            # Extract ad text
            body_text = self._safe_text_content(
                card,
                '[class*="text"], [class*="description"], p, span'
            )

            # Extract headline
            headline = self._safe_text_content(
                card,
                'h1, h2, h3, [class*="headline"], [class*="title"]'
            )

            # Extract image URL
            image_url = None
            try:
                img = card.locator('img').first
                if img:
                    image_url = img.get_attribute('src')
            except:
                pass

            # Extract date/timing information
            date_text = self._safe_text_content(
                card,
                '[class*="date"], [class*="time"], time'
            )

            # Generate unique ID
            ad_id = f"google_{int(time.time())}_{idx}"

            # Take screenshot
            screenshot_path = None
            try:
                screenshot_path = self.save_screenshot(page, ad_id)
            except Exception as e:
                logger.warning(f"Failed to capture screenshot for ad {ad_id}: {e}")

            # Create AdData object
            ad_data = AdData(
                id=ad_id,
                platform="google",
                headline=headline,
                body_text=body_text,
                image_url=image_url,
                page_url=page.url,
                screenshot_path=screenshot_path,
                metadata={
                    'date_text': date_text,
                    'card_index': idx
                }
            )

            return ad_data

        except Exception as e:
            logger.error(f"Error extracting single ad: {e}")
            return None

    def _safe_text_content(self, element, selector: str) -> str:
        """Safely extract text content from an element.

        Args:
            element: Parent element
            selector: CSS selector

        Returns:
            Text content or empty string
        """
        try:
            target = element.locator(selector).first
            if target:
                text = target.text_content()
                return text.strip() if text else ""
        except:
            pass
        return ""
