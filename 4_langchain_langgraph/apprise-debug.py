import apprise
from dotenv import load_dotenv
import os

load_dotenv(override=True)
# Replace with your exact URL
url = os.getenv("NTFY_URL")

print(f"Testing URL: {url}")

ap = apprise.Apprise()
if ap.add(url):
    print("✅ URL parsed successfully!")
    # Try sending
    if ap.notify(body="Test", title="Test"):
        print("✅ Notification sent!")
    else:
        print("❌ Notification failed (Network/Auth issue)")
else:
    print("❌ URL format invalid.")
    
    # Debug: Try to see if the scheme is recognized
    print(f"Supported schemes: {ap.details()}")