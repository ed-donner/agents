# WindowWolf RAG System

This document describes the RAG (Retrieval-Augmented Generation) system integrated into the WindowWolf chatbot application.

## Overview

The RAG system enhances the WindowWolf chatbot by providing intelligent document retrieval and context-aware responses. It uses vector embeddings to find the most relevant information from your business documents and incorporates that context into the AI's responses.

## Architecture

### Components

1. **RAGSystem** (`rag_system.py`): Core vector database and embedding functionality
2. **RAGManager** (`rag_manager.py`): High-level management and integration
3. **RAGUtils** (`rag_utils.py`): Command-line utilities for system management
4. **WindowWolfApp** (`WindowWolfApp.py`): Main application with RAG integration

### Technology Stack

- **Vector Database**: ChromaDB for persistent storage
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2 model)
- **Document Processing**: PyPDF for PDF extraction
- **Integration**: OpenAI GPT models with RAG-enhanced prompts

## Features

### Document Processing
- Automatic chunking of large documents with overlap
- Support for PDF and text files
- Metadata tracking for source attribution
- Smart sentence boundary detection

### Vector Search
- Semantic similarity search
- Configurable result limits
- Relevance scoring
- Source tracking

### Integration
- Seamless integration with existing chatbot
- Dynamic context injection
- Backward compatibility with original system
- Quality control integration

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. The RAG system will automatically initialize when you run the main application.

## Usage

### Running the Application

The RAG system is automatically integrated into your existing WindowWolf app:

```bash
python WindowWolfApp.py
```

The system will:
1. Initialize the RAG manager
2. Process your existing PDF and text documents
3. Create vector embeddings
4. Store them in ChromaDB
5. Enhance responses with relevant context

### Command Line Utilities

Use the RAG utilities for system management:

```bash
# Initialize/reload documents
python rag_utils.py init [--force] [--path /path/to/documents]

# Search the knowledge base
python rag_utils.py search "What services do you offer?" [--results 5]

# View system statistics
python rag_utils.py stats

# Test the system with sample queries
python rag_utils.py test

# Add custom documents
python rag_utils.py add "Custom content here" "custom_doc_id"

# Clear all documents (with confirmation)
python rag_utils.py clear [--confirm]
```

## How It Works

### 1. Document Processing
When the system starts, it:
- Reads your `WindowWolfChatbot.pdf` and `WindowWolfSummary.txt` files
- Chunks the content into manageable pieces (500 characters with 50 character overlap)
- Generates embeddings for each chunk using SentenceTransformers
- Stores everything in ChromaDB with metadata

### 2. Query Processing
When a user asks a question:
- The system generates an embedding for the user's query
- Searches the vector database for similar content
- Retrieves the most relevant chunks (default: 3 results)
- Formats the context with source information and relevance scores

### 3. Response Generation
The retrieved context is:
- Added to the system prompt as "Additional Relevant Information (RAG)"
- Used by the AI to generate more accurate, context-aware responses
- Integrated with your existing quality control system

## Configuration

### Document Paths
The system looks for documents in the following locations:
- `WindowWolfChatbot.pdf` - Main business document
- `WindowWolfSummary.txt` - Business summary

### Chunking Parameters
- **Chunk Size**: 500 characters (configurable in `rag_system.py`)
- **Overlap**: 50 characters (configurable in `rag_system.py`)
- **Max Context**: 2000 characters (configurable in `rag_manager.py`)

### Search Parameters
- **Default Results**: 3 chunks per query
- **Similarity Threshold**: No minimum (all results returned)
- **Context Length**: 2000 characters maximum

## File Structure

```
My_AIProjects/
├── WindowWolfApp.py          # Main application (updated with RAG)
├── rag_system.py             # Core RAG functionality
├── rag_manager.py            # RAG management and integration
├── rag_utils.py              # Command-line utilities
├── requirements.txt          # Updated dependencies
├── RAG_README.md            # This documentation
├── ww_rag.db/               # ChromaDB database (created automatically)
├── WindowWolfChatbot.pdf    # Source document
└── WindowWolfSummary.txt    # Source document
```

## Database

The system uses ChromaDB for vector storage:
- **Location**: `ww_rag.db/` directory
- **Collection**: `window_wolf_docs`
- **Persistence**: Automatic saving and loading
- **Backup**: Regular database files can be backed up

## Performance

### Initialization
- First run: ~30-60 seconds (depending on document size)
- Subsequent runs: ~5-10 seconds (loads existing database)

### Query Processing
- Search time: ~100-500ms per query
- Context retrieval: ~50-200ms
- Total overhead: ~150-700ms per user message

### Memory Usage
- Embedding model: ~100MB
- Database: ~10-50MB (depending on document size)
- Total additional memory: ~110-150MB

## Troubleshooting

### Common Issues

1. **"No module named 'sentence_transformers'"**
   - Run: `pip install sentence-transformers`

2. **"ChromaDB connection failed"**
   - Check file permissions in the project directory
   - Delete `ww_rag.db/` folder and restart

3. **"Documents not found"**
   - Ensure `WindowWolfChatbot.pdf` and `WindowWolfSummary.txt` exist
   - Check file paths in the error message

4. **"Slow performance"**
   - First run is always slower due to embedding generation
   - Subsequent runs should be much faster

### Debug Mode

Enable debug logging by modifying the logging level in `rag_system.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Customization

### Adding New Documents

1. **Via Command Line**:
```bash
python rag_utils.py add "Your document content" "document_id"
```

2. **Via Code**:
```python
from rag_manager import RAGManager
manager = RAGManager()
manager.add_custom_document("Content", "doc_id")
```

### Modifying Search Parameters

Edit `rag_manager.py`:
```python
def get_context_for_query(self, query: str, max_context_length: int = 2000):
    # Change max_context_length or other parameters
```

### Custom Embedding Models

Edit `rag_system.py`:
```python
def __init__(self, ...):
    # Change to a different model
    self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
```

## Benefits

### For Users
- More accurate and relevant responses
- Better understanding of business context
- Consistent information across conversations

### For Business
- Leverages existing documentation
- Reduces need for manual prompt engineering
- Improves customer experience
- Maintains knowledge consistency

## Future Enhancements

Potential improvements:
- Support for more document types (Word, HTML, etc.)
- Multi-language support
- Real-time document updates
- Advanced filtering and metadata search
- Integration with external knowledge bases
- Performance optimization for larger document sets

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Test with the command-line utilities
4. Verify document file paths and permissions
