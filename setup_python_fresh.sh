#!/bin/bash

echo "==============================================="
echo " Fresh Python 3.11 Installation Script for macOS"
echo " (Auto-detects shell: Zsh or Bash)"
echo "==============================================="
sleep 2

# ------------------------------
# Step 1: Detect shell and config file
# ------------------------------
if [[ "$SHELL" == */zsh ]]; then
    SHELL_NAME="zsh"
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    SHELL_NAME="bash"
    SHELL_RC="$HOME/.bash_profile"
else
    SHELL_NAME="bash"
    SHELL_RC="$HOME/.bash_profile"
fi

echo "🔹 Detected shell: $SHELL_NAME"
echo "🔹 Configuration file: $SHELL_RC"

# ------------------------------
# Step 2: Ensure Homebrew is installed
# ------------------------------
if ! command -v brew &>/dev/null; then
    echo "⚠️ Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo "✅ Homebrew installed successfully."
fi

# ------------------------------
# Step 3: Update Homebrew
# ------------------------------
echo "🔹 Updating Homebrew..."
brew update

# ------------------------------
# Step 4: Install Python 3.11
# ------------------------------
if brew list | grep -q "^python@3.11\$"; then
    echo "✅ Python 3.11 is already installed via Homebrew."
else
    echo "🔹 Installing Python 3.11..."
    brew install python@3.11
fi

# ------------------------------
# Step 5: Link Python 3.11 as default
# ------------------------------
echo "🔹 Linking Python 3.11 as the default version..."
brew link python@3.11 --overwrite --force

# ------------------------------
# Step 6: Update shell configuration
# ------------------------------
echo "🔹 Updating $SHELL_RC..."

# Backup existing configuration
cp "$SHELL_RC" "$SHELL_RC.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null

# Remove old Python paths
sed -i '' '/python@/d' "$SHELL_RC" 2>/dev/null
sed -i '' '/export PATH=.*python/d' "$SHELL_RC" 2>/dev/null

# Add clean Python 3.11 setup
{
    echo ""
    echo "# >>> Python 3.11 environment setup >>>"
    echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"'
    echo 'alias python="python3"'
    echo 'alias pip="pip3"'
    echo "# <<< Python 3.11 environment setup <<<"
} >> "$SHELL_RC"

# ------------------------------
# Step 7: Reload configuration safely
# ------------------------------
echo "🔹 Reloading your shell configuration..."
source "$SHELL_RC"

# ------------------------------
# Step 8: Upgrade pip and tools
# ------------------------------
echo "🔹 Upgrading pip, setuptools, and virtualenv..."
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip setuptools wheel virtualenv

# ------------------------------
# Done
# ------------------------------
echo "✅ Python 3.11 setup is complete!"
echo "   Please restart your terminal if you still see old Python versions."
echo "   Verify with: python3 --version"
python3 --version
