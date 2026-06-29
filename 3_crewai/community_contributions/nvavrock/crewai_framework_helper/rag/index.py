"""Index upstream CrewAI into Chroma for RAG retrieval."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.paths import index_dir, project_root

DEFAULT_INDEX_PATHS = (
    "lib/crewai",
    "lib/crewai-core",
    "lib/crewai-tools",
    "lib/crewai-files",
    "lib/cli",
    "docs/edge/en",
    "AGENTS.md",
    "README.md",
)

CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java",
    ".rb", ".php", ".cs", ".cpp", ".c", ".h", ".hpp", ".sql", ".r",
    ".yaml", ".yml", ".toml", ".md", ".mdx", ".json",
}
SKIP_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".rag_index",
    "output", ".uv", "dist", "build", ".pytest_cache",
    "tests", "test", "__tests__", "fixtures",
}
SKIP_PATH_PREFIXES = ("docs/v",)


def load_env() -> None:
    load_dotenv(project_root() / ".env")


def embedding_model() -> str:
    return os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def index_paths() -> list[str]:
    raw = os.getenv("INDEX_PATHS")
    if raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return list(DEFAULT_INDEX_PATHS)


def _kind_for_path(rel: str) -> str:
    if rel.startswith("docs/"):
        return "docs"
    if rel in {"AGENTS.md", "README.md"}:
        return "meta"
    return "source"


def clean_mdx(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    text = re.sub(r"^import\s+.+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"<[A-Z][A-Za-z0-9]*[^>]*>", " ", text)
    text = re.sub(r"</[A-Z][A-Za-z0-9]*>", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def preprocess_file(path: Path, text: str) -> str:
    if path.suffix.lower() == ".mdx":
        return clean_mdx(text)
    return text


def _path_skipped(rel_posix: str) -> bool:
    return any(rel_posix.startswith(prefix) for prefix in SKIP_PATH_PREFIXES)


def collect_files(repo_path: Path, paths: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for entry in paths:
        target = (repo_path / entry).resolve()
        if not str(target).startswith(str(repo_path.resolve())):
            continue
        if target.is_file():
            candidates = [target]
        elif target.is_dir():
            candidates = list(target.rglob("*"))
        else:
            continue

        for path in candidates:
            if not path.is_file() or path in seen:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            rel = path.relative_to(repo_path).as_posix()
            if _path_skipped(rel):
                continue
            if path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            if path.stat().st_size > 500_000:
                continue
            seen.add(path)
            files.append(path)

    return sorted(files)


def build_documents(repo_path: Path, paths: list[str] | None = None) -> list[dict]:
    paths = paths or index_paths()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\nclass ", "\ndef ", "\nfunction ", "\n\n", "\n", " "],
    )
    docs: list[dict] = []
    for file_path in collect_files(repo_path, paths):
        try:
            raw = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        text = preprocess_file(file_path, raw)
        if not text:
            continue
        rel = file_path.relative_to(repo_path).as_posix()
        kind = _kind_for_path(rel)
        for i, chunk in enumerate(splitter.split_text(text)):
            docs.append(
                {
                    "page_content": chunk,
                    "metadata": {"source": rel, "chunk": i, "kind": kind},
                }
            )
    return docs


def get_vectorstore() -> Chroma:
    load_env()
    embeddings = OpenAIEmbeddings(model=embedding_model())
    return Chroma(
        collection_name="codebase",
        embedding_function=embeddings,
        persist_directory=str(index_dir()),
    )


def write_manifest(
    repo_path: Path,
    chunk_count: int,
    file_count: int,
    upstream_commit: str | None = None,
) -> None:
    manifest = {
        "indexed_at": datetime.now(UTC).isoformat(),
        "repo_path": str(repo_path),
        "chunk_count": chunk_count,
        "file_count": file_count,
        "index_paths": index_paths(),
        "embedding_model": embedding_model(),
        "upstream_commit": upstream_commit,
    }
    index_dir().mkdir(parents=True, exist_ok=True)
    (index_dir() / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def index_repo(
    repo_path: Path,
    reset: bool = False,
    dry_run: bool = False,
    paths: list[str] | None = None,
) -> int:
    load_env()
    repo_path = repo_path.resolve()
    paths = paths or index_paths()
    files = collect_files(repo_path, paths)
    docs = build_documents(repo_path, paths)

    print(f"Repo: {repo_path}")
    print(f"Paths: {', '.join(paths)}")
    print(f"Files: {len(files)}  Chunks: {len(docs)}")

    if dry_run:
        by_kind: dict[str, int] = {}
        for doc in docs:
            kind = doc["metadata"]["kind"]
            by_kind[kind] = by_kind.get(kind, 0) + 1
        for kind, count in sorted(by_kind.items()):
            print(f"  {kind}: {count} chunks")
        return len(docs)

    if not docs:
        print("No indexable content found.")
        return 0

    if reset and index_dir().exists():
        shutil.rmtree(index_dir())

    store = get_vectorstore()
    store.reset_collection()

    batch_size = 100
    for start in range(0, len(docs), batch_size):
        batch = docs[start : start + batch_size]
        store.add_texts(
            texts=[d["page_content"] for d in batch],
            metadatas=[d["metadata"] for d in batch],
            ids=[f"{d['metadata']['source']}:{d['metadata']['chunk']}" for d in batch],
        )
        print(f"  embedded {min(start + batch_size, len(docs))}/{len(docs)}")

    from rag.upstream import current_commit

    write_manifest(repo_path, len(docs), len(files), current_commit(repo_path))
    print(f"Indexed {len(docs)} chunks from {len(files)} files.")
    return len(docs)


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Index upstream CrewAI for RAG")
    parser.add_argument(
        "repo",
        nargs="?",
        default=os.getenv("TARGET_REPO", "upstream/crewai"),
        help="Path to repository to index",
    )
    parser.add_argument("--reset", action="store_true", help="Clear existing index first")
    parser.add_argument("--dry-run", action="store_true", help="Count files/chunks only")
    parser.add_argument(
        "--paths",
        help="Comma-separated paths to index (overrides INDEX_PATHS env)",
    )
    parser.add_argument(
        "--github",
        action="store_true",
        help="Sync upstream from GitHub before indexing",
    )
    args = parser.parse_args()

    repo = Path(args.repo)
    if args.github or not repo.exists():
        from rag.upstream import sync_upstream

        repo = sync_upstream()

    paths = [p.strip() for p in args.paths.split(",")] if args.paths else None
    index_repo(repo, reset=args.reset, dry_run=args.dry_run, paths=paths)


if __name__ == "__main__":
    main()
