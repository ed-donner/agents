# Advanced Digital Twin with RAG

AI-powered digital twin persona using RAG created from Linkedin using OPENAI function calling, advanced retrieval techniques and their evaluation.

## Core Features

**RAG System**
- Hybrid search: BM25 + semantic embeddings
- Cross-encoder reranking
- Query expansion
- ChromaDB vector storage
- 4 retrieval methods: bm25, semantic, hybrid, hybrid_rerank

**Evaluation Framework**
- MRR, nDCG, Precision, Recall
- LLM-as-judge for quality assessment
- Automated comparison reports

**Application**
- Gradio UI
- OpenAI function calling
- Pushover notifications

**Tests**
- Tests to test all components and pipeline.
