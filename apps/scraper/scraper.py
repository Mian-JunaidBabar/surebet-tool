"""
Surebet Tool - Web Scraper Service
==================================

This script scrapes betting odds from BetExplorer and sends the data to the backend API.
It extracts event information, odds, and deep links for the "Go to Bet" functionality.

Author: Surebet Tool Team
Version: 1.0.0
"""

import requests
import time
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin


# Configuration Constants
TARGET_URL = "https://www.betexplorer.com/football/england/premier-league/"
BACKEND_API_URL = "http://backend:8000/api/v1/data/ingest"
BASE_DOMAIN = "https://www.betexplorer.com"

# Scraping Configuration
TIMEOUT_MS = 30000  # 30 seconds timeout
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


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
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned


def parse_odds(odds_text: str) -> Optional[float]:
    """
    Parse odds text and convert to float.
    
    Args:
        odds_text: Raw odds text from website
        
    Returns:
        Float odds value or None if parsing fails
    """
    if not odds_text:
        return None
    
    try:
        # Clean the text and extract numeric value
        cleaned = clean_text(odds_text)
        # Remove any non-numeric characters except decimal point
        numeric_text = re.sub(r'[^\d.]', '', cleaned)
        
        if numeric_text:
            odds_value = float(numeric_text)
            # Validate odds range (typical betting odds are between 1.01 and 100)
            if 1.0 <= odds_value <= 100.0:
                return odds_value
    except (ValueError, TypeError):
        pass
    
    return None


def generate_event_id(event_name: str) -> str:
    """
    Generate a unique event ID from the event name.
    
    Args:
        event_name: The event name
        
    Returns:
        Unique event ID string
    """
    # Create a simple hash-like ID from the event name
    cleaned_name = re.sub(r'[^\w\s-]', '', event_name.lower())
    event_id = re.sub(r'\s+', '-', cleaned_name.strip())
    
    # Add timestamp to ensure uniqueness
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    
    return f"{event_id}-{timestamp}"


def extract_event_data(row_element) -> Optional[Dict[str, Any]]:
    """
    Extract all data from a single table row element.
    
    Args:
        row_element: Playwright element representing a table row
        
    Returns:
        Dictionary with extracted event data or None if extraction fails
    """
    try:
        # Extract event name
        participant_element = row_element.query_selector(".table-main__participant")
        if not participant_element:
            print("⚠️  No participant element found in row")
            return None
        
        event_name = clean_text(participant_element.text_content())
        if not event_name:
            print("⚠️  Empty event name found")
            return None
        
        # Extract deep link URL
        link_element = participant_element.query_selector("a")
        if not link_element:
            print(f"⚠️  No link found for event: {event_name}")
            return None
        
        relative_url = link_element.get_attribute("href")
        if not relative_url:
            print(f"⚠️  No href attribute found for event: {event_name}")
            return None
        
        # Create absolute URL
        deep_link_url = urljoin(BASE_DOMAIN, relative_url)
        
        # Extract odds
        odds_elements = row_element.query_selector_all(".table-main__odds")
        if len(odds_elements) < 3:
            print(f"⚠️  Not enough odds found for event: {event_name} (found {len(odds_elements)})")
            return None
        
        # Extract Home (1), Draw (X), Away (2) odds
        home_odds_text = odds_elements[0].text_content() if len(odds_elements) > 0 else ""
        draw_odds_text = odds_elements[1].text_content() if len(odds_elements) > 1 else ""
        away_odds_text = odds_elements[2].text_content() if len(odds_elements) > 2 else ""
        
        # Parse odds to float
        home_odds = parse_odds(home_odds_text)
        draw_odds = parse_odds(draw_odds_text)
        away_odds = parse_odds(away_odds_text)
        
        # Validate that we have all three odds
        if None in [home_odds, draw_odds, away_odds]:
            print(f"⚠️  Invalid odds for event: {event_name}")
            print(f"    Home: {home_odds_text} -> {home_odds}")
            print(f"    Draw: {draw_odds_text} -> {draw_odds}")
            print(f"    Away: {away_odds_text} -> {away_odds}")
            return None
        
        # Generate unique event ID
        event_id = generate_event_id(event_name)
        
        # Structure data according to backend schema
        event_data = {
            "event_id": event_id,
            "event": event_name,
            "sport": "Football",
            "outcomes": [
                {
                    "bookmaker": "BetExplorerAvg",
                    "name": "Home Win",
                    "odds": home_odds,
                    "deep_link_url": deep_link_url
                },
                {
                    "bookmaker": "BetExplorerAvg",
                    "name": "Draw",
                    "odds": draw_odds,
                    "deep_link_url": deep_link_url
                },
                {
                    "bookmaker": "BetExplorerAvg",
                    "name": "Away Win",
                    "odds": away_odds,
                    "deep_link_url": deep_link_url
                }
            ]
        }
        
        print(f"✅ Extracted: {event_name}")
        print(f"    Odds: {home_odds} | {draw_odds} | {away_odds}")
        print(f"    Link: {deep_link_url}")
        
        return event_data
        
    except Exception as e:
        print(f"❌ Error extracting data from row: {str(e)}")
        return None


