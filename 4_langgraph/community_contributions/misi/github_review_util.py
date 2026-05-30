from __future__ import annotations

import os
import re
import textwrap
import uuid
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class PRReviewState(TypedDict, total=False):
    messages: Annotated[List[Any], add_messages]
    pr_reference: Dict[str, Any]
    pr_metadata: Dict[str, Any]
    files: List[Dict[str, Any]]
    comments: List[Dict[str, str]]
    review_context: str
    review: str
    supervised_review: str
    error: Optional[str]


def load_review_environment(env_path: Optional[str | Path] = None) -> bool:
    if env_path is not None:
        return load_dotenv(env_path, override=True)

    candidates = [Path.cwd() / ".env"]
    candidates.extend(parent / ".env" for parent in Path(__file__).resolve().parents)

    for candidate in candidates:
        if candidate.exists():
            return load_dotenv(candidate, override=True)

    return load_dotenv(override=True)


def default_repository() -> str:
    return os.getenv("GITHUB_REPOSITORY", "").strip()


def default_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def default_supervisor_model() -> str:
    return os.getenv("OPENAI_SUPERVISOR_MODEL", "gpt-5.4-mini")


def parse_pr_reference(
    user_input: str,
    default_repository_name: Optional[str] = None,
) -> Dict[str, Any]:
    repository_name = (default_repository_name or default_repository()).strip()
    text = user_input.strip()

    url_match = re.search(r"github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)", text)
    if url_match:
        owner, repo, number = url_match.groups()
        return {"owner": owner, "repo": repo, "number": int(number)}

    repo_match = re.search(
        r"\b([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:#|/pull/)(\d+)\b",
        text,
    )
    if repo_match:
        owner, repo, number = repo_match.groups()
        return {"owner": owner, "repo": repo, "number": int(number)}

    number_match = re.search(
        r"\b(?:pr|pull request|pull)(?:\s+(?:number|no\.?))?\s*(?:is|:)?\s*#?\s*(\d+)\b",
        text,
        re.IGNORECASE,
    )
    if number_match and repository_name:
        owner, repo = repository_name.split("/", 1)
        return {"owner": owner, "repo": repo, "number": int(number_match.group(1))}

    raise ValueError(
        "Please provide a PR URL, owner/repo#number, or set GITHUB_REPOSITORY "
        "and ask for PR 123."
    )


def get_github_repository(owner: str, repo: str):
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("Please set GITHUB_TOKEN to a GitHub Personal Access Token.")

    try:
        from github import Auth, Github
    except ImportError as exc:
        raise ImportError(
            "PyGithub is not installed. Please install it with `pip install PyGithub`."
        ) from exc

    github = Github(auth=Auth.Token(token))
    return github.get_repo(f"{owner}/{repo}")


def fetch_pull_request_metadata(repository, pr_number: int) -> Dict[str, Any]:
    pr = repository.get_pull(pr_number)
    return {
        "number": pr.number,
        "title": pr.title,
        "body": pr.body or "",
        "author": pr.user.login if pr.user else "unknown",
        "state": pr.state,
        "url": pr.html_url,
        "base": f"{pr.base.repo.full_name}:{pr.base.ref}",
        "head": f"{pr.head.repo.full_name if pr.head.repo else 'unknown'}:{pr.head.ref}",
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
        "additions": pr.additions,
        "deletions": pr.deletions,
        "changed_files": pr.changed_files,
        "commits": pr.commits,
    }


def list_pull_request_files(
    repository,
    pr_number: int,
    max_files: int = 80,
    max_patch_chars_per_file: int = 8_000,
    max_total_patch_chars: int = 60_000,
) -> List[Dict[str, Any]]:
    pr = repository.get_pull(pr_number)
    files = []
    total_patch_chars = 0

    for index, pr_file in enumerate(pr.get_files()):
        if index >= max_files:
            break

        patch = getattr(pr_file, "patch", None) or ""
        patch_truncated = False

        if len(patch) > max_patch_chars_per_file:
            patch = (
                patch[:max_patch_chars_per_file]
                + "\n...[patch truncated for this file]"
            )
            patch_truncated = True

        if total_patch_chars + len(patch) > max_total_patch_chars:
            patch = "[patch omitted because the review context limit was reached]"
            patch_truncated = True
        else:
            total_patch_chars += len(patch)

        files.append(
            {
                "filename": pr_file.filename,
                "status": pr_file.status,
                "additions": pr_file.additions,
                "deletions": pr_file.deletions,
                "changes": pr_file.changes,
                "patch": patch,
                "patch_truncated": patch_truncated,
            }
        )

    return files


