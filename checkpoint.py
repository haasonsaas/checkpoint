import argparse
import json
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import Checkpoint
from vector_store import VectorStore


class CheckpointManager:
    def __init__(self):
        self.vector_store = VectorStore()
    
    def create_checkpoint(
        self,
        version: str,
        description: str,
        config: dict = None,
        metadata: dict = None,
        db: Session = None
    ) -> Checkpoint:
        """Create a new checkpoint version"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            # Check if version already exists
            existing = db.query(Checkpoint).filter(Checkpoint.version == version).first()
            if existing:
                raise ValueError(f"Checkpoint version {version} already exists")
            
            # Create new checkpoint
            checkpoint = Checkpoint(
                version=version,
                description=description,
                config=json.dumps(config or {}),
                metadata=json.dumps(metadata or {})
            )
            
            db.add(checkpoint)
            db.commit()
            db.refresh(checkpoint)
            
            print(f"Created checkpoint {version}")
            return checkpoint
            
        finally:
            if should_close:
                db.close()
    
    def list_checkpoints(self, db: Session = None) -> list:
        """List all checkpoints"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            checkpoints = db.query(Checkpoint).order_by(Checkpoint.created_at.desc()).all()
            return checkpoints
        finally:
            if should_close:
                db.close()
    
    def get_checkpoint(self, version: str, db: Session = None) -> Checkpoint:
        """Get a specific checkpoint"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            checkpoint = db.query(Checkpoint).filter(Checkpoint.version == version).first()
            if not checkpoint:
                raise ValueError(f"Checkpoint {version} not found")
            return checkpoint
        finally:
            if should_close:
                db.close()
    
    def set_active_checkpoint(self, version: str, db: Session = None):
        """Set a checkpoint as the active one"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            # Deactivate all checkpoints
            db.query(Checkpoint).update({"is_active": False})
            
            # Activate the specified one
            checkpoint = db.query(Checkpoint).filter(Checkpoint.version == version).first()
            if not checkpoint:
                raise ValueError(f"Checkpoint {version} not found")
            
            checkpoint.is_active = True
            db.commit()
            
            print(f"Set {version} as active checkpoint")
            
        finally:
            if should_close:
                db.close()
    
    def get_active_checkpoint(self, db: Session = None) -> Checkpoint:
        """Get the currently active checkpoint"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            checkpoint = db.query(Checkpoint).filter(Checkpoint.is_active == True).first()
            return checkpoint
        finally:
            if should_close:
                db.close()
    
    def delete_checkpoint(self, version: str, db: Session = None):
        """Delete a checkpoint and its vector data"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            checkpoint = db.query(Checkpoint).filter(Checkpoint.version == version).first()
            if not checkpoint:
                raise ValueError(f"Checkpoint {version} not found")
            
            # Delete vector collection
            self.vector_store.delete_collection(version)
            
            # Delete checkpoint record
            db.delete(checkpoint)
            db.commit()
            
            print(f"Deleted checkpoint {version}")
            
        finally:
            if should_close:
                db.close()
    
    def update_checkpoint_config(
        self,
        version: str,
        config: dict,
        db: Session = None
    ):
        """Update checkpoint configuration"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            checkpoint = db.query(Checkpoint).filter(Checkpoint.version == version).first()
            if not checkpoint:
                raise ValueError(f"Checkpoint {version} not found")
            
            checkpoint.config = json.dumps(config)
            db.commit()
            
            print(f"Updated config for checkpoint {version}")
            
        finally:
            if should_close:
                db.close()


def main():
    parser = argparse.ArgumentParser(description="Manage ghost checkpoints")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create checkpoint
    create_parser = subparsers.add_parser("create", help="Create a new checkpoint")
    create_parser.add_argument("--version", type=str, required=True, help="Checkpoint version")
    create_parser.add_argument("--description", type=str, required=True, help="Description")
    create_parser.add_argument("--config", type=str, help="Config JSON string")
    
    # List checkpoints
    subparsers.add_parser("list", help="List all checkpoints")
    
    # Set active
    activate_parser = subparsers.add_parser("activate", help="Set active checkpoint")
    activate_parser.add_argument("--version", type=str, required=True, help="Checkpoint version")
    
    # Delete checkpoint
    delete_parser = subparsers.add_parser("delete", help="Delete a checkpoint")
    delete_parser.add_argument("--version", type=str, required=True, help="Checkpoint version")
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    manager = CheckpointManager()
    
    if args.command == "create":
        config = json.loads(args.config) if args.config else {}
        manager.create_checkpoint(args.version, args.description, config)
        
    elif args.command == "list":
        checkpoints = manager.list_checkpoints()
        print("\nCheckpoints:")
        for cp in checkpoints:
            active = " [ACTIVE]" if cp.is_active else ""
            print(f"  {cp.version}: {cp.description}{active}")
            print(f"    Created: {cp.created_at}")
            
    elif args.command == "activate":
        manager.set_active_checkpoint(args.version)
        
    elif args.command == "delete":
        confirm = input(f"Delete checkpoint {args.version}? This cannot be undone. (yes/no): ")
        if confirm.lower() == "yes":
            manager.delete_checkpoint(args.version)
        else:
            print("Cancelled")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
