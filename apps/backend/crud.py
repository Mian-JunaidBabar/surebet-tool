from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import models
import schemas
from typing import List, Optional


def get_event_by_event_id(db: Session, event_id: str) -> Optional[models.Event]:
    """
    Get an event by its event_id (unique identifier from scraper).
    
    Args:
        db: Database session
        event_id: Unique event identifier
        
    Returns:
        Event model or None if not found
    """
    return db.query(models.Event).filter(models.Event.event_id == event_id).first()


def create_event(db: Session, event: schemas.EventCreate) -> models.Event:
    """
    Create a new event with its outcomes.
    
    Args:
        db: Database session
        event: Event creation schema
        
    Returns:
        Created event model
    """
    try:
        # Create the event
        db_event = models.Event(
            event_id=event.event_id,
            event=event.event,
            sport=event.sport
        )
        db.add(db_event)
        db.flush()  # Get the event ID without committing

        # Create all outcomes for this event
        for outcome_data in event.outcomes:
            db_outcome = models.Outcome(
                bookmaker=outcome_data.bookmaker,
                name=outcome_data.name,
                odds=outcome_data.odds,
                deep_link_url=outcome_data.deep_link_url,
                event_id=db_event.id
            )
            db.add(db_outcome)

        db.commit()
        db.refresh(db_event)
        return db_event

    except SQLAlchemyError as e:
        db.rollback()
        raise e


def update_event_outcomes(db: Session, existing_event: models.Event, event: schemas.EventCreate) -> models.Event:
    """
    Update an existing event by replacing all its outcomes with fresh data.
    
    Args:
        db: Database session
        existing_event: Existing event model
        event: Event update schema with new outcomes
        
    Returns:
        Updated event model
    """
    try:
        # Update event basic info (in case it changed)
        existing_event.event = event.event
        existing_event.sport = event.sport

        # Delete all existing outcomes for this event
        db.query(models.Outcome).filter(models.Outcome.event_id == existing_event.id).delete()

        # Create new outcomes with fresh odds
        for outcome_data in event.outcomes:
            db_outcome = models.Outcome(
                bookmaker=outcome_data.bookmaker,
                name=outcome_data.name,
                odds=outcome_data.odds,
                deep_link_url=outcome_data.deep_link_url,
                event_id=existing_event.id
            )
            db.add(db_outcome)

        db.commit()
        db.refresh(existing_event)
        return existing_event

    except SQLAlchemyError as e:
        db.rollback()
        raise e


def upsert_event(db: Session, event: schemas.EventCreate) -> models.Event:
    """
    Upsert an event: create if it doesn't exist, update outcomes if it does.
    
    This is the main function used by the data ingestion endpoint.
    It ensures that we always have fresh odds data for each event.
    
    Args:
        db: Database session
        event: Event creation/update schema
        
    Returns:
        Created or updated event model
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Check if event already exists
        existing_event = get_event_by_event_id(db, event.event_id)
        
        if existing_event:
            # Event exists - update with fresh outcomes
            print(f"🔄 Updating existing event: {event.event}")
            return update_event_outcomes(db, existing_event, event)
        else:
            # Event doesn't exist - create new
            print(f"✨ Creating new event: {event.event}")
            return create_event(db, event)
            
    except SQLAlchemyError as e:
        print(f"❌ Database error during upsert for event {event.event_id}: {str(e)}")
        raise e


def get_all_events(db: Session) -> List[models.Event]:
    """
    Get all events with their outcomes.
    
    Args:
        db: Database session
        
    Returns:
        List of all event models with outcomes
    """
    return db.query(models.Event).all()


def get_events_with_multiple_outcomes(db: Session) -> List[models.Event]:
    """
    Get events that have 2 or more outcomes (potential surebets).
    
    Args:
        db: Database session
        
    Returns:
        List of event models that have multiple outcomes
    """
    return db.query(models.Event).join(models.Outcome).group_by(models.Event.id).having(db.func.count(models.Outcome.id) >= 2).all()