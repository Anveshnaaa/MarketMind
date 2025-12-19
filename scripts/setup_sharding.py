"""Setup sharding for collections in the MongoDB sharded cluster.

This script:
1. Enables sharding on the database
2. Creates shard keys for collections
3. Creates indexes for query performance
"""

import logging
from pymongo import MongoClient
from pymongo.errors import OperationFailure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_sharding() -> None:
    """Setup sharding for the startup_analytics database."""
    # Connect to mongos
    client = MongoClient("mongodb://localhost:27017/")
    
    try:
        # Verify we're connected to mongos
        hello_result = client.admin.command("hello")
        if hello_result.get("msg") != "isdbgrid":
            logger.error("Not connected to mongos! Please connect to the mongos router.")
            return
        
        logger.info("✓ Connected to mongos router")
        
        # Enable sharding on the database
        try:
            client.admin.command({"enableSharding": "startup_analytics"})
            logger.info("✓ Enabled sharding on startup_analytics database")
        except OperationFailure as e:
            if "already enabled" in str(e):
                logger.info("✓ Sharding already enabled on startup_analytics")
            else:
                raise
        
        # Shard the raw_startups collection with hashed _id
        # This provides even distribution for high-volume inserts
        try:
            client.admin.command({
                "shardCollection": "startup_analytics.raw_startups",
                "key": {"_id": "hashed"}
            })
            logger.info("✓ Sharded raw_startups with hashed _id key")
        except OperationFailure as e:
            if "already sharded" in str(e):
                logger.info("✓ raw_startups already sharded")
            else:
                logger.warning(f"Could not shard raw_startups: {e}")
        
        # Shard the clean_startups collection with compound key
        # This co-locates documents by sector for efficient aggregation
        try:
            # First ensure the shard key fields exist as an index
            db = client["startup_analytics"]
            db.clean_startups.create_index([("sector", 1), ("_id", 1)])
            
            client.admin.command({
                "shardCollection": "startup_analytics.clean_startups",
                "key": {"sector": 1, "_id": 1}
            })
            logger.info("✓ Sharded clean_startups with compound key {sector: 1, _id: 1}")
        except OperationFailure as e:
            if "already sharded" in str(e):
                logger.info("✓ clean_startups already sharded")
            else:
                logger.warning(f"Could not shard clean_startups: {e}")
        
        # Create indexes for query performance
        db = client["startup_analytics"]
        
        # Indexes on clean_startups
        logger.info("Creating indexes on clean_startups...")
        db.clean_startups.create_index([("sector", 1)])
        db.clean_startups.create_index([("founded_year", 1)])
        db.clean_startups.create_index([("status", 1)])
        logger.info("✓ Created indexes on clean_startups")
        
        # Indexes on aggregated_sectors
        # Note: aggregated_sectors is NOT sharded (small collection)
        logger.info("Creating indexes on aggregated_sectors...")
        db.aggregated_sectors.create_index([("sector", 1)], unique=True)
        db.aggregated_sectors.create_index([("total_startups", 1)])
        db.aggregated_sectors.create_index([("growth_rate", 1)])
        db.aggregated_sectors.create_index([("risk_score", 1)])
        logger.info("✓ Created indexes on aggregated_sectors")
        
        # Show sharding status
        logger.info("\n" + "="*60)
        logger.info("SHARDING STATUS")
        logger.info("="*60)
        
        status = client.admin.command("shardingStatus")
        
        # Show shards
        logger.info("\nShards:")
        for shard in status.get("shards", []):
            logger.info(f"  - {shard['_id']}: {shard['host']}")
        
        # Show databases
        logger.info("\nDatabases:")
        for db_info in status.get("databases", []):
            db_name = db_info.get("database", {}).get("_id")
            if db_name == "startup_analytics":
                logger.info(f"  - {db_name}")
                logger.info(f"    Primary: {db_info.get('database', {}).get('primary')}")
                logger.info(f"    Partitioned: {db_info.get('database', {}).get('partitioned')}")
                
                # Show collections
                collections = db_info.get("collections", {})
                if collections:
                    logger.info("    Collections:")
                    for coll_name, coll_info in collections.items():
                        logger.info(f"      * {coll_name}")
                        logger.info(f"        Shard Key: {coll_info.get('shardKey', 'N/A')}")
                        logger.info(f"        Unique: {coll_info.get('unique', False)}")
        
        logger.info("\n" + "="*60)
        logger.info("✓ Sharding setup complete!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error setting up sharding: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    setup_sharding()
