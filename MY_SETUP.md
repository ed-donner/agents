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

## Updating the Course from Ed Donner

My Git setup has two remotes:

- `origin` = Ed Donner's official course repository
- `personal` = my private GitHub repository

My working branch is `course-updated`, which is backed up to
`personal/main`.

### Before updating

Always save my current work first:

    git status
    git add .
    git commit -m "Save work before course update"
    git push

If `git status` says `nothing to commit, working tree clean`,
there is no need to make another commit.

### Check for new course updates

Download information about Ed's latest changes without changing
my files:

    git fetch origin

Then check how far my working branch is behind Ed's course:

    git rev-list --left-right --count HEAD...origin/main

The two numbers show:

    first number  = commits I have that Ed does not
    second number = commits Ed has that I do not

### Bring in Ed's updates

While on my `course-updated` branch:

    git merge origin/main

If Git completes the merge without conflicts, the course has
been updated successfully.

Then back up the updated version to my private GitHub:

    git push

### If Git reports conflicts

DO NOT discard files or randomly choose "Accept Incoming" or
"Accept Current".

My work is committed, so it is safe.

Run:

    git status

Review which files have conflicts and resolve them individually.

Jupyter `.ipynb` notebooks can be particularly difficult to merge
because they are stored internally as JSON.

If the update becomes confusing, stop before making further changes
and investigate the conflict rather than deleting or overwriting files.

### Important

Do not use:

    git push origin

`origin` belongs to Ed Donner and is only used as the source of
official course updates.

My own work is pushed to:

    personal/main

A normal:

    git push

from `course-updated` pushes to my private `personal/main`.
