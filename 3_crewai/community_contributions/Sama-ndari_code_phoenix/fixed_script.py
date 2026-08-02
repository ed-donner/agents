import requests

def fetch_data():
    # Use a valid URL instead of a placeholder
    url = "https://jsonplaceholder.typicode.com/posts"  # Use a valid URL for testing
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed with status code " + str(response.status_code)}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print(fetch_data())