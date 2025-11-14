"""
Surebet Tool - Web Scraper Service
====================================================================

This is a FastAPI service that scrapes betting odds from multiple configured targets.
It can be triggered via API and runs scraping in the background.
It dynamically handles different website structures using a strategy pattern.

Author: Surebet Tool Team
Version: 3.0.0
"""

import requests
import time
import re
import logging
from fastapi import FastAPI, BackgroundTasks
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Constants
BACKEND_API_URL = "http://backend:8000/api/v1/data/ingest"
SCRAPER_TARGETS_URL = "http://backend:8000/api/v1/scraper/targets?active_only=true"

# Scraping Configuration
TIMEOUT_MS = 30000  # 30 seconds timeout
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Create FastAPI app
app = FastAPI(
    title="Surebet Scraper Service",
    description="Multi-site scraping service for betting odds",
    version="3.0.0"
)


def clean_text(text: str) -> str:
    """
    Clean and normalize text extracted from web elements.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = " ".join(text.split())
    return text.strip()


def extract_odds(odds_text: str) -> Optional[float]:
    """
    Extract numeric odds from text.
    
    Args:
        odds_text: Raw odds text
        
    Returns:
        Float odds or None if not found
    """
    if not odds_text:
        return None
    
    # Try to extract numeric value
    match = re.search(r'(\d+\.?\d*)', odds_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    
    return None


def scrape_betexplorer(page, target_url: str) -> List[Dict[str, Any]]:
    """
    Scrape betting odds from BetExplorer.com
    
    This function handles BetExplorer's specific structure:
    - Navigates to sport homepage
    - Finds and clicks on a league link
    - Waits for odds table to load
    - Extracts event data with odds
    
    Args:
        page: Playwright page object
        target_url: URL to scrape
        
    Returns:
        List of scraped event dictionaries
    """
    logger.info(f"🎯 Starting BetExplorer scraping for: {target_url}")
    events = []
    
    try:
        # Navigate to the target URL
        logger.info(f"📍 Navigating to {target_url}")
        page.goto(target_url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        
        # Smart navigation: Find and click a league link
        logger.info("🔍 Looking for league links...")
        
        try:
            # Wait for league links to appear
            page.wait_for_selector("a.list-events__item__title", timeout=10000)
            
            # Find the first league link
            league_links = page.query_selector_all("a.list-events__item__title")
            
            if league_links:
                first_league = league_links[0]
                league_name = clean_text(first_league.text_content() or "")
                logger.info(f"✅ Found league: {league_name}")
                
                # Click the league link
                first_league.click()
                logger.info("👆 Clicked on league link")
                
                # Wait for the odds table to load
                page.wait_for_selector(".table-main--leaguefixtures", timeout=15000)
                logger.info("✅ Odds table loaded")
                
            else:
                logger.warning("⚠️  No league links found, trying to scrape current page")
                
        except PlaywrightTimeoutError:
            logger.warning("⚠️  Timeout waiting for league links, trying to scrape current page")
        
        # Now scrape the odds from the current page
        try:
            # Wait for the main odds table
            page.wait_for_selector(".table-main--leaguefixtures", timeout=10000)
            
            # Find all match rows
            rows = page.query_selector_all("tr.table-main__tt, tr.table-main__tr")
            logger.info(f"📊 Found {len(rows)} potential event rows")
            
            for row in rows:
                try:
                    # Extract event name
                    event_link = row.query_selector("td.table-main__tt > a, td.table-main__participant > a")
                    if not event_link:
                        continue
                    
                    event_name = clean_text(event_link.text_content() or "")
                    if not event_name:
                        continue
                    
                    # Get the deep link (full URL)
                    href = event_link.get_attribute("href") or ""
                    deep_link = urljoin("https://www.betexplorer.com", href) if href else ""
                    
                    # Extract odds from the row
                    odds_cells = row.query_selector_all("td.table-main__detail-odds")
                    odds_list = []
                    
                    for cell in odds_cells:
                        odds_text = clean_text(cell.text_content() or "")
                        odds_value = extract_odds(odds_text)
                        if odds_value:
                            odds_list.append(odds_value)
                    
                    # Only add events that have odds data
                    if odds_list:
                        event_data = {
                            "event_name": event_name,
                            "odds": odds_list,
                            "deep_link": deep_link,
                            "source": "BetExplorer",
                            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        events.append(event_data)
                        logger.info(f"✅ Scraped: {event_name} with {len(odds_list)} odds")
                    
                except Exception as row_error:
                    logger.error(f"❌ Error parsing row: {str(row_error)}")
                    continue
            
        except PlaywrightTimeoutError:
            logger.error("❌ Timeout waiting for odds table")
        
    except Exception as e:
        logger.error(f"❌ Error scraping BetExplorer: {str(e)}")
    
    logger.info(f"✅ BetExplorer scraping complete: {len(events)} events found")
    return events


def scrape_oddschecker(page, target_url: str) -> List[Dict[str, Any]]:
    """
    Scrape betting odds from Oddschecker.com
    
    This function handles Oddschecker's specific structure:
    - Navigates to the target page
    - Waits for event rows to load
    - Extracts event names, odds, and deep links
    
    Args:
        page: Playwright page object
        target_url: URL to scrape
        
    Returns:
        List of scraped event dictionaries
    """
    logger.info(f"🎯 Starting Oddschecker scraping for: {target_url}")
    events = []
    
    try:
        # Navigate to the target URL
        logger.info(f"📍 Navigating to {target_url}")
        page.goto(target_url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        
        # Wait for the main content to load
        try:
            page.wait_for_selector(".match-coupon__event-row, .event-row, [data-event-row]", timeout=15000)
            logger.info("✅ Event rows loaded")
        except PlaywrightTimeoutError:
            logger.warning("⚠️  Timeout waiting for event rows")
            return events
        
        # Find all event rows (try multiple selectors)
        event_rows = page.query_selector_all(".match-coupon__event-row, .event-row, [data-event-row]")
        logger.info(f"📊 Found {len(event_rows)} event rows")
        
        for row in event_rows:
            try:
                # Extract event name
                event_name_elem = row.query_selector(
                    ".match-coupon__event-row-name, .event-name, .participant-name, a.name"
                )
                
                if not event_name_elem:
                    continue
                
                event_name = clean_text(event_name_elem.text_content() or "")
                if not event_name:
                    continue
                
                # Get deep link
                event_link = event_name_elem if event_name_elem.evaluate("el => el.tagName") == "A" else event_name_elem.query_selector("a")
                deep_link = ""
                
                if event_link:
                    href = event_link.get_attribute("href") or ""
                    deep_link = urljoin("https://www.oddschecker.com", href) if href else ""
                
                # Extract odds (try multiple selectors for different page layouts)
                odds_elements = row.query_selector_all(
                    ".odds, .all-odds, [data-best-odd], .bet-btn"
                )
                odds_list = []
                
                for elem in odds_elements:
                    odds_text = clean_text(elem.text_content() or "")
                    odds_value = extract_odds(odds_text)
                    if odds_value:
                        odds_list.append(odds_value)
                
                # Only add events with odds
                if odds_list:
                    event_data = {
                        "event_name": event_name,
                        "odds": odds_list,
                        "deep_link": deep_link,
                        "source": "Oddschecker",
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    events.append(event_data)
                    logger.info(f"✅ Scraped: {event_name} with {len(odds_list)} odds")
                
            except Exception as row_error:
                logger.error(f"❌ Error parsing Oddschecker row: {str(row_error)}")
                continue
        
    except Exception as e:
        logger.error(f"❌ Error scraping Oddschecker: {str(e)}")
    
    logger.info(f"✅ Oddschecker scraping complete: {len(events)} events found")
    return events


def scrape_oddsportal(page, target_url: str) -> List[Dict[str, Any]]:
    """
    Scrape betting odds from Oddsportal.com
    
    This function handles Oddsportal's specific structure.
    
    Args:
        page: Playwright page object
        target_url: URL to scrape
        
    Returns:
        List of scraped event dictionaries
    """
    logger.info(f"🎯 Starting Oddsportal scraping for: {target_url}")
    events = []
    
    try:
        # Navigate to the target URL
        logger.info(f"📍 Navigating to {target_url}")
        page.goto(target_url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        
        # Wait for content to load
        try:
            page.wait_for_selector(".eventRow, [data-v-event], .event-line", timeout=15000)
            logger.info("✅ Event rows loaded")
        except PlaywrightTimeoutError:
            logger.warning("⚠️  Timeout waiting for event rows")
            return events
        
        # Find all event rows
        event_rows = page.query_selector_all(".eventRow, [data-v-event], .event-line")
        logger.info(f"📊 Found {len(event_rows)} event rows")
        
        for row in event_rows:
            try:
                # Extract event name
                event_name_elem = row.query_selector(".name, .event-name, a.participant")
                
                if not event_name_elem:
                    continue
                
                event_name = clean_text(event_name_elem.text_content() or "")
                if not event_name:
                    continue
                
                # Get deep link
                event_link = event_name_elem if event_name_elem.evaluate("el => el.tagName") == "A" else row.query_selector("a")
                deep_link = ""
                
                if event_link:
                    href = event_link.get_attribute("href") or ""
                    deep_link = urljoin("https://www.oddsportal.com", href) if href else ""
                
                # Extract odds
                odds_elements = row.query_selector_all(".odds-nowrp, .odds, [data-odd]")
                odds_list = []
                
                for elem in odds_elements:
                    odds_text = clean_text(elem.text_content() or "")
                    odds_value = extract_odds(odds_text)
                    if odds_value:
                        odds_list.append(odds_value)
                
                # Only add events with odds
                if odds_list:
                    event_data = {
                        "event_name": event_name,
                        "odds": odds_list,
                        "deep_link": deep_link,
                        "source": "Oddsportal",
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    events.append(event_data)
                    logger.info(f"✅ Scraped: {event_name} with {len(odds_list)} odds")
                
            except Exception as row_error:
                logger.error(f"❌ Error parsing Oddsportal row: {str(row_error)}")
                continue
        
    except Exception as e:
        logger.error(f"❌ Error scraping Oddsportal: {str(e)}")
    
    logger.info(f"✅ Oddsportal scraping complete: {len(events)} events found")
    return events


def route_scraper(page, target_url: str, target_name: str) -> List[Dict[str, Any]]:
    """
    Route scraping request to the appropriate scraper function based on URL.
    
    This is the strategy router that determines which scraper to use.
    
    Args:
        page: Playwright page object
        target_url: URL to scrape
        target_name: Name of the target for logging
        
    Returns:
        List of scraped events
    """
    logger.info(f"🔀 Routing scraper for: {target_name} ({target_url})")
    
    # Route based on URL domain
    if "betexplorer.com" in target_url.lower():
        return scrape_betexplorer(page, target_url)
    elif "oddschecker.com" in target_url.lower():
        return scrape_oddschecker(page, target_url)
    elif "oddsportal.com" in target_url.lower():
        return scrape_oddsportal(page, target_url)
    else:
        logger.warning(f"⚠️  Unknown site: {target_url}, attempting BetExplorer strategy")
        return scrape_betexplorer(page, target_url)


def fetch_scraper_targets() -> List[Dict[str, Any]]:
    """
    Fetch active scraper targets from the backend API.
    
    Returns:
        List of target dictionaries
    """
    try:
        logger.info(f"📡 Fetching scraper targets from: {SCRAPER_TARGETS_URL}")
        response = requests.get(SCRAPER_TARGETS_URL, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        targets = data.get("data", [])
        
        logger.info(f"✅ Fetched {len(targets)} active targets")
        return targets
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch targets: {str(e)}")
        return []


def send_data_to_backend(events: List[Dict[str, Any]]) -> bool:
    """
    Send scraped data to the backend API.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        True if successful, False otherwise
    """
    if not events:
        logger.warning("⚠️  No events to send to backend")
        return False
    
    try:
        logger.info(f"📤 Sending {len(events)} events to backend...")
        
        payload = {"events": events}
        response = requests.post(
            BACKEND_API_URL,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        logger.info(f"✅ Successfully sent {len(events)} events to backend")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send data to backend: {str(e)}")
        return False


def run_the_scrape():
    """
    Main scraping orchestration function.
    
    This function:
    1. Fetches active scraper targets from the backend
    2. Launches a Playwright browser
    3. For each target, routes to the appropriate scraper
    4. Aggregates all scraped data
    5. Sends the data to the backend
    """
    logger.info("🚀 Starting scraping job...")
    
    # Fetch targets
    targets = fetch_scraper_targets()
    
    if not targets:
        logger.warning("⚠️  No active targets found, aborting scrape")
        return
    
    all_events = []
    
    # Start Playwright
    with sync_playwright() as p:
        logger.info("🌐 Launching browser...")
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        try:
            for target in targets:
                target_id = target.get("id")
                target_name = target.get("name", "Unknown")
                target_url = target.get("url", "")
                
                if not target_url:
                    logger.warning(f"⚠️  Target {target_name} has no URL, skipping")
                    continue
                
                logger.info(f"\n{'='*60}")
                logger.info(f"📍 Processing target: {target_name}")
                logger.info(f"🔗 URL: {target_url}")
                logger.info(f"{'='*60}\n")
                
                # Create a new page for this target
                page = browser.new_page()
                
                try:
                    # Route to appropriate scraper
                    events = route_scraper(page, target_url, target_name)
                    
                    if events:
                        # Add target ID to each event
                        for event in events:
                            event["target_id"] = target_id
                        
                        all_events.extend(events)
                        logger.info(f"✅ Added {len(events)} events from {target_name}")
                    else:
                        logger.warning(f"⚠️  No events found for {target_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error scraping {target_name}: {str(e)}")
                
                finally:
                    # Always close the page
                    page.close()
                    logger.info(f"🔒 Closed page for {target_name}")
                
                # Small delay between targets
                time.sleep(RETRY_DELAY)
            
        finally:
            # Always close the browser
            browser.close()
            logger.info("🔒 Browser closed")
    
    # Send all data to backend
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Scraping Summary")
    logger.info(f"{'='*60}")
    logger.info(f"Total events scraped: {len(all_events)}")
    logger.info(f"Targets processed: {len(targets)}")
    
    if all_events:
        success = send_data_to_backend(all_events)
        if success:
            logger.info("✅ Scraping job completed successfully!")
        else:
            logger.error("❌ Scraping completed but failed to send data to backend")
    else:
        logger.warning("⚠️  No events were scraped from any target")
    
    logger.info(f"{'='*60}\n")


# FastAPI Endpoints

@app.get("/")
async def root():
    """Root endpoint - service status"""
    return {
        "service": "Surebet Scraper",
        "version": "3.0.0",
        "status": "running",
        "supported_sites": ["BetExplorer", "Oddschecker", "Oddsportal"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "scraper",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


@app.post("/run-scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """
    Trigger a scraping job.
    
    The scraping runs in the background, so this endpoint returns immediately.
    """
    logger.info("📨 Received scrape trigger request")
    
    # Add the scraping task to background tasks
    background_tasks.add_task(run_the_scrape)
    
    return {
        "status": "accepted",
        "message": "Scraping job started in background",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


# Server entry point
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Surebet Scraper Service...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
