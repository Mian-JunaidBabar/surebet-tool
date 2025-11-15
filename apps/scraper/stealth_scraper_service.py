"""
Stealth Scraper Service Module

This module implements an advanced web scraping system using playwright-stealth
and proxy support to bypass anti-bot protections like Cloudflare.

Key features:
- Stealth mode using playwright_stealth to avoid detection
- Proxy support for residential IP rotation
- Human-like behavior simulation (mouse movements, random delays)
- Resilient selectors using role-based and text-based queries
"""

import os
import time
import random
import logging
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, Browser
from playwright_stealth import stealth_sync

logger = logging.getLogger(__name__)

# Target URLs for scraping
TARGET_URLS = [
    "https://www.betexplorer.com/football/",
    "https://www.oddschecker.com/football",
]


def simulate_human_behavior(page: Page):
    """
    Simulate human-like behavior to avoid bot detection.
    
    Includes:
    - Random mouse movements
    - Random scrolling
    - Random delays between actions
    - Random viewport resizing
    """
    try:
        # Random delay before interacting (more variation)
        time.sleep(random.uniform(1.0, 4.0))
        
        # Get viewport size
        viewport = page.viewport_size
        if viewport:
            width = viewport['width']
            height = viewport['height']
            
            # Simulate more natural mouse movements
            for _ in range(random.randint(3, 6)):
                x = random.randint(100, width - 100)
                y = random.randint(100, height - 100)
                # Move mouse with slight delay between steps for smoothness
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.05, 0.25))
            
            # Simulate realistic scrolling patterns
            # Initial scroll down
            scroll_amount = random.randint(300, 800)
            page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(0.8, 2.0))
            
            # Small scroll adjustments (like reading)
            for _ in range(random.randint(1, 3)):
                small_scroll = random.randint(-100, 200)
                page.mouse.wheel(0, small_scroll)
                time.sleep(random.uniform(0.4, 1.2))
            
            # Occasional scroll back up
            if random.random() > 0.5:
                page.mouse.wheel(0, -random.randint(50, 200))
                time.sleep(random.uniform(0.3, 0.9))
        
        logger.info("✅ Simulated human-like behavior")
    except Exception as e:
        logger.warning(f"⚠️  Error simulating human behavior: {str(e)}")


def scrape_betexplorer(page: Page, url: str) -> List[Dict]:
    """
    Scrape BetExplorer using production-grade selectors.
    
    Uses robust selectors:
    - Row: .table-main__row:has-text('vs')
    - Event name: a.table-main__participant
    - Odds: td.table-main__odds (nth(0) for home, nth(1) for draw, nth(2) for away)
    
    Args:
        page: Playwright page object
        url: URL to scrape
        
    Returns:
        List of events with odds
    """
    events = []
    
    try:
        logger.info(f"🎯 Scraping BetExplorer: {url}")
        
        # Navigate and wait for content
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        simulate_human_behavior(page)
        
        # Wait for table rows to load
        try:
            page.wait_for_selector(".table-main__row", timeout=10000)
        except Exception as e:
            logger.warning(f"⚠️ Timeout waiting for BetExplorer rows: {str(e)}")
            return events
        
        # Get all event rows (only those with 'vs' text)
        rows = page.locator(".table-main__row:has-text('vs')").all()
        logger.info(f"📊 Found {len(rows)} event rows on BetExplorer")
        
        for row in rows[:20]:  # Limit to 20 rows
            try:
                # Extract event name
                event_link = row.locator("a.table-main__participant").first
                event_name = event_link.text_content() if event_link else None
                
                if not event_name:
                    continue
                
                event_name = event_name.strip()
                
                # Extract deep link
                href = event_link.get_attribute("href") if event_link else None
                deep_link = f"https://www.betexplorer.com{href}" if href else url
                
                # Extract odds (home, draw, away)
                odds = []
                odds_cells = row.locator("td.table-main__odds").all()
                
                for i in range(min(3, len(odds_cells))):  # Get first 3 odds
                    try:
                        odds_text = odds_cells[i].text_content()
                        if odds_text:
                            odds_value = float(odds_text.strip())
                            if 1.01 <= odds_value <= 100:
                                odds.append(odds_value)
                    except (ValueError, AttributeError):
                        continue
                
                if event_name and len(odds) >= 2:
                    events.append({
                        "event_name": event_name,
                        "odds": odds,
                        "source": "BetExplorer",
                        "deep_link": deep_link
                    })
                    logger.debug(f"  ✓ {event_name}: {odds}")
                    
            except Exception as e:
                logger.debug(f"  ⚠️ Error processing row: {str(e)}")
                continue
        
        logger.info(f"✅ Scraped {len(events)} events from BetExplorer")
        
    except Exception as e:
        logger.error(f"❌ Error scraping BetExplorer: {str(e)}")
    
    return events


