"""Audio Generator Agent - Converts text to speech using MiniMax TTS."""

import os
import aiohttp
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import uuid

from .base import Agent, function_tool


@function_tool
async def synthesize_speech(
    text: str, 
    # voice_id: str = "Chinese (Mandarin)_Warm_Bestie",
    voice_id: str = "Chinese (Mandarin)_News_Anchor",
    speed: float = 0.95,
    pitch: int = -1
) -> str:
    """Synthesize speech from text using MiniMax TTS.
    
    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        speed: Speech speed (0.5-2.0)
        pitch: Pitch adjustment (-20 to 20)
        
    Returns:
        Path to the generated audio file
    """
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        raise ValueError("MINIMAX_API_KEY must be set in environment variables")
    
    url = "https://api.minimaxi.chat/v1/t2a_v2"
    
    # Generate unique filename to avoid collisions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    audio_filename = f"news_summary_{timestamp}_{unique_id}.mp3"
    audio_path = Path(audio_filename).absolute()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "speech-02-hd",
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "pitch": pitch,
            "emotion": "neutral"
        }
    }
    
    # Use aiohttp for async HTTP request
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                
                # MiniMax returns hex-encoded audio in result['data']['audio']
                if 'data' in result and 'audio' in result['data']:
                    # Convert hex-encoded audio to bytes
                    audio_data = bytes.fromhex(result['data']['audio'])
                    
                    # Write audio file asynchronously
                    async with aiofiles.open(audio_path, 'wb') as f:
                        await f.write(audio_data)
                    
                    return str(audio_path)
                else:
                    raise Exception(f"Unexpected response format: {result}")
            else:
                error_text = await response.text()
                raise Exception(f"Error: {response.status} - {error_text}")


# Create the Audio Generator Agent
AUDIO_GENERATOR_INSTRUCTIONS = """You are an audio generator agent. Your task is to convert text 
summaries into audio files using the MiniMax TTS API. 

When given text, use the synthesize_speech tool to generate high-quality Chinese audio.
Return the path to the generated audio file."""

audio_generator_agent = Agent(
    name="Audio Generator",
    instructions=AUDIO_GENERATOR_INSTRUCTIONS,
    tools=[synthesize_speech],
    model="gemini-2.5-flash",
)
