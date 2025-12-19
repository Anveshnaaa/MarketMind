"""Startup data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class StartupRaw(BaseModel):
    """Raw startup data."""

    name: str
    sector: str
    founded_year: Optional[int] = None
    funding_rounds: Optional[int] = Field(None, ge=0)
    total_funding: Optional[float] = Field(None, ge=0)
    last_funding_date: Optional[str] = None
    status: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    employee_count: Optional[int] = Field(None, ge=0)
    first_funding_year: Optional[int] = None
    last_funding_year: Optional[int] = None
    time_to_first_funding_days: Optional[int] = Field(None, ge=0)
    time_to_last_funding_days: Optional[int] = Field(None, ge=0)

    @field_validator("founded_year", "first_funding_year", "last_funding_year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1900 or v > 2030):
            raise ValueError(f"Invalid year: {v}")
        return v


class StartupClean(BaseModel):
    """Cleaned startup data."""

    name: str
    sector: str
    founded_year: Optional[int] = None
    funding_rounds: int = 0
    total_funding: float = 0.0
    last_funding_date: Optional[datetime] = None
    status: str = "unknown"
    country: Optional[str] = None
    city: Optional[str] = None
    employee_count: Optional[int] = None
    first_funding_year: Optional[int] = None
    last_funding_year: Optional[int] = None
    time_to_first_funding_days: Optional[int] = None
    time_to_last_funding_days: Optional[int] = None
    funding_stage: str = "unknown"
    capital_range: str = "unknown"

    @field_validator("sector")
    @classmethod
    def normalize_sector(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("status")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        if not v:
            return "unknown"
        return v.strip().lower()


class SectorAggregate(BaseModel):
    """Sector aggregation data."""

    sector: str
    total_startups: int = Field(ge=0)
    active_startups: int = Field(ge=0)
    closed_startups: int = Field(ge=0)
    total_funding: float = Field(ge=0)
    avg_funding_per_startup: float = Field(ge=0)
    median_funding: float = Field(ge=0)
    avg_funding_rounds: float = Field(ge=0)
    avg_time_to_first_funding_days: Optional[float] = None
    avg_employee_count: Optional[float] = None
    founded_year_min: Optional[int] = None
    founded_year_max: Optional[int] = None
    growth_rate: float
    saturation_score: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    top_countries: list[str] = Field(default_factory=list)
    capital_distribution: dict[str, int] = Field(default_factory=dict)



