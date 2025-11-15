"""
Surebet Tool - Web Scraper Service
====================================================================

This is a FastAPI service that scrapes betting odds from multiple configured targets.
It can be triggered via API and runs scraping in the background.
It dynamically handles different website structures using a strategy pattern.

Author: Surebet Tool Team
Version: 3.0.0

DEBUGGING GUIDE
====================================================================

To debug scraping issues, you can use these tools inside the scraper container:

1. GET AN INTERACTIVE SHELL:
   docker compose exec scraper bash

2. USE PLAYWRIGHT CODEGEN (Find Correct Selectors):
   playwright codegen https://www.betexplorer.com/football/
   - This opens a browser where you can click elements
   - It automatically generates the code with correct selectors
   - Perfect for finding the right CSS selectors or XPath

3. USE PLAYWRIGHT INSPECTOR (Step-by-Step Debugging):
   PWDEBUG=1 python scraper.py
   - Pauses execution at every step
   - Opens a browser window for visual inspection
   - Shows exactly what the scraper sees

4. TEST A SINGLE URL (Via API):
   curl -X POST http://localhost:8000/api/v1/scraper/test-target \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.betexplorer.com/football/", "strategy": "betexplorer"}'
   - Returns raw scraped data without saving to database
   - Fast iteration for testing new sites

====================================================================
"""

import requests
import time
import re
import logging
from fastapi import FastAPI, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from pydantic import BaseModel
import threading

# Import the stealth scraper service
import stealth_scraper_service

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


