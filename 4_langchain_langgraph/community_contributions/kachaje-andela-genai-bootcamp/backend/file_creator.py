import re
from pathlib import Path
from typing import Dict, List
from backend.utils.logger import get_logger

logger = get_logger()


def create_project(plan: str, language: str, session_id: str) -> Dict:
    sandbox_dir = Path("sandbox") / session_id

    try:
        logger.log_file_operation(
            operation="create_directory",
            file_path=str(sandbox_dir),
            success=True,
            details={"session_id": session_id},
        )
        sandbox_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.log_file_operation(
            operation="create_directory",
            file_path=str(sandbox_dir),
            success=False,
            error=str(e),
            details={"session_id": session_id},
        )
        raise

    files_created = []
    files_skipped = []

    file_names_from_structure = _extract_file_names_from_plan(plan, language)
    
    code_blocks_with_names = []
    code_block_with_name_pattern = r"```(\w+):([^\s\n]+)\s*\n(.*?)```"
    matched_positions = set()
    for match in re.finditer(code_block_with_name_pattern, plan, re.DOTALL):
        matched_positions.add((match.start(), match.end()))
        lang, filename, code = match.groups()
        code_blocks_with_names.append((filename, code))
    
    simple_code_blocks = []
    for match in re.finditer(r"```(?:\w+)?\n(.*?)```", plan, re.DOTALL):
        is_already_matched = any(
            match.start() >= pos_start and match.end() <= pos_end
            for pos_start, pos_end in matched_positions
        )
        if not is_already_matched:
            simple_code_blocks.append(match.group(1))
    if code_blocks_with_names:
        logger.logger.info(
            f"Found {len(code_blocks_with_names)} code blocks with potential file names for session {session_id}"
        )
        for file_name_hint, code in code_blocks_with_names:
            try:
                if file_name_hint:
                    filename = file_name_hint.strip()
                    if not any(filename.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]):
                        ext = _get_extension(language)
                        if not filename.endswith(ext):
                            filename = f"{filename}{ext}"
                else:
                    ext = _get_extension(language)
                    if file_names_from_structure:
                        block_index = len(files_created)
                        if block_index < len(file_names_from_structure):
                            filename = file_names_from_structure[block_index]
                            if not filename.endswith(ext):
                                filename = f"{filename}{ext}"
                        else:
                            filename = f"file{block_index}{ext}"
                    else:
                        filename = f"main{ext}" if len(files_created) == 0 else f"file{len(files_created)}{ext}"
                
                filepath = sandbox_dir / filename
                code_stripped = code.strip()
                
                if str(filepath) in files_created:
                    files_skipped.append(str(filepath))
                    continue
                
                filepath.write_text(code_stripped)
                files_created.append(str(filepath))

                logger.log_file_operation(
                    operation="create_file",
                    file_path=str(filepath),
                    success=True,
                    details={
                        "language": language,
                        "filename": filename,
                        "size": len(code_stripped),
                        "session_id": session_id,
                    },
                )
            except Exception as e:
                logger.log_file_operation(
                    operation="create_file",
                    file_path=(
                        str(sandbox_dir / filename)
                        if "filename" in locals()
                        else "unknown"
                    ),
                    success=False,
                    error=str(e),
                    details={"session_id": session_id},
                )
                raise
    
    elif simple_code_blocks:
        logger.logger.info(
            f"Found {len(simple_code_blocks)} code blocks (no file names) for session {session_id}"
        )
        for i, code in enumerate(simple_code_blocks):
            try:
                ext = _get_extension(language)
                if file_names_from_structure and i < len(file_names_from_structure):
                    filename = file_names_from_structure[i]
                    if not filename.endswith(ext):
                        filename = f"{filename}{ext}"
                else:
                    filename = f"main{ext}" if i == 0 else f"file{i}{ext}"
                
                filepath = sandbox_dir / filename
                code_stripped = code.strip()
                filepath.write_text(code_stripped)
                files_created.append(str(filepath))

                logger.log_file_operation(
                    operation="create_file",
                    file_path=str(filepath),
                    success=True,
                    details={
                        "language": language,
                        "extension": ext,
                        "size": len(code_stripped),
                        "session_id": session_id,
                    },
                )
            except Exception as e:
                logger.log_file_operation(
                    operation="create_file",
                    file_path=(
                        str(sandbox_dir / filename)
                        if "filename" in locals()
                        else "unknown"
                    ),
                    success=False,
                    error=str(e),
                    details={"session_id": session_id, "block_index": i},
                )
                raise

    if not files_created:
        try:
            ext = _get_extension(language)
            main_file = sandbox_dir / f"main{ext}"
            fallback_content = f"# {plan}\n"

            main_file.write_text(fallback_content)
            files_created.append(str(main_file))

            logger.log_file_operation(
                operation="create_file",
                file_path=str(main_file),
                success=True,
                details={
                    "language": language,
                    "extension": ext,
                    "reason": "no_code_blocks_found",
                    "session_id": session_id,
                },
            )
        except Exception as e:
            logger.log_file_operation(
                operation="create_file",
                file_path=str(main_file) if "main_file" in locals() else "unknown",
                success=False,
                error=str(e),
                details={"session_id": session_id},
            )
            raise

    try:
        readme = sandbox_dir / "README.md"
        readme.write_text(f"# Project Plan\n\n{plan}\n")
        files_created.append(str(readme))

        logger.log_file_operation(
            operation="create_file",
            file_path=str(readme),
            success=True,
            details={
                "file_type": "readme",
                "plan_length": len(plan),
                "session_id": session_id,
            },
        )
    except Exception as e:
        logger.log_file_operation(
            operation="create_file",
            file_path=str(readme) if "readme" in locals() else "unknown",
            success=False,
            error=str(e),
            details={"session_id": session_id},
        )
        raise

    logger.logger.info(
        f"Project creation completed for session {session_id}: "
        f"{len(files_created)} files created, {len(files_skipped)} files skipped in {sandbox_dir}"
    )

    return {
        "files_created": files_created,
        "files_skipped": files_skipped,
        "project_path": str(sandbox_dir),
        "status": "success",
    }


