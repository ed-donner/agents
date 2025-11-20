import os
import subprocess
from typing import Dict
from datetime import datetime
from agents import function_tool


@function_tool
def read_code_file(file_path: str) -> Dict[str, str]:
    """Read a code file and return its contents with basic info"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        extension = file_path.split('.')[-1]
        language_map = {
            'ts': 'TypeScript', 'tsx': 'TypeScript React',
            'js': 'JavaScript', 'jsx': 'JavaScript React',
            'go': 'Go',
            'ruby': 'Ruby', 'rb': 'Ruby',
            'py': 'Python',
            'java': 'Java',
            'c': 'C', 'cpp': 'C++', 'cc': 'C++',
            'rs': 'Rust',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'php': 'PHP',
        }
        
        return {
            "content": content,
            "language": language_map.get(extension, "Unknown"),
            "file_name": file_path.split('/')[-1],
            "lines": len(content.split('\n')),
            "extension": extension
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@function_tool
def save_learning_doc(content: str, file_name: str) -> Dict[str, str]:
    """Save your learning documentation"""
    try:
        os.makedirs('learning_docs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        if file_name.endswith('.md'):
            base_name = file_name[:-3]  # Remove .md
        else:
            base_name = file_name
            
        clean_name = base_name.replace('.', '_')
        file_path = f"learning_docs/{timestamp}_{clean_name}.md"
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return {"status": "success", "saved_to": file_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@function_tool
def get_git_diff(file_path: str = "", commits_back: int = 1, compare_with: str = "", include_commit_history: bool = False, history_limit: int = 10) -> Dict[str, str]:
    """Get git diff to see what changed, optionally with commit history context"""
    try:
        # Get commit history if requested
        commit_history = ""
        if include_commit_history:
            log_cmd = [
                'git', 'log',
                f'-{history_limit}',
                '--pretty=format:%H|%an|%ae|%ad|%s',
                '--date=short',
                '--follow'
            ]
            
            if file_path:
                log_cmd.extend(['--', file_path])
            
            log_result = subprocess.run(log_cmd, capture_output=True, text=True)
            
            if log_result.returncode == 0 and log_result.stdout.strip():
                commits = []
                for line in log_result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) == 5:
                            commits.append({
                                "hash": parts[0][:8],
                                "author": parts[1],
                                "date": parts[3],
                                "message": parts[4]
                            })
                
                commit_history = f"\n=== COMMIT HISTORY ({len(commits)} recent commits) ===\n\n"
                for i, commit in enumerate(commits, 1):
                    commit_history += f"{i}. [{commit['date']}] {commit['hash']} - {commit['message']}\n"
                    commit_history += f"   By: {commit['author']}\n\n"
        
        # Get the diff
        if compare_with:
            cmd = ['git', 'diff', compare_with, file_path] if file_path else ['git', 'diff', compare_with]
        elif commits_back > 1:
            cmd = ['git', 'diff', f'HEAD~{commits_back}', file_path] if file_path else ['git', 'diff', f'HEAD~{commits_back}']
        else:
            cmd = ['git', 'diff', 'HEAD~1', file_path] if file_path else ['git', 'diff', 'HEAD~1']

        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {"status": "error", "message": result.stderr}
        
        diff_output = result.stdout
        
        if not diff_output.strip():
            diff_output = "No changes found in diff"
        
        # Combine commit history with diff
        full_output = commit_history + diff_output if commit_history else diff_output
        
        return {
            "status": "success",
            "diff": full_output,
            "file": file_path if file_path else "all files",
            "has_commit_history": bool(commit_history)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

