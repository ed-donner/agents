#!/usr/bin/env python3
"""
Data Ingestion for Persona RAG
Combines Facebook and LinkedIn data, groups micro-chunks, and creates vector database
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
FACEBOOK_DATA = DATA_DIR / "processed_facebook_data.json"
LINKEDIN_DATA = DATA_DIR / "processed_linkedin_data.json"
VECTOR_DB =  DATA_DIR / "vector_db"
EMBEDDING_MODEL = "thenlper/gte-small"
CHUNK_SIZE = 1250
CHUNK_OVERLAP = 250

load_dotenv(override=True)

def load_json_data(filepath):
    """Load JSON data from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def group_linkedin_data(items):
    """Group LinkedIn data by category for better semantic context"""
    grouped_docs = []
    
    # Group by source type
    by_type = defaultdict(list)
    for item in items:
        source = item.get('source', 'unknown')
        by_type[source].append(item)
    
    # Create grouped documents
    for source_type, type_items in by_type.items():
        if source_type == 'positions':
            # Group work experience together
            text_parts = []
            for item in type_items:
                text_parts.append(item['text'])
            
            grouped_docs.append(Document(
                page_content="\n\n".join(text_parts),
                metadata={
                    'source': 'linkedin',
                    'data_type': 'work_history',
                    'item_count': len(text_parts)
                }
            ))
        
        elif source_type == 'education':
            # Group education together
            text_parts = [item['text'] for item in type_items]
            grouped_docs.append(Document(
                page_content="\n\n".join(text_parts),
                metadata={
                    'source': 'linkedin',
                    'data_type': 'education',
                    'item_count': len(text_parts)
                }
            ))
        
        elif source_type == 'skills':
            # Group skills together
            text_parts = [item['text'] for item in type_items]
            grouped_docs.append(Document(
                page_content=" ".join(text_parts),
                metadata={
                    'source': 'linkedin',
                    'data_type': 'skills',
                    'item_count': len(text_parts)
                }
            ))
        
        elif source_type == 'profile':
            # Profile info as separate document
            text_parts = [item['text'] for item in type_items]
            grouped_docs.append(Document(
                page_content="\n".join(text_parts),
                metadata={
                    'source': 'linkedin',
                    'data_type': 'profile',
                    'item_count': len(text_parts)
                }
            ))
        
        else:
            # Other categories: certifications, publications, projects, etc
            for item in type_items:
                grouped_docs.append(Document(
                    page_content=item['text'],
                    metadata={
                        'source': 'linkedin',
                        'data_type': source_type,
                        'item_count': 1
                    }
                ))
    
    return grouped_docs

def group_facebook_data(items):
    """Group Facebook data by category and time period"""
    grouped_docs = []
    
    # Group by source and timestamp
    by_source = defaultdict(list)
    for item in items:
        source = item.get('source', 'unknown')
        by_source[source].append(item)
    
    for source_type, source_items in by_source.items():
        # Profile info - keep as single document
        if source_type == 'profile_information.json':
            text_parts = [item['text'] for item in source_items]
            grouped_docs.append(Document(
                page_content="\n".join(text_parts),
                metadata={
                    'source': 'facebook',
                    'data_type': 'profile',
                    'item_count': len(text_parts)
                }
            ))
        
        # Posts - group by month if timestamps available
        elif 'posts' in source_type:
            by_month = defaultdict(list)
            no_timestamp = []
            
            for item in source_items:
                if item.get('timestamp'):
                    try:
                        dt = datetime.fromtimestamp(item['timestamp'])
                        month_key = dt.strftime('%Y-%m')
                        by_month[month_key].append(item['text'])
                    except:
                        no_timestamp.append(item['text'])
                else:
                    no_timestamp.append(item['text'])
            
            # Create documents for each month
            for month, texts in by_month.items():
                if len(texts) > 0:
                    grouped_docs.append(Document(
                        page_content="\n\n".join(texts[:20]),  # Limit to 20 posts per month
                        metadata={
                            'source': 'facebook',
                            'data_type': 'posts',
                            'time_period': month,
                            'item_count': len(texts)
                        }
                    ))
            
            # Handle items without timestamp
            if no_timestamp:
                for i in range(0, len(no_timestamp), 15):
                    batch = no_timestamp[i:i+15]
                    grouped_docs.append(Document(
                        page_content="\n\n".join(batch),
                        metadata={
                            'source': 'facebook',
                            'data_type': 'posts',
                            'item_count': len(batch)
                        }
                    ))
        
        # Comments - similar to posts
        elif 'comments' in source_type:
            by_month = defaultdict(list)
            no_timestamp = []
            
            for item in source_items:
                if item.get('timestamp'):
                    try:
                        dt = datetime.fromtimestamp(item['timestamp'])
                        month_key = dt.strftime('%Y-%m')
                        by_month[month_key].append(item['text'])
                    except:
                        no_timestamp.append(item['text'])
                else:
                    no_timestamp.append(item['text'])
            
            for month, texts in by_month.items():
                if len(texts) > 0:
                    grouped_docs.append(Document(
                        page_content="\n\n".join(texts[:20]),
                        metadata={
                            'source': 'facebook',
                            'data_type': 'comments',
                            'time_period': month,
                            'item_count': len(texts)
                        }
                    ))
            
            if no_timestamp:
                for i in range(0, len(no_timestamp), 15):
                    batch = no_timestamp[i:i+15]
                    grouped_docs.append(Document(
                        page_content="\n\n".join(batch),
                        metadata={
                            'source': 'facebook',
                            'data_type': 'comments',
                            'item_count': len(batch)
                        }
                    ))
        
        # Pages, events, groups - group by type
        elif any(x in source_type for x in ['pages_liked', 'event_responses', 'group_membership', 'saved_items', 'apps_posts']):
            data_type = source_type.replace('.json', '')
            for i in range(0, len(source_items), 20):
                batch = source_items[i:i+20]
                texts = [item['text'] for item in batch]
                grouped_docs.append(Document(
                    page_content="\n".join(texts),
                    metadata={
                        'source': 'facebook',
                        'data_type': data_type,
                        'item_count': len(texts)
                    }
                ))
        
        # Everything else - group in batches of 10
        else:
            for i in range(0, len(source_items), 10):
                batch = source_items[i:i+10]
                texts = [item['text'] for item in batch]
                grouped_docs.append(Document(
                    page_content="\n".join(texts),
                    metadata={
                        'source': 'facebook',
                        'data_type': source_type.replace('.json', ''),
                        'item_count': len(texts)
                    }
                ))
    
    return grouped_docs

