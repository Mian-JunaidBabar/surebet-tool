from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from pydantic import BaseModel
import socketio
import logging
import requests

# Import our new modules for The Odds API
import odds_api_service
import data_transformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
import models
import schemas
import crud
from database import SessionLocal, engine, get_db


# Pydantic model for test scrape requests
class TestScrapeRequest(BaseModel):
    """Request model for testing scraper without database saves"""
    url: str
    strategy: str  # "betexplorer", "oddschecker", or "oddsportal"


# Create database tables
models.Base.metadata.create_all(bind=engine)

# Database seeding - Add default scraper target if none exist
logger.info("🌱 Checking for default data...")
db = SessionLocal()
try:
    # Check if any scraper targets exist
    existing_targets = db.query(models.ScraperTarget).first()

    if existing_targets is None:
        logger.info("📍 No scraper targets found. Creating default targets...")

        default_targets = [
            {"name": "BetExplorer - Premier League", "url": "https://www.betexplorer.com/football/england/premier-league/", "is_active": True},
            {"name": "BetExplorer - NBA", "url": "https://www.betexplorer.com/basketball/usa/nba/", "is_active": True},
            {"name": "BetExplorer - NHL", "url": "https://www.betexplorer.com/hockey/usa/nhl/", "is_active": True},
            {"name": "Oddschecker - Football", "url": "https://www.oddschecker.com/football", "is_active": True},
            {"name": "Oddschecker - Horse Racing", "url": "https://www.oddschecker.com/horse-racing", "is_active": True},
            {"name": "Oddsportal - Germany Bundesliga", "url": "https://www.oddsportal.com/football/germany/bundesliga/", "is_active": True},
            {"name": "Oddsportal - Tennis ATP", "url": "https://www.oddsportal.com/tennis/atp-singles/", "is_active": True},
        ]

        for target in default_targets:
            scraper_target = models.ScraperTarget(**target)
            db.add(scraper_target)
            logger.info(f"✅ Created default scraper target: {scraper_target.name}")

        db.commit()
        logger.info(f"✅ Created {len(default_targets)} default scraper targets")
        # Seed default global settings
        if db.query(models.Setting).filter(models.Setting.key == "raptor_mini_enabled").first() is None:
            db.add(models.Setting(key="raptor_mini_enabled", value="true"))
            logger.info("✅ Seeded default setting: raptor_mini_enabled=true")
            db.commit()
    else:
        logger.info("✅ Scraper targets already exist, skipping seeding")
        
except Exception as e:
    logger.error(f"❌ Error during database seeding: {str(e)}")
    db.rollback()
finally:
    db.close()
    logger.info("🌱 Database seeding check complete")

# Initialize Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Allow all origins
    logger=True,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    allow_upgrades=True,
    cookie=None
)

# Initialize FastAPI application
app = FastAPI(
    title="Surebet Tool API",
    description="Complete API for ingesting scraped betting data and serving surebet opportunities with real-time updates",
    version="2.0.0"
)

# Configure CORS before mounting Socket.IO
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO app at /socket.io path
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=app,
    socketio_path='socket.io'
)


