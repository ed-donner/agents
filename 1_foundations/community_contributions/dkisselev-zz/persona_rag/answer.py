"""
RAG Answer Module for Persona
Retrieval pipeline with sub-query generation, semantic search, and reranking
"""
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
import numpy as np
from dotenv import load_dotenv

load_dotenv(override=True)

# Configuration
DATA_DIR = Path(__file__).parent / "data"
VECTOR_DB = str(DATA_DIR / "vector_db")
EMBEDDING_MODEL = "thenlper/gte-small"
LLM_MODEL = "gpt-4o-mini"
PERSONA_NAME = "Dmitry Kisselev"

# Retrieval parameters
RETRIEVAL_K = 20  # Retrieve candidates for reranking
FINAL_K = 5  # Return top K after reranking

USE_QUERY_EXPANSION = False  # Disabled: hurt accuracy, completeness, MRR
USE_HYBRID_SEARCH = False  # Disabled: hurt accuracy, completeness, MRR

# System prompt for persona
SYSTEM_PROMPT = """You are {PERSONA_NAME}, answering questions about yourself.
Respond naturally in first person as if you're talking about your own life, career, and experiences.
Use the context provided to answer accurately. If you don't know something, say so honestly.

Context (with metadata):
{context}
"""

# Initialize components
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = None
retriever = None
llm = ChatOpenAI(temperature=0, model_name=LLM_MODEL)

# Initialize reranker
_reranker = None

def get_reranker():
    """Lazy load cross-encoder reranker"""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _reranker

# Initialize BM25 for hybrid search
_bm25 = None
_bm25_docs = None

def get_bm25():
    """Initialize BM25 index from all documents in vector store"""
    global _bm25, _bm25_docs
    if _bm25 is None:
        # Get all documents from vector store
        collection = vectorstore._collection
        all_data = collection.get(include=["documents", "metadatas"])
        
        # Create Document objects
        _bm25_docs = [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(all_data['documents'], all_data['metadatas'])
        ]
        
        # Tokenize documents
        tokenized_docs = [doc.page_content.lower().split() for doc in _bm25_docs]
        _bm25 = BM25Okapi(tokenized_docs)
    
    return _bm25, _bm25_docs

def initialize_retriever():
    """Initialize vector store and retriever"""
    global vectorstore, retriever
    if vectorstore is None:
        vectorstore = Chroma(persist_directory=VECTOR_DB, embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})
    return retriever

# Sub-query generation
output_parser = CommaSeparatedListOutputParser()

template = """
You are a helpful assistant. Given a user question, generate 1 to 3 
sub-queries that are optimized for a vector database search.
The sub-queries should cover the different parts of the user's question.

Question: {question}

Format your response as a comma-separated list.
"""
query_gen_prompt = ChatPromptTemplate.from_template(template)
query_gen_chain = query_gen_prompt | llm | output_parser

def expand_query(question: str) -> list[str]:
    """
    Query Expansion: Generate 2-3 variations of the query to improve retrieval coverage.
    """
    expansion_prompt = f"""Given this question, generate 2 alternative phrasings that would help find relevant information.
Keep the variations concise and focused on the same topic.

Original question: {question}

Provide ONLY 2 alternative phrasings, one per line, without numbering or extra text:"""
    
    try:
        response = llm.invoke([HumanMessage(content=expansion_prompt)])
        variations = [line.strip() for line in response.content.strip().split('\n') if line.strip()]
        # Return original + variations (limit to 3 total)
        return [question] + variations[:2]
    except Exception as e:
        print(f"Query expansion failed: {e}")
        return [question]

