import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.data_loader import load_all_documents
from helpers.notification import PushoverNotifier
from helpers.config import get_config


def test_data_loader():
    print("\n" + "="*60)
    print("TEST: Data Loader")
    print("="*60)
    
    try:
        documents = load_all_documents("me")
        assert isinstance(documents, dict), "Documents should be a dictionary"
        assert len(documents) > 0, "Should load at least one document"
        
        for name, content in documents.items():
            assert isinstance(content, str), f"{name} should be a string"
            assert len(content) > 0, f"{name} should not be empty"
            print(f"✓ Loaded {name}: {len(content)} characters")
        
        print("✅ Data loader test PASSED")
        return True
    except Exception as e:
        print(f"❌ Data loader test FAILED: {e}")
        return False


def test_pushover_notifier():
    print("\n" + "="*60)
    print("TEST: Pushover Notifier")
    print("="*60)
    
    try:
        notifier = PushoverNotifier("test_user", "test_token")
        assert hasattr(notifier, 'send'), "Notifier should have send method"
        assert notifier.enabled == True, "Notifier should be enabled with credentials"
        
        notifier_disabled = PushoverNotifier("", "")
        assert notifier_disabled.enabled == False, "Notifier should be disabled without credentials"
        result = notifier_disabled.send("Test message")
        assert result == False, "Should return False when disabled"
        
        print("✓ Notifier initialization works")
        print("✓ Notifier handles missing credentials")
        print("✅ Pushover notifier test PASSED")
        return True
    except Exception as e:
        print(f"❌ Pushover notifier test FAILED: {e}")
        return False


def test_config():
    print("\n" + "="*60)
    print("TEST: Configuration")
    print("="*60)
    
    try:
        config = get_config()
        assert isinstance(config, dict), "Config should be a dictionary"
        
        required_keys = ["openai_api_key", "pushover_user", "pushover_token", "name", "rag_enabled", "rag_method", "top_k"]
        for key in required_keys:
            assert key in config, f"Config should contain '{key}'"
        
        assert config["openai_api_key"] is not None, "OpenAI API key should be set"
        assert isinstance(config["rag_enabled"], bool), "rag_enabled should be boolean"
        assert isinstance(config["top_k"], int), "top_k should be integer"
        
        print(f"✓ Config loaded with {len(config)} keys")
        print(f"✓ RAG enabled: {config['rag_enabled']}")
        print(f"✓ RAG method: {config['rag_method']}")
        print("✅ Configuration test PASSED")
        return True
    except Exception as e:
        print(f"❌ Configuration test FAILED: {e}")
        return False


def run_all_tests():
    print("\n" + "="*70)
    print("RUNNING HELPER TESTS")
    print("="*70)
    
    tests = [
        test_data_loader,
        test_pushover_notifier,
        test_config
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "="*70)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("="*70)
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

