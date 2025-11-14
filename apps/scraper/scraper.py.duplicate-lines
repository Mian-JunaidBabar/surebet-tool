""""""

Surebet Tool - Web Scraper ServiceSurebet Tool - Web Scraper Service

====================================================================



This is a FastAPI service that scrapes betting odds from configured targets.This script dynamically scrapes betting odds from configured targets and sends the data to the backend API.

It can be triggered via API and runs scraping in the background.It extracts event information, odds, and deep links for the "Go to Bet" functionality.



Author: Surebet Tool TeamAuthor: Surebet Tool Team

Version: 3.0.0Version: 2.0.0

""""""



import requestsimport requests

import timeimport time

import reimport re

import loggingimport logging

from fastapi import FastAPI, BackgroundTasksfrom playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutErrorfrom typing import List, Dict, Any, Optional

from typing import List, Dict, Any, Optionalfrom urllib.parse import urljoin

from urllib.parse import urljoin

# Configure logging

# Configure logginglogging.basicConfig(

logging.basicConfig(    level=logging.INFO,

    level=logging.INFO,    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

)logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# Configuration Constants

# Configuration ConstantsBACKEND_API_URL = "http://backend:8000/api/v1/data/ingest"

BACKEND_API_URL = "http://backend:8000/api/v1/data/ingest"SCRAPER_TARGETS_URL = "http://backend:8000/api/v1/scraper/targets?active_only=true"

SCRAPER_TARGETS_URL = "http://backend:8000/api/v1/scraper/targets?active_only=true"BASE_DOMAIN = "https://www.betexplorer.com"

BASE_DOMAIN = "https://www.betexplorer.com"

# Scraping Configuration

# Scraping ConfigurationTIMEOUT_MS = 30000  # 30 seconds timeout

TIMEOUT_MS = 30000  # 30 seconds timeoutMAX_RETRIES = 3

MAX_RETRIES = 3RETRY_DELAY = 2  # seconds

RETRY_DELAY = 2  # seconds



# Create FastAPI appdef clean_text(text: str) -> str:

