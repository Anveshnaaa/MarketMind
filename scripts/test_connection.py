"""Test connection to MongoDB sharded cluster."""

from src.database.connection import get_database, get_mongo_client

def test_connection():
    """Test connection to mongos."""
    print("Testing connection to MongoDB sharded cluster...")
    
    # Test client connection
    client = get_mongo_client()
    hello = client.admin.command("hello")
    
    print(f"✓ Connected to: {hello.get('msg', 'unknown')}")
    print(f"✓ Connection type: {'mongos (sharded cluster)' if hello.get('msg') == 'isdbgrid' else 'mongod (replica set/standalone)'}")
    
    # Test database access
    db = get_database()
    print(f"✓ Database: {db.name}")
    
    collections = db.list_collection_names()
    print(f"✓ Collections: {collections if collections else '(none yet - database is empty)'}")
    
    # Show sharding status
    sh_status = client.admin.command("shardingStatus")
    shards = sh_status.get("shards", [])
    print(f"✓ Number of shards: {len(shards)}")
    for shard in shards:
        print(f"  - {shard['_id']}")
    
    print("\n✅ Connection test successful!")
    print("Ready to run data pipeline.")

if __name__ == "__main__":
    test_connection()
