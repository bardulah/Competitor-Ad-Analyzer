"""Facebook Ad Library scraper."""

import logging
import time
from typing import List, Dict, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from .base_scraper import BaseScraper, AdData
from config import FACEBOOK_AD_LIBRARY_URL

logger = logging.getLogger(__name__)


class FacebookAdScraper(BaseScraper):
    """Scraper for Facebook Ad Library."""

    def get_platform_name(self) -> str:
        return "facebook"

    def scrape(self, query: str, limit: int = 50, country: str = "US", **kwargs) -> List[AdData]:
        """Scrape ads from Facebook Ad Library.

        Args:
            query: Search query (advertiser name or keyword)
            limit: Maximum number of ads to scrape
            country: Country code (default: US)
            **kwargs: Additional parameters

        Returns:
            List of scraped ad data
        """
        logger.info(f"Starting Facebook Ad Library scrape for query: '{query}'")

        page = self.create_page()

        try:
            # Navigate to Facebook Ad Library
            url = f"{FACEBOOK_AD_LIBRARY_URL}?active_status=all&ad_type=all&country={country}&q={query}"
            logger.info(f"Navigating to: {url}")

            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(3)  # Wait for dynamic content

            # Handle any consent dialogs
            self._handle_consent_dialog(page)

            # Scroll to load more ads
            self._scroll_to_load_ads(page, limit)

            # Extract ad data
            ads = self._extract_ads_from_page(page, limit)

            logger.info(f"Successfully scraped {len(ads)} ads from Facebook")
            self.scraped_ads.extend(ads)

            return ads

        except Exception as e:
            logger.error(f"Error scraping Facebook ads: {e}")
            raise
        finally:
            page.close()

    def _handle_consent_dialog(self, page: Page):
        """Handle cookie/consent dialogs."""
        try:
            # Try to find and click common consent buttons
            consent_selectors = [
                'button[data-cookiebanner="accept_button"]',
                'button:has-text("Accept")',
                'button:has-text("Allow")',
            ]

            for selector in consent_selectors:
                try:
                    page.click(selector, timeout=3000)
                    logger.info("Accepted consent dialog")
                    time.sleep(1)
                    break
                except:
                    continue
        except Exception as e:
            logger.debug(f"No consent dialog found or error handling it: {e}")

    def _scroll_to_load_ads(self, page: Page, target_count: int):
        """Scroll page to load more ads dynamically.

        Args:
            page: Playwright page object
            target_count: Target number of ads to load
        """
        logger.info("Scrolling to load ads...")

        last_height = page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 20

        while scroll_attempts < max_attempts:
            # Scroll down
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # Calculate new scroll height
            new_height = page.evaluate("document.body.scrollHeight")

            # Check if we've loaded enough ads
            ad_count = page.locator('[data-testid="ad-card"]').count()
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
            # Wait for ads to load
            page.wait_for_selector('[data-testid="ad-card"], [role="article"]', timeout=10000)

            # Facebook Ad Library structure varies, so we use multiple selectors
            ad_cards = page.locator('[data-testid="ad-card"], [role="article"]').all()

            logger.info(f"Found {len(ad_cards)} ad cards")

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

        except PlaywrightTimeoutError:
            logger.warning("Timeout waiting for ads to load")
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
            # Extract advertiser name
            advertiser = self._safe_text_content(
                card,
                'a[role="link"], span:has-text("by"), [data-testid="page-name"]'
            )

            # Extract ad text/body
            body_text = self._safe_text_content(
                card,
                '[data-testid="ad-text"], [dir="auto"]'
            )

            # Extract CTA button text
            cta = self._safe_text_content(
                card,
                'button, a[role="button"], [data-testid="cta-button"]'
            )

            # Extract image URL
            image_url = None
            try:
                img = card.locator('img').first
                if img:
                    image_url = img.get_attribute('src')
            except:
                pass

            # Extract date information
            date_text = self._safe_text_content(
                card,
                '[data-testid="ad-date-info"], span:has-text("Started")'
            )

            # Generate unique ID
            ad_id = f"fb_{int(time.time())}_{idx}"

            # Take screenshot of the ad card
            screenshot_path = None
            try:
                screenshot_path = self.save_screenshot(page, ad_id)
            except Exception as e:
                logger.warning(f"Failed to capture screenshot for ad {ad_id}: {e}")

            # Create AdData object
            ad_data = AdData(
                id=ad_id,
                platform="facebook",
                advertiser=advertiser,
                body_text=body_text,
                cta=cta,
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
