"""Data aggregation."""

import logging
from typing import Any

import pandas as pd
from pymongo.collection import Collection

from src.database.connection import get_database
from src.database.operations import insert_documents, count_documents, get_schema_sample
from src.models.startup import SectorAggregate
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def load_clean_data() -> pd.DataFrame:
    """Load cleaned data from MongoDB."""
    logger.info("Loading cleaned data...")
    db = get_database()
    collection: Collection = db["clean_startups"]

    # Load all documents
    cursor = collection.find({})
    df = pd.DataFrame(list(cursor))

    # Remove MongoDB _id field
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])

    logger.info(f"Loaded {len(df):,} cleaned records")
    return df


def aggregate_by_sector(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate data by sector."""
    logger.info("Aggregating by sector...")

    # Convert date strings back to datetime if needed
    if "last_funding_date" in df.columns:
        df["last_funding_date"] = pd.to_datetime(df["last_funding_date"], errors="coerce")

    # Group by sector
    grouped = df.groupby("sector")

    aggregated_data: list[dict[str, Any]] = []

    for sector, group_df in grouped:
        # Basic counts
        total_startups = len(group_df)
        active_startups = len(group_df[group_df["status"] == "active"])
        closed_startups = len(group_df[group_df["status"] == "closed"])

        # Funding metrics
        total_funding = group_df["total_funding"].sum()
        avg_funding = group_df["total_funding"].mean() if total_startups > 0 else 0.0
        median_funding = group_df["total_funding"].median() if total_startups > 0 else 0.0
        avg_funding_rounds = group_df["funding_rounds"].mean() if total_startups > 0 else 0.0

        # Time metrics
        avg_time_to_first = (
            group_df["time_to_first_funding_days"].mean()
            if "time_to_first_funding_days" in group_df.columns
            else None
        )
        if pd.isna(avg_time_to_first):
            avg_time_to_first = None

        # Employee metrics
        avg_employees = group_df["employee_count"].mean() if total_startups > 0 else None
        if pd.isna(avg_employees):
            avg_employees = None

        # Founding year range
        founded_years = group_df["founded_year"].dropna()
        founded_year_min = int(founded_years.min()) if len(founded_years) > 0 else None
        founded_year_max = int(founded_years.max()) if len(founded_years) > 0 else None

        # Growth rate (year-over-year startup count growth)
        if founded_year_min and founded_year_max and founded_year_max > founded_year_min:
            years = list(range(founded_year_min, founded_year_max + 1))
            if len(years) >= 2:
                startups_by_year = group_df.groupby("founded_year").size()
                if len(startups_by_year) >= 2:
                    recent_years = sorted(years)[-3:]  # Last 3 years
                    recent_counts = [startups_by_year.get(y, 0) for y in recent_years]
                    if recent_counts[0] > 0:
                        growth_rate = (recent_counts[-1] - recent_counts[0]) / recent_counts[0]
                    else:
                        growth_rate = 0.0
                else:
                    growth_rate = 0.0
            else:
                growth_rate = 0.0
        else:
            growth_rate = 0.0

        # Saturation score (based on competition density)
        # Higher number of startups in sector = higher saturation
        max_startups_in_sector = df.groupby("sector").size().max()
        saturation_score = min(1.0, total_startups / max_startups_in_sector) if max_startups_in_sector > 0 else 0.0

        # Risk score (based on failure rate)
        failure_rate = closed_startups / total_startups if total_startups > 0 else 0.0
        risk_score = failure_rate

        # Top countries
        country_counts = group_df["country"].value_counts().head(5)
        top_countries = country_counts.index.tolist()

        # Capital distribution
        capital_dist = group_df["capital_range"].value_counts().to_dict()

        sector_data = {
            "sector": sector,
            "total_startups": int(total_startups),
            "active_startups": int(active_startups),
            "closed_startups": int(closed_startups),
            "total_funding": float(total_funding),
            "avg_funding_per_startup": float(avg_funding),
            "median_funding": float(median_funding),
            "avg_funding_rounds": float(avg_funding_rounds),
            "avg_time_to_first_funding_days": (
                float(avg_time_to_first) if avg_time_to_first is not None else None
            ),
            "avg_employee_count": float(avg_employees) if avg_employees is not None else None,
            "founded_year_min": founded_year_min,
            "founded_year_max": founded_year_max,
            "growth_rate": float(growth_rate),
            "saturation_score": float(saturation_score),
            "risk_score": float(risk_score),
            "top_countries": top_countries,
            "capital_distribution": capital_dist,
        }

        # Validate with Pydantic
        try:
            validated = SectorAggregate(**sector_data)
            aggregated_data.append(validated.model_dump())
        except Exception as e:
            logger.warning(f"Validation error for sector {sector}: {e}")

    df_aggregated = pd.DataFrame(aggregated_data)
    logger.info(f"Aggregated {len(df_aggregated)} sectors")

    return df_aggregated


def save_aggregated_data(df: pd.DataFrame) -> int:
    """Save aggregated data to MongoDB."""
    logger.info("Saving aggregated data...")

    # Convert DataFrame to list of dictionaries
    documents = df.replace({pd.NA: None, pd.NaT: None}).to_dict("records")

    # Insert into aggregated collection
    inserted_count = insert_documents("aggregated_sectors", documents)

    logger.info(f"Successfully saved {inserted_count:,} aggregated documents")
    return inserted_count


def create_indexes() -> None:
    """Create indexes."""
    logger.info("Creating indexes...")
    db = get_database()
    collection = db["aggregated_sectors"]
    collection.create_index("sector", unique=True)
    collection.create_index("total_startups")
    collection.create_index("growth_rate")
    collection.create_index("risk_score")

    logger.info("Indexes created successfully")


def show_aggregated_collection_info() -> None:
    """Show aggregated collection info."""
    count = count_documents("aggregated_sectors")
    logger.info(f"\n{'='*60}")
    logger.info(f"Collection: aggregated_sectors")
    logger.info(f"Total Documents: {count:,}")
    logger.info(f"{'='*60}")

    # Show schema sample
    samples = get_schema_sample("aggregated_sectors", 3)
    if samples:
        logger.info("\nSample Aggregated Documents:")
        for i, sample in enumerate(samples, 1):
            logger.info(f"\nSample {i}:")
            for key, value in list(sample.items())[:15]:
                logger.info(f"  {key}: {value} ({type(value).__name__})")


def main() -> None:
    setup_logging()

    logger.info("Starting data aggregation pipeline (Aggregated Layer)")

    # Load cleaned data
    df_clean = load_clean_data()

    # Aggregate by sector
    df_aggregated = aggregate_by_sector(df_clean)

    # Save aggregated data
    save_aggregated_data(df_aggregated)

    # Create indexes
    create_indexes()

    # Show collection info
    show_aggregated_collection_info()

    logger.info("Data aggregation pipeline completed successfully!")


if __name__ == "__main__":
    main()


