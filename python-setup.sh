#!/bin/bash

echo "🔍 Checking for Homebrew..."
if ! command -v brew &>/dev/null; then
  echo "🍺 Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "✅ Homebrew is already installed."
fi

echo "🔄 Updating Homebrew..."
brew update

echo "🐍 Installing Python 3.11 via Homebrew..."
brew install python@3.11

echo "🔗 Linking Python 3.11..."
brew link --overwrite python@3.11

echo "🔧 Installing uv (ultraviolet Python package manager)..."
brew install uv

echo "📁 Creating a new virtual environment with Python 3.11..."
python3.11 -m venv .venv

echo "🎛️ Activating the virtual environment..."
source .venv/bin/activate

echo "📦 Installing certifi and requests to fix SSL issues..."
pip install --upgrade pip
pip install certifi requests

echo "🔐 Configuring SSL cert environment variables..."
export SSL_CERT_FILE=$(python -m certifi)
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"

echo "🛠️ Backing up existing .zshrc to .zshrc.backup..."
cp ~/.zshrc ~/.zshrc.backup 2>/dev/null

echo "🧹 Writing clean .zshrc setup..."
cat <<'EOF' > ~/.zshrc
# Basic shell setup
autoload -Uz colors && colors
setopt autocd
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000

# Path setup
export PATH="$HOME/.local/bin:$PATH"
if [ -d "/opt/homebrew/bin" ]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi
if [ -d "/opt/homebrew/opt/python@3.11/bin" ]; then
  export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"
fi
if [ -d "$HOME/.cargo/bin" ]; then
  export PATH="$HOME/.cargo/bin:$PATH"
fi

# Python aliases
alias python='python3.11'
alias pip='python3.11 -m pip'

# SSL cert fix
export SSL_CERT_FILE=$(python3.11 -m certifi)
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"

# Venv activation helper
activate_venv() {
  if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated."
  else
    echo "⚠️ No .venv found."
  fi
}

# Prompt
PROMPT='%F{cyan}%n@%m%f:%F{green}%~%f %# '
EOF

echo "✅ Done! Please run: source ~/.zshrc"
