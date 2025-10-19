# System Architecture - The Checkpoint

## Overview

The Checkpoint is a digital ghost system that uses RAG (Retrieval-Augmented Generation) to create conversational AI approximations of people based on their written data.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Interfaces                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web UI     │  │  CLI Tool    │  │  API Client  │      │
│  │  (React)     │  │  (Python)    │  │    (HTTP)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
         ┌───────────────────────────────────────────┐
         │         FastAPI Server                     │
         │  ┌─────────────────────────────────────┐  │
         │  │       API Endpoints                  │  │
         │  │  /chat  /checkpoints  /history      │  │
         │  └─────────────────────────────────────┘  │
         └───────────────────┬───────────────────────┘
                             ▼
         ┌───────────────────────────────────────────┐
         │         Ghost Engine (Core)                │
         │  ┌─────────────────────────────────────┐  │
         │  │  • Context Retrieval                │  │
         │  │  • Prompt Construction              │  │
         │  │  • Response Generation              │  │
         │  │  • History Management               │  │
         │  └─────────────────────────────────────┘  │
         └───────┬───────────────────────┬───────────┘
                 ▼                       ▼
    ┌────────────────────┐   ┌────────────────────┐
    │   Vector Store      │   │  SQL Database      │
    │   (ChromaDB)        │   │  (SQLite)          │
    │                     │   │                     │
    │  • Embeddings       │   │  • Checkpoints     │
    │  • Semantic Search  │   │  • Messages        │
    │  • Per-checkpoint   │   │  • Source Docs     │
    │    collections      │   │  • Metadata        │
    └────────────────────┘   └────────────────────┘
                 ▲                       ▲
                 │                       │
         ┌───────┴───────────────────────┴───────┐
         │      Data Ingestion Pipeline           │
         │  ┌─────────────────────────────────┐  │
         │  │  • File readers                 │  │
         │  │  • Text chunking                │  │
         │  │  • Embedding generation         │  │
         │  │  • Storage management           │  │
         │  └─────────────────────────────────┘  │
         └─────────────────────────────────────┘
                             ▲
                             │
         ┌───────────────────────────────────────┐
         │       External Services                │
         │  ┌─────────────────────────────────┐  │
         │  │  OpenAI API                      │  │
         │  │  • text-embedding-3-small       │  │
         │  │  • gpt-4-turbo-preview          │  │
         │  └─────────────────────────────────┘  │
         └─────────────────────────────────────┘
```

## Component Details

### 1. Client Layer

**Web UI (React + Vite)**
- Modern single-page application
- Real-time chat interface
- Checkpoint switching
- Source visualization
- Markdown rendering

**CLI Tool (Python + Rich)**
- Interactive terminal interface
- Batch operations
- Scripting support
- System management

### 2. API Layer (FastAPI)

**Core Endpoints:**
- `POST /chat` - Send message and get response
- `POST /chat/regenerate` - Regenerate last response
- `GET /history/{version}` - Retrieve conversation history
- `POST /checkpoints` - Create new checkpoint
- `GET /checkpoints` - List all checkpoints
- `POST /checkpoints/{version}/activate` - Set active checkpoint
- `DELETE /checkpoints/{version}` - Delete checkpoint

**Features:**
- CORS support for web clients
- Request validation with Pydantic
- Automatic API documentation (Swagger/OpenAPI)
- Dependency injection for database sessions

### 3. Ghost Engine (Core Logic)

The heart of the system that orchestrates response generation:

```python
class GhostEngine:
    def generate_response(message, checkpoint, config):
        1. Query vector store for relevant context
        2. Build system prompt with context
        3. Retrieve conversation history
        4. Construct messages array
        5. Call OpenAI API
        6. Store messages in database
        7. Return response with sources
