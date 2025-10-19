from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
from typing import Optional

from database import get_db, init_db
from models import (
    ChatRequest, ChatResponse, CheckpointCreate, CheckpointResponse,
    Checkpoint, Message
)
from ghost_engine import GhostEngine
from checkpoint import CheckpointManager
from vector_store import VectorStore

app = FastAPI(title="The Checkpoint - Digital Ghost API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
ghost_engine = GhostEngine()
checkpoint_manager = CheckpointManager()


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {
        "name": "The Checkpoint",
        "description": "Digital Ghost API",
        "version": "1.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message and get a response from the ghost"""
    try:
        # Determine checkpoint version
        if request.checkpoint_version:
            checkpoint = checkpoint_manager.get_checkpoint(request.checkpoint_version, db)
        else:
            checkpoint = checkpoint_manager.get_active_checkpoint(db)
            if not checkpoint:
                raise HTTPException(status_code=400, detail="No active checkpoint. Please specify a version.")
        
        # Get checkpoint config
        config = json.loads(checkpoint.config) if checkpoint.config else {}
        
        # Generate response
        result = ghost_engine.generate_response(
            user_message=request.message,
            checkpoint_version=checkpoint.version,
            db=db,
            checkpoint_config=config
        )
        
        return ChatResponse(
            response=result["response"],
            checkpoint_version=checkpoint.version,
            sources=result["sources"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@app.post("/chat/regenerate", response_model=ChatResponse)
async def regenerate(
    checkpoint_version: Optional[str] = None,
    temperature: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Regenerate the last response"""
    try:
        # Determine checkpoint version
        if checkpoint_version:
            checkpoint = checkpoint_manager.get_checkpoint(checkpoint_version, db)
        else:
            checkpoint = checkpoint_manager.get_active_checkpoint(db)
        
        if not checkpoint:
            raise HTTPException(status_code=400, detail="No active checkpoint")
        
        result = ghost_engine.regenerate_response(
            checkpoint_version=checkpoint.version,
            db=db,
            temperature_override=temperature
        )
        
        return ChatResponse(
            response=result["response"],
            checkpoint_version=checkpoint.version,
            sources=result["sources"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{checkpoint_version}")
async def get_history(
    checkpoint_version: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get conversation history for a checkpoint"""
    messages = (
        db.query(Message)
        .filter(Message.checkpoint_version == checkpoint_version)
        .order_by(Message.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in reversed(messages)
    ]


@app.post("/checkpoints", response_model=CheckpointResponse)
async def create_checkpoint(
    checkpoint: CheckpointCreate,
    db: Session = Depends(get_db)
):
    """Create a new checkpoint"""
    try:
        cp = checkpoint_manager.create_checkpoint(
            version=checkpoint.version,
            description=checkpoint.description,
            config=checkpoint.config,
            metadata=checkpoint.metadata,
            db=db
        )
        return CheckpointResponse.from_orm(cp)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/checkpoints", response_model=list[CheckpointResponse])
async def list_checkpoints(db: Session = Depends(get_db)):
    """List all checkpoints"""
    checkpoints = checkpoint_manager.list_checkpoints(db)
    return [CheckpointResponse.from_orm(cp) for cp in checkpoints]


@app.get("/checkpoints/{version}", response_model=CheckpointResponse)
async def get_checkpoint(version: str, db: Session = Depends(get_db)):
    """Get a specific checkpoint"""
    try:
        cp = checkpoint_manager.get_checkpoint(version, db)
        return CheckpointResponse.from_orm(cp)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/checkpoints/{version}/activate")
async def activate_checkpoint(version: str, db: Session = Depends(get_db)):
    """Set a checkpoint as active"""
    try:
        checkpoint_manager.set_active_checkpoint(version, db)
        return {"message": f"Checkpoint {version} is now active"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/checkpoints/{version}")
async def delete_checkpoint(version: str, db: Session = Depends(get_db)):
    """Delete a checkpoint"""
    try:
        checkpoint_manager.delete_checkpoint(version, db)
        return {"message": f"Checkpoint {version} deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/stats/{checkpoint_version}")
async def get_stats(checkpoint_version: str, db: Session = Depends(get_db)):
    """Get statistics for a checkpoint"""
    message_count = (
        db.query(Message)
        .filter(Message.checkpoint_version == checkpoint_version)
        .count()
    )
    
    return {
        "checkpoint_version": checkpoint_version,
        "total_messages": message_count,
        "conversation_count": message_count // 2  # Approximate
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