app = FastAPI(    """

    title="Surebet Scraper Service",    Clean and normalize text extracted from web elements.

    description="Scraping service for betting odds",    

    version="3.0.0"    Args:

)        text: Raw text to clean

        

    Returns:

def clean_text(text: str) -> str:        Cleaned text string

    """    """

    Clean and normalize text extracted from web elements.    if not text:

            return ""

    Args:    

        text: Raw text to clean    # Remove extra whitespace and normalize

            cleaned = re.sub(r'\s+', ' ', text.strip())

    Returns:    return cleaned

        Cleaned text string

    """

    if not text:def parse_odds(odds_text: str) -> Optional[float]:

        return ""    """

        Parse odds text and convert to float.

    # Remove extra whitespace and normalize    

    cleaned = re.sub(r'\s+', ' ', text.strip())    Args:

    return cleaned        odds_text: Raw odds text from website

        

    Returns:

def parse_odds(odds_text: str) -> Optional[float]:        Float odds value or None if parsing fails

    """    """

    Parse odds text and convert to float.    if not odds_text:

            return None

    Args:    

        odds_text: Raw odds text from website    try:

                # Clean the text and extract numeric value

    Returns:        cleaned = clean_text(odds_text)

        Float odds value or None if parsing fails        # Remove any non-numeric characters except decimal point

    """        numeric_text = re.sub(r'[^\d.]', '', cleaned)

    if not odds_text:        

        return None        if numeric_text:

                odds_value = float(numeric_text)

    try:            # Validate odds range (typical betting odds are between 1.01 and 100)

        # Clean the text and extract numeric value            if 1.0 <= odds_value <= 100.0:

        cleaned = clean_text(odds_text)                return odds_value

        # Remove any non-numeric characters except decimal point    except (ValueError, TypeError):

        numeric_text = re.sub(r'[^\d.]', '', cleaned)        pass

            

        if numeric_text:    return None

            odds_value = float(numeric_text)

            # Validate odds range (typical betting odds are between 1.01 and 100)

            if 1.0 <= odds_value <= 100.0:def generate_event_id(event_name: str) -> str:

                return odds_value    """

    except (ValueError, TypeError):    Generate a unique event ID from the event name.

        pass    

        Args:

    return None        event_name: The event name

        

    Returns:

def generate_event_id(event_name: str) -> str:        Unique event ID string

    """    """

    Generate a unique event ID from the event name.    # Create a simple hash-like ID from the event name

        cleaned_name = re.sub(r'[^\w\s-]', '', event_name.lower())

    Args:    event_id = re.sub(r'\s+', '-', cleaned_name.strip())

        event_name: The event name    

            # Add timestamp to ensure uniqueness

    Returns:    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp

        Unique event ID string    

    """    return f"{event_id}-{timestamp}"

    # Create a simple hash-like ID from the event name

    cleaned_name = re.sub(r'[^\w\s-]', '', event_name.lower())

    event_id = re.sub(r'\s+', '-', cleaned_name.strip())def extract_event_data(row_element, target_name: str) -> Optional[Dict[str, Any]]:

        """

    # Add timestamp to ensure uniqueness    Extract all data from a single table row element.

    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp    

        Args:

    return f"{event_id}-{timestamp}"        row_element: Playwright element representing a table row

        target_name: Name of the scraping target for logging and bookmaker field

        

def extract_event_data(row_element, target_name: str) -> Optional[Dict[str, Any]]:    Returns:

    """        Dictionary with extracted event data or None if extraction fails

    Extract all data from a single table row element.    """

        try:

    Args:        # Extract event name

        row_element: Playwright element representing a table row        participant_element = row_element.query_selector(".table-main__participant")

        target_name: Name of the scraping target for logging and bookmaker field        if not participant_element:

                    logger.warning("No participant element found in row")

    Returns:            return None

        Dictionary with extracted event data or None if extraction fails        

    """        event_name = clean_text(participant_element.text_content())

    try:        if not event_name:

        # Extract event name            logger.warning("Empty event name found")

        participant_element = row_element.query_selector(".table-main__participant")            return None

        if not participant_element:        

            logger.warning("No participant element found in row")        # Extract deep link URL

            return None        link_element = participant_element.query_selector("a")

                if not link_element:

        event_name = clean_text(participant_element.text_content())            logger.warning(f"No link found for event: {event_name}")

        if not event_name:            return None

            logger.warning("Empty event name found")        

            return None        relative_url = link_element.get_attribute("href")

                if not relative_url:

        # Extract deep link URL            logger.warning(f"No href attribute found for event: {event_name}")

        link_element = participant_element.query_selector("a")            return None

        if not link_element:        

            logger.warning(f"No link found for event: {event_name}")        # Create absolute URL

            return None        deep_link_url = urljoin(BASE_DOMAIN, relative_url)

                

        relative_url = link_element.get_attribute("href")        # Extract odds

        if not relative_url:        odds_elements = row_element.query_selector_all(".table-main__odds")

            logger.warning(f"No href attribute found for event: {event_name}")        if len(odds_elements) < 3:

            return None            logger.warning(f"Not enough odds found for event: {event_name} (found {len(odds_elements)})")

                    return None

        # Create absolute URL        

        deep_link_url = urljoin(BASE_DOMAIN, relative_url)        # Extract Home (1), Draw (X), Away (2) odds

                home_odds_text = odds_elements[0].text_content() if len(odds_elements) > 0 else ""

        # Extract odds        draw_odds_text = odds_elements[1].text_content() if len(odds_elements) > 1 else ""

        odds_elements = row_element.query_selector_all(".table-main__odds")        away_odds_text = odds_elements[2].text_content() if len(odds_elements) > 2 else ""

        if len(odds_elements) < 3:        

            logger.warning(f"Not enough odds found for event: {event_name} (found {len(odds_elements)})")        # Parse odds to float

            return None        home_odds = parse_odds(home_odds_text)

                draw_odds = parse_odds(draw_odds_text)

        # Extract Home (1), Draw (X), Away (2) odds        away_odds = parse_odds(away_odds_text)

        home_odds_text = odds_elements[0].text_content() if len(odds_elements) > 0 else ""        

        draw_odds_text = odds_elements[1].text_content() if len(odds_elements) > 1 else ""        # Validate that we have all three odds

        away_odds_text = odds_elements[2].text_content() if len(odds_elements) > 2 else ""        if None in [home_odds, draw_odds, away_odds]:

                    logger.warning(f"Invalid odds for event: {event_name}")

        # Parse odds to float            logger.warning(f"  Home: {home_odds_text} -> {home_odds}")

        home_odds = parse_odds(home_odds_text)            logger.warning(f"  Draw: {draw_odds_text} -> {draw_odds}")

        draw_odds = parse_odds(draw_odds_text)            logger.warning(f"  Away: {away_odds_text} -> {away_odds}")

        away_odds = parse_odds(away_odds_text)            return None

                

        # Validate that we have all three odds        # Generate unique event ID

        if None in [home_odds, draw_odds, away_odds]:        event_id = generate_event_id(event_name)

            logger.warning(f"Invalid odds for event: {event_name}")        

            logger.warning(f"  Home: {home_odds_text} -> {home_odds}")        # Structure data according to backend schema

            logger.warning(f"  Draw: {draw_odds_text} -> {draw_odds}")        event_data = {

            logger.warning(f"  Away: {away_odds_text} -> {away_odds}")            "event_id": event_id,

            return None            "event": event_name,

                    "sport": "Football",

        # Generate unique event ID            "outcomes": [

        event_id = generate_event_id(event_name)                {

                            "bookmaker": target_name,

        # Structure data according to backend schema                    "name": "Home Win",

        event_data = {                    "odds": home_odds,

            "event_id": event_id,                    "deep_link_url": deep_link_url

            "event": event_name,                },

            "sport": "Football",                {

            "outcomes": [                    "bookmaker": target_name,

                {                    "name": "Draw",

                    "bookmaker": target_name,                    "odds": draw_odds,

                    "name": "Home Win",                    "deep_link_url": deep_link_url

                    "odds": home_odds,                },

                    "deep_link_url": deep_link_url                {

                },                    "bookmaker": target_name,

                {                    "name": "Away Win",

                    "bookmaker": target_name,                    "odds": away_odds,

                    "name": "Draw",                    "deep_link_url": deep_link_url

                    "odds": draw_odds,                }

                    "deep_link_url": deep_link_url            ]

                },        }

                {        

                    "bookmaker": target_name,        logger.info(f"✅ Extracted: {event_name}")

                    "name": "Away Win",        logger.info(f"  Odds: {home_odds} | {draw_odds} | {away_odds}")

                    "odds": away_odds,        logger.info(f"  Link: {deep_link_url}")

                    "deep_link_url": deep_link_url        

                }        return event_data

            ]        

        }    except Exception as e:

                logger.error(f"Error extracting data from row: {str(e)}")

        logger.info(f"✅ Extracted: {event_name}")        return None

        logger.info(f"  Odds: {home_odds} | {draw_odds} | {away_odds}")

        logger.info(f"  Link: {deep_link_url}")

        def scrape_betting_data(target_url: str, target_name: str) -> List[Dict[str, Any]]:

        return event_data    """

            Main scraping function using Playwright for a specific target URL.

    except Exception as e:    

        logger.error(f"Error extracting data from row: {str(e)}")    Args:

        return None        target_url: The URL to scrape

        target_name: Name of the target for logging

    

def scrape_betting_data(target_url: str, target_name: str) -> List[Dict[str, Any]]:    Returns:

    """        List of structured event data dictionaries

    Main scraping function using Playwright for a specific target URL.    """

    Now includes smart navigation to find and click league links.    scraped_data = []

        

    Args:    logger.info(f"🚀 Starting scrape for: {target_name}")

        target_url: The URL to scrape    logger.info(f"🎯 Target URL: {target_url}")

        target_name: Name of the target for logging    

        with sync_playwright() as p:

    Returns:        browser = None

        List of structured event data dictionaries        try:

    """            logger.info("🌐 Launching browser...")

    scraped_data = []            browser = p.chromium.launch(headless=True)

                page = browser.new_page()

    logger.info(f"🚀 Starting scrape for: {target_name}")            

    logger.info(f"🎯 Target URL: {target_url}")            # Set user agent to avoid bot detection

                page.set_extra_http_headers({

    with sync_playwright() as p:                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

        browser = None            })

        try:            

            logger.info("🌐 Launching browser...")            logger.info(f"🔄 Navigating to {target_url}...")

            browser = p.chromium.launch(headless=True)            page.goto(target_url, wait_until="domcontentloaded")

            page = browser.new_page()            

                        logger.info("⏳ Waiting for odds table to load...")

            # Set user agent to avoid bot detection            try:

            page.set_extra_http_headers({                page.wait_for_selector(".table-main--leaguefixtures", timeout=TIMEOUT_MS)

                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"                logger.info("✅ Odds table loaded successfully")

            })            except PlaywrightTimeoutError:

                            logger.error("❌ Timeout waiting for odds table to load")

            logger.info(f"🔄 Navigating to {target_url}...")                return scraped_data

            page.goto(target_url, wait_until="domcontentloaded")            

                        # Give a moment for dynamic content to fully load

            # Smart navigation: Find and click a league link if we're on a sport homepage            time.sleep(2)

            logger.info("🔍 Looking for league links...")            

            time.sleep(2)  # Wait for page to fully load            logger.info("🔍 Finding match rows...")

                        match_rows = page.query_selector_all(".table-main__row")

            # Try to find a prominent league link            

            league_link = page.query_selector("a.list-events__item__title")            if not match_rows:

                            logger.warning("❌ No match rows found on the page")

            if league_link:                return scraped_data

                league_name = clean_text(league_link.text_content())            

                logger.info(f"📍 Found league: {league_name}")            logger.info(f"📊 Found {len(match_rows)} match rows to process")

                logger.info("🖱️  Clicking league link...")            

                            # Process each row

                # Click the league link            for idx, row in enumerate(match_rows, 1):

                league_link.click()                logger.info(f"[{idx}/{len(match_rows)}] Processing row...")

                                

                # Wait for navigation                event_data = extract_event_data(row, target_name)

                page.wait_for_load_state("domcontentloaded")                if event_data:

                logger.info(f"✅ Navigated to league page: {page.url}")                    scraped_data.append(event_data)

                                else:

                # Give page a moment to load                    logger.warning(f"Skipped row {idx} due to extraction failure")

                time.sleep(2)            

            else:            logger.info(f"🎉 Scraping completed! Successfully extracted {len(scraped_data)} events")

                logger.info("ℹ️  No league link found, assuming we're already on odds page")            

                    except PlaywrightTimeoutError as e:

            logger.info("⏳ Waiting for odds table to load...")            logger.error(f"Playwright timeout error: {str(e)}")

            try:        except Exception as e:

                page.wait_for_selector(".table-main--leaguefixtures", timeout=TIMEOUT_MS)            logger.error(f"Unexpected error during scraping: {str(e)}")

                logger.info("✅ Odds table loaded successfully")            

            except PlaywrightTimeoutError:        finally:

                logger.error("❌ Timeout waiting for odds table to load")            if browser:

                return scraped_data                logger.info("🔒 Closing browser...")

                            browser.close()

            # Give a moment for dynamic content to fully load    

            time.sleep(2)    return scraped_data

            

            logger.info("🔍 Finding match rows...")

            match_rows = page.query_selector_all(".table-main__row")def send_data_to_backend(scraped_data: List[Dict[str, Any]]) -> bool:

                """

            if not match_rows:    Send scraped data to the backend API.

                logger.warning("❌ No match rows found on the page")    

                return scraped_data    Args:

                    scraped_data: List of structured event dictionaries

            logger.info(f"📊 Found {len(match_rows)} match rows to process")        

                Returns:

            # Process each row        True if successful, False otherwise

            for idx, row in enumerate(match_rows, 1):    """

                logger.info(f"[{idx}/{len(match_rows)}] Processing row...")    if not scraped_data:

                        logger.warning("No data to send to backend")

                event_data = extract_event_data(row, target_name)        return False

                if event_data:    

                    scraped_data.append(event_data)    logger.info(f"📤 Sending {len(scraped_data)} events to backend...")

                else:    logger.info(f"🎯 Backend URL: {BACKEND_API_URL}")

                    logger.warning(f"Skipped row {idx} due to extraction failure")    

                for attempt in range(MAX_RETRIES):

            logger.info(f"🎉 Scraping completed! Successfully extracted {len(scraped_data)} events")        try:

                        response = requests.post(

        except PlaywrightTimeoutError as e:                BACKEND_API_URL,

            logger.error(f"Playwright timeout error: {str(e)}")                json=scraped_data,

        except Exception as e:                headers={

            logger.error(f"Unexpected error during scraping: {str(e)}")                    "Content-Type": "application/json",

                                "User-Agent": "Surebet-Scraper/2.0.0"

        finally:                },

            if browser:                timeout=30

                logger.info("🔒 Closing browser...")            )

                browser.close()            

                if response.status_code == 200:

    return scraped_data                response_data = response.json()

                logger.info("✅ Data sent successfully!")

                logger.info(f"📊 Backend response: {response_data.get('message', 'No message')}")