def scrape_oddschecker(page: Page, url: str) -> List[Dict]:
    """
    Scrape Oddschecker using production-grade data-testid selectors.
    
    Uses data-testid attributes:
    - Row: [data-testid="coupon-event-row"]
    - Event name: [data-testid="coupon-event-name"]
    - Odds cells: [data-testid^="odds-cell-"] (extract bookmaker from testid)
    
    Args:
        page: Playwright page object
        url: URL to scrape
        
    Returns:
        List of events with odds
    """
    events = []
    
    try:
        logger.info(f"🎯 Scraping Oddschecker: {url}")
        
        # Navigate and wait for content
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        simulate_human_behavior(page)
        
        # Wait for event rows to load
        try:
            page.wait_for_selector('[data-testid="coupon-event-row"]', timeout=10000)
        except Exception as e:
            logger.warning(f"⚠️ Timeout waiting for Oddschecker rows: {str(e)}")
            return events
        
        # Get all event rows
        rows = page.locator('[data-testid="coupon-event-row"]').all()
        logger.info(f"📊 Found {len(rows)} event rows on Oddschecker")
        
        for row in rows[:20]:  # Limit to 20 rows
            try:
                # Extract event name
                event_name_el = row.locator('[data-testid="coupon-event-name"]').first
                event_name = event_name_el.text_content() if event_name_el else None
                
                if not event_name:
                    continue
                
                event_name = event_name.strip()
                
                # Extract deep link
                link = row.locator("a").first
                href = link.get_attribute("href") if link else None
                deep_link = f"https://www.oddschecker.com{href}" if href and href.startswith('/') else href or url
                
                # Extract odds from odds cells
                # Oddschecker has odds cells with data-testid like "odds-cell-{bookmaker}"
                odds = []
                odds_cells = row.locator('[data-testid^="odds-cell-"]').all()
                
                for cell in odds_cells[:10]:  # Limit to 10 odds cells
                    try:
                        # Get odds value from cell text
                        odds_text = cell.text_content()
                        if odds_text:
                            # Parse fractional or decimal odds
                            odds_text = odds_text.strip()
                            
                            # Try decimal format first (e.g., "2.50")
                            try:
                                odds_value = float(odds_text)
                                if 1.01 <= odds_value <= 100:
                                    odds.append(odds_value)
                            except ValueError:
                                # Try fractional format (e.g., "6/4")
                                if '/' in odds_text:
                                    parts = odds_text.split('/')
                                    if len(parts) == 2:
                                        try:
                                            numerator = float(parts[0])
                                            denominator = float(parts[1])
                                            if denominator != 0:
                                                decimal_odds = (numerator / denominator) + 1
                                                if 1.01 <= decimal_odds <= 100:
                                                    odds.append(round(decimal_odds, 2))
                                        except ValueError:
                                            pass
                    except Exception as e:
                        logger.debug(f"  ⚠️ Error parsing odds cell: {str(e)}")
                        continue
                
                if event_name and len(odds) >= 2:
                    events.append({
                        "event_name": event_name,
                        "odds": odds,
                        "source": "Oddschecker",
                        "deep_link": deep_link
                    })
                    logger.debug(f"  ✓ {event_name}: {odds}")
                    
            except Exception as e:
                logger.debug(f"  ⚠️ Error processing row: {str(e)}")
                continue
        
        logger.info(f"✅ Scraped {len(events)} events from Oddschecker")
        
    except Exception as e:
        logger.error(f"❌ Error scraping Oddschecker: {str(e)}")
    
    return events


