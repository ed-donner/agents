from tqdm import tqdm
import hashlib
from kb_state import KBState
from utils import get_llm 
from models import KBEntry, KBOutput 


def content_processor(state: KBState) -> dict:
    """Cleans, chunks, and formats approved sources."""
    llm = get_llm().with_structured_output(KBOutput)

    all_entries: list[KBEntry] = []
    sources = state["approved_sources"]
    unique_entries: list[KBEntry] = []

    with tqdm(total=len(sources), desc="Processing sources", unit='source') as pbar:
        for source in sources:
            prompt = f'''
            Process the following source for inclusion into clean, RAG-ready knowledge base chunks.

            **Source:** {source.title}
            **URL:** {source.url}
            **Subtopic:** {source.subtopic}
            **Topic:** {state["topic"]}

            **Raw Content:**
            {source.content}

            Instructions:
            1. Remove any remaining boilerplate, ads, navigation, or irrelevant content.
            2. Extract the core informational content that is relevant to the subtopic and topic.
            3. Chunk the content into coherent pieces (aim for 300-800 tokens per chunk), preserving semantic coherence.
            4. Ensure each chunk is self-contained and can be understood independently.
            5. Format as clean markdown, removing any extraneous formatting or characters.
            6. Tag each chunk with metadata (e.g., topic, subtopic, source URL, author, plublication date) for later retrieval.
            '''

            result: KBOutput = llm.invoke(prompt)
            all_entries.extend(result.entries)

            pbar.set_postfix(entries=len(all_entries), current=source.title[:30])
            pbar.update(1)

    seen = set()
    for entry in all_entries:
        key = hashlib.sha256(
            entry.content.encode('utf-8')).hexdigest()[:16]
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    source_counters: dict[str, int] = {}
    for entry in unique_entries:
        url = entry.source_url
        if url not in source_counters:
            source_counters[url] = 0
        entry.metadata.chunk_index = source_counters[url]
        source_counters[url] += 1

    return {
        'kb_entries': unique_entries,
        'messages': [{
            'role': 'processor',
            'content': f'Processed {len(state["approved_sources"])} sources into {len(all_entries)} KB entries.'
        }]
    }


