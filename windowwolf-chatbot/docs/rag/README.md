# WindowWolf RAG System Documentation

This directory contains comprehensive documentation for the WindowWolf RAG (Retrieval-Augmented Generation) system.

## Documentation Files

- **[RAG_README.md](RAG_README.md)** - Complete user guide and technical documentation
- **[RAG_IMPLEMENTATION_SUMMARY.md](RAG_IMPLEMENTATION_SUMMARY.md)** - Implementation overview and summary

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Your App**:
   ```bash
   python WindowWolfApp.py
   ```

3. **Test the System**:
   ```bash
   python tests/test_rag.py
   ```

4. **Manage the System**:
   ```bash
   python rag_utils.py stats
   ```

## System Overview

The RAG system enhances your WindowWolf chatbot by:
- Processing your existing business documents (PDF and text files)
- Creating vector embeddings for intelligent search
- Providing context-aware responses based on your actual business information
- Maintaining all existing functionality while adding powerful new capabilities

## Key Features

- ✅ **Automatic Document Processing**: Processes your existing `WindowWolfChatbot.pdf` and `WindowWolfSummary.txt`
- ✅ **Intelligent Search**: Semantic similarity search for relevant information
- ✅ **Enhanced Responses**: Context-aware AI responses based on your business documents
- ✅ **Backward Compatibility**: All existing functionality preserved
- ✅ **Management Tools**: Command-line utilities for system management
- ✅ **Quality Control Integration**: Works with your existing Gemini evaluation system

## Directory Structure

```
My_AIProjects/
├── WindowWolfApp.py              # Main application (RAG-enhanced)
├── rag_utils.py                  # RAG utilities entry point
├── rag_system/                   # RAG system package
│   ├── __init__.py              # Package initialization
│   ├── rag_system.py            # Core RAG functionality
│   ├── rag_manager.py           # RAG management and integration
│   └── rag_utils.py             # Command-line utilities
├── tests/                       # Test files
│   └── test_rag.py             # RAG system test suite
├── docs/                        # Documentation
│   └── rag/                    # RAG-specific documentation
│       ├── README.md           # This file
│       ├── RAG_README.md       # Complete user guide
│       └── RAG_IMPLEMENTATION_SUMMARY.md  # Implementation summary
├── requirements.txt             # Updated dependencies
├── WindowWolfChatbot.pdf       # Source document
├── WindowWolfSummary.txt       # Source document
└── ww_rag.db/                  # ChromaDB database (auto-created)
```

## Support

For detailed information, troubleshooting, and advanced usage, see the complete documentation files in this directory.

