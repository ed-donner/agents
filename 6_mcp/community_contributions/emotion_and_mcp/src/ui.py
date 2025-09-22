import gradio as gr
import requests
import json
import os
import sys
import time
import urllib.parse
import threading
from queue import Queue, Empty

# Get the base URLs from the environment, with a default fallback
MCP_BASE = os.getenv("SG_BASE", "http://127.0.0.1:8000")
DIRECT_API_BASE = os.getenv("DIRECT_API_BASE", "http://127.0.0.1:5001")

# Shared state for communication between threads
q = Queue()
session_id_event = threading.Event()
session_id_container = {}
sse_thread = None

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
        
        # Retry a few times if the gateway returns a a 503
        for i in range(retries):
            time.sleep(delay_seconds * (i + 1)) # Exponential backoff
            r = requests.post(endpoint, json=body, timeout=30)
            if r.status_code != 503:
                return r.status_code, r.text
    except Exception as e:
        return 0, str(e)
    
    return 503, "All retries failed to get a non-503 or 202 response."

def sse_reader(base_url):
    """Continuously reads from the SSE stream in a separate thread, with auto-reconnect."""
    while True:
        sse_url = f"{base_url}/sse"
        response = None
        try:
            # Clear previous session ID and event on reconnect
            if session_id_event.is_set():
                session_id_event.clear()
                session_id_container.clear()
                print("\nReconnecting to SSE stream...")

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
            print("Attempting to reconnect in 5 seconds...")
            time.sleep(5)
        finally:
            if response:
                response.close()

def _call_direct_api(text: str) -> tuple[int, str]:
    """Sends a request to the direct API endpoint."""
    direct_api_url = f"{DIRECT_API_BASE}/predict"
    payload = {
        "text": text
    }
    
    try:
        r = requests.post(direct_api_url, json=payload, timeout=30)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)

def process_message(input_text, api_choice):
    """
    Main function for the Gradio UI. It handles the message submission,
    sends the POST request, and waits for a result.
    """
    if api_choice == "Direct API":
        yield "Calling Direct API..."
        status_code, response_text = _call_direct_api(input_text)
        if status_code == 200:
            try:
                response_data = json.loads(response_text)
                prediction = response_data.get("prediction")
                emoji = response_data.get("emoji")
                confidence = response_data.get("confidence")
                
                if prediction and confidence:
                    formatted_result = f"Prediction: {prediction} {emoji} (Confidence: {confidence:.2%})"
                    yield f"Direct API Response:\n{formatted_result}"
                else:
                    yield f"Direct API Response: {response_text}"
            except json.JSONDecodeError:
                yield f"ERROR: Direct API response was not valid JSON: {response_text}"
        else:
            yield f"ERROR: Direct API call failed. Status: {status_code}. Response: {response_text}"
        return
    
    elif api_choice == "Supergateway (MCP)":
        # Wait for the session ID to be set by the background thread
        yield "Waiting for SSE connection to be established..."
        if not session_id_event.wait(timeout=10):
            yield "ERROR: Failed to establish SSE connection within 10 seconds. Please refresh the page and try again."
            return

        session_id = session_id_container.get('id')
        if not session_id:
            yield "ERROR: Session ID was not captured. Please restart the application."
            return

        # Send the 'tools/call' request with retry logic.
        message_url = f"{MCP_BASE}/message?sessionId={urllib.parse.quote_plus(session_id)}"
        print(f"3. Sending 'tools/call' request to {message_url}...")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "emotion_detection",
                "arguments": {"text": input_text},
            },
        }
        
        post_response_code, post_response_text = _post_with_retry(message_url, payload)
        
        if post_response_code != 200:
            yield f"ERROR: POST request failed. Status: {post_response_code}. Response: {post_response_text}"
            return
        
        yield "Request sent. Waiting for response..."
        
        # Wait for the result from the reader thread's queue.
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
                            yield f"RECEIVED RESULT: {final_result}"
                            return
            except (Empty, json.JSONDecodeError, KeyError, IndexError):
                continue
        
        yield "TIMEOUT: Waited too long for the result."

# Function to start the background thread on Gradio load
def start_sse_thread():
    global sse_thread
    if sse_thread is None or not sse_thread.is_alive():
        print("Starting background SSE reader thread...")
        sse_thread = threading.Thread(target=sse_reader, args=(MCP_BASE,), daemon=True)
        sse_thread.start()

# Gradio UI components
with gr.Blocks(title="MCP Emotion Detector") as demo:
    gr.Markdown("# MCP Emotion Detector")
    gr.Markdown("Select your API endpoint and enter a message to send to the Supergateway.")
    
    with gr.Row():
        api_choice = gr.Radio(choices=["Supergateway (MCP)", "Direct API"], label="API Endpoint", value="Supergateway (MCP)")
    
    with gr.Row():
        message_input = gr.Textbox(
            label="Message to Analyze"
        )
        output_textbox = gr.Textbox(label="Result", interactive=False)
    
    # Add a separate gr.Examples component
    gr.Examples(
        examples=[
            "I am so happy with this test!",
            "I feel quite neutral about this.",
            "I am getting angry with this failure.",
            "I am filled with sadness.",
            "This news has made me feel love.",
            "I am so angry right now.",
            "I am scared of the dark."
        ],
        inputs=message_input,
        label="Try these examples"
    )

    with gr.Row():
        submit_btn = gr.Button("Submit", variant="primary")

    submit_btn.click(
        fn=process_message,
        inputs=[message_input, api_choice],
        outputs=output_textbox
    )
    
    # Start the SSE thread when the Gradio app is loaded in the browser
    demo.load(fn=start_sse_thread)

if __name__ == "__main__":
    demo.launch()

