from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
import models
import schemas
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


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
            logger.info(f"🔄 Updating existing event: {event.event}")
            return update_event_outcomes(db, existing_event, event)
        else:
            # Event doesn't exist - create new
            logger.info(f"✨ Creating new event: {event.event}")
            return create_event(db, event)
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error during upsert for event {event.event_id}: {str(e)}")
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
    return db.query(models.Event).join(models.Outcome).group_by(models.Event.id).having(func.count(models.Outcome.id) >= 2).all()


# ============================================================================
# Settings CRUD Operations
# ============================================================================

def get_all_settings(db: Session) -> dict[str, str]:
    """
    Get all settings as a dictionary.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary of all settings (key-value pairs)
    """
    settings = db.query(models.Setting).all()
    return {setting.key: setting.value for setting in settings}


def get_setting(db: Session, key: str) -> Optional[models.Setting]:
    """
    Get a single setting by key.
    
    Args:
        db: Database session
        key: Setting key
        
    Returns:
        Setting model or None if not found
    """
    return db.query(models.Setting).filter(models.Setting.key == key).first()


def update_setting(db: Session, key: str, value: str) -> models.Setting:
    """
    Update or create a single setting.
    
    Args:
        db: Database session
        key: Setting key
        value: Setting value
        
    Returns:
        Updated or created setting model
    """
    try:
        setting = get_setting(db, key)
        if setting:
            setting.value = value
        else:
            setting = models.Setting(key=key, value=value)
            db.add(setting)
        
        db.commit()
        db.refresh(setting)
        return setting
        
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def update_settings(db: Session, settings: dict[str, str]) -> dict[str, str]:
    """
    Update multiple settings at once.
    
    Args:
        db: Database session
        settings: Dictionary of settings to update
        
    Returns:
        Dictionary of all updated settings
    """
    try:
        for key, value in settings.items():
            update_setting(db, key, value)
        
        return get_all_settings(db)
        
    except SQLAlchemyError as e:
        db.rollback()
        raise e


# ============================================================================
# Scraper Target CRUD Operations
# ============================================================================

def get_all_scraper_targets(db: Session) -> List[models.ScraperTarget]:
    """
    Get all scraper targets.
    
    Args:
        db: Database session
        
    Returns:
        List of all scraper target models
    """
    return db.query(models.ScraperTarget).all()


def get_active_scraper_targets(db: Session) -> List[models.ScraperTarget]:
    """
    Get only active scraper targets.
    
    Args:
        db: Database session
        
    Returns:
        List of active scraper target models
    """
    return db.query(models.ScraperTarget).filter(models.ScraperTarget.is_active == True).all()


def get_scraper_target(db: Session, target_id: int) -> Optional[models.ScraperTarget]:
    """
    Get a single scraper target by ID.
    
    Args:
        db: Database session
        target_id: Scraper target ID
        
    Returns:
        ScraperTarget model or None if not found
    """
    return db.query(models.ScraperTarget).filter(models.ScraperTarget.id == target_id).first()


def create_scraper_target(db: Session, target: schemas.ScraperTargetCreate) -> models.ScraperTarget:
    """
    Create a new scraper target.
    
    Args:
        db: Database session
        target: Scraper target creation schema
        
    Returns:
        Created scraper target model
    """
    try:
        db_target = models.ScraperTarget(
            name=target.name,
            url=target.url,
            is_active=target.is_active
        )
        db.add(db_target)
        db.commit()
        db.refresh(db_target)
        return db_target
        
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def update_scraper_target(db: Session, target_id: int, target_update: schemas.ScraperTargetUpdate) -> Optional[models.ScraperTarget]:
    """
    Update a scraper target.
    
    Args:
        db: Database session
        target_id: Scraper target ID
        target_update: Scraper target update schema
        
    Returns:
        Updated scraper target model or None if not found
    """
    try:
        db_target = get_scraper_target(db, target_id)
        if not db_target:
            return None
        
        # Update only provided fields
        if target_update.name is not None:
            db_target.name = target_update.name
        if target_update.url is not None:
            db_target.url = target_update.url
        if target_update.is_active is not None:
            db_target.is_active = target_update.is_active
        
        db.commit()
        db.refresh(db_target)
        return db_target
        
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def delete_scraper_target(db: Session, target_id: int) -> bool:
    """
    Delete a scraper target.
    
    Args:
        db: Database session
        target_id: Scraper target ID
        
    Returns:
        True if deleted, False if not found
    """
    try:
        db_target = get_scraper_target(db, target_id)
        if not db_target:
            return False
        
        db.delete(db_target)
        db.commit()
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        raise e