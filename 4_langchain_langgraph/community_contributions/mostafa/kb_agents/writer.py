import os
import hashlib
import chromadb
from kb_state import KBState


def generate_entry_id(source_url: str, chunk_index: int) -> str:
    """Generates a unique ID for each KB entry based on source URL and chunk index."""
    url_hash = hashlib.sha256(source_url.encode('utf-8')).hexdigest()[:12]
    return f'{url_hash}-chunk-{chunk_index}'


def write_outputs(state: KBState) -> dict:
    """Writes markdown files and populates ChromaDB."""

    kb_name = state.get("kb_name", "default_kb")

    output_dir = os.path.join('kb_output', kb_name)
    chromadb_dir = os.path.join('chroma_db', kb_name)

    os.makedirs(output_dir, exist_ok=True)

    # 1. Write each kb_entry as a markdown file
    for entry in state["kb_entries"]:
        entry_id = generate_entry_id(entry.source_url, entry.metadata.chunk_index)
        filepath = os.path.join(output_dir, f'{entry_id}.md')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('---\n\n')
            f.write(f'**ID:** {entry_id}\n\n')
            f.write(f'**Source URL:** {entry.source_url}\n\n')
            f.write(f'**Title:** {entry.source_title}\n\n')
            f.write(f'**Subtopic:** {entry.subtopic}\n\n')
            f.write(f'**chunk_index:** {entry.metadata.chunk_index}\n\n')
            f.write(f'**author:** {entry.metadata.author}\n\n')
            f.write(
                f'**publication_date:** {entry.metadata.publication_date}\n\n')
            f.write('---\n\n')
            f.write(entry.content)

    # 2. Embed and insert into ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="knowledge_base")

    ids = [
        generate_entry_id(
            entry.source_url, entry.metadata.chunk_index
        ) for entry in state["kb_entries"]
    ]

    collection.add(
        documents=[entry.content for entry in state["kb_entries"]],
        metadatas=[{
            'source_url': entry.source_url,
            'source_title': entry.source_title,
            'subtopic': entry.subtopic,
            'chunk_index': entry.metadata.chunk_index,
            **entry.metadata.model_dump()
        } for entry in state["kb_entries"]],
        ids=ids
    )

    return {
        'messages': [{
            'role': 'system',
            'content': f'Wrote {len(state["kb_entries"])} markdown files to {output_dir} and inserted into ChromaDB at {chromadb_dir}.'
        }]
    }


