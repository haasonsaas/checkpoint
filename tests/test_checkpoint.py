import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from checkpoint import CheckpointManager
from models import Base, Checkpoint


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db_url = f"sqlite:///{temp_db.name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal()
    
    os.unlink(temp_db.name)


@pytest.fixture
def manager():
    """Create a CheckpointManager instance"""
    return CheckpointManager()


def test_create_checkpoint(manager, test_db):
    """Test creating a new checkpoint"""
    checkpoint = manager.create_checkpoint(
        version="0.1",
        description="Test checkpoint",
        config={"test": "config"},
        db=test_db
    )
    
    assert checkpoint.version == "0.1"
    assert checkpoint.description == "Test checkpoint"
    assert checkpoint.is_active == False


def test_create_duplicate_checkpoint(manager, test_db):
    """Test that duplicate versions raise an error"""
    manager.create_checkpoint(version="0.1", description="First", db=test_db)
    
    with pytest.raises(ValueError, match="already exists"):
        manager.create_checkpoint(version="0.1", description="Second", db=test_db)


def test_list_checkpoints(manager, test_db):
    """Test listing all checkpoints"""
    manager.create_checkpoint(version="0.1", description="First", db=test_db)
    manager.create_checkpoint(version="0.2", description="Second", db=test_db)
    
    checkpoints = manager.list_checkpoints(db=test_db)
    
    assert len(checkpoints) == 2
    assert checkpoints[0].version in ["0.1", "0.2"]


def test_get_checkpoint(manager, test_db):
    """Test getting a specific checkpoint"""
    manager.create_checkpoint(version="0.1", description="Test", db=test_db)
    
    checkpoint = manager.get_checkpoint(version="0.1", db=test_db)
    
    assert checkpoint.version == "0.1"
    assert checkpoint.description == "Test"


def test_get_nonexistent_checkpoint(manager, test_db):
    """Test getting a checkpoint that doesn't exist"""
    with pytest.raises(ValueError, match="not found"):
        manager.get_checkpoint(version="0.999", db=test_db)


def test_set_active_checkpoint(manager, test_db):
    """Test setting a checkpoint as active"""
    manager.create_checkpoint(version="0.1", description="First", db=test_db)
    manager.create_checkpoint(version="0.2", description="Second", db=test_db)
    
    manager.set_active_checkpoint(version="0.2", db=test_db)
    
    active = manager.get_active_checkpoint(db=test_db)
    assert active.version == "0.2"
    
    # Only one should be active
    checkpoints = manager.list_checkpoints(db=test_db)
    active_count = sum(1 for cp in checkpoints if cp.is_active)
    assert active_count == 1


def test_update_checkpoint_config(manager, test_db):
    """Test updating checkpoint configuration"""
    manager.create_checkpoint(version="0.1", description="Test", db=test_db)
    
    new_config = {"temperature": 0.7, "personality": "formal"}
    manager.update_checkpoint_config(version="0.1", config=new_config, db=test_db)
    
    checkpoint = manager.get_checkpoint(version="0.1", db=test_db)
    import json
    assert json.loads(checkpoint.config) == new_config


def test_get_active_checkpoint_none(manager, test_db):
    """Test getting active checkpoint when none exists"""
    manager.create_checkpoint(version="0.1", description="Test", db=test_db)
    
    active = manager.get_active_checkpoint(db=test_db)
    assert active is None
