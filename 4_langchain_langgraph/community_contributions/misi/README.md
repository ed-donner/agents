# GitHub PR Reviewer

This folder contains a LangGraph-based GitHub pull request reviewer with a
Gradio chat UI.

Files:

- `github_review.ipynb` starts the notebook UI, draws the normal and supervised
  graphs, and launches Gradio.
- `github_review_util.py` contains the GitHub loading logic, PR-reference
  parser, LangGraph state, review node, optional supervisor node, and helper
  functions.

## What It Does

The app reviews a GitHub pull request from chat. You can mention the PR as:

```text
Review PR 123
Review owner/repo#123
Review https://github.com/owner/repo/pull/123
```

If you only provide a PR number, `GITHUB_REPOSITORY` must be set to
`owner/repo`.

The graph loads:

- PR metadata
- changed files and patches
- issue comments
- review comments

Then the reviewer model produces a code-review style response focused on
correctness, regressions, security, data loss, and missing-test risks.

## Graph Workflows

Default workflow:

```text
START -> fetch_pr_context -> review_pull_request -> END
```

Supervised workflow:

```text
START -> fetch_pr_context -> review_pull_request -> supervise_review -> END
```

The Gradio UI has a visible `Use supervisor` checkbox under the title. When it
is unchecked, the app uses the default workflow. When it is checked, the app uses
the supervised workflow.

## Supervisor Mode

The supervisor uses a stronger model by default and validates each concrete
finding from the reviewer against the same PR context.

For each finding, the supervisor keeps the normal review format and adds the
first bullet inside the finding:

```html
<span style="color: #15803d; font-weight: 700;">Verified</span>
```

or:

```html
<span style="color: #dc2626; font-weight: 700;">False positive</span>
```

If a finding is marked `False positive`, the supervisor is instructed to remove
the `Recommendation` bullet and add a bold validation note instead:

```markdown
- **Validation note:** The PR context does not show ...
```

## Environment

The notebook calls `load_review_environment()`, which looks for `.env` in the
current working directory and then walks upward from this folder. You can also
set these variables in your shell.

Required OpenAI setting:

```sh
export OPENAI_API_KEY="your-openai-api-key"
```

Optional model settings:

```sh
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_SUPERVISOR_MODEL="gpt-5.4-mini"
```

GitHub settings:

```sh
export GITHUB_TOKEN="github_pat_or_classic_pat"
export GITHUB_REPOSITORY="owner/repo"
```

`GITHUB_REPOSITORY` is optional when the chat message includes a full URL or
`owner/repo#number`. It is required for short references like `PR 123`.

## GitHub PAT Setup

Create a GitHub Personal Access Token at:

```text
https://github.com/settings/tokens
```

For a fine-grained token, grant access to the repository you want to review and
use read-only permissions:

- Contents: Read-only
- Metadata: Read-only
- Pull requests: Read-only
- Issues: Read-only

For a classic token against a private repository, the `repo` scope is usually
enough.

After creating the token:

1. Set `GITHUB_TOKEN` to the token value.
2. Set `GITHUB_REPOSITORY` to `owner/repo` if you want to use short PR numbers.

Never commit `.env` files or tokens.

## Dependencies

The repo already declares the relevant packages in `pyproject.toml` and
`requirements.txt`, including:

- `gradio`
- `langgraph`
- `langchain-openai`
- `pygithub`
- `python-dotenv`

If dependencies need to be installed through `uv`, run from the repo root:

```sh
uv sync
```

## Running

Open and run:

```text
4_langgraph/community_contributions/misi/github_review.ipynb
```

The notebook:

1. imports `github_review_util.py`
2. loads environment variables
3. builds the normal review graph
4. builds the supervised review graph
5. displays graph diagrams
6. launches the Gradio chat UI

In the Gradio chat, type a PR reference in the conversation and ask for a review.
For example:

```text
The PR number is 123. Please review it.
```

or:

```text
Please review owner/repo#123 with the supervisor.
```

The checkbox controls whether the supervisor graph is used; the chat text is not
used to toggle supervisor mode.

## Implementation Notes

- `MemorySaver` is used as the LangGraph checkpointer.
- Each Gradio request uses a fresh thread config.
- The notebook sends the full visible chat history into the graph, so a PR
  reference mentioned earlier in the conversation can still be resolved.
- File patches are truncated per file and across the whole PR context to keep
  the prompt bounded.
- The reviewer and supervisor both use only the loaded PR context; they are not
  instructed to browse GitHub independently.
