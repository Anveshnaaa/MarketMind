"""Generate synthetic startup data for testing and demonstration."""

import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Sample data for realistic generation
SECTORS = [
    "Technology",
    "Healthcare",
    "Finance",
    "E-commerce",
    "Education",
    "Real Estate",
    "Transportation",
    "Energy",
    "Food & Beverage",
    "Entertainment",
    "Manufacturing",
    "Agriculture",
    "Retail",
    "Telecommunications",
    "Media",
    "Consulting",
    "Travel",
    "Fitness",
    "Legal",
    "Construction",
]

STATUSES = ["active", "closed", "acquired", "ipo", "unknown"]

COUNTRIES = ["USA", "UK", "Canada", "Germany", "France", "India", "China", "Australia", "Japan", "Brazil"]

CITIES = {
    "USA": ["San Francisco", "New York", "Austin", "Seattle", "Boston", "Los Angeles"],
    "UK": ["London", "Manchester", "Edinburgh"],
    "Canada": ["Toronto", "Vancouver", "Montreal"],
    "Germany": ["Berlin", "Munich", "Hamburg"],
    "France": ["Paris", "Lyon", "Marseille"],
    "India": ["Bangalore", "Mumbai", "Delhi"],
    "China": ["Beijing", "Shanghai", "Shenzhen"],
    "Australia": ["Sydney", "Melbourne"],
    "Japan": ["Tokyo", "Osaka"],
    "Brazil": ["São Paulo", "Rio de Janeiro"],
}


def generate_startup_data(num_records: int = 1000000) -> pd.DataFrame:
    """Generate synthetic startup data."""
    logger.info(f"Generating {num_records:,} records...")

    data: list[dict[str, Any]] = []

    for i in range(num_records):
        # Basic info
        name = f"Startup_{i+1:06d}"
        sector = random.choice(SECTORS)
        country = random.choice(COUNTRIES)
        city = random.choice(CITIES.get(country, ["Unknown"]))

        # Founding year (2010-2023)
        founded_year = random.randint(2010, 2023)
        founded_date = datetime(founded_year, random.randint(1, 12), random.randint(1, 28))

        # Funding information
        has_funding = random.random() > 0.2  # 80% have funding
        if has_funding:
            funding_rounds = random.randint(1, 8)
            # Total funding based on rounds and sector
            base_funding = random.uniform(10000, 50000000)
            total_funding = base_funding * (1 + funding_rounds * 0.3)

            # First funding date (within 2 years of founding)
            first_funding_date = founded_date + timedelta(days=random.randint(0, 730))
            first_funding_year = first_funding_date.year

            # Last funding date
            if funding_rounds > 1:
                last_funding_date = first_funding_date + timedelta(
                    days=random.randint(90, 365 * 3)
                )
            else:
                last_funding_date = first_funding_date
            last_funding_year = last_funding_date.year

            time_to_first_funding = (first_funding_date - founded_date).days
            time_to_last_funding = (last_funding_date - founded_date).days
        else:
            funding_rounds = 0
            total_funding = 0.0
            first_funding_year = None
            last_funding_year = None
            last_funding_date = None
            time_to_first_funding = None
            time_to_last_funding = None

        # Status (correlated with funding and age)
        if not has_funding:
            status = random.choice(["closed", "unknown"])
        elif founded_year < 2015:
            status = random.choices(
                ["active", "closed", "acquired", "ipo"],
                weights=[0.4, 0.3, 0.2, 0.1],
            )[0]
        else:
            status = random.choices(
                ["active", "closed", "acquired"],
                weights=[0.7, 0.2, 0.1],
            )[0]

        # Employee count (correlated with funding)
        if total_funding > 0:
            max_employees = max(2, int(min(1000, total_funding / 50000)))
            employee_count = random.randint(1, max_employees)
        else:
            employee_count = random.randint(1, 20)

        record = {
            "name": name,
            "sector": sector,
            "founded_year": founded_year,
            "funding_rounds": funding_rounds if has_funding else None,
            "total_funding": round(total_funding, 2) if has_funding else None,
            "last_funding_date": last_funding_date.strftime("%Y-%m-%d") if last_funding_date else None,
            "status": status,
            "country": country,
            "city": city,
            "employee_count": employee_count,
            "first_funding_year": first_funding_year,
            "last_funding_year": last_funding_year,
            "time_to_first_funding_days": time_to_first_funding,
            "time_to_last_funding_days": time_to_last_funding,
        }

        data.append(record)

        if (i + 1) % 100000 == 0:
            logger.info(f"Generated {i+1:,} records...")

    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df):,} records with {len(df.columns)} columns")
    return df


def save_data(df: pd.DataFrame, output_path: Path, format: str = "csv") -> None:
    """Save DataFrame to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format.lower() == "csv":
        df.to_csv(output_path, index=False)
    elif format.lower() == "json":
        df.to_json(output_path, orient="records", lines=True)
    elif format.lower() == "parquet":
        df.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Saved to {output_path}")


