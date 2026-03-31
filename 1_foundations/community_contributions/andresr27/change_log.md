# Change Log

## Week 1: Carrer Agent with RAG
**Goal:** Build over the course Career Agent shown in Day 4 using Retrieval Augmented Generation to answer specific questions not available in Linkedin.
- **ChromaDB Integration:** Set up persistent vector storage for extracted data.
- **Extract properties from Markdown sections:** To minimize files commited I extracted the summary property from a private Markdown file using a new function.
- **Context Retrieval:** Added logic to augment LLM prompts with retrieved documents. These are loaded before the UI runs.

### Dependencies Added:
- chromadb
- glob

### Next Steps
- **Evaluate responses:** Create a Pydantic model for the Evaluation and generate metrics to assess the model performance.