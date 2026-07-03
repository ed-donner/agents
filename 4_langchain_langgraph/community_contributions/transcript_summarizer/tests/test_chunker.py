import pytest
from src.core.chunker import TextChunker, TextChunk

class TestTextChunker:
    """Test cases for text chunking functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = TextChunker(chunk_size=100, overlap_size=20)
        self.sample_text = """
        This is a sample text for testing the chunking functionality. 
        It contains multiple sentences that should be processed correctly. 
        The chunker should handle this text appropriately and create meaningful chunks.
        Each chunk should respect the token limits while maintaining readability.
        This helps ensure that the summarization process works effectively.
        """
    
    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        chunks = self.chunker.chunk_text(self.sample_text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
        assert all(chunk.token_count <= self.chunker.chunk_size for chunk in chunks)
    
    def test_chunk_by_sentences(self):
        """Test sentence-based chunking."""
        chunks = self.chunker.chunk_by_sentences(self.sample_text)
        
        assert len(chunks) > 0
        assert all(chunk.token_count <= self.chunker.chunk_size for chunk in chunks)
    
    def test_short_text(self):
        """Test chunking of short text that fits in one chunk."""
        short_text = "This is a short text."
        chunks = self.chunker.chunk_text(short_text)
        
        assert len(chunks) == 1
        assert chunks[0].content.strip() == short_text.strip()
    
    def test_empty_text(self):
        """Test handling of empty text."""
        chunks = self.chunker.chunk_text("")
        assert len(chunks) == 0
    
    def test_chunk_stats(self):
        """Test chunk statistics calculation."""
        chunks = self.chunker.chunk_text(self.sample_text)
        stats = self.chunker.get_chunk_stats(chunks)
        
        assert "total_chunks" in stats
        assert "total_tokens" in stats
        assert "avg_tokens_per_chunk" in stats
        assert stats["total_chunks"] == len(chunks)
    
    def test_chunk_ids(self):
        """Test that chunks have sequential IDs."""
        chunks = self.chunker.chunk_text(self.sample_text)
        
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == i
