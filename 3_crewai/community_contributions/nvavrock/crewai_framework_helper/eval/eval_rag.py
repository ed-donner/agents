"""Evaluate RAG retrieval against golden queries."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from rag.index import index_dir, load_env
from rag.paths import project_root
from rag.retrieve import search

QUERIES_FILE = Path(__file__).resolve().parent / "rag_queries.yaml"


def results_dir() -> Path:
    d = project_root() / "eval" / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_queries() -> dict:
    with QUERIES_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def hit_relevant(hit: dict, kinds: list[str], source_patterns: list[str]) -> bool:
    kind_ok = not kinds or hit.get("kind") in kinds
    source = hit.get("source", "")
    pattern_ok = any(p in source for p in source_patterns)
    return kind_ok and pattern_ok


def evaluate_query(spec: dict, top_k: int) -> dict:
    kinds = spec.get("kinds") or []
    patterns = spec.get("source_patterns") or []
    min_hits = spec.get("min_hits", 1)
    hits = search(spec["query"], top_k=top_k)
    relevant = [h for h in hits if hit_relevant(h, kinds, patterns)]
    passed = len(relevant) >= min_hits
    return {
        "id": spec["id"],
        "category": spec.get("category", ""),
        "query": spec["query"],
        "passed": passed,
        "relevant_count": len(relevant),
        "min_hits": min_hits,
        "top_hits": [
            {
                "source": h["source"],
                "kind": h["kind"],
                "score": h["score"],
                "relevant": hit_relevant(h, kinds, patterns),
            }
            for h in hits
        ],
    }


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Evaluate framework RAG golden queries")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    if not index_dir().exists():
        raise SystemExit("No RAG index. Run: uv run bootstrap-index --yes")

    cfg = load_queries()
    top_k = cfg.get("top_k", 3)
    threshold = cfg.get("pass_threshold_pct", 80)

    results = [evaluate_query(q, top_k) for q in cfg["queries"]]
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    pct = round(100 * passed / total, 1) if total else 0
    overall_pass = pct >= threshold

    payload = {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "index_dir": str(index_dir()),
        "pass_threshold_pct": threshold,
        "passed": passed,
        "total": total,
        "pass_rate_pct": pct,
        "overall_pass": overall_pass,
        "results": results,
    }

    out_path = results_dir() / f"rag_{datetime.now(UTC).strftime('%Y%m%d')}.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n")

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"RAG evaluation: {passed}/{total} passed ({pct}%) — threshold {threshold}%")
    print(f"Overall: {'PASS' if overall_pass else 'FAIL'}")
    print(f"Results: {out_path}\n")
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['id']}: {r['relevant_count']}/{r['min_hits']} relevant — {r['query'][:50]}")


if __name__ == "__main__":
    main()
