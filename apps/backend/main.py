from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import socketio
import subprocess
import logging

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

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Database seeding - Add default scraper target if none exist
logger.info("🌱 Checking for default data...")
db = SessionLocal()
try:
    # Check if any scraper targets exist
    existing_targets = db.query(models.ScraperTarget).first()
    
    if existing_targets is None:
        logger.info("📍 No scraper targets found. Creating default target...")
        
        # Create default scraper target
        default_target = models.ScraperTarget(
            name="BetExplorer Premier League",
            url="https://www.betexplorer.com/football/england/premier-league/",
            is_active=True
        )
        
        db.add(default_target)
        db.commit()
        db.refresh(default_target)
        
        logger.info(f"✅ Created default scraper target: {default_target.name}")
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
    
    Args:
        outcomes: List of outcome models
        
    Returns:
        Tuple of (is_surebet, profit_percentage, total_inverse_odds)
    """
    if len(outcomes) < 2:
        return False, 0.0, 0.0
    
    # Calculate sum of inverse odds: (1/odds1) + (1/odds2) + ...
    total_inverse_odds = sum(1/outcome.odds for outcome in outcomes)
    
    # If sum < 1, it's a surebet
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
    Trigger the scraper to run immediately.
    
    This endpoint starts the scraper process in the background using Docker Compose.
    
    Returns:
        Success message with scraper status
    """
    try:
        logger.info("Triggering scraper run...")
        
        # Start scraper in background
        process = subprocess.Popen(
            ["docker-compose", "exec", "-T", "scraper", "python", "scraper.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info(f"Scraper process started with PID: {process.pid}")
        
        return {
            "message": "Scraper triggered successfully",
            "status": "running",
            "process_id": process.pid
        }
        
    except Exception as e:
        logger.error(f"Error triggering scraper: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering scraper: {str(e)}")


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
