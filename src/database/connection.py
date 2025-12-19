"""MongoDB connection."""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.utils.config import get_config

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    """Get MongoDB client (connects to mongos router for sharded cluster).
    
    Note: When running from host machine, use directConnection=True.
    When running from Docker (same network), don't use directConnection.
    """
    global _client
    if _client is None:
        config = get_config()

        # For sharded cluster, connect to mongos router
        host = config.mongodb_host
        
        # Build connection string with or without authentication
        if config.mongodb_username and config.mongodb_password:
            connection_string = (
                f"mongodb://{config.mongodb_username}:{config.mongodb_password}"
                f"@{host}:{config.mongodb_port}/"
                f"?authSource={config.mongodb_auth_source}"
            )
        else:
            connection_string = f"mongodb://{host}:{config.mongodb_port}/"

        try:
            # Use directConnection=True when connecting from host to avoid
            # DNS resolution issues with internal Docker hostnames
            # When running from within Docker network, this can be False
            use_direct = host == "localhost"
            
            _client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                directConnection=use_direct,
            )
            _client.admin.command("ping")
            
            # Check connection type
            hello = _client.admin.command("hello")
            conn_type = "mongos" if hello.get("msg") == "isdbgrid" else "mongod"
            logger.info(f"Connected to MongoDB {conn_type} at {host}:{config.mongodb_port}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    return _client


def get_database() -> Database:
    """Get database."""
    config = get_config()
    client = get_mongo_client()
    return client[config.mongodb_database]