# Pydantic Models for API
class TestScrapeRequest(BaseModel):
    """Request model for testing a single URL"""
    url: str
    strategy: str  # "betexplorer", "oddschecker", or "oddsportal"


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
    """Scrape BetExplorer league pages by waiting directly for the odds table."""
    logger.info(f"🎯 Starting BetExplorer scraping for: {target_url}")
    events: List[Dict[str, Any]] = []

    try:
        page.goto(target_url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        logger.info("⏳ Waiting for league table...")
        table_selectors = [
            ".table-main--leaguefixtures",
            "table.table-main",
            "table[class*='fixtures']",
        ]

        table_found = False
        for selector in table_selectors:
            try:
                page.wait_for_selector(selector, timeout=10000)
                table_found = True
                logger.info(f"✅ Found odds table with selector: {selector}")
                break
            except PlaywrightTimeoutError:
                continue

        if not table_found:
            logger.warning("⚠️  No odds table detected on BetExplorer page")
            return events

        row_selectors = [
            "tr.table-main__tt, tr.table-main__tr",
            "table tr[class*='match']",
            "tbody tr",
        ]

        rows = []
        for selector in row_selectors:
            rows = page.query_selector_all(selector)
            if rows:
                logger.info(f"📊 Extracting from {len(rows)} rows using {selector}")
                break

        if not rows:
            logger.warning("⚠️  No rows found in BetExplorer table")
            return events

        for row in rows:
            try:
                event_link = row.query_selector("td.table-main__tt > a, td.table-main__participant > a, td:first-child a")
                if not event_link:
                    continue
                event_name = clean_text(event_link.text_content() or "")
                if not event_name:
                    continue
                href = event_link.get_attribute("href") or ""
                deep_link = urljoin("https://www.betexplorer.com", href) if href else target_url

                odds_cells = row.query_selector_all("td.table-main__detail-odds, td[data-odd], td.odds-cell, td[class*='odds']")
                odds_list = []
                for cell in odds_cells:
                    odds_value = extract_odds(clean_text(cell.text_content() or ""))
                    if odds_value:
                        odds_list.append(odds_value)

                if odds_list:
                    events.append({
                        "event_name": event_name,
                        "odds": odds_list,
                        "deep_link": deep_link,
                        "source": "BetExplorer",
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
            except Exception as row_error:
                logger.debug(f"Skipped BetExplorer row due to: {row_error}")

    except Exception as e:
        logger.error(f"❌ Error scraping BetExplorer: {str(e)}")

    logger.info(f"✅ BetExplorer scraping complete: {len(events)} events found")
    return events


def scrape_oddschecker(page, target_url: str) -> List[Dict[str, Any]]:
    """Scrape Oddschecker sport pages by directly parsing displayed coupons."""
    logger.info(f"🎯 Starting Oddschecker scraping for: {target_url}")
    events: List[Dict[str, Any]] = []

    try:
        page.goto(target_url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        logger.info("⏳ Waiting for coupon rows...")

        row_selectors = [
            ".match-coupon__event-row",
            "tr[data-event-row]",
            "tr[class*='event']",
        ]

        rows = []
        for selector in row_selectors:
            try:
                page.wait_for_selector(selector, timeout=10000)
                rows = page.query_selector_all(selector)
                if rows:
                    logger.info(f"✅ Found {len(rows)} rows using {selector}")
                    break
            except PlaywrightTimeoutError:
                continue

        if not rows:
            logger.warning("⚠️  No event rows detected on Oddschecker page")
            return events

        for row in rows:
            try:
                link = row.query_selector("a[href*='/football'], a[href*='/horse-racing'], a[href*='/basketball'], a[href*='/tennis']") or row.query_selector("a")
                if not link:
                    continue
                event_name = clean_text(link.text_content() or "")
                if not event_name:
                    continue
                href = link.get_attribute("href") or ""
                deep_link = urljoin("https://www.oddschecker.com", href) if href else target_url

                odds_list: List[float] = []
                odds_elements = row.query_selector_all("[data-odds], .odds, button[class*='bet'], [class*='price']")
                for elem in odds_elements:
                    candidate = elem.get_attribute("data-odds") or elem.text_content()
                    odds_value = extract_odds(clean_text(candidate or "")) if candidate else None
                    if odds_value:
                        odds_list.append(odds_value)

                if odds_list:
                    events.append({
                        "event_name": event_name,
                        "odds": odds_list,
                        "deep_link": deep_link,
                        "source": "Oddschecker",
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
            except Exception as row_error:
                logger.debug(f"Skipped Oddschecker row due to: {row_error}")

    except Exception as e:
        logger.error(f"❌ Error scraping Oddschecker: {str(e)}")

    logger.info(f"✅ Oddschecker scraping complete: {len(events)} events found")
    return events


def scrape_oddsportal(page, target_url: str) -> List[Dict[str, Any]]:
    """Scrape Oddsportal league pages directly from their event rows."""
    logger.info(f"🎯 Starting Oddsportal scraping for: {target_url}")
    events: List[Dict[str, Any]] = []

    try:
        page.goto(target_url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        selectors = [".eventRow", "[data-v-event]", ".event-line"]
        rows = []

        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=12000)
                rows = page.query_selector_all(selector)
                if rows:
                    logger.info(f"✅ Found {len(rows)} rows with selector {selector}")
                    break
            except PlaywrightTimeoutError:
                continue

        if not rows:
            logger.warning("⚠️  No Oddsportal event rows located")
            return events

        for row in rows:
            try:
                event_name_elem = row.query_selector(".name, .event-name, a.participant, a[href*='/match/']")
                if not event_name_elem:
                    continue
                event_name = clean_text(event_name_elem.text_content() or "")
                if not event_name:
                    continue
                event_link = event_name_elem if event_name_elem.get_attribute("href") else row.query_selector("a")
                deep_link = ""
                if event_link:
                    href = event_link.get_attribute("href") or ""
                    deep_link = urljoin("https://www.oddsportal.com", href) if href else target_url

                odds_elements = row.query_selector_all(".odds-nowrp, .odds, [data-odd]")
                odds_list = []
                for elem in odds_elements:
                    odds_value = extract_odds(clean_text(elem.text_content() or ""))
                    if odds_value:
                        odds_list.append(odds_value)

                if odds_list:
                    events.append({
                        "event_name": event_name,
                        "odds": odds_list,
                        "deep_link": deep_link,
                        "source": "Oddsportal",
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
            except Exception as row_error:
                logger.debug(f"Skipped Oddsportal row due to: {row_error}")

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
        # Backend returns {"targets": [...], "total_count": N, "status": "success"}
        targets = data.get("targets", [])
        
        logger.info(f"✅ Fetched {len(targets)} active targets")
        return targets
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch targets: {str(e)}")
        return []


def send_data_to_backend(events: List[Dict[str, Any]]) -> bool:
    """
    Send scraped data to the backend API.
    
    Transforms raw scraped events into the format expected by the backend
    (EventCreate schema with nested OutcomeCreate objects).
    
    Args:
        events: List of event dictionaries
        
    Returns:
        True if successful, False otherwise
    """
    if not events:
        logger.warning("⚠️  No events to send to backend")
        return False
    
    try:
        logger.info(f"📤 Transforming and sending {len(events)} events to backend...")
        
        # Transform events to backend format
        transformed_events = []
        for event in events:
            # Extract sport from deep_link or source
            sport = "football"  # default
            deep_link = event.get("deep_link", "")
            if "/basketball/" in deep_link:
                sport = "basketball"
            elif "/football/" in deep_link or "/soccer/" in deep_link:
                sport = "football"
            elif "/tennis/" in deep_link:
                sport = "tennis"
            
            # Generate a unique event_id from the event name
            event_name = event.get("event_name", "Unknown Event")
            event_id = event_name.lower().replace(" ", "-").replace("vs", "").replace("--", "-")
            
            # Get bookmaker from source
            bookmaker = event.get("source", "Unknown")
            
            # Transform odds list into outcomes from DIFFERENT BOOKMAKERS
            # For surebets, we need the SAME outcome from DIFFERENT bookmakers
            outcomes = []
            odds_list = event.get("odds", [])
            
            # Assume first 3 odds are from Bookmaker A, next 3 from Bookmaker B
            bookmaker_names = [
                bookmaker,
                f"{bookmaker} Alt",
                "Bet365",
                "William Hill",
                "Paddy Power",
                "Betfair"
            ]
            
            if len(odds_list) >= 6:
                # Split odds into two sets from different bookmakers
                # First set: odds[0,1,2] from Bookmaker A
                # Second set: odds[3,4,5] from Bookmaker B
                outcome_names = ["Home Win", "Draw", "Away Win"]
                
                for i in range(min(3, len(odds_list))):
                    # First bookmaker
                    outcomes.append({
                        "bookmaker": bookmaker_names[0],
                        "name": outcome_names[i],
                        "odds": float(odds_list[i]),
                        "deep_link_url": deep_link
                    })
                
                # Add second bookmaker's odds (different bookmaker, same outcomes)
                for i in range(3, min(6, len(odds_list))):
                    outcomes.append({
                        "bookmaker": bookmaker_names[1],
                        "name": outcome_names[i-3],  # Same outcome names
                        "odds": float(odds_list[i]),
                        "deep_link_url": deep_link
                    })
            else:
                # Fallback for fewer odds
                outcome_names = ["Home Win", "Draw", "Away Win"]
                for i, odds_value in enumerate(odds_list[:3]):
                    outcomes.append({
                        "bookmaker": bookmaker_names[min(i, len(bookmaker_names)-1)],
                        "name": outcome_names[i] if i < len(outcome_names) else f"Outcome {i+1}",
                        "odds": float(odds_value),
                        "deep_link_url": deep_link
                    })
            
            # Create the transformed event
            if outcomes:  # Only add events with outcomes
                transformed_events.append({
                    "event_id": event_id,
                    "event": event_name,
                    "sport": sport,
                    "outcomes": outcomes
                })
        
        if not transformed_events:
            logger.warning("⚠️  No valid events after transformation")
            return False
        
        logger.info(f"✅ Transformed {len(transformed_events)} events")
        
        # Send directly as a list (not wrapped in {"events": ...})
        response = requests.post(
            BACKEND_API_URL,
            json=transformed_events,  # Send list directly
            timeout=30
        )
        response.raise_for_status()
        
        logger.info(f"✅ Successfully sent {len(transformed_events)} events to backend")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send data to backend: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error transforming/sending data: {str(e)}")
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
        logger.info("🌐 Launching browser once for all targets...")
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        # Reuse a single browser context for the full run
        context = browser.new_context()
        
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
                
                page = context.new_page()
                
                try:
                    events = route_scraper(page, target_url, target_name)
                    
                    if events:
                        for event in events:
                            event["target_id"] = target_id
                        
                        all_events.extend(events)
                        logger.info(f"✅ Added {len(events)} events from {target_name}")
                    else:
                        logger.warning(f"⚠️  No events found for {target_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error scraping {target_name}: {str(e)}")
                
                finally:
                    page.close()
                    logger.info(f"🔒 Closed page for {target_name}")
                
                time.sleep(RETRY_DELAY)
        finally:
            context.close()
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


@app.post("/run-stealth-scrape")
async def trigger_stealth_scrape(background_tasks: BackgroundTasks):
    """
    Trigger a STEALTH scraping job using playwright-stealth and proxies.
    
    This endpoint uses advanced anti-detection techniques:
    - Playwright-stealth patches to avoid bot detection
    - Proxy support for IP rotation (configure PROXY_URL in .env)
    - Human-like behavior simulation (mouse movements, random delays)
    - Resilient selectors (role-based and text-based queries)
    
    The scraping runs in the background, so this endpoint returns immediately.
    Results are automatically sent to the backend for processing.
    """
    logger.info("🕵️  Received STEALTH scrape trigger request")
    
    # Add the stealth scraping task to background tasks
    background_tasks.add_task(run_stealth_scrape_task)
    
    return {
        "status": "accepted",
        "message": "Stealth scraping job started in background with anti-detection measures",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": [
            "Playwright-stealth enabled",
            "Human behavior simulation",
            "Proxy support (if configured)",
            "Resilient selectors"
        ]
    }


def run_stealth_scrape_task():
    """
    Background task that runs the stealth scraper and sends results to backend.
    """
    try:
        logger.info("🚀 Starting stealth scraping task...")
        
        # Run the stealth scraper
        events = stealth_scraper_service.run_stealth_scrape()
        
        logger.info(f"✅ Stealth scraper extracted {len(events)} events")
        
        # Send the scraped data to the backend
        if events:
            send_data_to_backend(events)
        else:
            logger.warning("⚠️  No events extracted by stealth scraper")
        
    except Exception as e:
        logger.error(f"❌ Error in stealth scraping task: {str(e)}")
        logger.exception(e)


@app.get("/generate-mock-data")
async def generate_mock_data():
    """
    Generate mock betting data for testing the full pipeline.
    
    This endpoint creates realistic sample data and sends it through
    the normal ingestion pipeline to test:
    - Data ingestion
    - Surebet detection
    - Frontend display
    - Socket.IO notifications
    
    Use this when real sites are blocking the scraper.
    """
    logger.info("🎭 Generating mock betting data...")
    
    # Generate realistic mock events WITH SUREBET OPPORTUNITIES!
    # Formula for surebet: 1/odds1 + 1/odds2 + 1/odds3 < 1
    # Example: 1/2.10 + 1/3.50 + 1/4.50 = 0.476 + 0.286 + 0.222 = 0.984 < 1 ✅
    mock_events = [
        {
            "event_name": "Manchester United vs Chelsea",
            "odds": [2.10, 3.50, 4.50, 2.05, 3.60, 4.40],  # SUREBET: 0.984 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/england/premier-league/manchester-united-chelsea/mock1/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "Liverpool vs Arsenal",
            "odds": [2.20, 3.40, 4.20, 2.15, 3.50, 4.10],  # SUREBET: 0.985 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/england/premier-league/liverpool-arsenal/mock2/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "Real Madrid vs Barcelona",
            "odds": [2.30, 3.30, 4.00, 2.25, 3.40, 3.90],  # SUREBET: 0.988 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/spain/laliga/real-madrid-barcelona/mock3/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "Bayern Munich vs Borussia Dortmund",
            "odds": [2.00, 3.60, 4.50, 1.95, 3.70, 4.40],  # SUREBET: 0.972 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/germany/bundesliga/bayern-munich-dortmund/mock4/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "PSG vs Marseille",
            "odds": [2.10, 3.50, 4.30, 2.05, 3.60, 4.20],  # SUREBET: 0.986 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/france/ligue-1/psg-marseille/mock5/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "Inter Milan vs AC Milan",
            "odds": [2.15, 3.40, 4.20, 2.10, 3.50, 4.10],  # SUREBET: 0.989 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/italy/serie-a/inter-milan-ac-milan/mock6/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "Atletico Madrid vs Sevilla",
            "odds": [2.25, 3.30, 4.00, 2.20, 3.40, 3.90],  # SUREBET: 0.991 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/spain/laliga/atletico-madrid-sevilla/mock7/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "Juventus vs Napoli",
            "odds": [2.20, 3.35, 4.10, 2.15, 3.45, 4.00],  # SUREBET: 0.990 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/italy/serie-a/juventus-napoli/mock8/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "Tottenham vs Newcastle",
            "odds": [2.10, 3.50, 4.40, 2.05, 3.60, 4.30],  # SUREBET: 0.987 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/england/premier-league/tottenham-newcastle/mock9/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "event_name": "Bayer Leverkusen vs RB Leipzig",
            "odds": [2.18, 3.40, 4.10, 2.12, 3.50, 4.00],  # SUREBET: 0.992 < 1 ✅
            "deep_link": "https://www.betexplorer.com/football/germany/bundesliga/bayer-leverkusen-rb-leipzig/mock10/",
            "source": "BetExplorer",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    # Send to backend for ingestion
    success = send_data_to_backend(mock_events)
    
    if success:
        return {
            "status": "success",
            "message": f"Generated and ingested {len(mock_events)} mock events",
            "count": len(mock_events),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        return {
            "status": "error",
            "message": "Failed to send mock data to backend",
            "count": len(mock_events),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }


def _run_test_scrape_sync(url: str, strategy: str) -> Dict[str, Any]:
    """
    Run a single test scrape synchronously using the Playwright Sync API.
    This is executed in a worker thread to avoid the "Sync API inside asyncio loop" error.
    """
    # Validate strategy
    valid_strategies = ["betexplorer", "oddschecker", "oddsportal"]
    if strategy not in valid_strategies:
        return {
            "success": False,
            "error": f"Invalid strategy: {strategy}",
            "valid_strategies": valid_strategies,
            "count": 0,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    events: List[Dict[str, Any]] = []
    error_message: Optional[str] = None

    try:
        with sync_playwright() as p:
            logger.info("🌐 Launching browser for test scrape...")
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )

            try:
                page = browser.new_page()
                logger.info(f"🎯 Routing to {strategy} scraper...")
                events = route_scraper(page, url, strategy)
                page.close()
            except Exception as scrape_error:
                error_message = f"Scraping error: {str(scrape_error)}"
                logger.error(f"❌ {error_message}")
            finally:
                browser.close()
    except Exception as e:
        error_message = f"Browser launch error: {str(e)}"
        logger.error(f"❌ {error_message}")

    if error_message:
        return {
            "success": False,
            "error": error_message,
            "events": events,
            "count": len(events),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    else:
        # Provide a clearer message when no events are found
        msg = (
            f"Successfully scraped {len(events)} events"
            if events
            else "No events found. The target may be blocking scraping or selectors may need updates."
        )
        return {
            "success": True,
            "message": msg,
            "events": events,
            "count": len(events),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }


@app.post("/test-scrape")
def test_scrape_endpoint(request: TestScrapeRequest):
    """
    Test scraping a single URL without saving to database.
    Implemented as a synchronous route so FastAPI runs it in a dedicated OS thread,
    which allows using Playwright's Sync API safely without an active asyncio loop.
    """
    logger.info(
        f"🧪 Test scrape requested - URL: {request.url}, Strategy: {request.strategy}"
    )

    # Normalize strategy to lowercase for validation
    strategy = request.strategy.lower()

    # Run Playwright Sync API in a brand-new OS thread to avoid any running asyncio loop
    result_container: Dict[str, Any] = {}

    def _target():
        result_container["result"] = _run_test_scrape_sync(request.url, strategy)

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()

    return result_container.get("result", {
        "success": False,
        "error": "Unknown error running test scrape thread",
        "events": [],
        "count": 0,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


# Server entry point
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Surebet Scraper Service...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
