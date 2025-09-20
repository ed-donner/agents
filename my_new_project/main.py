import os
import json
from dotenv import load_dotenv
import whisper
from flask import Flask, request, render_template_string, redirect, url_for
import tempfile
import socket
import sys

# Always remember to do this!
load_dotenv(override=True)

PORT = 5050

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if is_port_in_use(PORT):
    print(f"Port {PORT} is already in use. Please free it before running this app.")
    sys.exit(1)

# Example function to transcribe audio using whisper

def transcribe_audio(audio_path, model_name='base'):
    """
    Transcribe an audio file using OpenAI's Whisper.
    :param audio_path: Path to the audio file (wav, mp3, etc.)
    :param model_name: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
    :return: Transcribed text
    """
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)
    return result['text']

app = Flask(__name__)

UPLOAD_FORM = '''
<!doctype html>
<title>Whisper Transcription</title>
<h1>Upload an audio file for transcription</h1>
<button onclick="document.getElementById('troubleshoot').style.display = (document.getElementById('troubleshoot').style.display === 'none' ? 'block' : 'none');">Troubleshooting</button>
<div id="troubleshoot" style="display:none; margin: 1em 0; padding: 1em; border: 1px solid #ccc; background: #f9f9f9;">
  <b>Port 5050 is already in use?</b><br>
  If you see an error like:<br>
  <pre>Address already in use\nPort 5050 is in use by another program. Either identify and stop that program, or start the server with a different port.</pre>
  <b>To release the port:</b>
  <ol>
    <li>Find the process using port 5050:<br>
      <code>lsof -i :5050</code>
    </li>
    <li>Kill the process (replace <code>1234</code> with the PID from above):<br>
      <code>kill 1234</code><br>
      If it does not terminate, force kill:<br>
      <code>kill -9 1234</code>
    </li>
    <li>Restart your Flask app.</li>
  </ol>
  <b>Tip:</b> Always stop the Flask server with <code>CTRL+C</code> in the terminal to release the port cleanly.
</div>
<form method=post enctype=multipart/form-data>
  <input type=file name=audio_file>
  <input type=submit value=Upload>
</form>
{% if error %}
  <div style="color: red;"><b>Error:</b> {{ error }}</div>
{% endif %}
{% if transcript %}
  <h2>Transcription Result:</h2>
  <pre>{{ transcript }}</pre>
{% endif %}
'''

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    transcript = None
    error = None
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            error = "No file part in the request."
            return render_template_string(UPLOAD_FORM, transcript=transcript, error=error)
        file = request.files['audio_file']
        if file.filename == '':
            error = "No selected file."
            return render_template_string(UPLOAD_FORM, transcript=transcript, error=error)
        if file:
            try:
                ext = os.path.splitext(file.filename)[1] or '.wav'
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    file.save(tmp.name)
                    transcript = transcribe_audio(tmp.name)
            except Exception as e:
                error = f"Transcription failed: {e}"
                print(error)
    return render_template_string(UPLOAD_FORM, transcript=transcript, error=error)

if __name__ == '__main__':
    app.run(debug=True, port=5050) 