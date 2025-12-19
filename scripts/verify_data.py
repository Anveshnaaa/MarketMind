"""Verify data in MongoDB collections - shows row/column counts for presentation."""

import logging
from pymongo.collection import Collection

from src.database.connection import get_database
from src.database.operations import count_documents, get_schema_sample
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def get_column_count(collection_name: str) -> int:
    """Get number of unique columns in a collection."""
    samples = get_schema_sample(collection_name, 10)
    if not samples:
        return 0

    all_keys = set()
    for sample in samples:
        all_keys.update(sample.keys())

    # Remove MongoDB _id
    all_keys.discard("_id")
    return len(all_keys)


def show_collection_stats(collection_name: str) -> None:
    """Show detailed collection statistics."""
    row_count = count_documents(collection_name)
    col_count = get_column_count(collection_name)

    print(f"\n{'='*70}")
    print(f"Collection: {collection_name}")
    print(f"{'='*70}")
    print(f"Row Count: {row_count:,}")
    print(f"Column Count: {col_count}")

    # Show sample schema
    samples = get_schema_sample(collection_name, 1)
    if samples:
        sample = samples[0]
        print(f"\nSample Schema (first document):")
        for key, value in list(sample.items())[:15]:
            value_type = type(value).__name__
            value_preview = str(value)[:50] if value else "None"
            print(f"  - {key}: {value_type} = {value_preview}")


def main() -> None:
    """Main verification function."""
    setup_logging()

    print("\n" + "="*70)
    print("STARTUP MARKET ANALYZER - DATA VERIFICATION")
    print("="*70)

    try:
        # Verify Raw Layer
        print("\n📊 RAW LAYER")
        show_collection_stats("raw_startups")

        # Verify Clean Layer
        print("\n🧹 CLEAN LAYER")
        show_collection_stats("clean_startups")

        # Verify Aggregated Layer
        print("\n📈 AGGREGATED LAYER")
        show_collection_stats("aggregated_sectors")

        print("\n" + "="*70)
        print("✅ Verification Complete!")
        print("="*70)

    except Exception as e:
        logger.error(f"Error during verification: {e}")
        print(f"\n❌ Error: {e}")
        print("Make sure MongoDB is running and data has been ingested.")


if __name__ == "__main__":
    main()