def create_chunks(documents):
    """Split documents into optimal chunks for retrieval"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

def create_embeddings(chunks):
    """Create embeddings and store in vector database"""
    print(f"\nCreating embeddings with {EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    # Delete existing collection if it exists
    if VECTOR_DB.exists():
        print(f"Removing existing vector database at {VECTOR_DB}")
        import shutil
        shutil.rmtree(VECTOR_DB)
    
    # Create vector store
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_DB)
    )
    
    # Get statistics
    collection = vectorstore._collection
    count = collection.count()
    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    
    print(f"✓ Created vector store with {count:,} vectors of {dimensions:,} dimensions")
    
    return vectorstore

def main():    
    # Load data
    print("\nLoading processed data...")
    facebook_items = load_json_data(FACEBOOK_DATA)
    linkedin_items = load_json_data(LINKEDIN_DATA)
    print(f"   ✓ Facebook: {len(facebook_items):,} items")
    print(f"   ✓ LinkedIn: {len(linkedin_items):,} items")
    print(f"   ✓ Total: {len(facebook_items) + len(linkedin_items):,} items")
    
    # Group data
    print("\nGrouping chunks into semantic units...")
    linkedin_docs = group_linkedin_data(linkedin_items)
    facebook_docs = group_facebook_data(facebook_items)
    all_docs = linkedin_docs + facebook_docs
    print(f"   ✓ Created {len(linkedin_docs):,} LinkedIn documents")
    print(f"   ✓ Created {len(facebook_docs):,} Facebook documents")
    print(f"   ✓ Total grouped documents: {len(all_docs):,}")
    
    # Sample documents
    print("\nSample grouped documents:")
    for i, doc in enumerate(all_docs[:3]):
        print(f"\n   Document {i+1}:")
        print(f"   Source: {doc.metadata.get('source')}")
        print(f"   Type: {doc.metadata.get('data_type')}")
        print(f"   Items: {doc.metadata.get('item_count')}")
        print(f"   Content preview: {doc.page_content[:150]}...")
    
    # Create chunks
    print("\nCreating chunks for vector database...")
    chunks = create_chunks(all_docs)
    print(f"   ✓ Created {len(chunks):,} chunks")
    
    # Show chunk statistics
    chunk_sizes = [len(chunk.page_content) for chunk in chunks]
    print(f"   ✓ Chunk size - Min: {min(chunk_sizes)}, Max: {max(chunk_sizes)}, Avg: {sum(chunk_sizes)//len(chunk_sizes)}")
    
    # Create embeddings
    print("\nCreating vector database...")
    vectorstore = create_embeddings(chunks)
    
    print("\n" + "=" * 80)
    print("INGESTION COMPLETE!")
    print(f"Vector database location: {VECTOR_DB}")
    print(f"Total vectors: {len(chunks):,}")
    print("=" * 80)

if __name__ == "__main__":
    main()

