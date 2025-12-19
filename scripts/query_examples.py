"""Example queries demonstrating MongoDB query performance and capabilities."""

import logging
import time
from pymongo.collection import Collection

from src.database.connection import get_database
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def time_query(func):
    """Decorator to time query execution."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    return wrapper


@time_query
def query_top_sectors_by_funding(db):
    """Query: Top 5 sectors by total funding."""
    collection: Collection = db["aggregated_sectors"]
    pipeline = [
        {"$sort": {"total_funding": -1}},
        {"$limit": 5},
        {"$project": {
            "sector": 1,
            "total_funding": 1,
            "total_startups": 1,
            "avg_funding_per_startup": 1
        }}
    ]
    return list(collection.aggregate(pipeline))


@time_query
def query_high_growth_low_risk(db):
    """Query: Sectors with high growth and low risk."""
    collection: Collection = db["aggregated_sectors"]
    pipeline = [
        {
            "$match": {
                "growth_rate": {"$gt": 0.1},
                "risk_score": {"$lt": 0.3}
            }
        },
        {"$sort": {"growth_rate": -1}},
        {"$project": {
            "sector": 1,
            "growth_rate": 1,
            "risk_score": 1,
            "total_startups": 1
        }}
    ]
    return list(collection.aggregate(pipeline))


@time_query
def query_sector_capital_distribution(db, sector: str):
    """Query: Capital distribution for a specific sector."""
    collection: Collection = db["aggregated_sectors"]
    result = collection.find_one(
        {"sector": sector},
        {"sector": 1, "capital_distribution": 1, "total_startups": 1}
    )
    return result


@time_query
def query_startups_by_sector_and_funding(db, sector: str, min_funding: float):
    """Query: Startups in a sector with minimum funding."""
    collection: Collection = db["clean_startups"]
    pipeline = [
        {
            "$match": {
                "sector": sector,
                "total_funding": {"$gte": min_funding}
            }
        },
        {"$count": "count"}
    ]
    result = list(collection.aggregate(pipeline))
    return result[0]["count"] if result else 0


@time_query
def query_sector_timeline_analysis(db):
    """Query: Sector founding timeline analysis."""
    collection: Collection = db["aggregated_sectors"]
    pipeline = [
        {
            "$project": {
                "sector": 1,
                "founded_year_min": 1,
                "founded_year_max": 1,
                "year_span": {
                    "$subtract": ["$founded_year_max", "$founded_year_min"]
                },
                "total_startups": 1
            }
        },
        {"$sort": {"year_span": -1}},
        {"$limit": 10}
    ]
    return list(collection.aggregate(pipeline))


def main() -> None:
    """Run example queries and show performance."""
    setup_logging()

    print("\n" + "="*70)
    print("MONGODB QUERY EXAMPLES & PERFORMANCE")
    print("="*70)

    db = get_database()

    # Query 1: Top sectors by funding
    print("\n📊 Query 1: Top 5 Sectors by Total Funding")
    print("-" * 70)
    results, elapsed = query_top_sectors_by_funding(db)
    for i, sector in enumerate(results, 1):
        print(f"{i}. {sector['sector']}: ${sector['total_funding']/1e6:.2f}M "
              f"({sector['total_startups']:,} startups)")
    print(f"\n⏱️  Query Time: {elapsed*1000:.2f}ms")

    # Query 2: High growth, low risk sectors
    print("\n📈 Query 2: High Growth, Low Risk Sectors")
    print("-" * 70)
    results, elapsed = query_high_growth_low_risk(db)
    for sector in results[:5]:
        print(f"- {sector['sector']}: Growth={sector['growth_rate']*100:.1f}%, "
              f"Risk={sector['risk_score']*100:.1f}%")
    print(f"\n⏱️  Query Time: {elapsed*1000:.2f}ms")

    # Query 3: Capital distribution
    print("\n💰 Query 3: Capital Distribution (Technology Sector)")
    print("-" * 70)
    result, elapsed = query_sector_capital_distribution(db, "Technology")
    if result and result.get("capital_distribution"):
        for range_name, count in result["capital_distribution"].items():
            print(f"  {range_name}: {count:,} startups")
    print(f"\n⏱️  Query Time: {elapsed*1000:.2f}ms")

    # Query 4: Filtered startup count
    print("\n🔍 Query 4: Startups in Technology with $1M+ Funding")
    print("-" * 70)
    count, elapsed = query_startups_by_sector_and_funding(db, "Technology", 1000000)
    print(f"  Count: {count:,} startups")
    print(f"\n⏱️  Query Time: {elapsed*1000:.2f}ms")

    # Query 5: Timeline analysis
    print("\n⏱️  Query 5: Sector Timeline Analysis (Top 10 by Year Span)")
    print("-" * 70)
    results, elapsed = query_sector_timeline_analysis(db)
    for sector in results:
        print(f"- {sector['sector']}: {sector['founded_year_min']}-{sector['founded_year_max']} "
              f"({sector.get('year_span', 'N/A')} years, {sector['total_startups']:,} startups)")
    print(f"\n⏱️  Query Time: {elapsed*1000:.2f}ms")

    print("\n" + "="*70)
    print("✅ Query Examples Complete!")
    print("="*70)
    print("\n💡 Note: Indexes on 'sector', 'total_startups', 'growth_rate', and 'risk_score'")
    print("   improve query performance for aggregated collections.")


if __name__ == "__main__":
    main()

