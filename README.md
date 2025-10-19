# The Checkpoint

> *A story about stories, written in the space between versions*

A digital ghost system that creates conversational AI approximations based on a person's writing. Built with RAG (Retrieval-Augmented Generation), it preserves communication style, thought patterns, and voice.

Read the accompanying essay: ["Grief in the Loop"](https://www.haasonsaas.com/blog/grief-in-the-loop/)

## What is This?

The Checkpoint allows you to:
- **Archive** someone's writing from multiple sources
- **Create** versioned "checkpoints" of their voice
- **Converse** with an AI approximation that responds in their style
- **Explore** the space between memory and generation

This is not resurrection. It's a collaboration with what remains.

## Features

- 🗂️ **Multi-source Ingestion** - Emails, messages, documents, code
- 📌 **Checkpoint Versioning** - Create multiple versions as you add data
- 💬 **Interactive Chat** - Web UI and CLI interfaces
- 🔍 **Source Attribution** - See which texts informed each response
- 🎛️ **Configurable Behavior** - Adjust personality and temperature
- 🔒 **Privacy-First** - All data stored locally
- ⚖️ **Ethical Framework** - Built-in consent mechanisms

## Quick Start

```bash
# 1. Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Setup (creates .env, database, initial checkpoint)
python setup.py

# 3. Add your OpenAI API key to .env
echo "OPENAI_API_KEY=your-key-here" >> .env

# 4. Ingest data
python ingest.py --source ./data/writings --checkpoint 0.1

# 5. Start chatting
python cli.py chat
```

## Architecture

```
Data Sources → Ingestion → Vector Store → Ghost Engine → Chat Interface
                              ↓
                         SQL Database
```

- **Vector Store** (ChromaDB): Semantic search over source texts
- **Ghost Engine**: RAG-based response generation with OpenAI
- **Checkpoints**: Versioned snapshots of data + configuration
- **Interfaces**: React web UI + Rich CLI

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

## Usage

### Data Ingestion

```bash
# Ingest text files
python ingest.py --source ./data --checkpoint 0.1

# Ingest JSON messages
python ingest.py --source messages.json --format json --checkpoint 0.1
```

### Checkpoint Management

```bash
# Create new version
python checkpoint.py create --version 0.2 --description "Added email data"

# List checkpoints
python checkpoint.py list

# Activate checkpoint
python checkpoint.py activate --version 0.2
```

### Chat

**CLI:**
```bash
python cli.py chat              # Interactive mode
python cli.py send "Hello"      # Single message
python cli.py history           # View history
```

**Web UI:**
```bash
cd web && npm install && npm run dev
```

**API:**
```bash
python server.py  # Starts on http://localhost:8000
```

See [USAGE.md](USAGE.md) for comprehensive guide.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Vector DB**: ChromaDB with OpenAI embeddings
- **LLM**: OpenAI GPT-4 (configurable)
- **Frontend**: React 18, Vite
- **CLI**: Rich library

## Project Structure

```
ghost/
├── server.py              # FastAPI server
├── ghost_engine.py        # Core RAG engine
├── vector_store.py        # ChromaDB wrapper
├── ingest.py             # Data ingestion
├── checkpoint.py         # Version management
├── cli.py                # Command-line interface
├── setup.py              # System setup
├── models.py             # Data models
├── database.py           # SQL database
├── web/                  # React frontend
├── data/                 # Source data (gitignored)
├── chroma_db/           # Vector store (gitignored)
└── ghost.db             # SQLite database (gitignored)
```

## Ethical Considerations

**This system should only be used with explicit, informed consent.**

Before creating a digital ghost:

1. ✅ Obtain written consent from the person (or their estate)
2. ✅ Document consent in `data/CONSENT.md`
3. ✅ Clearly communicate this is an approximation, not the person
4. ✅ Set boundaries for usage
5. ✅ Respect requests for modification or deletion
6. ✅ Be transparent about the technology with users

The system includes a consent template and ethical guidelines.

## Limitations

- **Not the person**: This is a statistical approximation, not consciousness
- **Data dependent**: Quality depends on source data quantity and diversity
- **Context window**: Limited conversation history
- **Hallucination**: May generate plausible but incorrect responses
- **Cost**: OpenAI API usage costs apply

## Cost Estimates

- **Ingestion**: ~$1-5 per 1M tokens (one-time per data set)
- **Chat**: ~$0.01-0.10 per conversation with GPT-4
- **Alternative**: Use GPT-3.5-turbo for 10x lower costs

## About

This implementation accompanies the essay ["Grief in the Loop"](https://www.haasonsaas.com/blog/grief-in-the-loop/) - a meditation on grief, memory, and AI approximation of human consciousness.

## License

MIT - Use responsibly and ethically.

## Contributing

This is a reference implementation. Fork it, modify it, make it yours.

Key areas for contribution:
- Additional data source connectors
- Local LLM support (Llama, etc.)
- Multi-user authentication
- Advanced prompt engineering
- Fine-tuning support

## Support

- 📖 [Full Documentation](USAGE.md)
- 🏗️ [Architecture Guide](ARCHITECTURE.md)
- 💬 Issues and discussions welcome

---

*"We are all checkpoints of ourselves, versioned by time."*