def scrape_betting_data() -> List[Dict[str, Any]]:
    """
    Main scraping function using Playwright.
    
    Returns:
        List of structured event data dictionaries
    """
    scraped_data = []
    
    print("🚀 Starting web scraper...")
    print(f"🎯 Target URL: {TARGET_URL}")
    
    with sync_playwright() as p:
        browser = None
        try:
            print("🌐 Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set user agent to avoid bot detection
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            
            print(f"🔄 Navigating to {TARGET_URL}...")
            page.goto(TARGET_URL, wait_until="domcontentloaded")
            
            print("⏳ Waiting for odds table to load...")
            try:
                page.wait_for_selector(".table-main--leaguefixtures", timeout=TIMEOUT_MS)
                print("✅ Odds table loaded successfully")
            except PlaywrightTimeoutError:
                print("❌ Timeout waiting for odds table to load")
                return scraped_data
            
            # Give a moment for dynamic content to fully load
            time.sleep(2)
            
            print("🔍 Finding match rows...")
            match_rows = page.query_selector_all(".table-main__row")
            
            if not match_rows:
                print("❌ No match rows found on the page")
                return scraped_data
            
            print(f"📊 Found {len(match_rows)} match rows to process")
            
            # Process each row
            for idx, row in enumerate(match_rows, 1):
                print(f"\n[{idx}/{len(match_rows)}] Processing row...")
                
                event_data = extract_event_data(row)
                if event_data:
                    scraped_data.append(event_data)
                else:
                    print(f"⚠️  Skipped row {idx} due to extraction failure")
            
            print(f"\n🎉 Scraping completed! Successfully extracted {len(scraped_data)} events")
            
        except PlaywrightTimeoutError as e:
            print(f"❌ Playwright timeout error: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error during scraping: {str(e)}")
            
        finally:
            if browser:
                print("🔒 Closing browser...")
                browser.close()
    
    return scraped_data


def send_data_to_backend(scraped_data: List[Dict[str, Any]]) -> bool:
    """
    Send scraped data to the backend API.
    
    Args:
        scraped_data: List of structured event dictionaries
        
    Returns:
        True if successful, False otherwise
    """
    if not scraped_data:
        print("⚠️  No data to send to backend")
        return False
    
    print(f"\n📤 Sending {len(scraped_data)} events to backend...")
    print(f"🎯 Backend URL: {BACKEND_API_URL}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                BACKEND_API_URL,
                json=scraped_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Surebet-Scraper/1.0.0"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ Data sent successfully!")
                print(f"📊 Backend response: {response_data.get('message', 'No message')}")
                print(f"📈 Events processed: {response_data.get('events_processed', 'Unknown')}")
                print(f"🔄 Status: {response_data.get('status', 'Unknown')}")
                return True
            else:
                print(f"❌ Backend returned error status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection error (attempt {attempt + 1}/{MAX_RETRIES})")
            print("    Make sure the backend service is running!")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error sending data (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    
    print(f"❌ Failed to send data after {MAX_RETRIES} attempts")
    return False


def main():
    """
    Main function that orchestrates the scraping and data sending process.
    """
    print("=" * 60)
    print("🎰 SUREBET TOOL - WEB SCRAPER")
    print("=" * 60)
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Scrape data from the website
        scraped_data = scrape_betting_data()
        
        if not scraped_data:
            print("\n❌ No data was scraped. Exiting...")
            return
        
        # Step 2: Send data to backend
        success = send_data_to_backend(scraped_data)
        
        if success:
            print("\n🎉 Scraper completed successfully!")
        else:
            print("\n❌ Scraper completed with errors")
            
    except KeyboardInterrupt:
        print("\n🛑 Scraper interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
    finally:
        print(f"⏰ Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)


if __name__ == "__main__":
    main()