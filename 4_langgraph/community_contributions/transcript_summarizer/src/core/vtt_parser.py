import webvtt
from typing import List, Optional
from dataclasses import dataclass
import re

@dataclass
class TranscriptSegment:
    """Represents a segment of transcript with timing information."""
    start_time: str
    end_time: str
    text: str
    
class VTTParser:
    """Parser for WebVTT transcript files."""
    
    def __init__(self):
        self.segments: List[TranscriptSegment] = []
    
    def parse_file(self, file_path: str) -> List[TranscriptSegment]:
        """
        Parse a VTT file and extract transcript segments.
        
        Args:
            file_path: Path to the VTT file
            
        Returns:
            List of TranscriptSegment objects
        """
        try:
            vtt = webvtt.read(file_path)
            segments = []
            
            for caption in vtt:
                # Clean the text by removing HTML tags and extra whitespace
                clean_text = self._clean_text(caption.text)
                if clean_text.strip():  # Only add non-empty segments
                    segment = TranscriptSegment(
                        start_time=caption.start,
                        end_time=caption.end,
                        text=clean_text
                    )
                    segments.append(segment)
            
            self.segments = segments
            return segments
            
        except Exception as e:
            raise ValueError(f"Error parsing VTT file: {str(e)}")
    
    def parse_content(self, vtt_content: str) -> List[TranscriptSegment]:
        """
        Parse VTT content from a string.
        
        Args:
            vtt_content: VTT content as string
            
        Returns:
            List of TranscriptSegment objects
        """
        # Handle empty content gracefully
        if not vtt_content or not vtt_content.strip():
            return []
            
        try:
            # Write content to a temporary file and parse it
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False) as tmp_file:
                tmp_file.write(vtt_content)
                tmp_file_path = tmp_file.name
            
            try:
                segments = self.parse_file(tmp_file_path)
                return segments
            finally:
                os.unlink(tmp_file_path)
                
        except Exception as e:
            raise ValueError(f"Error parsing VTT content: {str(e)}")
    
    def get_full_transcript(self) -> str:
        """
        Get the full transcript text without timing information.
        
        Returns:
            Complete transcript as a single string
        """
        return " ".join([segment.text for segment in self.segments])
    
    def get_transcript_with_timestamps(self) -> str:
        """
        Get the transcript with timestamp markers.
        
        Returns:
            Transcript with timing information
        """
        formatted_segments = []
        for segment in self.segments:
            formatted_segments.append(
                f"[{segment.start_time} -> {segment.end_time}] {segment.text}"
            )
        return "\n".join(formatted_segments)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean transcript text by removing HTML tags and normalizing whitespace.
        
        Args:
            text: Raw text from VTT
            
        Returns:
            Cleaned text
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def get_duration_seconds(self) -> float:
        """
        Calculate total duration of the transcript in seconds.
        
        Returns:
            Duration in seconds
        """
        if not self.segments:
            return 0.0
        
        def time_to_seconds(time_str: str) -> float:
            """Convert VTT time format to seconds."""
            # Handle format: HH:MM:SS.mmm or MM:SS.mmm
            parts = time_str.split(':')
            if len(parts) == 3:  # HH:MM:SS.mmm
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            elif len(parts) == 2:  # MM:SS.mmm
                minutes, seconds = parts
                return int(minutes) * 60 + float(seconds)
            else:
                return float(parts[0])
        
        try:
            start_time = time_to_seconds(self.segments[0].start_time)
            end_time = time_to_seconds(self.segments[-1].end_time)
            return end_time - start_time
        except Exception:
            return 0.0