def scrape_with_stealth(url: str, page: Page) -> List[Dict]:
    """
    Scrape a single URL using site-specific production-grade selectors.
    
    Args:
        url: The URL to scrape
        page: The Playwright page object (already stealthed)
        
    Returns:
        List of events with odds data
    """
    # Route to site-specific scraper based on domain
    if "betexplorer.com" in url:
        return scrape_betexplorer(page, url)
    elif "oddschecker.com" in url:
        return scrape_oddschecker(page, url)
    else:
        logger.warning(f"⚠️ No specific scraper for URL: {url}")
        return []


def run_stealth_scrape() -> List[Dict]:
    """
    Main function to run the stealth scraper.
    
    This function:
    1. Loads proxy configuration from environment
    2. Launches a stealthed browser with proxy
    3. Scrapes target URLs with human-like behavior
    4. Returns aggregated results
    
    Returns:
        List of events with odds data from all scraped sources
    """
    # Load proxy configuration
    proxy_url = os.getenv("PROXY_URL", "")
    
    if proxy_url:
        logger.info(f"🔒 Using proxy: {proxy_url.split('@')[1] if '@' in proxy_url else 'configured'}")
    else:
        logger.warning("⚠️  No proxy configured - scraping without proxy (may be detected)")
    
    all_events = []
    targets_processed = 0
    targets_succeeded = 0
    
    try:
        with sync_playwright() as playwright:
            logger.info("🚀 Launching stealth browser...")
            
            # Configure browser launch options
            launch_options = {
                "headless": True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]
            }
            
            # Add proxy if configured
            if proxy_url:
                # Parse proxy URL
                # Format: http://username:password@host:port
                if "@" in proxy_url:
                    credentials, server = proxy_url.split("//")[1].split("@")
                    username, password = credentials.split(":")
                    
                    launch_options["proxy"] = {
                        "server": f"http://{server}",
                        "username": username,
                        "password": password
                    }
                else:
                    launch_options["proxy"] = {"server": proxy_url}
            
            # Launch browser
            browser: Browser = playwright.chromium.launch(**launch_options)
            
            # Randomize viewport size for more human-like behavior
            viewport_sizes = [
                {"width": 1920, "height": 1080},
                {"width": 1366, "height": 768},
                {"width": 1440, "height": 900},
                {"width": 1536, "height": 864},
            ]
            selected_viewport = random.choice(viewport_sizes)
            
            # Randomize user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            ]
            selected_ua = random.choice(user_agents)
            
            # Randomize timezone
            timezones = ["America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London"]
            selected_tz = random.choice(timezones)
            
            # Create context with realistic settings
            context = browser.new_context(
                viewport=selected_viewport,
                user_agent=selected_ua,
                locale="en-US",
                timezone_id=selected_tz,
                # Add more realistic browser features
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            
            # Create page and apply stealth patches
            page = context.new_page()
            stealth_sync(page)
            
            logger.info(f"✅ Browser launched with stealth mode (viewport: {selected_viewport['width']}x{selected_viewport['height']}, tz: {selected_tz})")
            
            # Scrape each target URL
            for url in TARGET_URLS:
                targets_processed += 1
                try:
                    events = scrape_with_stealth(url, page)
                    if events:
                        all_events.extend(events)
                        targets_succeeded += 1
                        logger.info(f"✅ Successfully scraped {url}: {len(events)} events")
                    else:
                        logger.warning(f"⚠️ No events found from {url}")
                    
                    # Random delay between sites (longer for more natural behavior)
                    delay = random.uniform(4, 8)
                    logger.info(f"⏳ Waiting {delay:.1f}s before next target...")
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"❌ Error scraping {url}: {str(e)}")
                    continue
            
            # Clean up
            context.close()
            browser.close()
            
            # Final summary log
            logger.info("=" * 80)
            logger.info(f"✅ Scraping job complete. Succeeded on {targets_succeeded}/{targets_processed} targets.")
            logger.info(f"📊 Found a total of {len(all_events)} events across all sites.")
            logger.info("=" * 80)
            
    except Exception as e:
        logger.error(f"❌ Fatal error in stealth scraper: {str(e)}")
        raise
    
    return all_events


if __name__ == "__main__":
    # Test the stealth scraper
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    results = run_stealth_scrape()
    print(f"\n✅ Scraped {len(results)} events:")
    for event in results[:5]:
        print(f"  - {event['event_name']}: {event['odds']}")
