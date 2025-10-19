import argparse
import os
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, init_db
from models import SourceDocument
from vector_store import VectorStore


class DataIngester:
    def __init__(self):
        self.vector_store = VectorStore()
        
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_len:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
        return [c for c in chunks if c]
    
    def ingest_text_file(
        self,
        filepath: Path,
        source_type: str,
        checkpoint_version: str,
        db: Session
    ):
        """Ingest a single text file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = self.chunk_text(content)
        
        metadata = {
            "filename": str(filepath),
            "source_type": source_type,
            "ingested_at": datetime.utcnow().isoformat()
        }
        
        # Add to vector store
        doc_ids = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {**metadata, "chunk_index": i}
            doc_id = f"{filepath.stem}_{i}"
            
            self.vector_store.add_documents(
                checkpoint_version=checkpoint_version,
                documents=[chunk],
                metadatas=[chunk_metadata],
                ids=[doc_id]
            )
            
            # Store in SQL database
            source_doc = SourceDocument(
                source_type=source_type,
                content=chunk,
                metadata=json.dumps(chunk_metadata),
                embedding_id=doc_id
            )
            db.add(source_doc)
            doc_ids.append(doc_id)
        
        db.commit()
        return doc_ids
    
    def ingest_directory(
        self,
        directory: Path,
        source_type: str,
        checkpoint_version: str,
        extensions: List[str] = None
    ):
        """Ingest all files from a directory"""
        if extensions is None:
            extensions = ['.txt', '.md', '.json', '.csv']
        
        db = SessionLocal()
        
        try:
            all_ids = []
            for filepath in directory.rglob('*'):
                if filepath.is_file() and filepath.suffix in extensions:
                    print(f"Ingesting {filepath}...")
                    ids = self.ingest_text_file(filepath, source_type, checkpoint_version, db)
                    all_ids.extend(ids)
            
            print(f"\nIngested {len(all_ids)} document chunks from {directory}")
            return all_ids
            
        finally:
            db.close()
    
    def ingest_json_messages(
        self,
        json_file: Path,
        checkpoint_version: str,
        message_field: str = "text"
    ):
        """Ingest messages from JSON file (e.g., Slack export)"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        db = SessionLocal()
        
        try:
            messages = data if isinstance(data, list) else [data]
            all_ids = []
            
            for i, msg in enumerate(messages):
                if isinstance(msg, dict) and message_field in msg:
                    text = msg[message_field]
                    
                    metadata = {
                        "source_type": "message",
                        "message_index": i,
                        **{k: v for k, v in msg.items() if k != message_field}
                    }
                    
                    doc_id = f"msg_{i}"
                    
                    self.vector_store.add_documents(
                        checkpoint_version=checkpoint_version,
                        documents=[text],
                        metadatas=[metadata],
                        ids=[doc_id]
                    )
                    
                    source_doc = SourceDocument(
                        source_type="message",
                        content=text,
                        metadata=json.dumps(metadata),
                        embedding_id=doc_id
                    )
                    db.add(source_doc)
                    all_ids.append(doc_id)
            
            db.commit()
            print(f"\nIngested {len(all_ids)} messages from {json_file}")
            return all_ids
            
        finally:
            db.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest data for digital ghost")
    parser.add_argument("--source", type=str, required=True, help="Source directory or file")
    parser.add_argument("--type", type=str, default="text", help="Source type (text, message, email, etc)")
    parser.add_argument("--checkpoint", type=str, default="0.1", help="Checkpoint version")
    parser.add_argument("--format", type=str, default="text", choices=["text", "json"], help="Source format")
    parser.add_argument("--extensions", type=str, default=".txt,.md,.json", help="File extensions to ingest (comma-separated)")
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    ingester = DataIngester()
    source_path = Path(args.source)
    
    if args.format == "json":
        ingester.ingest_json_messages(source_path, args.checkpoint)
    elif source_path.is_dir():
        extensions = [ext.strip() for ext in args.extensions.split(',')]
        ingester.ingest_directory(source_path, args.type, args.checkpoint, extensions)
    else:
        db = SessionLocal()
        try:
            ingester.ingest_text_file(source_path, args.type, args.checkpoint, db)
        finally:
            db.close()


if __name__ == "__main__":
    main()
