"""FastMCP tool definitions for video processing."""

from fastmcp import FastMCP
from typing import Literal, Optional
import asyncio
from pathlib import Path
from .utils import (
    get_video_info,
    run_ffmpeg_command,
    create_temp_output_path,
    validate_video_file,
    format_duration,
)

mcp = FastMCP("FFmpeg Video Processor")


@mcp.tool()
async def get_video_metadata(video_path: str) -> dict:
    """
    Get detailed metadata about a video file.
    
    Args:
        video_path: Full path to the video file
        
    Returns:
        Dictionary containing video information (duration, size, resolution, codecs, etc.)
    """
    is_valid, msg = validate_video_file(video_path)
    if not is_valid:
        return {"error": msg}
    
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, get_video_info, video_path)
    
    # Add human-readable formats
    if 'duration' in info and not 'error' in info:
        info['duration_formatted'] = format_duration(info['duration'])
    
    return info


@mcp.tool()
async def compress_video(
    video_path: str,
    quality: Literal["low", "medium", "high"] = "medium",
    target_size_mb: Optional[int] = None
) -> dict:
    """
    Compress a video to reduce file size while maintaining quality.
    
    Args:
        video_path: Full path to the input video file
        quality: Compression quality level (low=smaller file, high=better quality)
        target_size_mb: Optional target size in MB (overrides quality setting)
        
    Returns:
        Dictionary with output_path, original_size, new_size, and compression_ratio
    """
    is_valid, msg = validate_video_file(video_path)
    if not is_valid:
        return {"error": msg}
    
    # CRF values (lower = better quality, larger file)
    quality_map = {
        "low": 28,      # Smaller file
        "medium": 23,   # Balanced
        "high": 18      # Better quality
    }
    
    crf = quality_map[quality]
    output_path = create_temp_output_path(video_path, f"compressed_{quality}", "mp4")
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-c:v', 'libx264',      # H.264 codec
        '-crf', str(crf),       # Quality setting
        '-preset', 'medium',    # Encoding speed/compression ratio
        '-c:a', 'aac',          # Audio codec
        '-b:a', '128k',         # Audio bitrate
        '-y',                   # Overwrite output
        output_path
    ]
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_ffmpeg_command, cmd)
    
    if not success:
        return {"error": message}
    
    # Get size comparison
    original_info = await get_video_metadata(video_path)
    new_info = await get_video_metadata(output_path)
    
    return {
        "output_path": output_path,
        "original_size_mb": original_info.get('size_mb', 0),
        "new_size_mb": new_info.get('size_mb', 0),
        "compression_ratio": f"{(1 - new_info.get('size_mb', 0) / original_info.get('size_mb', 1)) * 100:.1f}%",
        "message": f"Successfully compressed video from {original_info.get('size_mb')}MB to {new_info.get('size_mb')}MB"
    }


@mcp.tool()
async def extract_audio(
    video_path: str,
    format: Literal["mp3", "wav", "aac", "flac"] = "mp3",
    quality: Literal["low", "medium", "high"] = "high"
) -> dict:
    """
    Extract audio from a video file.
    
    Args:
        video_path: Full path to the input video file
        format: Output audio format
        quality: Audio quality level
        
    Returns:
        Dictionary with output_path and audio information
    """
    is_valid, msg = validate_video_file(video_path)
    if not is_valid:
        return {"error": msg}
    
    output_path = create_temp_output_path(video_path, "audio", format)
    
    # Quality settings for different formats
    quality_settings = {
        "mp3": {"low": "128k", "medium": "192k", "high": "320k"},
        "aac": {"low": "96k", "medium": "128k", "high": "256k"},
        "wav": {"low": "16000", "medium": "44100", "high": "48000"},  # Sample rates
        "flac": {"low": "5", "medium": "8", "high": "12"}  # Compression levels
    }
    
    cmd = ['ffmpeg', '-i', video_path]
    
    if format in ["mp3", "aac"]:
        cmd.extend(['-b:a', quality_settings[format][quality]])
    elif format == "wav":
        cmd.extend(['-ar', quality_settings[format][quality]])
    elif format == "flac":
        cmd.extend(['-compression_level', quality_settings[format][quality]])
    
    cmd.extend(['-vn', '-y', output_path])  # -vn = no video
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_ffmpeg_command, cmd)
    
    if not success:
        return {"error": message}
    
    return {
        "output_path": output_path,
        "format": format,
        "quality": quality,
        "message": f"Successfully extracted audio as {format.upper()}"
    }


@mcp.tool()
async def convert_format(
    video_path: str,
    output_format: Literal["mp4", "webm", "avi", "mov", "mkv", "gif"] = "mp4"
) -> dict:
    """
    Convert video to a different format.
    
    Args:
        video_path: Full path to the input video file
        output_format: Target video format
        
    Returns:
        Dictionary with output_path and conversion details
    """
    is_valid, msg = validate_video_file(video_path)
    if not is_valid:
        return {"error": msg}
    
    output_path = create_temp_output_path(video_path, "converted", output_format)
    
    # Format-specific settings
    if output_format == "webm":
        cmd = [
            'ffmpeg', '-i', video_path,
            '-c:v', 'libvpx-vp9',
            '-c:a', 'libopus',
            '-y', output_path
        ]
    elif output_format == "gif":
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', 'fps=10,scale=480:-1:flags=lanczos',
            '-y', output_path
        ]
    else:
        # Default conversion
        cmd = [
            'ffmpeg', '-i', video_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y', output_path
        ]
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_ffmpeg_command, cmd)
    
    if not success:
        return {"error": message}
    
    return {
        "output_path": output_path,
        "format": output_format,
        "message": f"Successfully converted to {output_format.upper()}"
    }


