"""Data ingestion."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from pymongo.collection import Collection

from src.database.connection import get_database
from src.database.operations import insert_documents, count_documents, get_schema_sample
from src.pipeline.data_generator import generate_startup_data, save_data
from src.utils.config import get_config
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def load_data_from_file(file_path: Path) -> pd.DataFrame:
    """Load data from file."""
    logger.info(f"Loading data from {file_path}")

    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() == ".json":
        df = pd.read_json(file_path, lines=True)
    elif file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    logger.info(f"Loaded {len(df):,} rows and {len(df.columns)} columns")
    return df


def ingest_to_mongodb(df: pd.DataFrame, collection_name: str = "raw_startups") -> int:
    """Ingest data into MongoDB."""
    logger.info(f"Ingesting {len(df):,} records into {collection_name}")

    # Convert to dict format for MongoDB
    documents = df.replace({pd.NA: None, pd.NaT: None}).to_dict("records")

    # Insert documents
    inserted_count = insert_documents(collection_name, documents)

    logger.info(f"Successfully ingested {inserted_count:,} documents")
    return inserted_count


def show_collection_info(collection_name: str) -> None:
    """Show collection stats."""
    db = get_database()
    collection: Collection = db[collection_name]

    count = count_documents(collection_name)
    logger.info(f"\n{'='*60}")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"Total Documents: {count:,}")
    logger.info(f"{'='*60}")

    # Show schema sample
    samples = get_schema_sample(collection_name, 3)
    if samples:
        logger.info("\nSample Documents (Schema):")
        for i, sample in enumerate(samples, 1):
            logger.info(f"\nSample {i}:")
            for key, value in list(sample.items())[:10]:  # Show first 10 fields
                logger.info(f"  {key}: {value} ({type(value).__name__})")

    # Show column names
    if samples:
        all_keys = set()
        for sample in samples:
            all_keys.update(sample.keys())
        logger.info(f"\nColumns ({len(all_keys)}): {sorted(all_keys)}")


def main() -> None:
    setup_logging()
    config = get_config()

    logger.info("Starting data ingestion pipeline (Raw Layer)")

    # Check if data file exists, otherwise generate it
    data_dir = config.data_dir / "raw"
    data_file = data_dir / "startups.csv"

    if not data_file.exists():
        logger.info("Data file not found. Generating synthetic startup data...")
        df = generate_startup_data(num_records=1000000)
        save_data(df, data_file, format="csv")
    else:
        logger.info(f"Loading existing data from {data_file}")
        df = load_data_from_file(data_file)

    # Verify data meets requirements
    if len(df) < 750000:
        logger.warning(f"Dataset has {len(df):,} rows, but requirement is 750,000+")
    if len(df.columns) < 8:
        logger.warning(f"Dataset has {len(df.columns)} columns, but requirement is 8+")

    logger.info(f"Dataset: {len(df):,} rows, {len(df.columns)} columns")

    # Ingest to MongoDB
    inserted_count = ingest_to_mongodb(df, collection_name="raw_startups")

    # Show collection info
    show_collection_info("raw_startups")

    logger.info("Data ingestion pipeline completed successfully!")


if __name__ == "__main__":
    main()


