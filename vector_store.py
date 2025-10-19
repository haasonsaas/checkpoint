import chromadb
from chromadb.config import Settings
from openai import OpenAI
import os
from typing import List, Dict
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class VectorStore:
    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            persist_directory = os.getenv("CHROMA_PATH", "./chroma_db")
        
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
    def get_or_create_collection(self, checkpoint_version: str):
        """Get or create a collection for a specific checkpoint version"""
        collection_name = f"ghost_{checkpoint_version.replace('.', '_')}"
        return self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"checkpoint_version": checkpoint_version}
        )
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        response = client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def add_documents(
        self,
        checkpoint_version: str,
        documents: List[str],
        metadatas: List[Dict] = None,
        ids: List[str] = None
    ):
        """Add documents to the vector store"""
        collection = self.get_or_create_collection(checkpoint_version)
        
        # Generate embeddings
        embeddings = [self.get_embedding(doc) for doc in documents]
        
        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in documents],
            ids=ids
        )
        
        return ids
    
    def query(
        self,
        checkpoint_version: str,
        query_text: str,
        n_results: int = 5
    ) -> Dict:
        """Query the vector store for relevant documents"""
        collection = self.get_or_create_collection(checkpoint_version)
        
        query_embedding = self.get_embedding(query_text)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }
    
    def delete_collection(self, checkpoint_version: str):
        """Delete a checkpoint's collection"""
        collection_name = f"ghost_{checkpoint_version.replace('.', '_')}"
        try:
            self.chroma_client.delete_collection(name=collection_name)
        except:
            pass
    
    def list_collections(self) -> List[str]:
        """List all checkpoint collections"""
        collections = self.chroma_client.list_collections()
        return [c.name for c in collections if c.name.startswith("ghost_")]
