"""Tests for data pipeline functions."""

import pytest
import pandas as pd
from pathlib import Path

from src.pipeline.data_generator import generate_startup_data, SECTORS, STATUSES


def test_generate_startup_data() -> None:
    """Test data generation."""
    df = generate_startup_data(num_records=100)

    assert len(df) == 100
    assert "name" in df.columns
    assert "sector" in df.columns
    assert "founded_year" in df.columns
    assert "funding_rounds" in df.columns
    assert "total_funding" in df.columns
    assert "status" in df.columns
    assert "country" in df.columns
    assert "city" in df.columns
    assert len(df.columns) >= 8  # Requirement: at least 8 columns


def test_generate_data_sectors() -> None:
    """Test that generated data uses valid sectors."""
    df = generate_startup_data(num_records=50)

    # All sectors should be from the predefined list
    unique_sectors = df["sector"].unique()
    for sector in unique_sectors:
        assert sector in SECTORS


def test_generate_data_ranges() -> None:
    """Test that generated data has reasonable value ranges."""
    df = generate_startup_data(num_records=100)

    # Founded year should be in reasonable range
    assert df["founded_year"].min() >= 2010
    assert df["founded_year"].max() <= 2023

    # Funding should be non-negative
    funding_cols = ["total_funding", "funding_rounds"]
    for col in funding_cols:
        if col in df.columns:
            assert df[col].min() >= 0

    # Employee count should be positive
    if "employee_count" in df.columns:
        assert df["employee_count"].min() >= 1


def test_data_generator_meets_requirements() -> None:
    """Test that generated data meets project requirements."""
    df = generate_startup_data(num_records=1000000)

    # At least 750,000 rows (we generate 1M)
    assert len(df) >= 750000

    # At least 8 columns
    assert len(df.columns) >= 8

    # Check required columns exist
    required_cols = [
        "name",
        "sector",
        "founded_year",
        "funding_rounds",
        "total_funding",
        "status",
        "country",
        "city",
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"


