import tiktoken
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    start_index: int
    end_index: int
    token_count: int
    chunk_id: int

class TextChunker:
    """Handles intelligent text chunking for long documents."""
    
    def __init__(self, chunk_size: int = 2000, overlap_size: int = 200, model: str = "gpt-3.5-turbo"):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Maximum tokens per chunk
            overlap_size: Number of tokens to overlap between chunks
            model: Model name for tokenization
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        try:
            self.tokenizer = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def chunk_text(self, text: str, preserve_sentences: bool = True) -> List[TextChunk]:
        """
        Chunk text into smaller pieces while preserving context.
        
        Args:
            text: Input text to chunk
            preserve_sentences: Whether to try to preserve sentence boundaries
            
        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []
        
        # Tokenize the entire text
        tokens = self.tokenizer.encode(text)
        total_tokens = len(tokens)
        
        if total_tokens <= self.chunk_size:
            # Text fits in a single chunk
            return [TextChunk(
                content=text,
                start_index=0,
                end_index=len(text),
                token_count=total_tokens,
                chunk_id=0
            )]
        
        chunks = []
        chunk_id = 0
        start_token = 0
        
        while start_token < total_tokens:
            # Calculate end token for this chunk
            end_token = min(start_token + self.chunk_size, total_tokens)
            
            # Extract tokens for this chunk
            chunk_tokens = tokens[start_token:end_token]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # If we're preserving sentences and not at the end, try to break at sentence boundary
            if preserve_sentences and end_token < total_tokens:
                chunk_text = self._adjust_chunk_boundary(chunk_text)
                # Re-encode to get actual token count
                chunk_tokens = self.tokenizer.encode(chunk_text)
                end_token = start_token + len(chunk_tokens)
            
            # Create chunk
            chunk = TextChunk(
                content=chunk_text,
                start_index=self._get_char_index(text, start_token, tokens),
                end_index=self._get_char_index(text, end_token, tokens),
                token_count=len(chunk_tokens),
                chunk_id=chunk_id
            )
            chunks.append(chunk)
            
            # Calculate next start position with overlap
            start_token = max(end_token - self.overlap_size, start_token + 1)
            chunk_id += 1
            
            # Prevent infinite loop
            if start_token >= end_token:
                break
        
        return chunks
    
    def chunk_by_sentences(self, text: str) -> List[TextChunk]:
        """
        Chunk text by sentences, respecting token limits.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of TextChunk objects
        """
        import re
        
        # Split into sentences using regex
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_id = 0
        start_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            # If adding this sentence would exceed the limit, create a new chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunk = TextChunk(
                    content=current_chunk.strip(),
                    start_index=start_index,
                    end_index=start_index + len(current_chunk),
                    token_count=current_tokens,
                    chunk_id=chunk_id
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence
                current_tokens = len(self.tokenizer.encode(current_chunk))
                start_index += len(chunk.content) - len(overlap_text)
                chunk_id += 1
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens = len(self.tokenizer.encode(current_chunk))
        
        # Add the last chunk
        if current_chunk.strip():
            chunk = TextChunk(
                content=current_chunk.strip(),
                start_index=start_index,
                end_index=start_index + len(current_chunk),
                token_count=current_tokens,
                chunk_id=chunk_id
            )
            chunks.append(chunk)
        
        return chunks
    
    def _adjust_chunk_boundary(self, text: str) -> str:
        """
        Adjust chunk boundary to end at a sentence or at least a word boundary.
        
        Args:
            text: Text to adjust
            
        Returns:
            Adjusted text
        """
        # Try to find the last sentence ending
        import re
        sentence_endings = ['.', '!', '?']
        
        for i in range(len(text) - 1, -1, -1):
            if text[i] in sentence_endings and i < len(text) - 1:
                # Found a sentence ending, include it and any following whitespace
                end_index = i + 1
                while end_index < len(text) and text[end_index].isspace():
                    end_index += 1
                return text[:end_index]
        
        # If no sentence ending found, try to break at word boundary
        words = text.split()
        if len(words) > 1:
            return ' '.join(words[:-1])
        
        return text
    
    def _get_overlap_text(self, text: str) -> str:
        """
        Get overlap text from the end of a chunk.
        
        Args:
            text: Source text
            
        Returns:
            Overlap text
        """
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= self.overlap_size:
            return text
        
        overlap_tokens = tokens[-self.overlap_size:]
        return self.tokenizer.decode(overlap_tokens)
    
    def _get_char_index(self, full_text: str, token_index: int, all_tokens: List[int]) -> int:
        """
        Convert token index to character index in the original text.
        
        Args:
            full_text: Original full text
            token_index: Token index
            all_tokens: All tokens from the text
            
        Returns:
            Character index
        """
        if token_index >= len(all_tokens):
            return len(full_text)
        
        # This is an approximation - more accurate methods would require
        # maintaining a mapping during tokenization
        char_ratio = len(full_text) / len(all_tokens)
        return min(int(token_index * char_ratio), len(full_text))
    
    def get_chunk_stats(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Get statistics about the chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_tokens": 0,
                "avg_tokens_per_chunk": 0,
                "min_tokens": 0,
                "max_tokens": 0
            }
        
        token_counts = [chunk.token_count for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_tokens": sum(token_counts),
            "avg_tokens_per_chunk": sum(token_counts) / len(token_counts),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts)
        }
