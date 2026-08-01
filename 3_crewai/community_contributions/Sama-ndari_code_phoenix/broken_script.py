# broken_script.py
import requests

def fetch_data():
    # ERROR 1: The URL is fake and will timeout/fail
    url = "https://this-api-does-not-exist.com/api/v1/data"
    
    # ERROR 2: Typo in variable name 'respone' instead of 'response'
    response = requests.get(url)
    
    # ERROR 3: Logic error (status code check)
    if respone.status_code == 200:
        return respone.json()
    else:
        return {"error": "Failed"}

if __name__ == "__main__":
    print(fetch_data())