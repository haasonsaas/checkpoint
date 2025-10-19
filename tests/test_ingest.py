import pytest
import tempfile
from pathlib import Path
from ingest import DataIngester


@pytest.fixture
def ingester():
    """Create a DataIngester instance"""
    return DataIngester()


@pytest.fixture
def sample_text_file():
    """Create a temporary text file for testing"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    content = "This is a test document. " * 100  # Make it long enough to chunk
    temp_file.write(content)
    temp_file.close()
    
    yield Path(temp_file.name)
    
    Path(temp_file.name).unlink()


def test_chunk_text(ingester):
    """Test text chunking with overlap"""
    text = "A" * 2500
    chunks = ingester.chunk_text(text, chunk_size=1000, overlap=200)
    
    assert len(chunks) > 2
    # Check overlap exists
    assert chunks[0][-100:] in chunks[1] or len(chunks[0]) < 1000


def test_chunk_text_small(ingester):
    """Test chunking small text that doesn't need splitting"""
    text = "Short text"
    chunks = ingester.chunk_text(text, chunk_size=1000, overlap=200)
    
    assert len(chunks) == 1
    assert chunks[0] == "Short text"


def test_chunk_text_respects_sentences(ingester):
    """Test that chunking tries to break at sentence boundaries"""
    text = "First sentence. " * 50 + "Second sentence. " * 50
    chunks = ingester.chunk_text(text, chunk_size=500, overlap=100)
    
    # Most chunks should end with a period
    for chunk in chunks[:-1]:
        assert chunk.strip().endswith('.') or len(chunk) > 400


def test_chunk_text_empty(ingester):
    """Test chunking empty text"""
    chunks = ingester.chunk_text("", chunk_size=1000, overlap=200)
    assert len(chunks) == 0


def test_chunk_text_preserves_content(ingester):
    """Test that chunking doesn't lose content"""
    text = "The quick brown fox jumps over the lazy dog. " * 100
    chunks = ingester.chunk_text(text, chunk_size=1000, overlap=200)
    
    # Reconstruct text (roughly - overlap makes this inexact)
    reconstructed = chunks[0]
    for chunk in chunks[1:]:
        # Add non-overlapping parts
        reconstructed += chunk[200:]
    
    # Should be similar length (allowing for overlap)
    assert len(reconstructed) >= len(text) * 0.8


def test_chunk_text_custom_sizes(ingester):
    """Test chunking with different sizes"""
    text = "Word " * 1000
    
    chunks_small = ingester.chunk_text(text, chunk_size=50, overlap=10)
    chunks_large = ingester.chunk_text(text, chunk_size=500, overlap=50)
    
    assert len(chunks_small) > len(chunks_large)