@mcp.tool()
async def resize_video(
    video_path: str,
    resolution: Literal["480p", "720p", "1080p", "1440p", "4k"] = "720p"
) -> dict:
    """
    Resize video to a specific resolution.
    
    Args:
        video_path: Full path to the input video file
        resolution: Target resolution
        
    Returns:
        Dictionary with output_path and new dimensions
    """
    is_valid, msg = validate_video_file(video_path)
    if not is_valid:
        return {"error": msg}
    
    # Resolution mappings
    resolution_map = {
        "480p": "854:480",
        "720p": "1280:720",
        "1080p": "1920:1080",
        "1440p": "2560:1440",
        "4k": "3840:2160"
    }
    
    output_path = create_temp_output_path(video_path, f"resized_{resolution}", "mp4")
    
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', f'scale={resolution_map[resolution]}',
        '-c:a', 'copy',  # Copy audio without re-encoding
        '-y', output_path
    ]
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_ffmpeg_command, cmd)
    
    if not success:
        return {"error": message}
    
    new_info = await get_video_metadata(output_path)
    
    return {
        "output_path": output_path,
        "resolution": resolution,
        "dimensions": f"{new_info.get('width')}x{new_info.get('height')}",
        "message": f"Successfully resized to {resolution}"
    }


@mcp.tool()
async def extract_thumbnail(
    video_path: str,
    timestamp: float = 1.0
) -> dict:
    """
    Extract a thumbnail image from a video at a specific timestamp.
    
    Args:
        video_path: Full path to the input video file
        timestamp: Time in seconds to extract frame from
        
    Returns:
        Dictionary with output_path to the thumbnail image
    """
    is_valid, msg = validate_video_file(video_path)
    if not is_valid:
        return {"error": msg}
    
    output_path = create_temp_output_path(video_path, "thumbnail", "jpg")
    
    cmd = [
        'ffmpeg', '-i', video_path,
        '-ss', str(timestamp),
        '-vframes', '1',
        '-q:v', '2',  # High quality
        '-y', output_path
    ]
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_ffmpeg_command, cmd)
    
    if not success:
        return {"error": message}
    
    return {
        "output_path": output_path,
        "timestamp": timestamp,
        "message": f"Successfully extracted thumbnail at {timestamp}s"
    }


@mcp.tool()
async def trim_video(
    video_path: str,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
    duration: Optional[float] = None
) -> dict:
    """
    Extract a specific segment/clip from a video.
    
    Args:
        video_path: Full path to the input video file
        start_time: Start time in seconds (default: 0)
        end_time: End time in seconds (optional, mutually exclusive with duration)
        duration: Duration in seconds from start_time (optional, mutually exclusive with end_time)
        
    Returns:
        Dictionary with output_path to the trimmed video clip
    
    Examples:
        - First 10 seconds: start_time=0, duration=10
        - From 5s to 15s: start_time=5, end_time=15
        - Last 30 seconds: Use get_video_metadata first, then calculate start_time
    """
    is_valid, msg = validate_video_file(video_path)
    if not is_valid:
        return {"error": msg}
    
    # Validate parameters
    if end_time is not None and duration is not None:
        return {"error": "Cannot specify both end_time and duration. Use one or the other."}
    
    if end_time is not None and end_time <= start_time:
        return {"error": f"end_time ({end_time}s) must be greater than start_time ({start_time}s)"}
    
    # Calculate duration if end_time is provided
    if end_time is not None:
        duration = end_time - start_time
    
    # Build output path name
    if duration:
        suffix = f"trim_{int(start_time)}s-{int(start_time + duration)}s"
    else:
        suffix = f"trim_from_{int(start_time)}s"
    
    output_path = create_temp_output_path(video_path, suffix, "mp4")
    
    # Build FFmpeg command
    cmd = ['ffmpeg', '-i', video_path, '-ss', str(start_time)]
    
    if duration is not None:
        cmd.extend(['-t', str(duration)])
    
    # Copy codecs for fast processing (no re-encoding)
    cmd.extend(['-c', 'copy', '-y', output_path])
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_ffmpeg_command, cmd)
    
    if not success:
        return {"error": message}
    
    # Get info about the trimmed clip
    clip_info = await get_video_metadata(output_path)
    
    return {
        "output_path": output_path,
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration if duration else clip_info.get('duration'),
        "size_mb": clip_info.get('size_mb'),
        "message": f"Successfully extracted clip from {start_time}s" + 
                   (f" to {end_time}s" if end_time else f" ({duration}s duration)" if duration else "")
    }


# Run the server
if __name__ == "__main__":
    mcp.run()
