from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


class Event(Base):
    """
    SQLAlchemy model for betting events.
    
    This table stores unique betting events with their basic information.
    Each event can have multiple outcomes (odds) from different bookmakers.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)  # Unique identifier from scraper
    event = Column(String, nullable=False)  # Event name (e.g., "Team A vs Team B")
    sport = Column(String, nullable=False)  # Sport type (e.g., "Football")

    # Relationship to outcomes
    outcomes = relationship("Outcome", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Event(id={self.id}, event_id='{self.event_id}', event='{self.event}', sport='{self.sport}')>"


class Outcome(Base):
    """
    SQLAlchemy model for betting outcomes.
    
    This table stores individual betting outcomes (odds) for each event.
    Each outcome belongs to one event and represents one bookmaker's odds.
    """
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True, index=True)
    bookmaker = Column(String, nullable=False)  # Bookmaker name (e.g., "BetExplorerAvg")
    name = Column(String, nullable=False)  # Outcome name (e.g., "Home Win", "Draw", "Away Win")
    odds = Column(Float, nullable=False)  # Betting odds as float
    deep_link_url = Column(String, nullable=False)  # Direct URL to bet on this outcome

    # Foreign key to events table
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # Relationship to event
    event = relationship("Event", back_populates="outcomes")

    def __repr__(self):
        return f"<Outcome(id={self.id}, bookmaker='{self.bookmaker}', name='{self.name}', odds={self.odds})>"


class Setting(Base):
    """
    SQLAlchemy model for application settings.
    
    This is a simple key-value store for application configuration.
    Settings can be updated dynamically through the API.
    """
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)  # Setting key (e.g., "refresh_interval")
    value = Column(String, nullable=False)  # Setting value stored as string

    def __repr__(self):
        return f"<Setting(key='{self.key}', value='{self.value}')>"


class ScraperTarget(Base):
    """
    SQLAlchemy model for scraper targets.
    
    This table stores the list of websites/URLs that the scraper should monitor.
    Each target can be enabled/disabled dynamically.
    """
    __tablename__ = "scraper_targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Target name (e.g., "BetExplorer Premier League")
    url = Column(String, nullable=False)  # Target URL to scrape
    is_active = Column(Boolean, default=True, nullable=False)  # Whether this target is currently active

    def __repr__(self):
        return f"<ScraperTarget(id={self.id}, name='{self.name}', is_active={self.is_active})>"