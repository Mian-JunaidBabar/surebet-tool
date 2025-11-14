from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

# Import our modules
import models
import schemas
import crud
from database import SessionLocal, engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="Surebet Tool API",
    description="Complete API for ingesting scraped betting data and serving surebet opportunities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    print(f"📥 Received {event_count} events from scraper")
    
    processed_count = 0
    errors = []
    
    # Process each event
    for idx, event in enumerate(events, 1):
        try:
            print(f"  [{idx}] Processing: {event.event}")
            print(f"      Sport: {event.sport}")
            print(f"      Event ID: {event.event_id}")
            print(f"      Outcomes: {len(event.outcomes)}")
            
            # Log each outcome for the event
            for outcome in event.outcomes:
                print(f"        - {outcome.name}: {outcome.odds} ({outcome.bookmaker})")
            
            # Upsert the event (create or update with fresh outcomes)
            db_event = crud.upsert_event(db, event)
            processed_count += 1
            
        except SQLAlchemyError as e:
            error_msg = f"Database error for event {event.event_id}: {str(e)}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error for event {event.event_id}: {str(e)}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
    
    print(f"✅ Successfully processed {processed_count}/{event_count} events")
    
    if errors:
        print(f"⚠️  Encountered {len(errors)} errors:")
        for error in errors:
            print(f"    - {error}")
    
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
        
        print(f"🎯 Found {len(surebets)} surebet opportunities out of {len(events)} events")
        
        return schemas.SurebetsResponse(
            surebets=surebets,
            total_count=len(surebets),
            status="success"
        )
        
    except SQLAlchemyError as e:
        print(f"❌ Database error while fetching surebets: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching surebets")
    except Exception as e:
        print(f"❌ Unexpected error while fetching surebets: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Surebet Tool API...")
    print("📊 Database initialized and ready")
    print("🌐 API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
