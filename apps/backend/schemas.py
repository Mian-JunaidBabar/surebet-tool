from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class OutcomeBase(BaseModel):
    """Base schema for betting outcomes"""
    bookmaker: str
    name: str
    odds: float
    deep_link_url: str


class OutcomeCreate(OutcomeBase):
    """Schema for creating outcomes (from scraper)"""
    pass


class Outcome(OutcomeBase):
    """Schema for outcome responses (to frontend)"""
    id: int
    event_id: int

    model_config = ConfigDict(from_attributes=True)


class EventBase(BaseModel):
    """Base schema for betting events"""
    event_id: str
    event: str
    sport: str


class EventCreate(EventBase):
    """Schema for creating events (from scraper)"""
    outcomes: List[OutcomeCreate]


class Event(EventBase):
    """Schema for event responses (to frontend)"""
    id: int
    outcomes: List[Outcome]

    model_config = ConfigDict(from_attributes=True)


class SurebetEvent(Event):
    """Schema for surebet events with calculated profit"""
    profit_percentage: float
    total_inverse_odds: float

    model_config = ConfigDict(from_attributes=True)


class IngestionResponse(BaseModel):
    """Schema for data ingestion response"""
    message: str
    events_processed: int
    status: str


class SurebetsResponse(BaseModel):
    """Schema for surebets endpoint response"""
    surebets: List[SurebetEvent]
    total_count: int
    status: str


# Settings Schemas
class SettingBase(BaseModel):
    """Base schema for settings"""
    key: str
    value: str


class SettingCreate(SettingBase):
    """Schema for creating settings"""
    pass


class SettingUpdate(BaseModel):
    """Schema for updating settings"""
    value: str


class Setting(SettingBase):
    """Schema for setting responses"""
    model_config = ConfigDict(from_attributes=True)


class SettingsUpdate(BaseModel):
    """Schema for bulk settings update"""
    settings: dict[str, str]


class SettingsResponse(BaseModel):
    """Schema for settings endpoint response"""
    settings: dict[str, str]
    status: str


# Scraper Target Schemas
class ScraperTargetBase(BaseModel):
    """Base schema for scraper targets"""
    name: str
    url: str
    is_active: bool = True


class ScraperTargetCreate(ScraperTargetBase):
    """Schema for creating scraper targets"""
    pass


class ScraperTargetUpdate(BaseModel):
    """Schema for updating scraper targets"""
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None


class ScraperTarget(ScraperTargetBase):
    """Schema for scraper target responses"""
    id: int

    model_config = ConfigDict(from_attributes=True)


class ScraperTargetsResponse(BaseModel):
    """Schema for scraper targets endpoint response"""
    targets: List[ScraperTarget]
    total_count: int
    status: str