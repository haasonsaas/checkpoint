from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()


class Checkpoint(Base):
    __tablename__ = "checkpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    config = Column(Text)  # JSON string
    is_active = Column(Boolean, default=False)
    metadata = Column(Text)  # JSON string


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    checkpoint_version = Column(String, index=True)
    role = Column(String)  # user, assistant, system
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SourceDocument(Base):
    __tablename__ = "source_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String)  # email, slack, github, doc, etc
    content = Column(Text)
    metadata = Column(Text)  # JSON string
    ingested_at = Column(DateTime, default=datetime.utcnow)
    embedding_id = Column(String, index=True)


# Pydantic models for API
class CheckpointCreate(BaseModel):
    version: str
    description: str
    config: dict = {}
    metadata: dict = {}


class CheckpointResponse(BaseModel):
    id: int
    version: str
    description: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    checkpoint_version: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    checkpoint_version: str
    sources: list[dict] = []