def send_data_to_backend(scraped_data: List[Dict[str, Any]]) -> bool:                logger.info(f"📈 Events processed: {response_data.get('events_processed', 'Unknown')}")

    """                logger.info(f"🔄 Status: {response_data.get('status', 'Unknown')}")

    Send scraped data to the backend API.                return True

                else:

    Args:                logger.error(f"Backend returned error status: {response.status_code}")

        scraped_data: List of structured event dictionaries                logger.error(f"Response: {response.text}")

                        

    Returns:        except requests.exceptions.Timeout:

        True if successful, False otherwise            logger.warning(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")

    """        except requests.exceptions.ConnectionError:

    if not scraped_data:            logger.error(f"Connection error (attempt {attempt + 1}/{MAX_RETRIES})")

        logger.warning("No data to send to backend")            logger.error("Make sure the backend service is running!")

        return False        except requests.exceptions.RequestException as e:

                logger.error(f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")

    logger.info(f"📤 Sending {len(scraped_data)} events to backend...")        except Exception as e:

    logger.info(f"🎯 Backend URL: {BACKEND_API_URL}")            logger.error(f"Unexpected error sending data (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")

            

    for attempt in range(MAX_RETRIES):        if attempt < MAX_RETRIES - 1:

        try:            logger.info(f"⏳ Retrying in {RETRY_DELAY} seconds...")

            response = requests.post(            time.sleep(RETRY_DELAY)

                BACKEND_API_URL,    

                json=scraped_data,    logger.error(f"Failed to send data after {MAX_RETRIES} attempts")

                headers={    return False

                    "Content-Type": "application/json",

                    "User-Agent": "Surebet-Scraper/3.0.0"

                },def fetch_scraper_targets() -> List[Dict[str, Any]]:

                timeout=30    """

            )    Fetch active scraper targets from the backend API.

                

            if response.status_code == 200:    Returns:

                response_data = response.json()        List of active scraper target dictionaries with 'url', 'name', and 'is_active' fields

                logger.info("✅ Data sent successfully!")    """

                logger.info(f"📊 Backend response: {response_data.get('message', 'No message')}")    logger.info(f"📥 Fetching scraper targets from backend...")

                logger.info(f"📈 Events processed: {response_data.get('events_processed', 'Unknown')}")    logger.info(f"🎯 URL: {SCRAPER_TARGETS_URL}")

                logger.info(f"🔄 Status: {response_data.get('status', 'Unknown')}")    

                return True    for attempt in range(MAX_RETRIES):

            else:        try:

                logger.error(f"Backend returned error status: {response.status_code}")            response = requests.get(

                logger.error(f"Response: {response.text}")                SCRAPER_TARGETS_URL,

                                headers={

        except requests.exceptions.Timeout:                    "User-Agent": "Surebet-Scraper/2.0.0"

            logger.warning(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")                },

        except requests.exceptions.ConnectionError:                timeout=15

            logger.error(f"Connection error (attempt {attempt + 1}/{MAX_RETRIES})")            )

            logger.error("Make sure the backend service is running!")            

        except requests.exceptions.RequestException as e:            if response.status_code == 200:

            logger.error(f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")                data = response.json()

        except Exception as e:                targets = data.get('targets', [])

            logger.error(f"Unexpected error sending data (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")                logger.info(f"✅ Fetched {len(targets)} active scraper target(s)")

                        

        if attempt < MAX_RETRIES - 1:                for target in targets:

            logger.info(f"⏳ Retrying in {RETRY_DELAY} seconds...")                    logger.info(f"  - {target.get('name')}: {target.get('url')}")

            time.sleep(RETRY_DELAY)                

                    return targets

    logger.error(f"Failed to send data after {MAX_RETRIES} attempts")            else:

    return False                logger.error(f"Backend returned error status: {response.status_code}")

                logger.error(f"Response: {response.text}")

                

def fetch_scraper_targets() -> List[Dict[str, Any]]:        except requests.exceptions.Timeout:

    """            logger.warning(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")

    Fetch active scraper targets from the backend API.        except requests.exceptions.ConnectionError:

                logger.error(f"Connection error (attempt {attempt + 1}/{MAX_RETRIES})")

    Returns:            logger.error("Make sure the backend service is running!")

        List of active scraper target dictionaries with 'url', 'name', and 'is_active' fields        except requests.exceptions.RequestException as e:

    """            logger.error(f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")

    logger.info(f"📥 Fetching scraper targets from backend...")        except Exception as e:

    logger.info(f"🎯 URL: {SCRAPER_TARGETS_URL}")            logger.error(f"Unexpected error fetching targets (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")

            

    for attempt in range(MAX_RETRIES):        if attempt < MAX_RETRIES - 1:

        try:            logger.info(f"⏳ Retrying in {RETRY_DELAY} seconds...")

            response = requests.get(            time.sleep(RETRY_DELAY)

                SCRAPER_TARGETS_URL,    

                headers={    logger.error(f"Failed to fetch targets after {MAX_RETRIES} attempts")

                    "User-Agent": "Surebet-Scraper/3.0.0"    return []

                },

                timeout=15

            )def main():

                """

            if response.status_code == 200:    Main function that orchestrates the scraping and data sending process.

                data = response.json()    Fetches active targets from backend and scrapes each one.

                targets = data.get('targets', [])    """

                logger.info(f"✅ Fetched {len(targets)} active scraper target(s)")    logger.info("=" * 60)

                    logger.info("🎰 SUREBET TOOL - WEB SCRAPER")

                for target in targets:    logger.info("=" * 60)

                    logger.info(f"  - {target.get('name')}: {target.get('url')}")    logger.info(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

                

                return targets    try:

            else:        # Step 1: Fetch active scraper targets from backend

                logger.error(f"Backend returned error status: {response.status_code}")        targets = fetch_scraper_targets()

                logger.error(f"Response: {response.text}")

                        if not targets:

        except requests.exceptions.Timeout:            logger.warning("❌ No active scraper targets found. Exiting...")

            logger.warning(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")            return

        except requests.exceptions.ConnectionError:

            logger.error(f"Connection error (attempt {attempt + 1}/{MAX_RETRIES})")        # Step 2: Loop through each target and scrape data

            logger.error("Make sure the backend service is running!")        all_scraped_data = []

        except requests.exceptions.RequestException as e:

            logger.error(f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")        for idx, target in enumerate(targets, 1):

        except Exception as e:            target_url = target.get('url')

            logger.error(f"Unexpected error fetching targets (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")            target_name = target.get('name', 'Unknown')

        

        if attempt < MAX_RETRIES - 1:            if not target_url:

            logger.info(f"⏳ Retrying in {RETRY_DELAY} seconds...")                logger.warning(f"⚠️  Skipping target {idx}: Missing URL")

            time.sleep(RETRY_DELAY)                continue

    

    logger.error(f"Failed to fetch targets after {MAX_RETRIES} attempts")            logger.info(f"\n{'=' * 60}")

    return []            logger.info(f"📍 Processing target {idx}/{len(targets)}: {target_name}")

            logger.info(f"{'=' * 60}")



def run_the_scrape():            # Scrape data from this target

    """            scraped_data = scrape_betting_data(target_url, target_name)

    Main scraping logic that orchestrates fetching targets and scraping data.

    This runs in the background when triggered via the API.            if scraped_data:

    """                logger.info(f"✅ Successfully scraped {len(scraped_data)} events from {target_name}")

    logger.info("=" * 60)                all_scraped_data.extend(scraped_data)

    logger.info("🎰 SUREBET TOOL - WEB SCRAPER")            else:

    logger.info("=" * 60)                logger.warning(f"⚠️  No data scraped from {target_name}")

    logger.info(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

                # Add a small delay between targets to be respectful

    try:            if idx < len(targets):

        # Step 1: Fetch active scraper targets from backend                logger.info("⏳ Waiting 3 seconds before next target...")

        targets = fetch_scraper_targets()                time.sleep(3)

        

        if not targets:        # Step 3: Send all scraped data to backend

            logger.warning("❌ No active scraper targets found. Exiting...")        if not all_scraped_data:

            return            logger.warning("\n❌ No data was scraped from any target. Exiting...")

                    return

        # Step 2: Loop through each target and scrape data

        all_scraped_data = []        logger.info(f"\n{'=' * 60}")

                logger.info(f"📊 Total events scraped: {len(all_scraped_data)}")

        for idx, target in enumerate(targets, 1):        logger.info(f"{'=' * 60}")

            target_url = target.get('url')

            target_name = target.get('name', 'Unknown')        success = send_data_to_backend(all_scraped_data)

            

            if not target_url:        if success:

                logger.warning(f"⚠️  Skipping target {idx}: Missing URL")            logger.info("\n🎉 Scraper completed successfully!")

                continue        else:

                        logger.error("\n❌ Scraper completed with errors")

            logger.info(f"\n{'=' * 60}")

            logger.info(f"📍 Processing target {idx}/{len(targets)}: {target_name}")    except KeyboardInterrupt:

            logger.info(f"{'=' * 60}")        logger.warning("\n🛑 Scraper interrupted by user")

                except Exception as e:

            # Scrape data from this target        logger.error(f"\n💥 Fatal error: {str(e)}", exc_info=True)

            scraped_data = scrape_betting_data(target_url, target_name)    finally:

                    logger.info(f"⏰ Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

            if scraped_data:        logger.info("=" * 60)

                logger.info(f"✅ Successfully scraped {len(scraped_data)} events from {target_name}")

                all_scraped_data.extend(scraped_data)

            else:if __name__ == "__main__":

                logger.warning(f"⚠️  No data scraped from {target_name}")    main()
            
            # Add a small delay between targets to be respectful
            if idx < len(targets):
                logger.info("⏳ Waiting 3 seconds before next target...")
                time.sleep(3)
        
        # Step 3: Send all scraped data to backend
        if not all_scraped_data:
            logger.warning("\n❌ No data was scraped from any target. Exiting...")
            return
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"📊 Total events scraped: {len(all_scraped_data)}")
        logger.info(f"{'=' * 60}")
        
        success = send_data_to_backend(all_scraped_data)
        
        if success:
            logger.info("\n🎉 Scraper completed successfully!")
        else:
            logger.error("\n❌ Scraper completed with errors")
            
    except KeyboardInterrupt:
        logger.warning("\n🛑 Scraper interrupted by user")
    except Exception as e:
        logger.error(f"\n💥 Fatal error: {str(e)}", exc_info=True)
    finally:
        logger.info(f"⏰ Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)


# ============================================================================
# FastAPI Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint to verify service is running"""
    return {
        "message": "Surebet Scraper Service is running",
        "version": "3.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "scraper",
        "version": "3.0.0"
    }


@app.post("/run-scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """
    Trigger the scraper to run in the background.
    
    This endpoint immediately returns a response and runs the scraping
    in a background task to avoid blocking.
    
    Returns:
        Success message indicating scrape has started
    """
    logger.info("🔄 Scrape triggered via API")
    
    # Add the scraping task to background tasks
    background_tasks.add_task(run_the_scrape)
    
    return {
        "message": "Scrape run started in the background.",
        "status": "running"
    }


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting scraper service on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
