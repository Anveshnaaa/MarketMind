"""Data cleaning."""

import logging
from datetime import datetime
from typing import Any

import pandas as pd
from pymongo.collection import Collection

from src.database.connection import get_database
from src.database.operations import insert_documents, count_documents, get_schema_sample
from src.models.startup import StartupRaw, StartupClean
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def load_raw_data() -> pd.DataFrame:
    """Load raw data from MongoDB."""
    logger.info("Loading raw data...")
    db = get_database()
    collection: Collection = db["raw_startups"]

    # Load all documents
    cursor = collection.find({})
    df = pd.DataFrame(list(cursor))

    # Remove MongoDB _id field
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])

    logger.info(f"Loaded {len(df):,} raw records")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and transform data."""
    logger.info("Cleaning data...")
    initial_count = len(df)

    # Handle missing values
    logger.info("Handling missing values...")
    # Only fill NaN for truly missing values, not all zeros
    for col in ["funding_rounds", "total_funding", "employee_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Don't fill NaN - keep as is for now, will handle in Pydantic

    # Normalize text
    logger.info("Normalizing text...")
    text_cols = ["name", "sector", "status", "country", "city"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' strings with empty
            df[col] = df[col].replace("nan", "")

    # Normalize sector
    if "sector" in df.columns:
        df["sector"] = df["sector"].str.title()

    # Normalize status
    if "status" in df.columns:
        df["status"] = df["status"].str.lower()
        df["status"] = df["status"].fillna("unknown")

    # Standardize dates
    logger.info("Standardizing dates...")
    if "last_funding_date" in df.columns:
        # Convert to string first if needed, then to datetime
        df["last_funding_date"] = df["last_funding_date"].astype(str)
        df["last_funding_date"] = pd.to_datetime(
            df["last_funding_date"], errors="coerce"
        )

    # Remove duplicates
    logger.info("Removing duplicates...")
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["name", "sector", "founded_year"], keep="first")
    duplicates_removed = before_dedup - len(df)
    logger.info(f"Removed {duplicates_removed:,} duplicate records")

    # Add derived fields
    logger.info("Adding derived fields...")

    def categorize_funding_stage(row: pd.Series) -> str:
        """Categorize funding stage."""
        rounds = row.get("funding_rounds", 0) or 0
        total = row.get("total_funding", 0) or 0

        if rounds == 0 or total == 0:
            return "pre-seed"
        elif rounds == 1:
            return "seed"
        elif rounds == 2:
            return "series-a"
        elif rounds == 3:
            return "series-b"
        elif rounds >= 4:
            return "series-c-plus"
        else:
            return "unknown"

    df["funding_stage"] = df.apply(categorize_funding_stage, axis=1)

    def categorize_capital_range(row: pd.Series) -> str:
        """Categorize capital range."""
        total = row.get("total_funding", 0) or 0

        if total == 0:
            return "0-0"
        elif total < 1000000:
            return "0-1M"
        elif total < 10000000:
            return "1M-10M"
        elif total < 50000000:
            return "10M-50M"
        else:
            return "50M+"

    df["capital_range"] = df.apply(categorize_capital_range, axis=1)

    # Validate with Pydantic
    logger.info("Validating data...")
    clean_records: list[dict[str, Any]] = []
    validation_errors = 0

    for _, row in df.iterrows():
        try:
            # Convert row to dict, handling NaN
            row_dict = row.replace({pd.NA: None, pd.NaT: None}).to_dict()
            
            # Convert datetime to string for validation
            if "last_funding_date" in row_dict and pd.notna(row_dict["last_funding_date"]):
                row_dict["last_funding_date"] = str(row_dict["last_funding_date"])[:10]
            elif "last_funding_date" in row_dict:
                row_dict["last_funding_date"] = None

            # Validate with raw model first
            raw_model = StartupRaw(**row_dict)

            # Convert to clean model
            clean_dict = raw_model.model_dump()
            clean_dict["funding_stage"] = row.get("funding_stage", "unknown")
            clean_dict["capital_range"] = row.get("capital_range", "unknown")

            # Convert datetime to string for MongoDB
            if clean_dict.get("last_funding_date"):
                if isinstance(clean_dict["last_funding_date"], datetime):
                    clean_dict["last_funding_date"] = clean_dict["last_funding_date"].isoformat()

            clean_model = StartupClean(**clean_dict)
            clean_records.append(clean_model.model_dump())
        except Exception as e:
            validation_errors += 1
            if validation_errors <= 10:  # Log first 10 errors
                logger.warning(f"Validation error for record {row.get('name', 'unknown')}: {e}")

    logger.info(f"Validated {len(clean_records):,} records ({validation_errors:,} errors)")

    # Convert back to DataFrame
    df_clean = pd.DataFrame(clean_records)

    logger.info(
        f"Cleaning complete: {initial_count:,} -> {len(df_clean):,} records "
        f"({initial_count - len(df_clean):,} removed)"
    )

    return df_clean


def save_clean_data(df: pd.DataFrame) -> int:
    """Save cleaned data to MongoDB."""
    logger.info("Saving cleaned data...")

    # Convert DataFrame to list of dictionaries
    documents = df.replace({pd.NA: None, pd.NaT: None}).to_dict("records")

    # Insert into clean collection
    inserted_count = insert_documents("clean_startups", documents)

    logger.info(f"Successfully saved {inserted_count:,} cleaned documents")
    return inserted_count


def show_clean_collection_info() -> None:
    """Display cleaned collection information."""
    count = count_documents("clean_startups")
    logger.info(f"\n{'='*60}")
    logger.info(f"Collection: clean_startups")
    logger.info(f"Total Documents: {count:,}")
    logger.info(f"{'='*60}")

    # Show schema sample
    samples = get_schema_sample("clean_startups", 3)
    if samples:
        logger.info("\nSample Cleaned Documents:")
        for i, sample in enumerate(samples, 1):
            logger.info(f"\nSample {i}:")
            for key, value in list(sample.items())[:10]:
                logger.info(f"  {key}: {value} ({type(value).__name__})")


def main() -> None:
    setup_logging()

    logger.info("Starting data cleaning pipeline (Clean Layer)")

    # Load raw data
    df_raw = load_raw_data()

    # Clean data
    df_clean = clean_data(df_raw)

    # Save cleaned data
    save_clean_data(df_clean)

    # Show collection info
    show_clean_collection_info()

    logger.info("Data cleaning pipeline completed successfully!")


if __name__ == "__main__":
    main()


