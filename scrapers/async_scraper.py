"""Async scraper with parallel processing capabilities."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib
import uuid

from config import BROWSER_CONFIG, RATE_LIMIT_DELAY, SCREENSHOTS_DIR
from database import AdRepository, CheckpointRepository, get_session

logger = logging.getLogger(__name__)


class AsyncBaseScraper:
    """Async base class for ad scrapers with checkpointing and retry logic."""

    def __init__(self, headless: bool = True, session_id: Optional[str] = None):
        """Initialize async scraper.

        Args:
            headless: Whether to run browser in headless mode
            session_id: Optional session ID for checkpointing
        """
        self.headless = headless
        self.session_id = session_id or str(uuid.uuid4())
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.scraped_ads: List[Dict[str, Any]] = []

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()

    async def start_browser(self):
        """Start the Playwright browser asynchronously."""
        logger.info("Starting browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        logger.info("Browser started successfully")

    async def close_browser(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")

    async def create_page(self) -> Page:
        """Create a new browser page with anti-detection measures."""
        context = await self.browser.new_context(
            viewport=BROWSER_CONFIG['viewport'],
            user_agent=BROWSER_CONFIG['user_agent']
        )
        page = await context.new_page()

        # Add stealth measures
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        return page

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def save_screenshot(self, page: Page, ad_id: str) -> str:
        """Take a screenshot with retry logic.

        Args:
            page: Playwright page object
            ad_id: Unique identifier for the ad

        Returns:
            Path to saved screenshot
        """
        screenshot_path = SCREENSHOTS_DIR / f"{self.get_platform_name()}_{ad_id}_{int(datetime.utcnow().timestamp())}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"Screenshot saved: {screenshot_path}")
        return str(screenshot_path)

    def save_checkpoint(self, position: int, ad_id: Optional[str] = None, status: str = 'scraped'):
        """Save a checkpoint for resume capability.

        Args:
            position: Current position in scraping
            ad_id: ID of the ad being processed
            status: Status of the checkpoint
        """
        with CheckpointRepository() as repo:
            repo.save_checkpoint(
                session_id=self.session_id,
                platform=self.get_platform_name(),
                query=getattr(self, 'current_query', ''),
                position=position,
                ad_id=ad_id,
                status=status
            )

    def get_last_checkpoint(self) -> Optional[int]:
        """Get the last checkpoint position.

        Returns:
            Last position or None
        """
        with CheckpointRepository() as repo:
            checkpoint = repo.get_last_checkpoint(self.session_id)
            return checkpoint.position if checkpoint else None

    async def save_ad_to_db(self, ad_data: Dict[str, Any]):
        """Save ad to database asynchronously.

        Args:
            ad_data: Advertisement data dictionary
        """
        # Run database operation in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_ad_sync, ad_data)

    def _save_ad_sync(self, ad_data: Dict[str, Any]):
        """Synchronous database save operation."""
        with AdRepository() as repo:
            repo.save_ad(ad_data)

    async def rate_limit_delay(self):
        """Apply rate limiting delay asynchronously."""
        await asyncio.sleep(RATE_LIMIT_DELAY)

    def get_platform_name(self) -> str:
        """Return the platform name. Must be implemented by subclasses."""
        raise NotImplementedError()

    async def scrape(self, query: str, limit: int = 50, **kwargs) -> List[Dict[str, Any]]:
        """Scrape ads. Must be implemented by subclasses."""
        raise NotImplementedError()


class AsyncFacebookScraper(AsyncBaseScraper):
    """Async Facebook Ad Library scraper."""

    def get_platform_name(self) -> str:
        return "facebook"

    async def scrape(self, query: str, limit: int = 50, country: str = "US", resume: bool = True, **kwargs) -> List[Dict[str, Any]]:
        """Scrape ads from Facebook Ad Library asynchronously.

        Args:
            query: Search query (advertiser name or keyword)
            limit: Maximum number of ads to scrape
            country: Country code
            resume: Whether to resume from last checkpoint
            **kwargs: Additional parameters

        Returns:
            List of scraped ad data
        """
        self.current_query = query
        start_position = 0

        # Check for checkpoint
        if resume:
            last_checkpoint = self.get_last_checkpoint()
            if last_checkpoint is not None:
                start_position = last_checkpoint + 1
                logger.info(f"Resuming from position {start_position}")

        logger.info(f"Starting Facebook scrape for query: '{query}'")

        page = await self.create_page()

        try:
            # Navigate to Facebook Ad Library
            from config import FACEBOOK_AD_LIBRARY_URL
            url = f"{FACEBOOK_AD_LIBRARY_URL}?active_status=all&ad_type=all&country={country}&q={query}"
            logger.info(f"Navigating to: {url}")

            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)

            # Handle consent dialog
            await self._handle_consent_dialog(page)

            # Scroll to load more ads
            await self._scroll_to_load_ads(page, limit)

            # Extract ad data
            ads = await self._extract_ads_from_page(page, limit, start_position)

            logger.info(f"Successfully scraped {len(ads)} ads from Facebook")
            self.scraped_ads.extend(ads)

            return ads

        except Exception as e:
            logger.error(f"Error scraping Facebook ads: {e}")
            raise
        finally:
            await page.close()

    async def _handle_consent_dialog(self, page: Page):
        """Handle cookie/consent dialogs asynchronously."""
        try:
            consent_selectors = [
                'button[data-cookiebanner="accept_button"]',
                'button:has-text("Accept")',
                'button:has-text("Allow")',
            ]

            for selector in consent_selectors:
                try:
                    await page.click(selector, timeout=3000)
                    logger.info("Accepted consent dialog")
                    await asyncio.sleep(1)
                    break
                except:
                    continue
        except Exception as e:
            logger.debug(f"No consent dialog found or error handling it: {e}")

    async def _scroll_to_load_ads(self, page: Page, target_count: int):
        """Scroll page to load more ads dynamically."""
        logger.info("Scrolling to load ads...")

        last_height = await page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 20

        while scroll_attempts < max_attempts:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            new_height = await page.evaluate("document.body.scrollHeight")
            ad_count = await page.locator('[data-testid="ad-card"]').count()
            logger.info(f"Loaded {ad_count} ads so far...")

            if ad_count >= target_count or new_height == last_height:
                break

            last_height = new_height
            scroll_attempts += 1
            await self.rate_limit_delay()

    async def _extract_ads_from_page(self, page: Page, limit: int, start_position: int = 0) -> List[Dict[str, Any]]:
        """Extract ad data from the page asynchronously."""
        ads = []

        try:
            await page.wait_for_selector('[data-testid="ad-card"], [role="article"]', timeout=10000)
            ad_cards = await page.locator('[data-testid="ad-card"], [role="article"]').all()

            logger.info(f"Found {len(ad_cards)} ad cards")

            for idx in range(start_position, min(len(ad_cards), limit)):
                try:
                    card = ad_cards[idx]
                    ad_data = await self._extract_single_ad(page, card, idx)

                    if ad_data:
                        ads.append(ad_data)
                        await self.save_ad_to_db(ad_data)
                        self.save_checkpoint(idx, ad_data['id'], 'completed')
                        logger.info(f"Extracted ad {idx + 1}/{min(limit, len(ad_cards))}")

                    await self.rate_limit_delay()

                except Exception as e:
                    logger.warning(f"Error extracting ad {idx}: {e}")
                    self.save_checkpoint(idx, status='failed')
                    continue

        except Exception as e:
            logger.error(f"Error extracting ads: {e}")

        return ads

    async def _extract_single_ad(self, page: Page, card, idx: int) -> Dict[str, Any]:
        """Extract data from a single ad card asynchronously."""
        try:
            # Extract advertiser name
            advertiser = await self._safe_text_content(card, 'a[role="link"], span:has-text("by")')

            # Extract ad text/body
            body_text = await self._safe_text_content(card, '[data-testid="ad-text"], [dir="auto"]')

            # Extract CTA button text
            cta = await self._safe_text_content(card, 'button, a[role="button"]')

            # Extract image URL
            image_url = None
            try:
                img = card.locator('img').first
                if img:
                    image_url = await img.get_attribute('src')
            except:
                pass

            # Generate unique ID
            ad_id = f"fb_{int(datetime.utcnow().timestamp())}_{idx}"

            # Take screenshot
            screenshot_path = None
            try:
                screenshot_path = await self.save_screenshot(page, ad_id)
            except Exception as e:
                logger.warning(f"Failed to capture screenshot for ad {ad_id}: {e}")

            return {
                'id': ad_id,
                'platform': 'facebook',
                'advertiser': advertiser,
                'body_text': body_text,
                'cta': cta,
                'image_url': image_url,
                'page_url': page.url,
                'screenshot_path': screenshot_path,
                'scraped_at': datetime.utcnow(),
                'is_active': True
            }

        except Exception as e:
            logger.error(f"Error extracting single ad: {e}")
            return None

    async def _safe_text_content(self, element, selector: str) -> str:
        """Safely extract text content from an element asynchronously."""
        try:
            target = element.locator(selector).first
            if target:
                text = await target.text_content()
                return text.strip() if text else ""
        except:
            pass
        return ""


class AsyncGoogleScraper(AsyncBaseScraper):
    """Async Google Ads Transparency Center scraper."""

    def get_platform_name(self) -> str:
        return "google"

    async def scrape(self, query: str, limit: int = 50, region: str = "US", resume: bool = True, **kwargs) -> List[Dict[str, Any]]:
        """Scrape ads from Google Ads Transparency Center asynchronously."""
        self.current_query = query
        start_position = 0

        if resume:
            last_checkpoint = self.get_last_checkpoint()
            if last_checkpoint is not None:
                start_position = last_checkpoint + 1
                logger.info(f"Resuming from position {start_position}")

        logger.info(f"Starting Google Ads scrape for query: '{query}'")

        page = await self.create_page()

        try:
            from config import GOOGLE_ADS_TRANSPARENCY_URL
            logger.info(f"Navigating to: {GOOGLE_ADS_TRANSPARENCY_URL}")

            await page.goto(GOOGLE_ADS_TRANSPARENCY_URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            await self._perform_search(page, query)
            await self._select_advertiser(page)
            await self._scroll_to_load_ads(page, limit)

            ads = await self._extract_ads_from_page(page, limit, start_position)

            logger.info(f"Successfully scraped {len(ads)} ads from Google")
            self.scraped_ads.extend(ads)

            return ads

        except Exception as e:
            logger.error(f"Error scraping Google ads: {e}")
            raise
        finally:
            await page.close()

    async def _perform_search(self, page: Page, query: str):
        """Perform search for advertiser asynchronously."""
        try:
            search_selectors = [
                'input[type="text"]',
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
            ]

            for selector in search_selectors:
                try:
                    search_input = page.locator(selector).first
                    if await search_input.is_visible(timeout=5000):
                        await search_input.fill(query)
                        await asyncio.sleep(1)
                        await page.keyboard.press('Enter')
                        await asyncio.sleep(3)
                        logger.info("Search performed successfully")
                        return
                except:
                    continue

            logger.warning("Could not find search input")

        except Exception as e:
            logger.error(f"Error performing search: {e}")

    async def _select_advertiser(self, page: Page):
        """Select the first advertiser from search results."""
        try:
            await asyncio.sleep(2)

            result_selectors = [
                'a[href*="advertiser"]',
                '[role="button"]',
                '.advertiser-card',
            ]

            for selector in result_selectors:
                try:
                    results = await page.locator(selector).all()
                    if results:
                        await results[0].click()
                        await asyncio.sleep(3)
                        logger.info("Selected advertiser")
                        return
                except:
                    continue

            logger.warning("Could not find advertiser results to click")

        except Exception as e:
            logger.error(f"Error selecting advertiser: {e}")

    async def _scroll_to_load_ads(self, page: Page, target_count: int):
        """Scroll page to load more ads asynchronously."""
        logger.info("Scrolling to load ads...")

        last_height = await page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 15

        while scroll_attempts < max_attempts:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            new_height = await page.evaluate("document.body.scrollHeight")
            ad_count = await page.locator('[class*="creative"]').count()
            logger.info(f"Loaded {ad_count} ads so far...")

            if ad_count >= target_count or new_height == last_height:
                break

            last_height = new_height
            scroll_attempts += 1
            await self.rate_limit_delay()

    async def _extract_ads_from_page(self, page: Page, limit: int, start_position: int = 0) -> List[Dict[str, Any]]:
        """Extract ad data from the page asynchronously."""
        ads = []

        try:
            ad_selectors = [
                '[class*="creative"]',
                '[class*="ad-creative"]',
                '[role="listitem"]',
            ]

            ad_cards = []
            for selector in ad_selectors:
                try:
                    cards = await page.locator(selector).all()
                    if cards:
                        ad_cards = cards
                        logger.info(f"Found {len(cards)} ad cards")
                        break
                except:
                    continue

            if not ad_cards:
                logger.warning("No ad cards found")
                return ads

            for idx in range(start_position, min(len(ad_cards), limit)):
                try:
                    card = ad_cards[idx]
                    ad_data = await self._extract_single_ad(page, card, idx)

                    if ad_data:
                        ads.append(ad_data)
                        await self.save_ad_to_db(ad_data)
                        self.save_checkpoint(idx, ad_data['id'], 'completed')
                        logger.info(f"Extracted ad {idx + 1}/{min(limit, len(ad_cards))}")

                    await self.rate_limit_delay()

                except Exception as e:
                    logger.warning(f"Error extracting ad {idx}: {e}")
                    self.save_checkpoint(idx, status='failed')
                    continue

        except Exception as e:
            logger.error(f"Error extracting ads: {e}")

        return ads

    async def _extract_single_ad(self, page: Page, card, idx: int) -> Dict[str, Any]:
        """Extract data from a single ad card asynchronously."""
        try:
            body_text = await self._safe_text_content(card, '[class*="text"], p, span')
            headline = await self._safe_text_content(card, 'h1, h2, h3, [class*="headline"]')

            image_url = None
            try:
                img = card.locator('img').first
                if img:
                    image_url = await img.get_attribute('src')
            except:
                pass

            ad_id = f"google_{int(datetime.utcnow().timestamp())}_{idx}"

            screenshot_path = None
            try:
                screenshot_path = await self.save_screenshot(page, ad_id)
            except Exception as e:
                logger.warning(f"Failed to capture screenshot for ad {ad_id}: {e}")

            return {
                'id': ad_id,
                'platform': 'google',
                'headline': headline,
                'body_text': body_text,
                'image_url': image_url,
                'page_url': page.url,
                'screenshot_path': screenshot_path,
                'scraped_at': datetime.utcnow(),
                'is_active': True
            }

        except Exception as e:
            logger.error(f"Error extracting single ad: {e}")
            return None

    async def _safe_text_content(self, element, selector: str) -> str:
        """Safely extract text content from an element asynchronously."""
        try:
            target = element.locator(selector).first
            if target:
                text = await target.text_content()
                return text.strip() if text else ""
        except:
            pass
        return ""


async def scrape_multiple_platforms(query: str, limit: int = 50, platforms: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Scrape multiple platforms in parallel.

    Args:
        query: Search query
        limit: Max ads per platform
        platforms: List of platforms ('facebook', 'google'), defaults to all

    Returns:
        Dictionary mapping platform names to lists of ads
    """
    if platforms is None:
        platforms = ['facebook', 'google']

    results = {}

    # Create scraping tasks
    tasks = []

    if 'facebook' in platforms:
        async def scrape_fb():
            async with AsyncFacebookScraper() as scraper:
                return ('facebook', await scraper.scrape(query, limit))
        tasks.append(scrape_fb())

    if 'google' in platforms:
        async def scrape_google():
            async with AsyncGoogleScraper() as scraper:
                return ('google', await scraper.scrape(query, limit))
        tasks.append(scrape_google())

    # Run all tasks in parallel
    completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for result in completed_tasks:
        if isinstance(result, Exception):
            logger.error(f"Scraping task failed: {result}")
        else:
            platform, ads = result
            results[platform] = ads

    return results
