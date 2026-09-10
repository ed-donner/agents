# My Course Setup

## Repository Structure

This is my working copy of Ed Donner's AI Agents course.

### Git remotes

- `origin` → Ed Donner's course repository
  - Used to receive course updates.
  - Do not push personal work here.

- `personal` → My private GitHub repository (`Oceanslave/agents`)
  - Used to back up my course work and personal modifications.

### Branches

- `course-updated` → My current working branch.
- `max-backup-before-update` → Backup of my earlier course work before the repository update.

My local `course-updated` branch tracks `personal/main`.

## Saving My Work

After completing meaningful work:

    git add .
    git commit -m "Description of what I changed"
    git push

This saves the changes locally in Git and uploads them to my private
GitHub repository.

## Getting Course Updates

Do not blindly use `git pull`, because my working branch tracks
`personal/main`.

Course updates come from:

    origin/main

Before integrating major upstream changes, commit my currentrst.

## Secrets and API Keys

API keys are stored locally in:

    .env

`.env` and `.env.*` are excluded by `.gitignore`.

Never commit API keys, passwords, tokens, or other credentials.

To verify that `.env` is ignored:

    git status --ignored -s .env

Expected result:

    !! .env

## Current Git Identity

Name: Max Hartvigsen
Email: max@bork.net
GitHub: Oceanslave