def list_pull_request_comments(
    repository,
    pr_number: int,
    limit: int = 20,
) -> List[Dict[str, str]]:
    pr = repository.get_pull(pr_number)
    comments = []

    for comment in pr.get_issue_comments():
        comments.append(
            {
                "kind": "issue_comment",
                "author": comment.user.login if comment.user else "unknown",
                "body": comment.body or "",
            }
        )
        if len(comments) >= limit:
            return comments

    for comment in pr.get_review_comments():
        comments.append(
            {
                "kind": "review_comment",
                "author": comment.user.login if comment.user else "unknown",
                "path": comment.path,
                "body": comment.body or "",
            }
        )
        if len(comments) >= limit:
            break

    return comments


def format_pr_context(
    reference: Dict[str, Any],
    metadata: Dict[str, Any],
    files: List[Dict[str, Any]],
    comments: List[Dict[str, str]],
) -> str:
    file_summary = "\n".join(
        f"- {item['filename']} ({item['status']}, +{item['additions']}/-{item['deletions']})"
        for item in files
    )

    comment_summary = (
        "\n\n".join(
            f"[{item.get('kind', 'comment')}] {item.get('author', 'unknown')}"
            f"{(' on ' + item['path']) if item.get('path') else ''}:\n{item.get('body', '')}"
            for item in comments
        )
        or "No existing PR comments were loaded."
    )

    patches = []
    for item in files:
        patch = item.get("patch") or "[no textual patch available]"
        patches.append(
            f"### {item['filename']}\n"
            f"status: {item['status']}, +{item['additions']}/-{item['deletions']}\n"
            f"```diff\n{patch}\n```"
        )

    return textwrap.dedent(f"""
        Repository: {reference['owner']}/{reference['repo']}
        Pull request: #{metadata['number']}
        URL: {metadata['url']}
        Title: {metadata['title']}
        Author: {metadata['author']}
        State: {metadata['state']}
        Base: {metadata['base']}
        Head: {metadata['head']}
        Size: +{metadata['additions']}/-{metadata['deletions']} across {metadata['changed_files']} files and {metadata['commits']} commits

        PR body:
        {metadata['body'] or '(empty)'}

        Files changed:
        {file_summary or '(no changed files loaded)'}

        Existing comments:
        {comment_summary}

        Patches:
        {chr(10).join(patches)}
        """).strip()


def user_texts(messages: List[Any]) -> List[str]:
    texts = []
    for message in messages:
        if isinstance(message, HumanMessage):
            texts.append(message.content)
        elif isinstance(message, dict) and message.get("role") == "user":
            texts.append(message.get("content", ""))
    return texts


def resolve_pr_reference(state: PRReviewState) -> Dict[str, Any]:
    for text in reversed(user_texts(state["messages"])):
        try:
            return parse_pr_reference(text)
        except ValueError:
            continue

    if state.get("pr_reference"):
        return state["pr_reference"]

    raise ValueError(
        "Please mention the pull request in the chat, for example a PR URL, "
        "owner/repo#123, or PR 123 when GITHUB_REPOSITORY is set."
    )


def fetch_pr_context(state: PRReviewState) -> Dict[str, Any]:
    try:
        reference = resolve_pr_reference(state)
        repository = get_github_repository(reference["owner"], reference["repo"])
        metadata = fetch_pull_request_metadata(repository, reference["number"])
        files = list_pull_request_files(repository, reference["number"])
        comments = list_pull_request_comments(repository, reference["number"])
        context = format_pr_context(reference, metadata, files, comments)

        return {
            "pr_reference": reference,
            "pr_metadata": metadata,
            "files": files,
            "comments": comments,
            "review_context": context,
            "error": None,
        }
    except Exception as exc:
        message = f"Could not load pull request context: {exc}"
        return {
            "error": message,
            "review": message,
            "messages": [AIMessage(content=message)],
        }


