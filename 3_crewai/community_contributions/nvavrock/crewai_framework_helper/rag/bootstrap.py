"""One-shot: sync upstream CrewAI and build the RAG index."""

from __future__ import annotations

import argparse

from rag.index import index_repo, load_env, project_root
from rag.upstream import sync_upstream


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(
        description="Sync upstream crewAI and build the framework RAG index"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation after dry-run",
    )
    parser.add_argument(
        "--dry-run-only",
        action="store_true",
        help="Sync + dry-run only; do not embed",
    )
    args = parser.parse_args()

    repo = sync_upstream()
    count = index_repo(repo, dry_run=True)

    if count == 0:
        print("Nothing to index.")
        return

    if args.dry_run_only:
        print("Dry-run only; no embeddings written.")
        return

    if not args.yes:
        answer = input(f"Embed {count} chunks into {project_root() / '.rag_index'}? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("Aborted.")
            return

    index_repo(repo, reset=True)


if __name__ == "__main__":
    main()
