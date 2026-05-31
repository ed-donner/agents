import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

def test_pushover():
    """Test Pushover notification service"""
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    
    print("Testing Pushover Configuration...")
    print(f"PUSHOVER_TOKEN: {'✅ Found' if token else '❌ Missing'}")
    print(f"PUSHOVER_USER: {'✅ Found' if user else '❌ Missing'}")
    
    if not token or not user:
        print("\n❌ Missing credentials. Please add PUSHOVER_TOKEN and PUSHOVER_USER to your .env file")
        return
    
    # Test message
    test_message = "🔔 Test notification from digital twin app!"
    
    try:
        print(f"\n📤 Sending test message: '{test_message}'")
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "message": test_message,
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Check your phone/device for the Pushover notification")
        else:
            print(f"\n❌ FAILED! Status code: {response.status_code}")
            print(f"Error details: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network/Request Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_pushover()