```

**Key Features:**
- RAG-based context retrieval
- Dynamic prompt construction
- Conversation history management
- Temperature control
- Source attribution

### 4. Storage Layer

**Vector Store (ChromaDB)**
- Persistent on-disk storage
- Per-checkpoint collections
- Cosine similarity search
- OpenAI embeddings integration

**SQL Database (SQLite)**
- Checkpoint metadata
- Conversation history
- Source document tracking
- Configuration storage

**Schema:**
```sql
checkpoints:
  - id, version, description, created_at
  - config (JSON), metadata (JSON)
  - is_active (boolean)

messages:
  - id, checkpoint_version, role
  - content, timestamp

source_documents:
  - id, source_type, content
  - metadata (JSON), embedding_id
  - ingested_at
```

### 5. Data Ingestion Pipeline

**Capabilities:**
- Multiple source formats (text, JSON, markdown)
- Intelligent text chunking with overlap
- Batch processing
- Metadata preservation
- Duplicate detection

**Process Flow:**
```
1. Read source files
2. Parse and extract text
3. Chunk text (1000 chars, 200 overlap)
4. Generate embeddings via OpenAI
5. Store in vector database
6. Store metadata in SQL database
```

### 6. Checkpoint System

Checkpoints are versioned snapshots that include:
- Vector database collection
- Configuration parameters
- Creation metadata
- Active status

**Use Cases:**
- Different data sets (v0.1: emails, v0.2: + messages)
- Different personalities (v0.1: formal, v0.2: casual)
- Experimentation (try different configs)
- Time-based archives (monthly snapshots)

## Data Flow

### Chat Request Flow

```
1. User sends message via client
   ↓
2. API receives request, validates
   ↓
3. Ghost Engine queries vector store for context
   ↓
4. Engine retrieves conversation history
   ↓
5. System prompt constructed with context
   ↓
6. OpenAI API generates response
   ↓
7. Response and sources stored in DB
   ↓
8. Response returned to client
   ↓
9. Client displays formatted response
```

### Data Ingestion Flow

```
1. User provides source data directory
   ↓
2. Ingestion script scans files
   ↓
3. Files processed and chunked
   ↓
4. Embeddings generated (OpenAI)
   ↓
5. Chunks stored in ChromaDB
   ↓
6. Metadata stored in SQLite
   ↓
7. Ready for queries
```

## Scaling Considerations

**Current Design (Single User):**
- SQLite database
- Local file storage
- Synchronous processing

**Future Enhancements:**
- PostgreSQL for multi-user support
- S3/Cloud storage for large datasets
- Async processing for ingestion
- Redis for caching
- Load balancing for API
- Kubernetes deployment

## Security Considerations

1. **API Key Protection**: Environment variables, never committed
2. **Data Privacy**: Local storage, no external data sharing
3. **Access Control**: Single-user by default, add auth for multi-user
4. **Input Validation**: Pydantic models for all inputs
5. **Rate Limiting**: Add for production deployments

## Performance Characteristics

**Vector Search:**
- Query time: ~50-200ms
- Depends on collection size
- Optimized with ChromaDB indexing

**Response Generation:**
- Total time: ~2-5s
- Includes: retrieval + API call + storage
- Dominated by OpenAI API latency

**Data Ingestion:**
- ~100-500 documents/minute
- Limited by OpenAI embedding rate limits
- Can be parallelized

## Technology Choices

**Why RAG over Fine-tuning?**
- Lower cost (no fine-tuning fees)
- Easier updates (just add data)
- Better source attribution
- More flexible (change behavior via config)
- Faster iteration

**Why ChromaDB?**
- Simple setup
- Good Python integration
- Persistent storage
- No separate server needed

**Why SQLite?**
- Zero configuration
- Perfect for single-user
- ACID compliance
- Easy backup (single file)

**Why OpenAI?**
- High-quality embeddings
- Best-in-class language models
- Good documentation
- Simple API

## Extension Points

The system is designed for extensibility:

1. **Custom Data Sources**: Add processors in `ingest.py`
2. **Different LLMs**: Swap OpenAI for local models
3. **UI Customization**: Modify React components
4. **Prompt Engineering**: Update `build_system_prompt()`
5. **Storage Backends**: Replace ChromaDB or SQLite
