"""
Simple test script to verify the modules work correctly before adding UI
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

def find_env_file():
    """Search upward for .env file starting from current file location"""
    current_path = Path(__file__).resolve().parent
    
    for _ in range(10):
        env_path = current_path / ".env"
        if env_path.exists():
            return env_path
        
        parent = current_path.parent
        if parent == current_path:
            break
        current_path = parent
    
    return None

# Load environment variables from project root
env_path = find_env_file()
if env_path:
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✓ Loaded .env from: {env_path}")
else:
    print("⚠️  No .env file found, using system environment variables")
    load_dotenv()

# Set OpenAI configuration - get from environment
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

os.environ['OPENAI_API_KEY'] = openai_api_key

# Use OPENAI_BASE_URL from env or default to standard OpenAI
base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
os.environ['OPENAI_BASE_URL'] = base_url

print(f"✓ Loaded OpenAI API Key: {openai_api_key[:10]}...")
print(f"✓ Using Gateway: {base_url}\n")

from learning_manager import LearningManager


async def test_basic_analysis():
    """Test analyzing a simple Python file"""
    manager = LearningManager()
    
    # Test with this very file
    file_path = "test_modules.py"
    
    print("🧪 Testing Code Learning Assistant Modules")
    print("=" * 50)
    print(f"Analyzing file: {file_path}\n")
    
    final_result = None
    async for status in manager.analyze_code(
        file_path=file_path,
        task_description="Testing the code learning assistant system",
        include_git_diff=False
    ):
        print(f"📝 {status}")
        # The last item will be the final result
        final_result = status
    
    return final_result


if __name__ == "__main__":
    print("Starting module test...\n")
    result = asyncio.run(test_basic_analysis())
    print("\n✅ Module test complete!")

