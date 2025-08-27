#!/usr/bin/env python3
"""
Test script for real AI integration
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

async def test_real_ai():
    """Test the real AI integration"""
    try:
        print("🚀 Testing Real AI Integration...")
        
        # Import and test the art studio
        from src.core.art_studio import ArtStudio
        
        print("✅ Art Studio imported successfully")
        
        # Create the studio (this will validate config and OpenAI API)
        studio = ArtStudio()
        print("✅ Art Studio initialized successfully")
        
        # Test real AI concept generation
        print("\n🎨 Testing Real AI Concept Generation...")
        result = await studio.execute_creative_process("create art for a crypto coin")
        
        print("\n📊 Result:")
        print(f"Primary Agent: {result['primary_agent']}")
        print(f"Total Iterations: {result['total_iterations']}")
        print(f"Final Output: {result['final_output'][:200]}...")
        
        print("\n✅ Real AI test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_ai())
    if success:
        print("\n🎉 All tests passed! Real AI is working!")
    else:
        print("\n💥 Tests failed. Check the error messages above.")
        sys.exit(1)
