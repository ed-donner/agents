"""
A voice-activated assistant that interacts with Zoho Books and Dataverse using OpenAI's GPT-5 model.
It records audio input, transcribes it, determines the user's intent, fetches data from the relevant API, and responds with synthesized speech.
Author: Dinesh Uthayakumar
Date: 2024-10-15
Website: https://duitconsulting.com/
"""
import os
import requests
import sounddevice as sd
import whisper
from scipy.io.wavfile import write
from openai import OpenAI
from gtts import gTTS
import tempfile
import subprocess
import warnings
import json
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")


# === CONFIG ===
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

ZOHO_AUTH_TOKEN = os.getenv("ZOHO_AUTH_TOKEN")
ZOHO_ORG_ID = os.getenv("ZOHO_ORG_ID")

DATAVERSE_ENV = os.getenv("DATAVERSE_ENV_URL")
DATAVERSE_TOKEN = os.getenv("DATAVERSE_BEARER_TOKEN")

DURATION = 6  # seconds of voice input
FS = 44100

client = OpenAI(api_key=OPENAI_KEY)

# === FUNCTIONS ===

def record_audio(filename="command.wav"):
    print("🎙️ Listening for command...")
    audio = sd.rec(int(DURATION * FS), samplerate=FS, channels=1)
    sd.wait()
    write(filename, FS, audio)
    print("✅ Recording complete.")
    return filename


def transcribe_audio(filename):
    print("🗣️ Transcribing...")
    print(filename)

    model = whisper.load_model("base")
    try:
        result = model.transcribe(filename, language="en")
    except Exception as e:
        print("❌ Transcription error:", e)
    print("✅ You said:", result["text"])
    return result["text"].strip()

# The below version bypasses ffmpeg call and directly loads the audio file.
def transcribe_audio2(filename):
    model = whisper.load_model("base")

    # Directly load audio (bypasses ffmpeg call)
    audio = whisper.load_audio(os.path.abspath(filename))
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    options = whisper.DecodingOptions(language="en")
    result = whisper.decode(model, mel, options)

    print("✅ Transcription complete.")
    return result.text


def get_intent(text):
    print("🤖 Understanding command...")
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are a data assistant that decides which API to call."},
            {"role": "user", "content": f"The user said: '{text}'. Decide whether to fetch Zoho Books outstanding invoice total or Dataverse open opportunities revenue. Reply in JSON with 'source' and 'purpose'."}
        ]
    )
    print("✅ Intent identified.")
    return response.choices[0].message.content

def get_llm_response(text):
    print("🤖 Thinking...")
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": text}
        ]
    )
    print("✅ Intent identified.")
    return response.choices[0].message.content


def get_zoho_outstanding():
    print("📊 Fetching outstanding invoices from Zoho Books...")
    url = f"https://www.zohoapis.com/books/v3/invoices?organization_id={ZOHO_ORG_ID}&status=overdue"
    headers = {"content-type":"application/x-www-form-urlencoded;charset=UTF-8", "Authorization": f"Zoho-oauthtoken {ZOHO_AUTH_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    total_due = sum(float(inv.get("balance", 0)) for inv in data.get("invoices", []))
    return f"Total outstanding invoice amount in Zoho Books is ₹{total_due:,.2f}"


def get_dataverse_open_opportunities():
    print("💼 Fetching open opportunities from Dataverse...")
    url = f"{DATAVERSE_ENV}/api/data/v9.2/opportunities?$select=name,estimatedvalue,statecode&$filter=statecode eq 0"
    headers = {
        "Authorization": f"Bearer {DATAVERSE_TOKEN}"
    }
    r = requests.get(url, params = None, headers=headers)
    r.raise_for_status()
    data = r.json()
    total_revenue = sum(op.get("estimatedvalue", {}) for op in data.get("value", []))
    return f"Total estimated revenue from open opportunities is ₹{total_revenue:,.2f}"


def speak2(text):
    print("🗣️ Speaking result...")
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
        tts.save(fp.name)
        subprocess.run(["start", fp.name], shell=True)

def speak(text):
    print("🗣️ Speaking result...")
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        os.startfile(fp.name)

def main():
    try:
        file = record_audio()

        #For Evaluation, comment the above line and uncomment one of the below lines
        #file = "eval1_capital.wav"  # For testing with a pre-recorded file
        #file = "eval2_money_customers_owe.wav"  # For testing with a pre-recorded file
        #file = "eval3_total_estimated_revenue.wav"  # For testing with a pre-recorded file
        
        #check if a file exists
        if not os.path.exists(file):
            raise FileNotFoundError(f"Audio file '{file}' not found.")
        command = transcribe_audio(file)
        intent_str = get_intent(command)
        intent = json.loads(intent_str)

        print("Intent Output:", intent)

        intent_source = intent["source"].strip().lower()
        internt_purpose = intent["purpose"].strip().lower()

        if "zoho" in intent_source or "invoice" in intent_source:
            result = get_zoho_outstanding()
        elif "dataverse" in intent_source or "opportunity" in intent_source:
            result = get_dataverse_open_opportunities()
        else:
            result = get_llm_response(command)

        print("\n💬", result)
        speak(result)

    except Exception as e:
        print("❌ Error:", e)


if __name__ == "__main__":
    main()