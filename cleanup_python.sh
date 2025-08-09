#!/bin/bash

echo "==============================================="
echo " Python Cleanup Script for macOS"
echo " This will remove all non-system Python versions."
echo "==============================================="
sleep 2

# ------------------------------
# Step 1: Remove Homebrew Python
# ------------------------------
if command -v brew &>/dev/null; then
    echo "🔹 Checking Homebrew Python installations..."
    brew list | grep python@ | while read -r version; do
        echo "   ➤ Uninstalling $version"
        brew uninstall --ignore-dependencies "$version"
    done

    # Remove default python if installed
    if brew list | grep -q "^python\$"; then
        echo "   ➤ Uninstalling python"
        brew uninstall --ignore-dependencies python
    fi
else
    echo "⚠️ Homebrew not found, skipping..."
fi

# ------------------------------
# Step 2: Remove python.org pkg installation
# ------------------------------
echo "�� Removing /Library/Frameworks/Python.framework..."
sudo rm -rf /Library/Frameworks/Python.framework
sudo rm -rf /Applications/Python*

# Remove symlinks from /usr/local/bin
echo "🔹 Removing python symlinks from /usr/local/bin..."
sudo find /usr/local/bin -lname '*/Library/Frameworks/Python.framework/*' -delete

# ------------------------------
# Step 3: Remove Anaconda/Miniconda
# ------------------------------
if [ -d "$HOME/anaconda3" ]; then
    echo "🔹 Removing Anaconda..."
    rm -rf ~/anaconda3
fi

if [ -d "$HOME/miniconda3" ]; then
    echo "🔹 Removing Miniconda..."
    rm -rf ~/miniconda3
fi

# ------------------------------
# Step 4: Remove Pyenv and its versions
# ------------------------------
if [ -d "$HOME/.pyenv" ]; then
    echo "🔹 Removing Pyenv and its Python versions..."
    rm -rf ~/.pyenv
fi

# ------------------------------
# Step 5: Clean caches and pip leftovers
# ------------------------------
echo "🔹 Cleaning pip caches and local Python libraries..."
rm -rf ~/Library/Caches/pip
rm -rf ~/.cache/pip
rm -rf ~/.local

# ------------------------------
# Step 6: Remove other stray python binaries
# ------------------------------
echo "🔹 Removing stray Python binaries from /usr/local/bin..."
sudo rm -f /usr/local/bin/python*
sudo rm -f /usr/local/bin/pip*

# ------------------------------
# Step 7: Advise manual shell cleanup
# ------------------------------
echo "⚠️ Please check your ~/.zshrc or ~/.bash_profile and remove any old Python PATH entries manually."
echo "   Example: export PATH=\"/usr/local/opt/python@3.x/bin:\$PATH\""

# ------------------------------
# Done
# ------------------------------
echo "✅ Cleanup complete! Only system Python should remain."
echo "   You can now reinstall a fresh Python version via Homebrew or python.org."
