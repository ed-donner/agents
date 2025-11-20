"""
Simple test to verify imports and basic setup work
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

print("🧪 Testing Code Learning Assistant - Simple Test")
print("=" * 50)

# Test 1: Check environment variables
print("\n1️⃣ Checking environment variables...")
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"   ✅ OPENAI_API_KEY found: {openai_key[:10]}...")
else:
    print("   ❌ OPENAI_API_KEY not found")

# Test 2: Import modules
print("\n2️⃣ Testing module imports...")
try:
    from tools import read_code_file, save_learning_doc, get_git_diff
    print("   ✅ tools.py imported successfully")
except Exception as e:
    print(f"   ❌ Error importing tools: {e}")

try:
    import specialist_agents
    print("   ✅ specialist_agents.py imported successfully")
    print(f"      - language_teacher: {specialist_agents.language_teacher.name}")
    print(f"      - code_explainer: {specialist_agents.code_explainer.name}")
    print(f"      - change_documenter: {specialist_agents.change_documenter.name}")
    print(f"      - git_diff_analyzer: {specialist_agents.git_diff_analyzer.name}")
except Exception as e:
    print(f"   ❌ Error importing specialist_agents: {e}")

# Test 3: Test read_code_file tool
print("\n3️⃣ Testing read_code_file tool...")
try:
    # Function tools need to be invoked through their on_invoke_tool method
    # For direct testing, we import the raw functions
    from tools import read_code_file as read_file_func
    # Access the underlying function
    if hasattr(read_file_func, 'on_invoke_tool'):
        # It's a FunctionTool, test that it exists
        print(f"   ✅ read_code_file tool registered")
        print(f"      - Name: {read_file_func.name}")
        print(f"      - Description: {read_file_func.description[:50]}...")
    else:
        # Test by calling directly
        result = read_file_func("test_simple.py")
        if result.get("status") == "error":
            print(f"   ❌ Error: {result.get('message')}")
        else:
            print(f"   ✅ File read successfully")
            print(f"      - Language: {result.get('language')}")
            print(f"      - Lines: {result.get('lines')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Test save_learning_doc tool  
print("\n4️⃣ Testing save_learning_doc tool...")
try:
    from tools import save_learning_doc as save_doc_func
    if hasattr(save_doc_func, 'on_invoke_tool'):
        print(f"   ✅ save_learning_doc tool registered")
        print(f"      - Name: {save_doc_func.name}")
        print(f"      - Description: {save_doc_func.description[:50]}...")
    else:
        test_content = "# Test Document\n\nThis is a test."
        result = save_doc_func(test_content, "test_doc.md")
        if result.get("status") == "success":
            print(f"   ✅ Document saved: {result.get('saved_to')}")
        else:
            print(f"   ❌ Error: {result.get('message')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("✅ Basic module tests complete!")
print("\nNote: Full agent testing requires working OpenAI API access.")

