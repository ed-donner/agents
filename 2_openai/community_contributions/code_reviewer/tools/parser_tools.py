import ast
from agents import function_tool
from tree_sitter_languages import get_language, get_parser


CHUNK_SIZE_LINES = 300
CHUNK_OVERLAP_LINES = 10

LANGUAGE_MAP = {
    ".py":    ("python",     "python"),
    ".js":    ("javascript", "javascript"),
    ".ts":    ("typescript", "typescript"),
    ".java":  ("java",       "java"),
    ".go":    ("go",         "go"),
    ".rb":    ("ruby",       "ruby"),
    ".php":   ("php",        "php"),
    ".cs":    ("csharp",     "c_sharp"),
    ".cpp":   ("cpp",        "cpp"),
    ".c":     ("c",          "c"),
    ".h":     ("c",          "c"),
    ".rs":    ("rust",       "rust"),
    ".swift": ("swift",      "swift"),
    ".kt":    ("kotlin",     "kotlin"),
}


LANGUAGE_QUERIES = {
    "python": {
        "class":    ["class_definition"],
        "function": ["function_definition", "async_function_definition"],
        "import":   ["import_statement", "import_from_statement"],
    },
    "javascript": {
        "class":    ["class_declaration"],
        "function": ["function_declaration", "arrow_function",
                     "method_definition", "async_function_declaration"],
        "import":   ["import_statement"],
    },
    "typescript": {
        "class":    ["class_declaration"],
        "function": ["function_declaration", "arrow_function",
                     "method_definition", "async_function_declaration"],
        "import":   ["import_statement"],
    },
    "java": {
        "class":    ["class_declaration", "interface_declaration"],
        "function": ["method_declaration", "constructor_declaration"],
        "import":   ["import_declaration"],
    },
    "go": {
        "class":    ["type_declaration"],      
        "function": ["function_declaration", "method_declaration"],
        "import":   ["import_declaration"],
    },
    "ruby": {
        "class":    ["class", "module"],
        "function": ["method", "singleton_method"],
        "import":   ["call"],                 
    },
    "php": {
        "class":    ["class_declaration", "interface_declaration", "trait_declaration"],
        "function": ["function_definition", "method_declaration"],
        "import":   ["namespace_use_declaration"],
    },
    "csharp": {
        "class":    ["class_declaration", "interface_declaration"],
        "function": ["method_declaration", "constructor_declaration"],
        "import":   ["using_directive"],
    },
    "cpp": {
        "class":    ["class_specifier", "struct_specifier"],
        "function": ["function_definition"],
        "import":   ["preproc_include"],
    },
    "c": {
        "class":    ["struct_specifier"],
        "function": ["function_definition"],
        "import":   ["preproc_include"],
    },
    "rust": {
        "class":    ["struct_item", "impl_item", "trait_item"],
        "function": ["function_item"],
        "import":   ["use_declaration"],
    },
    "swift": {
        "class":    ["class_declaration", "struct_declaration", "protocol_declaration"],
        "function": ["function_declaration", "init_declaration"],
        "import":   ["import_declaration"],
    },
    "kotlin": {
        "class":    ["class_declaration", "object_declaration", "interface_declaration"],
        "function": ["function_declaration"],
        "import":   ["import_header"],
    },
}


@function_tool
def parse_code_tool(file_path: str, content: str) -> dict:
    """Parses a source file and extracts a structured map of its classes, functions, and imports."""
    extension = "." + file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    language_info = LANGUAGE_MAP.get(extension)
    line_count = len(content.splitlines())

    base_result = {
        "file_path": file_path,
        "language": language_info[0] if language_info else "unknown",
        "line_count": line_count,
        "classes": [],
        "functions": [],
        "imports": [],
        "parse_error": ""
    }

    if not language_info:
        base_result["parse_error"] = (
            f"Unsupported file extension '{extension}' for '{file_path}'. "
            f"Structural map skipped."
        )
        return base_result

    language_label, ts_language_name = language_info

    if language_label == "python":
        return _parse_python(file_path, content, line_count)

    return _parse_with_tree_sitter(
        file_path, content, line_count, language_label, ts_language_name
    )


