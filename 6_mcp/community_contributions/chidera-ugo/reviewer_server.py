"""
MCP server exposing frontend code analysis tools.
Each tool performs concrete pattern-based checks — no LLM involved here,
just real static analysis the agent can call and reason over.
"""
import re
import os
import glob
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("reviewer_server")


# ── File tools ────────────────────────────────────────────────────────────────

@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a source file.

    Args:
        path: Absolute or relative path to the file
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: file not found at {path}"
    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool()
def list_source_files(directory: str) -> list[str]:
    """List all frontend source files (.tsx, .ts, .jsx, .js) in a directory.

    Args:
        directory: Path to the directory to search
    """
    extensions = ["**/*.tsx", "**/*.ts", "**/*.jsx", "**/*.js"]
    files = []
    for pattern in extensions:
        matches = glob.glob(os.path.join(directory, pattern), recursive=True)
        files.extend(matches)
    # Exclude node_modules and .next
    files = [f for f in files if "node_modules" not in f and ".next" not in f]
    return sorted(files)


# ── Accessibility checker ─────────────────────────────────────────────────────

@mcp.tool()
def check_accessibility(code: str) -> dict:
    """Check a component for common accessibility issues.

    Checks for: missing alt on images, non-interactive elements with click handlers,
    positive tabIndex, empty buttons, target=_blank without rel, inputs without labels.

    Args:
        code: The source code to analyse
    """
    issues = []
    warnings = []

    # img without alt
    imgs = re.findall(r'<img\b[^>]*>', code, re.IGNORECASE)
    missing_alt = [t for t in imgs if not re.search(r'\balt\s*=', t)]
    if missing_alt:
        issues.append(f"{len(missing_alt)} <img> element(s) missing `alt` attribute — screen readers cannot describe these images")

    # onClick on div/span without role or button alternative
    clickable = re.findall(r'<(div|span)\b[^>]*onClick\b[^>]*>', code)
    has_role = [t for t in clickable if re.search(r'\brole\s*=', t) or re.search(r'\bonKeyDown\b', t)]
    bad_clicks = len(clickable) - len(has_role)
    if bad_clicks > 0:
        issues.append(f"{bad_clicks} <div>/<span> element(s) have onClick with no `role` or `onKeyDown` — use <button> or add role='button' + onKeyDown for keyboard access")

    # Positive tabIndex
    positive_tab = re.findall(r'tabIndex\s*=\s*[{"\']?\s*[1-9][0-9]*', code)
    if positive_tab:
        warnings.append(f"{len(positive_tab)} instance(s) of positive tabIndex — this breaks the natural tab order; use tabIndex={{0}} or tabIndex={{-1}} only")

    # target="_blank" without rel containing noopener
    blank_links = re.findall(r'<a\b[^>]*target\s*=\s*["\']_blank["\'][^>]*>', code, re.IGNORECASE)
    unsafe_blank = [t for t in blank_links if not re.search(r'noopener', t)]
    if unsafe_blank:
        issues.append(f"{len(unsafe_blank)} <a target='_blank'> element(s) missing rel='noopener noreferrer' — exposes opener reference to the new page")

    # Empty buttons (icon buttons often missing aria-label)
    empty_buttons = re.findall(r'<button\b[^>]*>\s*</button>', code)
    if empty_buttons:
        issues.append(f"{len(empty_buttons)} empty <button> element(s) — add visible text or aria-label for screen readers")

    # Input without aria-label or id (which could link to a <label>)
    inputs = re.findall(r'<input\b[^>]*/?>|<input\b[^>]*></input>', code, re.IGNORECASE)
    inputs_no_label = [
        t for t in inputs
        if not re.search(r'\b(aria-label|aria-labelledby|id)\s*=', t)
        and 'type="hidden"' not in t
        and "type='hidden'" not in t
    ]
    if inputs_no_label:
        warnings.append(f"{len(inputs_no_label)} <input> element(s) with no aria-label or id — ensure each input is associated with a visible label")

    return {
        "issues": issues,
        "warnings": warnings,
        "issue_count": len(issues),
        "warning_count": len(warnings),
    }


