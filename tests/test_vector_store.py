import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from vector_store import VectorStore


@pytest.fixture
def temp_db_path():
    """Create a temporary directory for test database"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_openai():
    """Mock OpenAI embedding responses"""
    with patch('vector_store.client') as mock_client:
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response
        yield mock_client


def test_vector_store_initialization(temp_db_path):
    """Test VectorStore can be initialized"""
    store = VectorStore(persist_directory=temp_db_path)
    assert store is not None
    assert store.embedding_model == "text-embedding-3-small"


def test_create_collection(temp_db_path, mock_openai):
    """Test creating a collection for a checkpoint"""
    store = VectorStore(persist_directory=temp_db_path)
    collection = store.get_or_create_collection("0.1")
    assert collection is not None


def test_add_documents(temp_db_path, mock_openai):
    """Test adding documents to vector store"""
    store = VectorStore(persist_directory=temp_db_path)
    
    documents = ["This is test document 1", "This is test document 2"]
    ids = store.add_documents(
        checkpoint_version="0.1",
        documents=documents
    )
    
    assert len(ids) == 2
    assert mock_openai.embeddings.create.call_count == 2


def test_query_documents(temp_db_path, mock_openai):
    """Test querying documents from vector store"""
    store = VectorStore(persist_directory=temp_db_path)
    
    # Add documents
    documents = ["The cat sat on the mat", "The dog played in the park"]
    store.add_documents(
        checkpoint_version="0.1",
        documents=documents
    )
    
    # Query
    results = store.query(
        checkpoint_version="0.1",
        query_text="cat",
        n_results=1
    )
    
    assert "documents" in results
    assert len(results["documents"]) <= 1


def test_delete_collection(temp_db_path, mock_openai):
    """Test deleting a checkpoint collection"""
    store = VectorStore(persist_directory=temp_db_path)
    
    # Create and populate collection
    store.add_documents(
        checkpoint_version="0.1",
        documents=["test document"]
    )
    
    # Delete
    store.delete_collection("0.1")
    
    # Should be able to create again
    collection = store.get_or_create_collection("0.1")
    assert collection is not None


def test_list_collections(temp_db_path, mock_openai):
    """Test listing all checkpoint collections"""
    store = VectorStore(persist_directory=temp_db_path)
    
    # Create multiple collections
    store.get_or_create_collection("0.1")
    store.get_or_create_collection("0.2")
    
    collections = store.list_collections()
    assert len(collections) >= 2
    assert any("0_1" in c for c in collections)
    assert any("0_2" in c for c in collections)
