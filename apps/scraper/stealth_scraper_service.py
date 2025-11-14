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
    """
    try:
        # Random delay before interacting
        time.sleep(random.uniform(1.5, 3.5))
        
        # Get viewport size
        viewport = page.viewport_size
        if viewport:
            width = viewport['width']
            height = viewport['height']
            
            # Simulate random mouse movements
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, width - 100)
                y = random.randint(100, height - 100)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            
            # Simulate scrolling
            scroll_amount = random.randint(200, 600)
            page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll back up a bit
            page.mouse.wheel(0, -random.randint(50, 150))
            time.sleep(random.uniform(0.3, 0.8))
        
        logger.info("✅ Simulated human-like behavior")
    except Exception as e:
        logger.warning(f"⚠️  Error simulating human behavior: {str(e)}")


def scrape_with_stealth(url: str, page: Page) -> List[Dict]:
    """
    Scrape a single URL using stealth techniques and resilient selectors.
    
    Args:
        url: The URL to scrape
        page: The Playwright page object (already stealthed)
        
    Returns:
        List of events with odds data
    """
    events = []
    
    try:
        logger.info(f"🎯 Navigating to: {url}")
        
        # Navigate with a realistic timeout
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # Simulate human behavior
        simulate_human_behavior(page)
        
        # Wait for content to load
        time.sleep(random.uniform(2, 4))
        
        # Try multiple strategies to find betting data
        # Strategy 1: Look for odds tables using role-based selectors
        try:
            tables = page.get_by_role("table").all()
            logger.info(f"📊 Found {len(tables)} tables on the page")
            
            for table in tables[:5]:  # Limit to first 5 tables
                try:
                    # Extract rows
                    rows = table.get_by_role("row").all()
                    
                    for row in rows[:10]:  # Limit rows per table
                        try:
                            cells = row.get_by_role("cell").all()
                            
                            if len(cells) >= 3:
                                # Try to extract event name and odds
                                event_text = cells[0].text_content() or ""
                                
                                # Look for decimal odds patterns (e.g., 2.50, 1.95)
                                odds = []
                                for cell in cells[1:]:
                                    text = cell.text_content() or ""
                                    # Try to parse as float
                                    try:
                                        odd = float(text.strip())
                                        if 1.01 <= odd <= 100:  # Valid odds range
                                            odds.append(odd)
                                    except ValueError:
                                        continue
                                
                                if event_text and len(odds) >= 2:
                                    events.append({
                                        "event_name": event_text.strip(),
                                        "odds": odds,
                                        "source": url.split('/')[2],  # domain name
                                        "deep_link": url
                                    })
                                    logger.debug(f"  ✓ Extracted: {event_text[:50]}... with {len(odds)} odds")
                        except Exception as e:
                            logger.debug(f"  ⚠️  Error processing row: {str(e)}")
                            continue
                except Exception as e:
                    logger.debug(f"  ⚠️  Error processing table: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"⚠️  Strategy 1 (tables) failed: {str(e)}")
        
        # Strategy 2: Look for specific betting-related text patterns
        try:
            # Look for elements containing "vs" or "odds"
            event_elements = page.get_by_text("vs", exact=False).all()
            logger.info(f"🔍 Found {len(event_elements)} elements with 'vs' text")
            
            for element in event_elements[:20]:  # Limit to 20 elements
                try:
                    event_text = element.text_content() or ""
                    
                    # Look for nearby odds
                    parent = element.locator("xpath=..")
                    parent_text = parent.text_content() or ""
                    
                    # Extract odds from parent text
                    import re
                    odds_pattern = r'\b([1-9]\d*\.?\d+)\b'
                    potential_odds = re.findall(odds_pattern, parent_text)
                    
                    odds = []
                    for odd_str in potential_odds:
                        try:
                            odd = float(odd_str)
                            if 1.01 <= odd <= 100:
                                odds.append(odd)
                        except ValueError:
                            continue
                    
                    if event_text and len(odds) >= 2:
                        events.append({
                            "event_name": event_text.strip(),
                            "odds": odds[:6],  # Limit to 6 odds
                            "source": url.split('/')[2],
                            "deep_link": url
                        })
                        logger.debug(f"  ✓ Extracted from text: {event_text[:50]}...")
                except Exception as e:
                    logger.debug(f"  ⚠️  Error processing element: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"⚠️  Strategy 2 (text search) failed: {str(e)}")
        
        logger.info(f"✅ Scraped {len(events)} events from {url}")
        
    except Exception as e:
        logger.error(f"❌ Error scraping {url}: {str(e)}")
    
    return events


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
            
            # Create context with realistic settings
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York"
            )
            
            # Create page and apply stealth patches
            page = context.new_page()
            stealth_sync(page)
            
            logger.info("✅ Browser launched with stealth mode enabled")
            
            # Scrape each target URL
            for url in TARGET_URLS:
                try:
                    events = scrape_with_stealth(url, page)
                    all_events.extend(events)
                    
                    # Random delay between sites
                    time.sleep(random.uniform(3, 6))
                except Exception as e:
                    logger.error(f"❌ Error scraping {url}: {str(e)}")
                    continue
            
            # Clean up
            context.close()
            browser.close()
            
            logger.info(f"✅ Stealth scraping complete! Total events: {len(all_events)}")
            
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
