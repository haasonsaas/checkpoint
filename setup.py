#!/usr/bin/env python3
"""Setup script to initialize the digital ghost system"""

import os
import sys
from pathlib import Path
from database import init_db
from checkpoint import CheckpointManager

def setup():
    print("🔮 Setting up The Checkpoint - Digital Ghost System\n")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("📝 Creating .env file from template...")
        
        # Copy .env.example to .env
        example_file = Path(".env.example")
        if example_file.exists():
            env_file.write_text(example_file.read_text())
            print("✅ Created .env file")
            print("\n⚠️  Please edit .env and add your OPENAI_API_KEY\n")
        else:
            print("❌ .env.example not found. Please create .env manually.")
            return False
    else:
        print("✅ .env file found")
    
    # Check for OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OPENAI_API_KEY not set in .env file")
        print("   Please add your OpenAI API key to continue.")
        return False
    
    print("✅ OpenAI API key configured")
    
    # Initialize database
    print("\n📊 Initializing database...")
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Create data directory
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    print("✅ Data directory created")
    
    # Create chroma directory
    chroma_dir = Path(os.getenv("CHROMA_PATH", "./chroma_db"))
    chroma_dir.mkdir(exist_ok=True)
    print("✅ Vector database directory created")
    
    # Create initial checkpoint
    print("\n📌 Creating initial checkpoint...")
    manager = CheckpointManager()
    try:
        manager.create_checkpoint(
            version="0.1",
            description="Initial checkpoint - base configuration",
            config={
                "personality_note": "Base personality without specific tuning",
                "temperature_note": "Using default temperature"
            },
            metadata={
                "created_by": "setup",
                "is_initial": True
            }
        )
        manager.set_active_checkpoint("0.1")
        print("✅ Created checkpoint v0.1")
    except ValueError as e:
        if "already exists" in str(e):
            print("ℹ️  Checkpoint v0.1 already exists")
        else:
            print(f"❌ Checkpoint creation failed: {e}")
            return False
    
    # Create consent template
    consent_file = data_dir / "CONSENT.md"
    if not consent_file.exists():
        consent_file.write_text("""# Consent Documentation

This file should document consent for creating a digital ghost.

## Consent Statement

I, [NAME], hereby consent to the creation of a digital ghost based on my writings and communications.

**Signed:** [SIGNATURE]  
**Date:** [DATE]

## Scope of Consent

- [ ] Personal emails
- [ ] Work communications
- [ ] Social media posts
- [ ] Documents and writings
- [ ] Code and technical writing

## Limitations

[Describe any limitations or restrictions on use]

## Duration

This consent is valid for [DURATION] and may be revoked at any time.
""")
        print("✅ Created consent template at data/CONSENT.md")
    
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Add source data to ./data directory")
    print("  2. Fill out data/CONSENT.md with appropriate consent")
    print("  3. Ingest data: python ingest.py --source ./data --checkpoint 0.1")
    print("  4. Start server: python server.py")
    print("  5. Start chatting: python cli.py chat")
    print("\nOr use the web interface:")
    print("  cd web && npm install && npm run dev")
    print()
    
    return True


if __name__ == "__main__":
    success = setup()
    sys.exit(0 if success else 1)