def _parse_python(file_path: str, content: str, line_count: int) -> dict:
    """Uses Python's built-in ast module for deep Python-specific parsing."""
    result = {
        "file_path": file_path,
        "language": "python",
        "line_count": line_count,
        "classes": [],
        "functions": [],
        "imports": [],
        "parse_error": ""
    }

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        result["parse_error"] = (
            f"Syntax error in '{file_path}' at line {e.lineno}: {e.msg}"
        )
        return result

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    f"import {alias.name}" +
                    (f" as {alias.asname}" if alias.asname else "")
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join(
                a.name + (f" as {a.asname}" if a.asname else "")
                for a in node.names
            )
            imports.append(f"from {module} import {names}")

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_classes = [
                ast.unparse(b) if hasattr(ast, "unparse") else "unknown"
                for b in node.bases
            ]
            methods = [
                _extract_python_function(item)
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes.append({
                "name": node.name,
                "base_classes": base_classes,
                "methods": methods
            })

    functions = [
        _extract_python_function(node)
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    result["classes"] = classes
    result["functions"] = functions
    result["imports"] = imports
    return result


def _extract_python_function(node) -> dict:
    """Extracts rich metadata from a Python function/method AST node."""
    params = [arg.arg for arg in node.args.args]
    return_annotation = ""
    if node.returns:
        try:
            return_annotation = ast.unparse(node.returns)
        except Exception:
            return_annotation = "unknown"

    has_docstring = (
        bool(node.body) and
        isinstance(node.body[0], ast.Expr) and
        isinstance(node.body[0].value, ast.Constant) and
        isinstance(node.body[0].value.value, str)
    )

    return {
        "name": node.name,
        "parameters": params,
        "return_annotation": return_annotation,
        "line_start": node.lineno,
        "line_end": node.end_lineno,
        "has_docstring": has_docstring
    }


def _parse_with_tree_sitter(
    file_path: str,
    content: str,
    line_count: int,
    language_label: str,
    ts_language_name: str
) -> dict:
    """Uses tree-sitter to parse any supported non-Python source file."""
    result = {
        "file_path": file_path,
        "language": language_label,
        "line_count": line_count,
        "classes": [],
        "functions": [],
        "imports": [],
        "parse_error": ""
    }

    try:
        parser = get_parser(ts_language_name)
        tree = parser.parse(bytes(content, "utf-8"))
    except Exception as e:
        result["parse_error"] = (
            f"tree-sitter failed to load parser for '{language_label}': {str(e)}"
        )
        return result

    queries = LANGUAGE_QUERIES.get(language_label, {})
    lines = content.splitlines()

    classes = []
    functions = []
    imports = []

    def walk(node):
        node_type = node.type

        if node_type in queries.get("class", []):
            name = _extract_node_name(node, lines)
            methods = []

            for child in node.children:
                if child.type in queries.get("function", []):
                    methods.append(_extract_ts_function(child, lines))

            classes.append({
                "name": name,
                "base_classes": _extract_base_classes(node, lines, language_label),
                "methods": methods
            })
            return

        if node_type in queries.get("function", []):
            parent_type = node.parent.type if node.parent else ""
            if parent_type not in queries.get("class", []):
                functions.append(_extract_ts_function(node, lines))

        if node_type in queries.get("import", []):
            start = node.start_point[0]
            end = node.end_point[0]
            import_text = "\n".join(lines[start:end + 1]).strip()
            imports.append(import_text)
            return

        for child in node.children:
            walk(child)

    walk(tree.root_node)

    result["classes"] = classes
    result["functions"] = functions
    result["imports"] = imports
    return result


def _extract_node_name(node, lines: list) -> str:
    """Extracts the name of a class or function node."""
    for child in node.children:
        if child.type == "identifier":
            start_line = child.start_point[0]
            start_col = child.start_point[1]
            end_col = child.end_point[1]
            return lines[start_line][start_col:end_col]
    return "unknown"


def _extract_ts_function(node, lines: list) -> dict:
    """Extracts basic metadata from a tree-sitter function node."""
    name = _extract_node_name(node, lines)
    line_start = node.start_point[0] + 1
    line_end = node.end_point[0] + 1

    parameters = []
    for child in node.children:
        if "parameter" in child.type:
            for param_child in child.children:
                if param_child.type == "identifier":
                    start_line = param_child.start_point[0]
                    start_col = param_child.start_point[1]
                    end_col = param_child.end_point[1]
                    parameters.append(lines[start_line][start_col:end_col])

    return {
        "name": name,
        "parameters": parameters,
        "return_annotation": "",
        "line_start": line_start,
        "line_end": line_end,
        "has_docstring": False
    }


def _extract_base_classes(node, lines: list, language_label: str) -> list:
    """Attempts to extract base class or interface names from a class node."""
    
    base_classes = []
    
    INHERITANCE_NODE_TYPES = {
        "superclass", "base_list", "super_interfaces",
        "implements", "extends_clause", "class_parents",
        "supertypes"
    }

    for child in node.children:
        if child.type in INHERITANCE_NODE_TYPES:
            for sub in child.children:
                if sub.type == "identifier" or sub.type == "type_identifier":
                    start_line = sub.start_point[0]
                    start_col = sub.start_point[1]
                    end_col = sub.end_point[1]
                    base_classes.append(lines[start_line][start_col:end_col])

    return base_classes


@function_tool
def chunk_code_tool(file_path: str, content: str) -> dict:
    """Splits a source file into overlapping chunks of up to CHUNK_SIZE_LINES lines."""
    lines = content.splitlines()
    total_lines = len(lines)
    chunks = []
    chunk_index = 0
    start = 0

    while start < total_lines:
        end = min(start + CHUNK_SIZE_LINES, total_lines)
        chunk_lines = lines[start:end]
        chunk_content = "\n".join(chunk_lines)

        chunks.append({
            "chunk_index": chunk_index,
            "file_path": file_path,
            "start_line": start + 1,
            "end_line": end,
            "content": chunk_content,
            "line_count": len(chunk_lines)
        })

        chunk_index += 1
        next_start = end - CHUNK_OVERLAP_LINES
        if next_start <= start:
            break
        start = next_start

    return {
        "file_path": file_path,
        "total_lines": total_lines,
        "total_chunks": len(chunks),
        "chunks": chunks
    }