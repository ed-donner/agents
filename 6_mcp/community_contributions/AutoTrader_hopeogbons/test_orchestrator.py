"""
Test script to verify orchestrator implementation.

This script performs basic validation without running a full trading cycle.
"""

import asyncio
import sys


async def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    try:
        from orchestrator import OrchestratorAgent
        from traders import Trader
        from trading_floor import names, lastnames, model_names
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


async def test_orchestrator_creation():
    """Test that orchestrator can be created."""
    print("\nTesting orchestrator creation...")
    try:
        from orchestrator import OrchestratorAgent
        from trading_floor import names, lastnames, model_names
        
        trader_configs = list(zip(names, lastnames, model_names))
        orchestrator = OrchestratorAgent(trader_configs)
        
        print(f"✓ Orchestrator created with {len(trader_configs)} trader configs")
        return True
    except Exception as e:
        print(f"✗ Orchestrator creation failed: {e}")
        return False


async def test_trader_methods():
    """Test that Trader has the required methods."""
    print("\nTesting trader methods...")
    try:
        from traders import Trader
        
        trader = Trader("TestTrader", "Test", "gpt-4o-mini")
        
        # Check that required methods exist
        assert hasattr(trader, 'run_with_shared_servers'), "Missing run_with_shared_servers method"
        assert hasattr(trader, 'get_account_report'), "Missing get_account_report method"
        assert hasattr(trader, 'get_strategy'), "Missing get_strategy method"
        
        print("✓ All required trader methods exist")
        return True
    except Exception as e:
        print(f"✗ Trader method check failed: {e}")
        return False


async def test_method_signatures():
    """Test that methods have correct signatures."""
    print("\nTesting method signatures...")
    try:
        from traders import Trader
        import inspect
        
        trader = Trader("TestTrader", "Test", "gpt-4o-mini")
        
        # Check get_account_report signature
        sig = inspect.signature(trader.get_account_report)
        assert 'accounts_mcp_server' in sig.parameters, "get_account_report missing accounts_mcp_server parameter"
        
        # Check get_strategy signature
        sig = inspect.signature(trader.get_strategy)
        assert 'accounts_mcp_server' in sig.parameters, "get_strategy missing accounts_mcp_server parameter"
        
        # Check run_with_shared_servers signature
        sig = inspect.signature(trader.run_with_shared_servers)
        assert 'trader_mcp_servers' in sig.parameters, "run_with_shared_servers missing trader_mcp_servers parameter"
        assert 'researcher_mcp_servers' in sig.parameters, "run_with_shared_servers missing researcher_mcp_servers parameter"
        
        print("✓ All method signatures correct")
        return True
    except Exception as e:
        print(f"✗ Method signature check failed: {e}")
        return False


async def test_orchestrator_structure():
    """Test that orchestrator has required attributes and methods."""
    print("\nTesting orchestrator structure...")
    try:
        from orchestrator import OrchestratorAgent
        from trading_floor import names, lastnames, model_names
        
        trader_configs = list(zip(names, lastnames, model_names))
        orchestrator = OrchestratorAgent(trader_configs)
        
        # Check attributes
        assert hasattr(orchestrator, 'trader_configs'), "Missing trader_configs attribute"
        assert hasattr(orchestrator, 'traders'), "Missing traders attribute"
        assert hasattr(orchestrator, 'shared_trader_mcp_servers'), "Missing shared_trader_mcp_servers attribute"
        assert hasattr(orchestrator, 'researcher_mcp_servers_by_name'), "Missing researcher_mcp_servers_by_name attribute"
        
        # Check methods
        assert hasattr(orchestrator, 'run_trading_cycle'), "Missing run_trading_cycle method"
        assert hasattr(orchestrator, 'run_forever'), "Missing run_forever method"
        
        print("✓ Orchestrator structure correct")
        return True
    except Exception as e:
        print(f"✗ Orchestrator structure check failed: {e}")
        return False


async def run_all_tests():
    """Run all tests and report results."""
    print("="*60)
    print("ORCHESTRATOR IMPLEMENTATION TESTS")
    print("="*60)
    
    tests = [
        test_imports,
        test_orchestrator_creation,
        test_trader_methods,
        test_method_signatures,
        test_orchestrator_structure,
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Implementation is correct.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