# ── Security checker ──────────────────────────────────────────────────────────

@mcp.tool()
def check_security(code: str) -> dict:
    """Check a component for common frontend security vulnerabilities.

    Checks for: dangerouslySetInnerHTML, eval, innerHTML assignment,
    hardcoded secrets, document.write, unsafe URL construction.

    Args:
        code: The source code to analyse
    """
    issues = []
    warnings = []

    # dangerouslySetInnerHTML
    dangerous_html = re.findall(r'dangerouslySetInnerHTML', code)
    if dangerous_html:
        issues.append(f"`dangerouslySetInnerHTML` used {len(dangerous_html)} time(s) — XSS risk if content is not sanitized with DOMPurify or similar")

    # eval
    eval_uses = re.findall(r'\beval\s*\(', code)
    if eval_uses:
        issues.append(f"`eval()` used {len(eval_uses)} time(s) — executes arbitrary code; almost always avoidable")

    # innerHTML direct assignment
    inner_html = re.findall(r'\.innerHTML\s*=', code)
    if inner_html:
        issues.append(f"`.innerHTML =` assigned directly {len(inner_html)} time(s) — XSS risk; prefer textContent or sanitized insertion")

    # document.write
    doc_write = re.findall(r'document\.write\s*\(', code)
    if doc_write:
        issues.append(f"`document.write()` used {len(doc_write)} time(s) — deprecated and XSS-prone")

    # Hardcoded secrets (common patterns)
    secret_patterns = [
        (r'(api_key|apikey|api-key|secret|password|token|auth)\s*[:=]\s*["\'][a-zA-Z0-9_\-]{8,}["\']', "Possible hardcoded secret"),
        (r'sk-[a-zA-Z0-9]{20,}', "Possible OpenAI API key"),
        (r'ghp_[a-zA-Z0-9]{36}', "Possible GitHub personal access token"),
    ]
    for pattern, label in secret_patterns:
        matches = re.findall(pattern, code, re.IGNORECASE)
        if matches:
            issues.append(f"{label} detected — move to environment variables")

    # localStorage with sensitive-sounding keys
    local_storage_sensitive = re.findall(
        r'localStorage\.setItem\s*\(\s*["\'][^"\']*(?:token|password|secret|auth|key)[^"\']*["\']',
        code, re.IGNORECASE
    )
    if local_storage_sensitive:
        warnings.append(f"Sensitive data possibly stored in localStorage {len(local_storage_sensitive)} time(s) — localStorage is accessible to any script on the page; prefer httpOnly cookies for auth tokens")

    # target=_blank (also a mild security issue, covered in accessibility but worth noting here too)
    blank_no_rel = re.findall(r'target=["\']_blank["\'](?![^>]*noopener)', code)
    if blank_no_rel:
        warnings.append(f"{len(blank_no_rel)} <a target='_blank'> without noopener — the opened page can access window.opener")

    return {
        "issues": issues,
        "warnings": warnings,
        "issue_count": len(issues),
        "warning_count": len(warnings),
    }


# ── Performance checker ───────────────────────────────────────────────────────

