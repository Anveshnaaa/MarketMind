"""MongoDB operations."""

import logging
from typing import Any, Optional
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError

from src.database.connection import get_database

logger = logging.getLogger(__name__)


def insert_documents(
    collection_name: str,
    documents: list[dict[str, Any]],
    batch_size: int = 1000,
) -> int:
    """Insert documents in batches."""
    db = get_database()
    collection = db[collection_name]

    inserted_count = 0
    total_docs = len(documents)

    for i in range(0, total_docs, batch_size):
        batch = documents[i : i + batch_size]
        try:
            result = collection.insert_many(batch, ordered=False)
            inserted_count += len(result.inserted_ids)
            logger.info(
                f"Inserted batch {i // batch_size + 1}: "
                f"{len(result.inserted_ids)} documents "
                f"({inserted_count}/{total_docs} total)"
            )
        except BulkWriteError as e:
            inserted_count += e.details.get("nInserted", 0)
            logger.warning(
                f"Batch insert had some failures: {e.details.get('nInserted', 0)} "
                f"inserted, {len(e.details.get('writeErrors', []))} errors"
            )

    logger.info(f"Total documents inserted into {collection_name}: {inserted_count}")
    return inserted_count


def count_documents(collection_name: str, filter_dict: Optional[dict[str, Any]] = None) -> int:
    """Count documents."""
    db = get_database()
    collection = db[collection_name]
    count = collection.count_documents(filter_dict or {})
    return count


def get_schema_sample(collection_name: str, sample_size: int = 5) -> list[dict[str, Any]]:
    """Get sample documents."""
    db = get_database()
    collection = db[collection_name]
    samples = list(collection.find().limit(sample_size))
    return samples


def get_collection_stats(collection_name: str) -> dict[str, Any]:
    """Get collection stats."""
    db = get_database()
    collection = db[collection_name]

    stats = {
        "count": collection.count_documents({}),
        "indexes": list(collection.list_indexes()),
        "sample": get_schema_sample(collection_name, 1),
    }

    return stats


