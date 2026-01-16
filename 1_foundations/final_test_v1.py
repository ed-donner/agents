import os
import anthropic

# This will tell us exactly where Python is looking
print(f"Loading anthropic from: {anthropic.__file__}")

try:
    from anthropic import Anthropic
    print("✅ Success! The Anthropic class was found.")
except ImportError as e:
    print(f"❌ Still failing: {e}")