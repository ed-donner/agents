# 📋 Community Contribution Workflow

This documents how to submit a PR to the course repository (`ed-donner/agents`).

## Prerequisites

- Your fork: `gkeskar/agents` (remote: `my-fork`)
- Course repo: `ed-donner/agents` (remote: `origin`)
- Personal git user configured

## Step-by-Step Workflow

### 1. Make Your Changes

```bash
cd /Users/gkeskar/projects/agents
# Create/edit files in community_contributions folder
```

### 2. Verify Git User (Personal Account)

```bash
git config user.name
# Should show: gkeskar

git config user.email  
# Should show: gandhali2001@yahoo.com
```

If not, set it:
```bash
git config user.name "gkeskar"
git config user.email "gandhali2001@yahoo.com"
```

### 3. Stage and Commit

```bash
# Stage your files
git add 6_mcp/community_contributions/shopping_list_mcp/

# Commit with descriptive message
git commit -m "Add Shopping List MCP Server with LLM integration

Features:
- Add/remove items with quantities and prices
- Budget tracking with visual warnings
- GPT-powered conversational assistant

Author: Gandhali Keskar"
```

### 4. Create Feature Branch

```bash
# Create and switch to feature branch
git branch shopping-list-mcp
git checkout shopping-list-mcp

# Or in one command:
git checkout -b shopping-list-mcp
```

### 5. Push to Your Fork

```bash
git push my-fork shopping-list-mcp
```

### 6. Create Pull Request

Visit the link shown in terminal, or:

1. Go to: https://github.com/gkeskar/agents
2. Click "Compare & pull request" button
3. Or: "Pull requests" → "New pull request"

**PR Settings:**
- Base repository: `ed-donner/agents`
- Base branch: `main`
- Head repository: `gkeskar/agents`
- Compare branch: `shopping-list-mcp`

### 7. Fill PR Description

Include:
- What the project does
- Files added
- Key features
- Your name

### 8. Submit and Wait for Review

The course instructor will review and merge!

---

## Quick Reference Commands

```bash
# Full workflow in one go:
cd /Users/gkeskar/projects/agents

# 1. Stage
git add 6_mcp/community_contributions/YOUR_PROJECT/

# 2. Commit
git commit -m "Add YOUR_PROJECT - brief description"

# 3. Create branch
git checkout -b your-project-name

# 4. Push
git push my-fork your-project-name

# 5. Create PR via GitHub web interface
```

---

## Remotes Reference

| Remote | URL | Purpose |
|--------|-----|---------|
| `origin` | `ed-donner/agents` | Course repo (PR target) |
| `my-fork` | `gkeskar/agents` | Your fork (push here) |
| `my-repo` | `gkeskar/gen-ai` | Personal portfolio |

---

## Checklist Before PR

- [ ] Files in correct `community_contributions` folder
- [ ] README.md included
- [ ] No `.env` or secrets committed
- [ ] No `__pycache__` or `.venv` folders
- [ ] Commit uses personal git user
- [ ] Feature branch created
- [ ] Pushed to `my-fork`
- [ ] PR created with good description

---

**Example PRs:**
- Protein Food Finder: https://github.com/ed-donner/agents/pull/458

