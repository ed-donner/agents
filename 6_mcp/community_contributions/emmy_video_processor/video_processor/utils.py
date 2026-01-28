"""
Utility functions for FFmpeg operations
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import json


def get_video_info(input_path: str) -> dict:
    """
    Get video metadata using ffprobe
    Returns dict with duration, width, height, size, codec, etc.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            input_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Extract useful info
        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)
        
        info = {
            'duration': float(data['format'].get('duration', 0)),
            'size_mb': round(int(data['format'].get('size', 0)) / (1024 * 1024), 2),
            'format': data['format'].get('format_name', 'unknown'),
        }
        
        if video_stream:
            info.update({
                'width': video_stream.get('width'),
                'height': video_stream.get('height'),
                'video_codec': video_stream.get('codec_name'),
                'fps': eval(video_stream.get('r_frame_rate', '0/1'))
            })
        
        if audio_stream:
            info.update({
                'audio_codec': audio_stream.get('codec_name'),
                'sample_rate': audio_stream.get('sample_rate')
            })
        
        return info
    except Exception as e:
        return {'error': str(e)}


def run_ffmpeg_command(cmd: list, timeout: int = 300) -> Tuple[bool, str]:
    """
    Execute FFmpeg command and return success status and message
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        return True, "Success"
    except subprocess.TimeoutExpired:
        return False, f"Operation timed out after {timeout} seconds"
    except subprocess.CalledProcessError as e:
        return False, f"FFmpeg error: {e.stderr}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def create_temp_output_path(original_path: str, suffix: str, extension: str) -> str:
    """
    Create a temporary output file path
    """
    temp_dir = tempfile.gettempdir()
    original_name = Path(original_path).stem
    output_name = f"{original_name}_{suffix}.{extension}"
    return os.path.join(temp_dir, output_name)


def validate_video_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate that the file exists and is a video
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    if not os.path.isfile(file_path):
        return False, "Path is not a file"
    
    # Check file extension
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg'}
    ext = Path(file_path).suffix.lower()
    
    if ext not in valid_extensions:
        return False, f"Unsupported file extension: {ext}"
    
    return True, "Valid"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