def _extract_file_names_from_plan(plan: str, language: str) -> List[str]:
    file_names = []
    ext = _get_extension(language)
    
    patterns = [
        # Pattern: `filename.py` or `filename.ext`
        r"`([^\s`]+\.\w+)`",
        # Pattern: * `filename.py` (bullet list)
        r"\*\s+`?([^\s`]+\.\w+)`?",
        # Pattern: - filename.py (dash list)
        r"-\s+`?([^\s`]+\.\w+)`?",
        # Pattern: + `filename.py` (plus prefix list)
        r"\+\s+`?([^\s`]+\.\w+)`?",
        # Pattern: ### `filename.py` (markdown header)
        r"###\s+`([^\s`]+\.\w+)`",
        # Pattern: filename.py: (with colon)
        r"([^\s]+\.\w+)\s*:",
        # Pattern: filename (without extension, add extension)
        r"`([^\s`]+)`\s*\(.*?\)",
    ]
    
    structure_section = ""
    structure_markers = [
        r"Project Structure[:\s]*(.*?)(?=\n\n|\*\*|##|$)",
        r"Files[:\s]*(.*?)(?=\n\n|\*\*|##|$)",
        r"Structure[:\s]*(.*?)(?=\n\n|\*\*|##|$)",
    ]
    
    for marker in structure_markers:
        match = re.search(marker, plan, re.IGNORECASE | re.DOTALL)
        if match:
            structure_section = match.group(1)
            break
    
    search_text = structure_section if structure_section else plan
    
    for pattern in patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            filename = match.strip()
            # Skip common non-file patterns, but allow __init__.py if explicitly mentioned
            if filename.lower() in ["readme.md", "requirements.txt", "package.json"]:
                continue
            # Add extension if missing
            if not any(filename.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".md", ".txt", ".json"]):
                filename = f"{filename}{ext}"
            if filename not in file_names:
                file_names.append(filename)
    
    code_block_file_pattern = r"```\w+:(.+?\.\w+)"
    code_block_matches = re.findall(code_block_file_pattern, plan)
    for match in code_block_matches:
        filename = match.strip()
        if filename not in file_names:
            file_names.append(filename)
    
    return file_names


def _get_extension(language: str) -> str:
    extensions = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "java": ".java",
        "go": ".go",
        "rust": ".rs",
        "cpp": ".cpp",
        "c": ".c",
    }
    return extensions.get(language.lower(), ".txt")
