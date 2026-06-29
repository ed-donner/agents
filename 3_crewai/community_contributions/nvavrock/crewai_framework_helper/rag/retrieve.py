"""Query the CrewAI framework RAG index."""

from __future__ import annotations

import argparse

from rag.index import get_vectorstore, index_dir, load_env

DEFAULT_TOP_K = 6


def search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    kind: str | None = None,
) -> list[dict]:
    load_env()
    if not index_dir().exists():
        raise FileNotFoundError(
            f"No RAG index at {index_dir()}. Run: uv run bootstrap-index --yes"
        )
    store = get_vectorstore()
    fetch_k = top_k * 4 if kind else top_k
    results = store.similarity_search_with_score(query, k=fetch_k)
    hits = [
        {
            "source": doc.metadata.get("source", "unknown"),
            "chunk": doc.metadata.get("chunk", 0),
            "kind": doc.metadata.get("kind", "source"),
            "score": round(float(score), 4),
            "text": doc.page_content,
        }
        for doc, score in results
    ]
    if kind:
        hits = [h for h in hits if h["kind"] == kind]
    return hits[:top_k]


def format_results(results: list[dict]) -> str:
    if not results:
        return "No matching content found in the index."
    parts: list[str] = []
    for i, hit in enumerate(results, start=1):
        parts.append(
            f"--- Result {i} [{hit['kind']}] {hit['source']} "
            f"(chunk {hit['chunk']}, score {hit['score']}) ---\n"
            f"{hit['text']}\n"
        )
    return "\n".join(parts)


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Search the CrewAI framework RAG index")
    parser.add_argument("query", help="Natural language or code search query")
    parser.add_argument("-k", type=int, default=DEFAULT_TOP_K, help="Number of results")
    parser.add_argument(
        "--kind",
        choices=["source", "docs", "meta"],
        help="Filter by content kind",
    )
    args = parser.parse_args()
    print(format_results(search(args.query, top_k=args.k, kind=args.kind)))


if __name__ == "__main__":
    main()