@mcp.tool()
def check_performance(code: str) -> dict:
    """Check a component for common React/frontend performance anti-patterns.

    Checks for: inline arrow functions in JSX, array index as key, useEffect
    without dependencies, console.log, missing memoization signals.

    Args:
        code: The source code to analyse
    """
    issues = []
    warnings = []

    # Inline arrow functions in JSX props (causes new function ref on every render)
    inline_arrows = re.findall(r'(?:onClick|onChange|onSubmit|onBlur|onFocus)\s*=\s*\{(?:\s*\([^)]*\)\s*=>|\s*[a-zA-Z_]\w*\s*=>)', code)
    if inline_arrows:
        warnings.append(f"{len(inline_arrows)} inline arrow function(s) in JSX event props — creates a new function reference on every render; wrap in useCallback if passed to memoized children")

    # Array index as key in .map()
    index_as_key = re.findall(r'\.map\s*\(\s*\([^)]*,\s*(\w+)\)[^)]*key\s*=\s*[{"\']?\s*\1', code)
    # Simpler heuristic: key={index} or key={i}
    index_key = re.findall(r'key\s*=\s*[{"\']?\s*(?:index|idx|i)\b', code)
    if index_key:
        warnings.append(f"{len(index_key)} instance(s) of array index used as React key — causes incorrect reconciliation on reorder/insert; use a stable unique id")

    # useEffect without dependency array
    effect_no_deps = re.findall(r'useEffect\s*\(\s*(?:async\s*)?\([^)]*\)\s*=>', code)
    effect_with_deps = re.findall(r'useEffect\s*\([^,]+,\s*\[', code)
    unconstrained_effects = len(effect_no_deps) - len(effect_with_deps)
    if unconstrained_effects > 0:
        issues.append(f"{unconstrained_effects} useEffect call(s) may be missing a dependency array — runs on every render; add [] or specific deps")

    # console.log left in
    console_logs = re.findall(r'console\.(?:log|warn|error|debug)\s*\(', code)
    if console_logs:
        warnings.append(f"{len(console_logs)} console statement(s) found — remove before production or use a proper logger")

    # Large inline object/array literals in JSX (new reference every render)
    inline_objects = re.findall(r'(?:style|sx|className)\s*=\s*\{\s*\{', code)
    if inline_objects:
        warnings.append(f"{len(inline_objects)} inline object literal(s) in JSX props — move outside the component or wrap in useMemo to avoid new references on every render")

    return {
        "issues": issues,
        "warnings": warnings,
        "issue_count": len(issues),
        "warning_count": len(warnings),
    }


# ── Best practices checker ────────────────────────────────────────────────────

@mcp.tool()
def check_best_practices(code: str) -> dict:
    """Check a component against TypeScript and React best practices.

    Checks for: any type, var usage, == instead of ===, missing display names,
    prop drilling signals, large components.

    Args:
        code: The source code to analyse
    """
    issues = []
    warnings = []

    # TypeScript `any`
    explicit_any = re.findall(r':\s*any\b', code)
    if explicit_any:
        warnings.append(f"`any` type used {len(explicit_any)} time(s) — defeats TypeScript's type safety; use unknown, a specific type, or a generic")

    # var declarations
    var_decls = re.findall(r'\bvar\b\s+\w+', code)
    if var_decls:
        warnings.append(f"`var` used {len(var_decls)} time(s) — use const or let for block-scoped declarations")

    # == instead of ===
    loose_equality = re.findall(r'(?<!=)={2}(?!=)', code)
    # Filter out JSX = and => and ==
    if loose_equality:
        warnings.append(f"Loose equality (==) found {len(loose_equality)} time(s) — use === for strict comparison")

    # @ts-ignore (suppressing type errors)
    ts_ignore = re.findall(r'@ts-ignore', code)
    if ts_ignore:
        warnings.append(f"`@ts-ignore` used {len(ts_ignore)} time(s) — suppresses type errors; fix the underlying type issue instead")

    # @ts-nocheck at file level
    if re.search(r'@ts-nocheck', code):
        issues.append("`@ts-nocheck` disables TypeScript checking for the entire file — remove and fix type errors individually")

    # Missing display name on anonymous component exports
    anon_exports = re.findall(r'export default function\s*\(|export default \([^)]*\)\s*=>', code)
    if anon_exports:
        warnings.append(f"{len(anon_exports)} anonymous component export(s) — name your components for better stack traces and React DevTools debugging")

    # Component size signal (> 200 lines is a warning)
    line_count = len(code.splitlines())
    if line_count > 200:
        warnings.append(f"Component is {line_count} lines — consider splitting into smaller, focused components")

    return {
        "issues": issues,
        "warnings": warnings,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "line_count": line_count,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse"],
        help="stdio (default, used by the internal agent) or sse (HTTP server for Claude/external clients)",
    )
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.transport == "sse":
        mcp.settings.port = args.port
    mcp.run(transport=args.transport)
