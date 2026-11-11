from pathlib import Path

SANDBOX_ROOT = Path("sandbox")


def ensure_sandbox_tree() -> Path:
    """Create the shared sandbox tree used by the flow outputs."""

    for relative_path in ("design", "backend", "frontend", "validation", "tests"):
        (SANDBOX_ROOT / relative_path).mkdir(parents=True, exist_ok=True)

    return SANDBOX_ROOT


def sandbox_path(*parts: str) -> Path:
    """Resolve a file path inside sandbox and create the parent directories."""

    root = ensure_sandbox_tree()
    target_path = root.joinpath(*parts)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path