def fetch_context(question: str) -> list[Document]:
    """
    Retrieve and rerank relevant context documents.
    Uses: (Query Expansion) + Sub-query generation + Semantic search + (Hybrid Search) + Reranking.
    """
    retriever = initialize_retriever()
    
    # Query expansion
    if USE_QUERY_EXPANSION:
        expanded_queries = expand_query(question)
        base_question = expanded_queries[0]
    else:
        base_question = question
    
    # Generate sub-queries
    try:
        sub_queries = query_gen_chain.invoke({"question": base_question})
        all_queries = [base_question] + sub_queries
    except Exception as e:
        print(f"Sub-query generation failed: {e}. Using original question.")
        all_queries = [base_question]
    
    # Add expanded queries if enabled
    if USE_QUERY_EXPANSION:
        all_queries.extend(expanded_queries[1:])  # Add variations
    
    # Initialize BM25 if hybrid search is enabled
    bm25 = None
    bm25_docs = None
    if USE_HYBRID_SEARCH:
        try:
            bm25, bm25_docs = get_bm25()
        except Exception as e:
            print(f"Failed to initialize BM25: {e}")
    
    # Retrieve documents for all queries
    all_docs = []
    seen_ids = set()
    
    for q in all_queries:
        # Semantic search
        try:
            docs = retriever.invoke(q)
            for doc in docs:
                doc_id = f"{doc.metadata.get('source', '')}:{hash(doc.page_content)}"
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_docs.append(doc)
        except Exception as e:
            print(f"Semantic retrieval failed for query '{q}': {e}")
        
        # BM25 search (if enabled)
        if USE_HYBRID_SEARCH and bm25 and bm25_docs:
            try:
                tokenized_query = q.lower().split()
                bm25_scores = bm25.get_scores(tokenized_query)
                top_bm25_indices = np.argsort(bm25_scores)[::-1][:RETRIEVAL_K]
                bm25_results = [bm25_docs[i] for i in top_bm25_indices]
                
                for doc in bm25_results:
                    doc_id = f"{doc.metadata.get('source', '')}:{hash(doc.page_content)}"
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        all_docs.append(doc)
            except Exception as e:
                print(f"BM25 retrieval failed for query '{q}': {e}")
    
    if not all_docs:
        print("No documents retrieved.")
        return []
    
    # Rerank with cross-encoder
    try:
        reranker = get_reranker()
        pairs = [[question, doc.page_content] for doc in all_docs]
        scores = reranker.predict(pairs)
        
        doc_scores = list(zip(all_docs, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        top_docs = [doc for doc, score in doc_scores[:FINAL_K]]
        
        return top_docs
    except Exception as e:
        print(f"Reranking failed: {e}. Returning top documents without reranking.")
        return all_docs[:FINAL_K]

def format_doc_with_metadata(doc: Document, idx: int) -> str:
    """Format document with metadata for context"""
    meta = doc.metadata
    formatted = f"--- Document {idx+1} ---\n"
    
    # Add metadata
    if 'source' in meta:
        formatted += f"Source: {meta['source']}\n"
    if 'data_type' in meta:
        formatted += f"Type: {meta['data_type']}\n"
    if 'time_period' in meta:
        formatted += f"Time Period: {meta['time_period']}\n"
    if 'item_count' in meta:
        formatted += f"Items: {meta['item_count']}\n"
    
    # Add content
    formatted += f"\nContent:\n{doc.page_content}\n"
    return formatted

def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """ Answer the given question using RAG."""
    # Fetch relevant context
    docs = fetch_context(question)
    
    # Format context with metadata
    context = "\n\n".join(format_doc_with_metadata(doc, i) for i, doc in enumerate(docs))
    
    # Build messages
    system_prompt = SYSTEM_PROMPT.format(context=context, PERSONA_NAME=PERSONA_NAME)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question[:5000]))
    
    # Get response
    response = llm.invoke(messages)
    return response.content, docs

if __name__ == "__main__":
    # Test the module
    print("Testing RAG answer module...")
    test_question = "What is your current role?"
    answer, docs = answer_question(test_question)
    print(f"\nQuestion: {test_question}")
    print(f"\nAnswer: {answer}")
    print(f"\nRetrieved {len(docs)} documents")
