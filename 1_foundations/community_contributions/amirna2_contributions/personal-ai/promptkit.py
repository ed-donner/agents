from pathlib import Path
import re

_pat = re.compile(r"\{([a-zA-Z0-9_\.]+)\}")

def _get(ctx, path):
    cur = ctx
    for p in path.split("."):
        cur = cur[p] if isinstance(cur, dict) else getattr(cur, p)
    return cur

def render(path, vars):
    txt = Path(path).read_text(encoding="utf-8")
    return _pat.sub(lambda m: str(_get(vars, m.group(1))), txt)
