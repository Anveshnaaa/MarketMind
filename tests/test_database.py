"""Tests for database operations."""

import pytest
from unittest.mock import Mock, patch

from src.database.connection import get_mongo_client, get_database
from src.database.operations import count_documents, insert_documents


@patch("src.database.connection.MongoClient")
def test_get_mongo_client(mock_mongo_client: Mock) -> None:
    """Test MongoDB client creation."""
    mock_client_instance = Mock()
    mock_mongo_client.return_value = mock_client_instance
    mock_client_instance.admin.command.return_value = {"ok": 1}

    client = get_mongo_client()
    assert client is not None
    mock_mongo_client.assert_called_once()


@patch("src.database.connection.get_mongo_client")
def test_get_database(mock_get_client: Mock) -> None:
    """Test database retrieval."""
    mock_client = Mock()
    mock_db = Mock()
    mock_client.__getitem__.return_value = mock_db
    mock_get_client.return_value = mock_client

    db = get_database()
    assert db is not None


@patch("src.database.operations.get_database")
def test_count_documents(mock_get_db: Mock) -> None:
    """Test document counting."""
    mock_collection = Mock()
    mock_collection.count_documents.return_value = 100
    mock_db = Mock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db

    count = count_documents("test_collection")
    assert count == 100
    mock_collection.count_documents.assert_called_once_with({})


@patch("src.database.operations.get_database")
def test_insert_documents(mock_get_db: Mock) -> None:
    """Test document insertion."""
    mock_collection = Mock()
    mock_result = Mock()
    mock_result.inserted_ids = ["id1", "id2", "id3"]
    mock_collection.insert_many.return_value = mock_result
    mock_db = Mock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db

    documents = [{"name": "Test1"}, {"name": "Test2"}, {"name": "Test3"}]
    inserted = insert_documents("test_collection", documents)

    assert inserted == 3
    mock_collection.insert_many.assert_called_once()


