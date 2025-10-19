# Usage Guide - The Checkpoint

## Quick Start

### 1. Installation

```bash
# Install Python dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup the system
python setup.py
```

You'll need to add your OpenAI API key to the `.env` file.

### 2. Prepare Your Data

Create a directory structure like this:

```
data/
├── CONSENT.md              # Required: consent documentation
├── emails/                 # Email archives
├── messages/              # Chat messages (JSON format)
├── writings/              # Documents, blog posts, etc.
└── code/                  # Code comments, documentation
```

**IMPORTANT**: Before ingesting any data, ensure you have proper consent documented in `data/CONSENT.md`.

### 3. Ingest Data

```bash
# Ingest text files from a directory
python ingest.py --source ./data/writings --checkpoint 0.1 --type writings

# Ingest JSON messages (Slack, Discord, etc.)
python ingest.py --source ./data/messages.json --checkpoint 0.1 --format json
```

### 4. Start the Server

```bash
python server.py
```

The API will be available at `http://localhost:8000`

### 5. Chat with the Ghost

**CLI Interface:**

```bash
# Interactive chat
python cli.py chat

# Chat with specific checkpoint
python cli.py chat --checkpoint 0.2

# Send single message
python cli.py send "How are you?"

# View conversation history
python cli.py history
```

**Web Interface:**

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

## Working with Checkpoints

Checkpoints are versioned snapshots of the ghost's configuration and training data.

### Creating Checkpoints

```bash
# Create a new checkpoint
python checkpoint.py create --version 0.2 --description "Added email data"

# Create with custom config
python checkpoint.py create \
  --version 0.3 \
  --description "More casual tone" \
  --config '{"personality_note": "More casual and humorous"}'
```

### Managing Checkpoints

```bash
# List all checkpoints
python checkpoint.py list

# Set active checkpoint
python checkpoint.py activate --version 0.2

# Delete a checkpoint
python checkpoint.py delete --version 0.1
```

## Advanced Usage

### Customizing Response Generation

Edit checkpoint config to control behavior:

```python
config = {
    "personality_note": "Slightly more formal in technical discussions",
    "temperature_note": "Using lower temperature for consistency",
    "context_docs": 10  # Number of context documents to retrieve
}
```

### Data Ingestion Formats

**Text Files:**
```bash
python ingest.py --source ./data --checkpoint 0.1 --extensions .txt,.md,.py
```

**JSON Messages:**
```json
[
  {
    "text": "Message content here",
    "timestamp": "2024-01-01T12:00:00Z",
    "metadata": {"source": "slack"}
  }
]
```

**Custom Processing:**

Edit `ingest.py` to add custom data processors for different formats.

### API Usage

```python
import requests

# Send a message
response = requests.post("http://localhost:8000/chat", json={
    "message": "What do you think about this?",
    "checkpoint_version": "0.1"
})

print(response.json()["response"])
```

## Ethical Guidelines

1. **Consent**: Always obtain explicit consent before creating a digital ghost
2. **Transparency**: Be clear that this is an AI approximation, not the actual person
3. **Privacy**: Carefully review what data you include
4. **Boundaries**: Set clear guidelines for how the ghost should be used
5. **Deletion**: Respect requests to delete or modify the ghost

## Tips for Better Results

1. **More data is better**: The system works best with substantial training data
2. **Diverse sources**: Include different types of writing (casual, formal, technical)
3. **Context matters**: Longer, complete conversations work better than fragments
4. **Iterate on checkpoints**: Create multiple versions as you add more data
5. **Tune temperature**: Lower for consistency, higher for creativity

## Troubleshooting

**No response generated:**
- Check OpenAI API key in `.env`
- Ensure data has been ingested for the active checkpoint
- Verify server is running

**Poor quality responses:**
- Add more training data
- Include more diverse sources
- Adjust checkpoint configuration
- Try different checkpoints

**Out of memory:**
- Reduce `MAX_CONTEXT_MESSAGES` in `.env`
- Process data in smaller batches
- Use smaller embedding model

## Cost Considerations

This system uses OpenAI's API which has costs:
- Embeddings: ~$0.0001 per 1K tokens
- Completions: ~$0.01 per 1K tokens (GPT-4)

Typical usage:
- Initial data ingestion: $1-5 depending on data size
- Per conversation: $0.01-0.10 depending on length

Consider using GPT-3.5-turbo for lower costs during development.
