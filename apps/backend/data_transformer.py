"""
Data Transformer Module

This module transforms data from The Odds API format into our internal database schema.
It maps the API's structure to our EventCreate and OutcomeCreate Pydantic models.
"""

from typing import List
import logging
import schemas

logger = logging.getLogger(__name__)


def transform_odds_api_data(api_data: list) -> List[schemas.EventCreate]:
    """
    Transform The Odds API data format into our internal schema.
    
    The Odds API returns data in this structure:
    [
        {
            "id": "event_id",
            "sport_title": "Soccer",
            "home_team": "Team A",
            "away_team": "Team B",
            "bookmakers": [
                {
                    "key": "bet365",
                    "title": "Bet365",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Team A", "price": 2.10},
                                {"name": "Draw", "price": 3.40},
                                {"name": "Team B", "price": 4.20}
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    
    We transform this into our EventCreate schema with nested OutcomeCreate objects.
    
    Args:
        api_data: List of event dictionaries from The Odds API
        
    Returns:
        List[schemas.EventCreate]: Transformed events ready for database insertion
    """
    transformed_events = []
    
    logger.info(f"🔄 Transforming {len(api_data)} events from The Odds API...")
    
    for api_event in api_data:
        try:
            # Extract basic event information
            event_id = api_event.get('id', 'unknown')
            sport_title = api_event.get('sport_title', 'Unknown Sport')
            home_team = api_event.get('home_team', 'Home')
            away_team = api_event.get('away_team', 'Away')
            
            # Create the event name in our format
            event_name = f"{home_team} vs {away_team}"
            
            # Collect all outcomes from all bookmakers
            outcomes = []
            bookmakers = api_event.get('bookmakers', [])
            
            logger.debug(f"  Processing event: {event_name} (ID: {event_id})")
            logger.debug(f"  Found {len(bookmakers)} bookmakers for this event")
            
            for bookmaker in bookmakers:
                bookmaker_key = bookmaker.get('key', 'unknown')
                bookmaker_title = bookmaker.get('title', 'Unknown Bookmaker')
                markets = bookmaker.get('markets', [])
                
                # Process each market (we're interested in 'h2h' - head to head)
                for market in markets:
                    market_key = market.get('key', '')
                    
                    # Only process head-to-head markets
                    if market_key == 'h2h':
                        market_outcomes = market.get('outcomes', [])
                        
                        # Transform each outcome
                        for outcome_data in market_outcomes:
                            outcome_name = outcome_data.get('name', 'Unknown')
                            outcome_odds = outcome_data.get('price', 0.0)
                            
                            # Create the OutcomeCreate object
                            outcome = schemas.OutcomeCreate(
                                bookmaker=bookmaker_title,
                                name=outcome_name,
                                odds=float(outcome_odds),
                                deep_link_url=f"https://{bookmaker_key}.com"
                            )
                            outcomes.append(outcome)
            
            # Only create the event if we have outcomes
            if outcomes:
                logger.debug(f"  Created {len(outcomes)} outcomes for event {event_name}")
                
                # Create the EventCreate object
                event = schemas.EventCreate(
                    event_id=event_id,
                    sport=sport_title,
                    event=event_name,
                    outcomes=outcomes
                )
                transformed_events.append(event)
            else:
                logger.warning(f"  ⚠️  Skipping event {event_name} - no outcomes found")
                
        except Exception as e:
            logger.error(f"❌ Error transforming event {api_event.get('id', 'unknown')}: {str(e)}")
            # Continue processing other events even if one fails
            continue
    
    logger.info(f"✅ Successfully transformed {len(transformed_events)} events")
    return transformed_events
