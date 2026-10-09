import requests
import os   
from dotenv import load_dotenv
load_dotenv()
env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}


url = "https://api.search.brave.com/res/v1/web/search"

params = {
    "q": "Live gigs by Uncle Acid and the Deadbeats in my area"
}

headers = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
    "X-Subscription-Token": env["BRAVE_API_KEY"]
}

response = requests.get(url, params=params, headers=headers, verify=False)
print(response.json())