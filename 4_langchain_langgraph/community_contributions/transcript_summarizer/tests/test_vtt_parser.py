import pytest
import tempfile
import os
from src.core.vtt_parser import VTTParser, TranscriptSegment

class TestVTTParser:
    """Test cases for VTT parser functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = VTTParser()
        self.sample_vtt = """WEBVTT

00:00:00.000 --> 00:00:03.000
Hello and welcome to our presentation.

00:00:03.000 --> 00:00:07.000
Today we'll discuss artificial intelligence.

00:00:07.000 --> 00:00:12.000
Let's start with the basics of machine learning.
"""

    def test_parse_content(self):
        """Test parsing VTT content from string."""
        segments = self.parser.parse_content(self.sample_vtt)
        
        assert len(segments) == 3
        assert segments[0].text == "Hello and welcome to our presentation."
        assert segments[0].start_time == "00:00:00.000"
        assert segments[0].end_time == "00:00:03.000"
    
    def test_get_full_transcript(self):
        """Test getting full transcript without timestamps."""
        self.parser.parse_content(self.sample_vtt)
        full_text = self.parser.get_full_transcript()
        
        expected = "Hello and welcome to our presentation. Today we'll discuss artificial intelligence. Let's start with the basics of machine learning."
        assert full_text == expected
    
    def test_get_transcript_with_timestamps(self):
        """Test getting transcript with timestamp markers."""
        self.parser.parse_content(self.sample_vtt)
        timestamped = self.parser.get_transcript_with_timestamps()
        
        assert "[00:00:00.000 -> 00:00:03.000]" in timestamped
        assert "Hello and welcome to our presentation." in timestamped
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        dirty_text = "<i>Hello</i>   world   <b>test</b>"
        clean_text = self.parser._clean_text(dirty_text)
        
        assert clean_text == "Hello world test"
    
    def test_empty_content(self):
        """Test handling of empty content."""
        segments = self.parser.parse_content("")
        assert len(segments) == 0
    
    def test_malformed_vtt(self):
        """Test handling of malformed VTT content."""
        malformed_vtt = "This is not a valid VTT file"
        
        with pytest.raises(ValueError):
            self.parser.parse_content(malformed_vtt)