@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {
        "message": "Surebet Tool API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


def calculate_surebet_profit(outcomes: List[models.Outcome]) -> tuple[bool, float, float]:
    """
    Calculate if an event is a surebet and its profit percentage.
    
    For a surebet, we need to find the BEST odds for each unique outcome type
    (e.g., "Home Win", "Draw", "Away Win") across all bookmakers.
    
    Args:
        outcomes: List of outcome models
        
    Returns:
        Tuple of (is_surebet, profit_percentage, total_inverse_odds)
    """
    if len(outcomes) < 2:
        return False, 0.0, 0.0
    
    # Group outcomes by outcome name (e.g., "Home Win", "Draw", "Away Win")
    # and find the BEST (highest) odds for each outcome type
    best_odds_per_outcome = {}
    
    for outcome in outcomes:
        outcome_name = outcome.name
        current_odds = outcome.odds
        
        if outcome_name not in best_odds_per_outcome:
            best_odds_per_outcome[outcome_name] = current_odds
        else:
            # Keep the highest odds (best for bettor)
            best_odds_per_outcome[outcome_name] = max(best_odds_per_outcome[outcome_name], current_odds)
    
    # Calculate sum of inverse odds using BEST odds for each outcome type
    total_inverse_odds = sum(1/odds for odds in best_odds_per_outcome.values())
    
    # If sum < 1, it's a surebet (arbitrage opportunity)
    is_surebet = total_inverse_odds < 1.0
    
    # Calculate profit percentage
    profit_percentage = (1 - total_inverse_odds) * 100 if is_surebet else 0.0
    
    return is_surebet, profit_percentage, total_inverse_odds


@app.post("/api/v1/data/ingest", response_model=schemas.IngestionResponse)
async def ingest_data(events: List[schemas.EventCreate], db: Session = Depends(get_db)):
    """
    Ingest scraped betting data from the scraper service.
    
    This endpoint receives betting events with outcomes and stores/updates them in the database.
    If an event already exists (same event_id), it replaces all outcomes with fresh data.
    
    Args:
        events: List of EventCreate objects containing betting data
        db: Database session dependency
        
    Returns:
        IngestionResponse with success message and event count
    """
    if not events:
        raise HTTPException(status_code=400, detail="No events provided")
    
    # Log receipt of data
    event_count = len(events)
    logger.info(f"📥 Received {event_count} events from scraper")
    
    processed_count = 0
    errors = []
    
    # Process each event
    for idx, event in enumerate(events, 1):
        try:
            logger.info(f"  [{idx}] Processing: {event.event}")
            logger.debug(f"      Sport: {event.sport}")
            logger.debug(f"      Event ID: {event.event_id}")
            logger.debug(f"      Outcomes: {len(event.outcomes)}")
            
            # Log each outcome for the event
            for outcome in event.outcomes:
                logger.debug(f"        - {outcome.name}: {outcome.odds} ({outcome.bookmaker})")
            
            # Upsert the event (create or update with fresh outcomes)
            db_event = crud.upsert_event(db, event)
            processed_count += 1
            
        except SQLAlchemyError as e:
            error_msg = f"Database error for event {event.event_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error for event {event.event_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
    
    logger.info(f"✅ Successfully processed {processed_count}/{event_count} events")
    
    if errors:
        logger.warning(f"⚠️  Encountered {len(errors)} errors:")
        for error in errors:
            logger.warning(f"    - {error}")
    
    # Calculate and emit surebets via WebSocket after successful ingestion
    try:
        events_db = crud.get_events_with_multiple_outcomes(db)
        surebets = []
        
        for event_db in events_db:
            is_surebet, profit_percentage, total_inverse_odds = calculate_surebet_profit(event_db.outcomes)
            
            if is_surebet:
                surebet_event = schemas.SurebetEvent(
                    id=event_db.id,
                    event_id=event_db.event_id,
                    event=event_db.event,
                    sport=event_db.sport,
                    outcomes=[
                        schemas.Outcome(
                            id=outcome.id,
                            event_id=outcome.event_id,
                            bookmaker=outcome.bookmaker,
                            name=outcome.name,
                            odds=outcome.odds,
                            deep_link_url=outcome.deep_link_url
                        )
                        for outcome in event_db.outcomes
                    ],
                    profit_percentage=profit_percentage,
                    total_inverse_odds=total_inverse_odds
                )
                surebets.append(surebet_event)
        
        # Emit to all connected WebSocket clients
        if surebets:
            await emit_new_surebets(surebets)
            logger.info(f"📡 Emitted {len(surebets)} surebets to WebSocket clients")
        
    except Exception as e:
        logger.error(f"Error calculating/emitting surebets: {str(e)}")
    
    # Return success response
    return schemas.IngestionResponse(
        message=f"Successfully processed {processed_count}/{event_count} events.",
        events_processed=processed_count,
        status="success" if processed_count == event_count else "partial_success"
    )


@app.get("/api/v1/surebets", response_model=schemas.SurebetsResponse)
async def get_surebets(db: Session = Depends(get_db)):
    """
    Get all surebet opportunities from the database.
    
    This endpoint fetches all events with 2+ outcomes, calculates which ones are surebets,
    and returns them with profit percentages sorted by highest profit first.
    
    Args:
        db: Database session dependency
        
    Returns:
        SurebetsResponse with list of surebet events and metadata
    """
    try:
        # Get all events with multiple outcomes (potential surebets)
        events = crud.get_events_with_multiple_outcomes(db)
        
        surebets = []
        
        for event in events:
            # Calculate if it's a surebet and its profit
            is_surebet, profit_percentage, total_inverse_odds = calculate_surebet_profit(event.outcomes)
            
            if is_surebet:
                # Create surebet event with profit calculation
                surebet_event = schemas.SurebetEvent(
                    id=event.id,
                    event_id=event.event_id,
                    event=event.event,
                    sport=event.sport,
                    outcomes=[
                        schemas.Outcome(
                            id=outcome.id,
                            event_id=outcome.event_id,
                            bookmaker=outcome.bookmaker,
                            name=outcome.name,
                            odds=outcome.odds,
                            deep_link_url=outcome.deep_link_url
                        )
                        for outcome in event.outcomes
                    ],
                    profit_percentage=profit_percentage,
                    total_inverse_odds=total_inverse_odds
                )
                surebets.append(surebet_event)
        
        # Sort by profit percentage (highest first)
        surebets.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        logger.info(f"🎯 Found {len(surebets)} surebet opportunities out of {len(events)} events")
        
        return schemas.SurebetsResponse(
            surebets=surebets,
            total_count=len(surebets),
            status="success"
        )
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error while fetching surebets: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching surebets")
    except Exception as e:
        logger.error(f"❌ Unexpected error while fetching surebets: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# The Odds API Endpoint - Production-Ready Integration
# ============================================================================

@app.post("/api/v1/odds/fetch")
async def fetch_odds_from_api(db: Session = Depends(get_db)):
    """
    Fetch live odds from The Odds API, transform, store, and detect surebets.
    
    This is the main orchestration endpoint that:
    1. Calls The Odds API to fetch live betting odds
    2. Extracts API usage information from response headers
    3. Transforms the API data to our internal schema
    4. Saves the data to the database (upserts events)
    5. Calculates surebet opportunities
    6. Emits surebets via WebSocket for real-time updates
    7. Returns both surebets and API usage information
    
    Returns:
        JSON response with surebets and API usage data:
        {
            "surebets": [...],
            "usage": {
                "used": "123",
                "remaining": "377"
            },
            "status": "success",
            "events_processed": 50
        }
    
    Raises:
        HTTPException: If API call fails or processing encounters errors
    """
    try:
        # Step A: Call The Odds API to fetch live odds
        logger.info("🎯 Initiating fetch from The Odds API...")
        response = odds_api_service.fetch_live_odds()
        
        # Step B: Extract usage information from response headers
        used = response.headers.get('x-requests-used', '0')
        remaining = response.headers.get('x-requests-remaining', '0')
        
        logger.info(f"📊 API Usage - Used: {used}, Remaining: {remaining}")
        
        # Get the JSON data from the response
        api_data = response.json()
        
        if not api_data:
            logger.warning("⚠️  No events returned from The Odds API")
            return {
                "surebets": [],
                "usage": {"used": used, "remaining": remaining},
                "status": "success",
                "events_processed": 0,
                "message": "No events available from The Odds API"
            }
        
        # Step C: Transform the API data to our internal schema
        logger.info(f"🔄 Transforming {len(api_data)} events...")
        transformed_events = data_transformer.transform_odds_api_data(api_data)
        
        # Step D: Save events to database using upsert
        logger.info(f"💾 Saving {len(transformed_events)} events to database...")
        events_processed = 0
        
        for event_data in transformed_events:
            try:
                # Use upsert to either create or update the event
                crud.upsert_event(db, event_data)
                events_processed += 1
            except Exception as e:
                logger.error(f"❌ Error upserting event {event_data.event_id}: {str(e)}")
                # Continue processing other events
                continue
        
        db.commit()
        logger.info(f"✅ Successfully saved {events_processed} events to database")
        
        # Step E: Calculate surebet opportunities
        logger.info("🔍 Calculating surebet opportunities...")
        events = crud.get_events_with_multiple_outcomes(db)
        
        calculated_surebets = []
        
        for event in events:
            is_surebet, profit_percentage, total_inverse_odds = calculate_surebet_profit(event.outcomes)
            
            if is_surebet:
                surebet_event = schemas.SurebetEvent(
                    id=event.id,
                    event_id=event.event_id,
                    event=event.event,
                    sport=event.sport,
                    outcomes=[
                        schemas.Outcome(
                            id=outcome.id,
                            event_id=outcome.event_id,
                            bookmaker=outcome.bookmaker,
                            name=outcome.name,
                            odds=outcome.odds,
                            deep_link_url=outcome.deep_link_url
                        )
                        for outcome in event.outcomes
                    ],
                    profit_percentage=profit_percentage,
                    total_inverse_odds=total_inverse_odds
                )
                calculated_surebets.append(surebet_event)
        
        # Sort by profit percentage (highest first)
        calculated_surebets.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        logger.info(f"🎯 Found {len(calculated_surebets)} surebet opportunities!")
        
        # Emit surebets via WebSocket for real-time frontend updates
        if calculated_surebets:
            try:
                # Convert to dict for WebSocket emission
                surebets_data = [
                    {
                        "id": sb.id,
                        "event_id": sb.event_id,
                        "event": sb.event,
                        "sport": sb.sport,
                        "profit_percentage": sb.profit_percentage,
                        "outcomes": [
                            {
                                "bookmaker": outcome.bookmaker,
                                "name": outcome.name,
                                "odds": outcome.odds,
                                "deep_link_url": outcome.deep_link_url
                            }
                            for outcome in sb.outcomes
                        ]
                    }
                    for sb in calculated_surebets
                ]
                
                # Emit the 'new_surebets' event to all connected clients
                await sio.emit('new_surebets', surebets_data)
                logger.info(f"📡 Emitted {len(calculated_surebets)} surebets via WebSocket")
            except Exception as e:
                logger.error(f"❌ Error emitting surebets via WebSocket: {str(e)}")
                # Don't fail the request if WebSocket emission fails
        
        # Step F: Return response with surebets and API usage
        return {
            "surebets": calculated_surebets,
            "usage": {
                "used": used,
                "remaining": remaining
            },
            "status": "success",
            "events_processed": events_processed,
            "total_surebets": len(calculated_surebets)
        }
        
    except ValueError as e:
        # API key not configured
        logger.error(f"❌ Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except requests.exceptions.RequestException as e:
        # API request failed
        logger.error(f"❌ The Odds API request failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Failed to fetch data from The Odds API")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"❌ Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while processing odds data")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================================================
# Settings Endpoints
# ============================================================================

@app.get("/api/v1/settings", response_model=schemas.SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """
    Get all application settings.
    
    Returns:
        SettingsResponse with all settings as key-value pairs
    """
    try:
        settings = crud.get_all_settings(db)
        logger.info(f"Retrieved {len(settings)} settings")
        
        return schemas.SettingsResponse(
            settings=settings,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching settings")


@app.post("/api/v1/settings", response_model=schemas.SettingsResponse)
async def update_settings_endpoint(
    settings_update: schemas.SettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update multiple application settings.
    
    Args:
        settings_update: Dictionary of settings to update
        db: Database session dependency
        
    Returns:
        SettingsResponse with updated settings
    """
    try:
        updated_settings = crud.update_settings(db, settings_update.settings)
        logger.info(f"Updated {len(settings_update.settings)} settings")
        
        return schemas.SettingsResponse(
            settings=updated_settings,
            status="success"
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error updating settings")
    except Exception as e:
        logger.error(f"Unexpected error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating settings")


# ============================================================================
# Scraper Target Management Endpoints
# ============================================================================

@app.get("/api/v1/scraper/targets", response_model=schemas.ScraperTargetsResponse)
async def get_scraper_targets(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all scraper targets or only active ones.
    
    Args:
        active_only: If True, return only active targets
        db: Database session dependency
        
    Returns:
        ScraperTargetsResponse with list of targets
    """
    try:
        if active_only:
            targets = crud.get_active_scraper_targets(db)
            logger.info(f"Retrieved {len(targets)} active scraper targets")
        else:
            targets = crud.get_all_scraper_targets(db)
            logger.info(f"Retrieved {len(targets)} scraper targets")
        
        return schemas.ScraperTargetsResponse(
            targets=[schemas.ScraperTarget.model_validate(t) for t in targets],
            total_count=len(targets),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error fetching scraper targets: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching scraper targets")


@app.post("/api/v1/scraper/targets", response_model=schemas.ScraperTarget)
async def create_scraper_target_endpoint(
    target: schemas.ScraperTargetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new scraper target.
    
    Args:
        target: Scraper target creation data
        db: Database session dependency
        
    Returns:
        Created scraper target
    """
    try:
        db_target = crud.create_scraper_target(db, target)
        logger.info(f"Created new scraper target: {db_target.name}")
        
        return schemas.ScraperTarget.model_validate(db_target)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error creating scraper target: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error creating scraper target")
    except Exception as e:
        logger.error(f"Unexpected error creating scraper target: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating scraper target")


@app.put("/api/v1/scraper/targets/{target_id}", response_model=schemas.ScraperTarget)
async def update_scraper_target_endpoint(
    target_id: int,
    target_update: schemas.ScraperTargetUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a scraper target.
    
    Args:
        target_id: ID of target to update
        target_update: Update data
        db: Database session dependency
        
    Returns:
        Updated scraper target
    """
    try:
        db_target = crud.update_scraper_target(db, target_id, target_update)
        
        if not db_target:
            raise HTTPException(status_code=404, detail="Scraper target not found")
        
        logger.info(f"Updated scraper target {target_id}: {db_target.name}")
        
        return schemas.ScraperTarget.model_validate(db_target)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating scraper target: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error updating scraper target")
    except Exception as e:
        logger.error(f"Unexpected error updating scraper target: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating scraper target")


@app.delete("/api/v1/scraper/targets/{target_id}")
async def delete_scraper_target_endpoint(
    target_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a scraper target.
    
    Args:
        target_id: ID of target to delete
        db: Database session dependency
        
    Returns:
        Success message
    """
    try:
        success = crud.delete_scraper_target(db, target_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Scraper target not found")
        
        logger.info(f"Deleted scraper target {target_id}")
        
        return {"message": "Scraper target deleted successfully", "status": "success"}
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting scraper target: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error deleting scraper target")
    except Exception as e:
        logger.error(f"Unexpected error deleting scraper target: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting scraper target")


# ============================================================================
# Scraper Control Endpoints
# ============================================================================

@app.post("/api/v1/scraper/run")
async def trigger_scraper():
    """
    Trigger the STEALTH scraper to run with advanced anti-detection measures.

    This endpoint uses:
    - Playwright-stealth to bypass bot detection
    - Residential proxy support (configure PROXY_URL in .env)
    - Human-like behavior simulation (mouse movements, scrolling, delays)
    - Production-grade selectors (data-testid and robust CSS selectors)

    The stealth scraper is designed to bypass Cloudflare and other
    anti-bot protections with reliable, modern selectors.

    Returns:
        Success message with scraper status and features
    """
    try:
        logger.info("🕵️ Triggering unified STEALTH scraper run...")

        # Make POST request to scraper service
        scraper_url = "http://scraper:8001/run-scrape"
        
        response = requests.post(
            scraper_url,
            timeout=5  # Short timeout since scraper runs in background
        )

        if response.status_code == 200:
            logger.info("✅ Stealth scraper triggered successfully")
            return response.json()
        else:
            logger.error(f"❌ Scraper service returned error: {response.status_code}")
            raise HTTPException(
                status_code=500,
                detail=f"Scraper service error: {response.text}"
            )

    except requests.exceptions.ConnectionError:
        logger.error("❌ Could not connect to scraper service")
        raise HTTPException(
            status_code=503,
            detail="Scraper service is not available"
        )
    except requests.exceptions.Timeout:
        logger.error("❌ Request to scraper service timed out")
        raise HTTPException(
            status_code=504,
            detail="Scraper service timed out"
        )
    except Exception as e:
        logger.error(f"❌ Error triggering scraper: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering scraper: {str(e)}")


@app.post("/api/v1/scraper/test-target")
async def test_scrape_target(request: TestScrapeRequest):
    """
    Test scraping a single URL without saving to database.
    
    This endpoint enables rapid iteration and debugging:
    - Accepts a URL and scraping strategy
    - Forwards request to scraper service
    - Returns raw scraped data without database persistence
    - Perfect for testing and development
    
    Example request:
    {
        "url": "https://www.betexplorer.com/football/",
        "strategy": "betexplorer"
    }
    
    Returns:
        Raw scraped data from the scraper service
    """
    try:
        logger.info(f"🧪 Test scrape requested - URL: {request.url}, Strategy: {request.strategy}")

        # Forward request to scraper service
        scraper_url = "http://scraper:8001/test-scrape"
        
        response = requests.post(
            scraper_url,
            json={
                "url": request.url,
                "strategy": request.strategy
            },
            timeout=60  # Longer timeout since we wait for scraping to complete
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Test scrape completed: {result.get('count', 0)} events scraped")
            return result
        else:
            logger.error(f"Scraper service returned error: {response.status_code}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Scraper service error: {response.text}"
            )

    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to scraper service")
        raise HTTPException(
            status_code=503,
            detail="Scraper service is not available"
        )
    except requests.exceptions.Timeout:
        logger.error("Request to scraper service timed out (>60s)")
        raise HTTPException(
            status_code=504,
            detail="Scraper service timed out - target site may be slow or unreachable"
        )
    except Exception as e:
        logger.error(f"Error during test scrape: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during test scrape: {str(e)}")


@app.post("/api/v1/scraper/generate-mock-data")
async def generate_mock_data():
    """
    Generate mock betting data for testing.
    
    This endpoint triggers the scraper to generate realistic sample data
    and send it through the normal ingestion pipeline. Perfect for:
    - Testing the full data flow
    - Demonstrating surebet detection
    - Frontend development
    - When real sites are blocking the scraper
    
    Returns:
        Success message with count of generated events
    """
    try:
        logger.info("🎭 Triggering mock data generation...")

        # Make GET request to scraper service
        scraper_url = "http://scraper:8001/generate-mock-data"
        
        response = requests.get(
            scraper_url,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Mock data generated: {result.get('count', 0)} events")
            return result
        else:
            logger.error(f"Scraper service returned error: {response.status_code}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Scraper service error: {response.text}"
            )

    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to scraper service")
        raise HTTPException(
            status_code=503,
            detail="Scraper service is not available"
        )
    except requests.exceptions.Timeout:
        logger.error("Request to scraper service timed out")
        raise HTTPException(
            status_code=504,
            detail="Scraper service timed out"
        )
    except Exception as e:
        logger.error(f"Error generating mock data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating mock data: {str(e)}")


@app.get("/api/v1/run-full-test")
async def run_full_end_to_end_test(db: Session = Depends(get_db)):
    """
    End-to-end testing endpoint.
    
    This endpoint:
    1. Triggers the scraper
    2. Waits 60 seconds for scraping to complete
    3. Checks the database for scraped events
    4. Returns a summary
    
    Returns:
        Test summary with event count
    """
    import time as time_module
    
    logger.info("=" * 60)
    logger.info("--- STARTING END-TO-END TEST ---")
    logger.info("=" * 60)
    
    try:
        # Step 1: Trigger the scraper
        logger.info("Step 1: Triggering scraper...")
        scraper_url = "http://scraper:8001/run-scrape"
        
        try:
            response = requests.post(scraper_url, timeout=5)
            response.raise_for_status()
            logger.info(f"✅ Scraper triggered successfully: {response.json()}")
        except Exception as trigger_error:
            logger.error(f"❌ Failed to trigger scraper: {str(trigger_error)}")
            return {
                "status": "error",
                "message": f"Failed to trigger scraper: {str(trigger_error)}",
                "events_count": 0
            }
        
        # Step 2: Wait for scraping to complete
        wait_seconds = 60
        logger.info(f"Step 2: Waiting {wait_seconds} seconds for scraping to complete...")
        time_module.sleep(wait_seconds)
        logger.info("✅ Wait complete")
        
        # Step 3: Query the database for events
        logger.info("Step 3: Querying database for scraped events...")
        events = crud.get_all_events(db)
        event_count = len(events)
        logger.info(f"✅ Found {event_count} events in database")
        
        # Step 4: Query scraper targets
        targets = crud.get_all_scraper_targets(db)
        target_count = len(targets)
        logger.info(f"✅ Found {target_count} scraper targets configured")
        
        logger.info("=" * 60)
        logger.info("--- END-TO-END TEST COMPLETE ---")
        logger.info("=" * 60)
        
        return {
            "status": "success",
            "message": f"Test complete. Scraper was triggered. The database now contains {event_count} events.",
            "events_count": event_count,
            "targets_count": target_count,
            "wait_time_seconds": wait_seconds,
            "timestamp": time_module.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logger.error(f"❌ Error during end-to-end test: {str(e)}")
        return {
            "status": "error",
            "message": f"Error during test: {str(e)}",
            "events_count": 0
        }


# ============================================================================
# Socket.IO Event Handlers
# ============================================================================

@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {sid}")


async def emit_new_surebets(surebets: List[schemas.SurebetEvent]):
    """
    Emit new surebets to all connected Socket.IO clients.
    
    Args:
        surebets: List of surebet events to broadcast
    """
    try:
        # Convert Pydantic models to dictionaries for JSON serialization
        surebets_data = [s.model_dump() for s in surebets]
        
        from datetime import datetime
        
        await sio.emit('new_surebets', {
            'surebets': surebets_data,
            'total_count': len(surebets_data),
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Emitted {len(surebets)} surebets to all clients")
        
    except Exception as e:
        logger.error(f"Error emitting surebets: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Surebet Tool API with WebSocket support...")
    logger.info("📊 Database initialized and ready")
    logger.info("🌐 API docs available at: http://localhost:8000/docs")
    logger.info("🔌 WebSocket server ready for real-time updates")
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
