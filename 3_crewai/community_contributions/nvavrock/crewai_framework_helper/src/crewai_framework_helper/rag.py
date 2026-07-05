"""RAG over upstream CrewAI source and docs (clone → index → search)."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_REPO_URL = "https://github.com/crewAIInc/crewAI"
DEFAULT_TOP_K = 6
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


def project_root() -> Path:
    env = os.getenv("FRAMEWORK_HELPER_ROOT")
    if env:
        return Path(env)
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "pyproject.toml").exists() and (
            candidate / "src" / "crewai_framework_helper" / "rag.py"
        ).is_file():
            return candidate
    return Path(__file__).resolve().parent.parent.parent


def upstream_repo_dir() -> Path:
    rel = os.getenv("UPSTREAM_DIR", "upstream/crewai")
    return (project_root() / rel).resolve()


def index_dir() -> Path:
    return Path(os.getenv("RAG_INDEX_DIR", project_root() / ".rag_index"))


def load_env() -> None:
    load_dotenv(project_root() / ".env")


def index_paths() -> list[str]:
    raw = os.getenv("INDEX_PATHS")
    if raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return list(DEFAULT_INDEX_PATHS)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def current_commit(repo: Path) -> str | None:
    if not (repo / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or None


def sync_upstream(force_ref: str | None = None) -> Path:
    load_env()
    url = os.getenv("UPSTREAM_REPO_URL", DEFAULT_REPO_URL)
    ref = force_ref or os.getenv("UPSTREAM_REF", "main")
    if ref not in ("main", "master"):
        probe = subprocess.run(
            ["git", "ls-remote", "--tags", url, ref, f"refs/tags/{ref}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if not probe.stdout.strip():
            print(f"Tag/ref '{ref}' not found; falling back to 'main'.")
            ref = "main"

    dest = upstream_repo_dir()
    dest.parent.mkdir(parents=True, exist_ok=True)

    if not (dest / ".git").exists():
        print(f"Cloning {url} (ref={ref}) -> {dest}")
        _run(["git", "clone", "--depth", "1", "--branch", ref, url, str(dest)])
    else:
        print(f"Updating {dest} (ref={ref})")
        _run(["git", "fetch", "origin", ref, "--depth", "1"], cwd=dest)
        _run(["git", "checkout", ref], cwd=dest)
        _run(["git", "reset", "--hard", f"origin/{ref}"], cwd=dest)

    commit = current_commit(dest)
    if commit:
        print(f"Upstream at {commit[:12]} ({ref})")
    return dest


def _kind_for_path(rel: str) -> str:
    if rel.startswith("docs/"):
        return "docs"
    if rel in {"AGENTS.md", "README.md"}:
        return "meta"
    return "source"


def _clean_mdx(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    text = re.sub(r"^import\s+.+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"<[A-Z][A-Za-z0-9]*[^>]*>", " ", text)
    text = re.sub(r"</[A-Z][A-Za-z0-9]*>", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _collect_files(repo_path: Path, paths: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    repo_path = repo_path.resolve()

    for entry in paths:
        target = (repo_path / entry).resolve()
        if not str(target).startswith(str(repo_path)):
            continue
        candidates = [target] if target.is_file() else list(target.rglob("*")) if target.is_dir() else []

        for path in candidates:
            if not path.is_file() or path in seen:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            rel = path.relative_to(repo_path).as_posix()
            if rel.startswith("docs/v"):
                continue
            if path.suffix.lower() not in CODE_EXTENSIONS or path.stat().st_size > 500_000:
                continue
            seen.add(path)
            files.append(path)

    return sorted(files)


def _build_documents(repo_path: Path, paths: list[str]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\nclass ", "\ndef ", "\nfunction ", "\n\n", "\n", " "],
    )
    docs: list[dict] = []
    for file_path in _collect_files(repo_path, paths):
        try:
            raw = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        text = _clean_mdx(raw) if file_path.suffix.lower() == ".mdx" else raw
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
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    return Chroma(
        collection_name="codebase",
        embedding_function=OpenAIEmbeddings(model=model),
        persist_directory=str(index_dir()),
    )


def index_repo(repo_path: Path, reset: bool = False, dry_run: bool = False) -> int:
    load_env()
    repo_path = repo_path.resolve()
    paths = index_paths()
    files = _collect_files(repo_path, paths)
    docs = _build_documents(repo_path, paths)

    print(f"Repo: {repo_path}")
    print(f"Files: {len(files)}  Chunks: {len(docs)}")

    if dry_run:
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

    index_dir().mkdir(parents=True, exist_ok=True)
    manifest = {
        "indexed_at": datetime.now(UTC).isoformat(),
        "repo_path": str(repo_path),
        "chunk_count": len(docs),
        "file_count": len(files),
        "upstream_commit": current_commit(repo_path),
    }
    (index_dir() / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Indexed {len(docs)} chunks from {len(files)} files.")
    return len(docs)


def search(query: str, top_k: int = DEFAULT_TOP_K, kind: str | None = None) -> list[dict]:
    load_env()
    if not index_dir().exists():
        raise FileNotFoundError(
            f"No RAG index at {index_dir()}. Run: uv run bootstrap-index --yes"
        )
    fetch_k = top_k * 4 if kind else top_k
    results = get_vectorstore().similarity_search_with_score(query, k=fetch_k)
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


def bootstrap_main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Sync upstream crewAI and build the RAG index")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    repo = sync_upstream()
    count = index_repo(repo, dry_run=True)
    if count == 0:
        print("Nothing to index.")
        return

    if not args.yes:
        answer = input(f"Embed {count} chunks into {index_dir()}? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("Aborted.")
            return

    index_repo(repo, reset=True)