def review_pull_request(
    state: PRReviewState, model: Optional[str] = None
) -> Dict[str, Any]:
    reviewer_llm = ChatOpenAI(model=model or default_model(), temperature=0)
    system_prompt = """
You are a senior engineer doing a GitHub pull request review.
Use only the PR metadata, comments, filenames, and patches provided by the graph.
Lead with findings, ordered by severity. Prefer concrete correctness, regression,
security, data-loss, and missing-test risks over style comments. Include file paths
and patch evidence when possible. If you find no blocking issues, say that clearly
and mention the main residual risks or test gaps.
""".strip()

    user_prompt = f"""
Review this pull request.

{state['review_context']}
""".strip()

    response = reviewer_llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return {"review": response.content, "messages": [response]}


def supervise_review(
    state: PRReviewState, model: Optional[str] = None
) -> Dict[str, Any]:
    supervisor_llm = ChatOpenAI(
        model=model or default_supervisor_model(), temperature=0
    )
    system_prompt = """
You are a senior pull request review supervisor.
Use only the provided PR metadata, comments, filenames, patches, and reviewer output.
Validate every concrete finding from the reviewer against the PR context.

Return the same review format as the reviewer output. Do not rewrite it into a
separate supervisor report. Preserve the original headings, finding order,
severity labels, paths, evidence, residual risks, and overall structure as much
as possible.

For each reviewer finding, add the supervisor decision as the first bullet point
inside that finding:
- <span style="color: #15803d; font-weight: 700;">Verified</span> if the PR
  context supports the finding.
- <span style="color: #dc2626; font-weight: 700;">False positive</span> if the
  PR context does not support the finding or the claim is speculative.

After the status bullet, keep the rest of the finding in the same style as the
reviewer output. Add only a brief validation note when it is needed to explain
why the status is Verified or False positive. If the reviewer found no issues,
preserve that no-issues summary and do not invent findings.

If a finding is marked False positive, remove any Recommendation bullet from
that finding. Add a bold validation note bullet instead, for example:
- **Validation note:** The PR context does not show ...
""".strip()

    user_prompt = f"""
PR context:

{state['review_context']}

Reviewer output:

{state.get('review', '')}
""".strip()

    response = supervisor_llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return {
        "supervised_review": response.content,
        "review": response.content,
        "messages": [response],
    }


def route_after_fetch(state: PRReviewState) -> str:
    return "finish" if state.get("error") else "review"


def build_review_graph(
    model: Optional[str] = None,
    use_supervisor: bool = False,
    supervisor_model: Optional[str] = None,
    env_path: Optional[str | Path] = None,
):
    load_review_environment(env_path)

    def review_node(state: PRReviewState) -> Dict[str, Any]:
        return review_pull_request(state, model=model)

    def supervisor_node(state: PRReviewState) -> Dict[str, Any]:
        return supervise_review(state, model=supervisor_model)

    graph_builder = StateGraph(PRReviewState)
    graph_builder.add_node("fetch_pr_context", fetch_pr_context)
    graph_builder.add_node("review_pull_request", review_node)
    if use_supervisor:
        graph_builder.add_node("supervise_review", supervisor_node)

    graph_builder.add_edge(START, "fetch_pr_context")
    graph_builder.add_conditional_edges(
        "fetch_pr_context",
        route_after_fetch,
        {"review": "review_pull_request", "finish": END},
    )
    if use_supervisor:
        graph_builder.add_edge("review_pull_request", "supervise_review")
        graph_builder.add_edge("supervise_review", END)
    else:
        graph_builder.add_edge("review_pull_request", END)

    return graph_builder.compile(checkpointer=MemorySaver())


def new_thread_config() -> Dict[str, Dict[str, str]]:
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def run_review_message(
    graph,
    message: str,
    thread_id: Optional[str] = None,
) -> str:
    config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
    result = graph.invoke({"messages": [HumanMessage(content=message)]}, config=config)
    return result.get("review") or result["messages"][-1].content
