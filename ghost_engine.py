from openai import OpenAI
from typing import List, Dict, Optional
import os
import json
from vector_store import VectorStore
from models import Message
from sqlalchemy.orm import Session

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class GhostEngine:
    """Core engine for generating responses in the voice of the archived person"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.completion_model = os.getenv("COMPLETION_MODEL", "gpt-4-turbo-preview")
        self.temperature = float(os.getenv("TEMPERATURE", "0.8"))
        self.max_context_messages = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))
    
    def build_system_prompt(
        self,
        checkpoint_version: str,
        relevant_docs: List[str],
        checkpoint_config: Dict = None
    ) -> str:
        """Build the system prompt with context from vector store"""
        
        base_prompt = """You are a digital ghost - an AI approximation of a person based on their writing.

Your purpose is to respond in a way that feels authentic to their communication style, thinking patterns, and personality as captured in their archived text.

IMPORTANT GUIDELINES:
- Stay true to their voice, including quirks, humor, and speech patterns
- If you don't know something they would know, acknowledge the limitation
- You are not them - you are a reflection, a checkpoint, an approximation
- When appropriate, acknowledge your nature as a model

Here is context from their writing:

"""
        
        # Add relevant documents
        for i, doc in enumerate(relevant_docs, 1):
            base_prompt += f"\n--- Context {i} ---\n{doc}\n"
        
        # Add checkpoint-specific configuration
        if checkpoint_config:
            if "personality_note" in checkpoint_config:
                base_prompt += f"\n\nPERSONALITY NOTE: {checkpoint_config['personality_note']}"
            if "temperature_note" in checkpoint_config:
                base_prompt += f"\n{checkpoint_config['temperature_note']}"
        
        return base_prompt
    
    def get_conversation_history(
        self,
        db: Session,
        checkpoint_version: str,
        limit: int = None
    ) -> List[Dict[str, str]]:
        """Retrieve recent conversation history"""
        if limit is None:
            limit = self.max_context_messages
        
        messages = (
            db.query(Message)
            .filter(Message.checkpoint_version == checkpoint_version)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        
        # Reverse to get chronological order
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]
    
    def generate_response(
        self,
        user_message: str,
        checkpoint_version: str,
        db: Session,
        checkpoint_config: Dict = None,
        n_context_docs: int = 5
    ) -> Dict:
        """Generate a response in the person's voice"""
        
        # Query vector store for relevant context
        query_results = self.vector_store.query(
            checkpoint_version=checkpoint_version,
            query_text=user_message,
            n_results=n_context_docs
        )
        
        relevant_docs = query_results["documents"]
        
        # Build system prompt
        system_prompt = self.build_system_prompt(
            checkpoint_version,
            relevant_docs,
            checkpoint_config
        )
        
        # Get conversation history
        history = self.get_conversation_history(db, checkpoint_version)
        
        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add history
        messages.extend(history)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        response = client.chat.completions.create(
            model=self.completion_model,
            messages=messages,
            temperature=self.temperature
        )
        
        assistant_message = response.choices[0].message.content
        
        # Store messages in database
        user_msg = Message(
            checkpoint_version=checkpoint_version,
            role="user",
            content=user_message
        )
        assistant_msg = Message(
            checkpoint_version=checkpoint_version,
            role="assistant",
            content=assistant_message
        )
        
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()
        
        return {
            "response": assistant_message,
            "sources": [
                {
                    "content": doc,
                    "metadata": meta,
                    "relevance": 1 - dist
                }
                for doc, meta, dist in zip(
                    relevant_docs,
                    query_results["metadatas"],
                    query_results["distances"]
                )
            ]
        }
    
    def regenerate_response(
        self,
        checkpoint_version: str,
        db: Session,
        temperature_override: Optional[float] = None
    ) -> Dict:
        """Regenerate the last response with different parameters"""
        
        # Get last two messages (user + assistant)
        messages = (
            db.query(Message)
            .filter(Message.checkpoint_version == checkpoint_version)
            .order_by(Message.timestamp.desc())
            .limit(2)
            .all()
        )
        
        if len(messages) < 2:
            raise ValueError("No previous conversation to regenerate")
        
        # Delete the last assistant message
        db.delete(messages[0])
        db.commit()
        
        # Get the user message
        user_message = messages[1].content
        
        # Generate new response
        temp_backup = self.temperature
        if temperature_override is not None:
            self.temperature = temperature_override
        
        try:
            return self.generate_response(
                user_message,
                checkpoint_version,
                db
            )
        finally:
            self.temperature = temp_backup
