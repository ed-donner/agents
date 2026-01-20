#!/usr/bin/env bash
set -e

# Go to workspace root (where .env should live)
cd /workspaces/"${GITHUB_REPOSITORY##*/}" 2>/dev/null || cd /workspaces

echo "Regenerating .env from Codespaces secrets..."

# Overwrite .env each time
cat > .env <<EOF
# Auto-generated from Codespaces secrets. Do NOT commit this file.

OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
GOOGLE_API_KEY=${GOOGLE_API_KEY}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
GROQ_API_KEY=${GROQ_API_KEY}
EOF

echo ".env generated."