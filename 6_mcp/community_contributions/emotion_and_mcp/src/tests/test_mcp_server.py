import requests
import json
import os
import sys
import time
import urllib.parse
import threading
from queue import Queue, Empty

def _post_with_retry(endpoint: str, body: dict, retries: int = 3, delay_seconds: float = 0.5) -> tuple[int, str]:
    """
    Sends a POST request with retry logic. Handles '202 Accepted' as a success and retries 
    on intermittent network issues (e.g., 503).
    """
    try:
        r = requests.post(endpoint, json=body, timeout=30)
        # 202 Accepted is the expected response for an async call.
        if r.status_code == 202:
            return 200, "Request Accepted" # Treat as a success for our script
        
        if r.status_code != 503:
            return r.status_code, r.text
        
        # Retry a few times if the gateway returns a 503
        for i in range(retries):
            time.sleep(delay_seconds * (i + 1)) # Exponential backoff
            r = requests.post(endpoint, json=body, timeout=30)
            if r.status_code != 503:
                return r.status_code, r.text
    except Exception as e:
        return 0, str(e)
    
    return 503, "All retries failed to get a non-503 or 202 response."

def test_mcp_connection(message: str):
    """
    A simple, procedural test to communicate with the MCP server.
    This script opens an SSE stream, gets a session ID, sends a tool call,
    and then waits for the result on the same stream.
    """
    print("--- Starting MCP Connection Test ---")

    # Get the base URL from the environment, with a default fallback
    mcp_base = os.getenv("SG_BASE", "http://127.0.0.1:8000")
    print(f"Using Supergateway base URL: {mcp_base}")

    # Shared state for communication between threads
    q = Queue()
    session_id_event = threading.Event()
    session_id_container = {}

    def sse_reader(base_url):
        """Continuously reads from the SSE stream in a separate thread."""
        sse_url = f"{base_url}/sse"
        response = None
        try:
            print("1. Connecting to SSE stream...")
            response = requests.get(
                sse_url,
                stream=True,
                timeout=(5, 60),
                headers={"Accept": "text/event-stream"},
            )
            response.raise_for_status()
            print("   - Connection successful.")

            for line in response.iter_lines(decode_unicode=True):
                if line and line.strip().startswith("data: "):
                    payload = line.strip()[len("data: "):]
                    
                    # First, check if we need to extract the session ID
                    if not session_id_event.is_set():
                        if "/message?sessionId=" in payload:
                            try:
                                parsed_url = urllib.parse.urlparse(payload)
                                query_params = urllib.parse.parse_qs(parsed_url.query)
                                if "sessionId" in query_params:
                                    session_id_container['id'] = query_params["sessionId"][0]
                                    session_id_event.set()
                                    print(f"2. Found session ID: {session_id_container['id']}")
                            except (ValueError, IndexError):
                                continue
                    
                    # Once the session is active, put all events in the queue
                    q.put(payload)
        except Exception as e:
            print(f"Reader thread encountered an error: {e}", file=sys.stderr)
        finally:
            if response:
                response.close()

    try:
        # Step 1: Start the background reader thread and let it manage the stream.
        print("   - Starting background reader thread...")
        threading.Thread(target=sse_reader, args=(mcp_base,), daemon=True).start()

        # Step 2: Wait for the session ID to be found and signaled by the reader thread.
        if not session_id_event.wait(timeout=5):
            print("ERROR: Reader thread failed to obtain session ID within timeout.", file=sys.stderr)
            return
        
        session_id = session_id_container.get('id')
        if not session_id:
            print("ERROR: Session ID was not captured.", file=sys.stderr)
            return

        # Step 3: Send the 'tools/call' request with retry logic.
        message_url = f"{mcp_base}/message?sessionId={urllib.parse.quote_plus(session_id)}"
        print(f"3. Sending 'tools/call' request to {message_url}...")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "emotion_detection",
                "arguments": {"text": message},
            },
        }
        
        post_response_code, post_response_text = _post_with_retry(message_url, payload)
        
        print(f"   - POST request status: {post_response_code}")
        if post_response_code != 200:
            print(f"ERROR: POST request failed. Response: {post_response_text}")
            return
        
        # Step 4: Wait for the result from the reader thread's queue.
        print("4. Waiting for tool result on SSE stream...")
        deadline = time.time() + 60  # Set a timeout for waiting
        while time.time() < deadline:
            try:
                payload = q.get(timeout=0.5)
                event_data = json.loads(payload)
                
                if event_data.get("id") == 1 and event_data.get("result"):
                    result = event_data["result"]
                    if isinstance(result, dict) and result.get("content"):
                        content = result["content"][0]
                        if content.get("text"):
                            final_result = content["text"]
                            print(f"5. RECEIVED RESULT: {final_result}")
                            return
            except (Empty, json.JSONDecodeError, KeyError, IndexError):
                continue
        
        print("TIMEOUT: Waited too long for the result.")
    
    except requests.exceptions.RequestException as e:
        print(f"FATAL ERROR: A network error occurred: {e}")
    except Exception as e:
        print(f"FATAL ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_message = sys.argv[1]
    else:
        input_message = "I am so happy with this test!"
    
    test_mcp_connection(input_message)