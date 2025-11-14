"""
The Odds API Service Module

This module handles all interactions with The Odds API (the-odds-api.com).
It fetches live odds data for upcoming sporting events.
"""

import os
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# The Odds API base URL
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"


def fetch_live_odds() -> requests.Response:
    """
    Fetch live odds from The Odds API.
    
    Makes a GET request to the /sports/upcoming/odds/ endpoint with the following parameters:
    - apiKey: The API key from environment variables
    - regions: "eu" (European bookmakers)
    - markets: "h2h" (head-to-head, for win/loss/draw)
    - oddsFormat: "decimal"
    
    Returns:
        requests.Response: The full response object containing both JSON data and headers
                          (including x-requests-used and x-requests-remaining)
    
    Raises:
        requests.exceptions.RequestException: If the API request fails
        ValueError: If the API key is not configured
    """
    # Get the API key from environment variables
    api_key = os.getenv("ODDS_API_KEY")
    
    if not api_key:
        logger.error("❌ ODDS_API_KEY not found in environment variables")
        raise ValueError("ODDS_API_KEY environment variable is not set")
    
    # Construct the endpoint URL
    endpoint = f"{ODDS_API_BASE_URL}/sports/upcoming/odds/"
    
    # Define query parameters according to API documentation
    params = {
        "apiKey": api_key,
        "regions": "eu",  # European bookmakers
        "markets": "h2h",  # Head-to-head (win/loss/draw)
        "oddsFormat": "decimal"  # Decimal odds format
    }
    
    try:
        logger.info(f"🔄 Fetching live odds from The Odds API...")
        logger.info(f"📍 Endpoint: {endpoint}")
        logger.info(f"⚙️  Parameters: regions={params['regions']}, markets={params['markets']}, oddsFormat={params['oddsFormat']}")
        
        # Make the GET request
        response = requests.get(endpoint, params=params, timeout=30)
        
        # Raise an exception for HTTP error status codes
        response.raise_for_status()
        
        # Log usage information from headers
        used = response.headers.get('x-requests-used', 'N/A')
        remaining = response.headers.get('x-requests-remaining', 'N/A')
        logger.info(f"✅ Successfully fetched odds data")
        logger.info(f"📊 API Usage - Used: {used}, Remaining: {remaining}")
        
        # Return the full response object (caller needs both JSON and headers)
        return response
        
    except requests.exceptions.Timeout:
        logger.error("❌ Request to The Odds API timed out")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection error while fetching odds: {str(e)}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP error from The Odds API: {e.response.status_code} - {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching odds from The Odds API: {str(e)}")
        raise
