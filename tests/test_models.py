"""Tests for Pydantic models."""

import pytest
from datetime import datetime

from src.models.startup import StartupRaw, StartupClean, SectorAggregate


def test_startup_raw_valid() -> None:
    """Test valid StartupRaw model."""
    data = {
        "name": "Test Startup",
        "sector": "Technology",
        "founded_year": 2020,
        "funding_rounds": 3,
        "total_funding": 5000000.0,
        "last_funding_date": "2023-01-15",
        "status": "active",
        "country": "USA",
        "city": "San Francisco",
        "employee_count": 50,
    }

    startup = StartupRaw(**data)
    assert startup.name == "Test Startup"
    assert startup.sector == "Technology"
    assert startup.founded_year == 2020


def test_startup_raw_missing_optional() -> None:
    """Test StartupRaw with missing optional fields."""
    data = {
        "name": "Minimal Startup",
        "sector": "Healthcare",
    }

    startup = StartupRaw(**data)
    assert startup.name == "Minimal Startup"
    assert startup.funding_rounds is None
    assert startup.total_funding is None


def test_startup_clean_validation() -> None:
    """Test StartupClean model validation and normalization."""
    data = {
        "name": "  test startup  ",
        "sector": "  technology  ",
        "status": "  ACTIVE  ",
        "funding_rounds": 2,
        "total_funding": 1000000.0,
    }

    startup = StartupClean(**data)
    assert startup.sector == "Technology"  # Normalized
    assert startup.status == "active"  # Normalized
    assert startup.funding_rounds == 2
    assert startup.total_funding == 1000000.0


def test_sector_aggregate_valid() -> None:
    """Test valid SectorAggregate model."""
    data = {
        "sector": "Technology",
        "total_startups": 1000,
        "active_startups": 750,
        "closed_startups": 250,
        "total_funding": 500000000.0,
        "avg_funding_per_startup": 500000.0,
        "median_funding": 300000.0,
        "avg_funding_rounds": 2.5,
        "growth_rate": 0.15,
        "saturation_score": 0.6,
        "risk_score": 0.25,
        "top_countries": ["USA", "UK"],
        "capital_distribution": {"0-1M": 300, "1M-10M": 500},
    }

    sector = SectorAggregate(**data)
    assert sector.sector == "Technology"
    assert sector.total_startups == 1000
    assert sector.growth_rate == 0.15
    assert len(sector.top_countries) == 2


def test_startup_raw_year_validation() -> None:
    """Test year validation in StartupRaw."""
    data = {
        "name": "Test",
        "sector": "Tech",
        "founded_year": 1800,  # Invalid year
    }

    with pytest.raises(Exception):  # Should raise validation error
        StartupRaw(**data)


