import asyncio
import logging
from typing import List, Dict, Any, Optional, TypedDict
from dataclasses import dataclass
import time
from concurrent.futures import ThreadPoolExecutor

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, START, END

from ..core.vtt_parser import VTTParser, TranscriptSegment
from ..core.chunker import TextChunker, TextChunk
from ..services.ollama_service import OllamaService, OllamaResponse
from ..services.gemini_service import GeminiService, GeminiResponse
from ..utils.config import Config

# Set up logging for debugging using config
config_instance = Config()
log_level = getattr(logging, config_instance.log_level.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

class SummarizationState(TypedDict):
    """State for the summarization workflow."""
    original_text: str
    chunks: Optional[List[TextChunk]]
    chunk_summaries: Optional[List[str]]
    final_summary: str
    processing_stats: Optional[Dict[str, Any]]
    error: Optional[str]
    # Add configuration tracking
    debug_config: Optional[Dict[str, Any]]

@dataclass
class SummarizationResult:
    """Result of the summarization process."""
    summary: str
    original_length: int
    summary_length: int
    chunks_processed: int
    processing_time: float
    compression_ratio: float
    error: Optional[str] = None

class TranscriptSummarizer:
    """Main summarizer class using LangGraph for workflow orchestration."""
    
    def __init__(self, config: Config):
        """
        Initialize the summarizer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        logger.info("🔧 INITIALIZATION DEBUG: TranscriptSummarizer initialized")
        logger.info(f"📊 Initial Config - Temperature: {config.temperature}")
        logger.info(f"📊 Initial Config - Chunk Size: {config.chunk_size}")
        logger.info(f"📊 Initial Config - Chunk Overlap: {config.chunk_overlap}")
        logger.info(f"📊 Initial Config - LLM Provider: {config.llm_provider}")
        logger.info(f"📊 Initial Config - Ollama URL: {config.ollama_base_url}")
        logger.info(f"📊 Initial Config - Ollama Model: {config.ollama_model_name}")
        logger.info(f"📊 Initial Config - Gemini Model: {config.gemini_model_name}")
        
        self.llm_service = self._initialize_llm_service(config)
        self.chunker = TextChunker(
            chunk_size=config.chunk_size,
            overlap_size=config.chunk_overlap
        )
        self.vtt_parser = VTTParser()
        self.workflow = self._create_workflow()
    
    def _initialize_llm_service(self, config: Config):
        """Initialize the appropriate LLM service based on configuration."""
        if config.llm_provider == "ollama":
            logger.info(f"Initializing OllamaService with base_url={config.ollama_base_url}, model={config.ollama_model_name}")
            return OllamaService(
                base_url=config.ollama_base_url,
                model=config.ollama_model_name,
                timeout=config.request_timeout
            )
        elif config.llm_provider == "gemini":
            if not config.gemini_api_key:
                raise ValueError("GEMINI_API_KEY must be set in .env for Gemini provider.")
            logger.info(f"Initializing GeminiService with model={config.gemini_model_name}")
            return GeminiService(
                api_key=config.gemini_api_key,
                model=config.gemini_model_name,
                timeout=config.request_timeout
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")

    def update_config(self, chunk_size: int, chunk_overlap: int, temperature: float):
        """
        Update configuration and recreate necessary components.
        
        Args:
            chunk_size: New chunk size
            chunk_overlap: New chunk overlap
            temperature: New temperature
        """
        logger.info("🔄 CONFIG UPDATE DEBUG: Updating configuration")
        logger.info(f"📊 OLD Config - Temperature: {self.config.temperature}")
        logger.info(f"📊 OLD Config - Chunk Size: {self.config.chunk_size}")
        logger.info(f"📊 OLD Config - Chunk Overlap: {self.config.chunk_overlap}")
        
        # Update config
        self.config.temperature = temperature
        self.config.chunk_size = chunk_size
        self.config.chunk_overlap = chunk_overlap
        
        logger.info(f"📊 NEW Config - Temperature: {self.config.temperature}")
        logger.info(f"📊 NEW Config - Chunk Size: {self.config.chunk_size}")
        logger.info(f"📊 NEW Config - Chunk Overlap: {self.config.chunk_overlap}")
        
        # Recreate chunker with new settings
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            overlap_size=chunk_overlap
        )
        logger.info("🔄 CONFIG UPDATE DEBUG: Chunker recreated with new settings")
        # Re-initialize LLM service if model name or provider changes (not handled by this update_config)
        # For now, assume model/provider changes require full re-initialization of Summarizer
    
    def _create_workflow(self):
        """Create the LangGraph workflow for summarization."""
        
        def parse_input(state: SummarizationState) -> SummarizationState:
            """Parse and validate input."""
            logger.info("🏁 WORKFLOW DEBUG: Starting parse_input node")
            if not state.get("original_text", "").strip():
                logger.error("❌ WORKFLOW DEBUG: Empty input text")
                return {**state, "error": "Empty input text"}
            
            # Initialize processing stats
            processing_stats = {
                "start_time": time.time(),
                "original_length": len(state["original_text"]),
                "original_words": len(state["original_text"].split())
            }
            
            # Add debug config to state
            debug_config = {
                "temperature": self.config.temperature,
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
                "llm_provider": self.config.llm_provider,
                "model_name": self.config.ollama_model_name if self.config.llm_provider == "ollama" else self.config.gemini_model_name
            }
            
            logger.info(f"🐛 WORKFLOW DEBUG: Configuration in parse_input - {debug_config}")
            
            return {**state, "processing_stats": processing_stats, "debug_config": debug_config}
        
        def chunk_text(state: SummarizationState) -> SummarizationState:
            """Chunk the text for processing."""
            logger.info("✂️ WORKFLOW DEBUG: Starting chunk_text node")
            debug_config = state.get("debug_config", {})
            logger.info(f"🐛 WORKFLOW DEBUG: Using chunk_size={debug_config.get('chunk_size')} and chunk_overlap={debug_config.get('chunk_overlap')}")
            
            if state.get("error"):
                return state
            
            try:
                # Log current chunker configuration
                logger.info(f"🔧 CHUNKER DEBUG: Chunker configured with size={self.chunker.chunk_size}, overlap={self.chunker.overlap_size}")
                
                chunks = self.chunker.chunk_by_sentences(state["original_text"])
                logger.info(f"📊 CHUNKER DEBUG: Created {len(chunks)} chunks")
                
                # Log chunk details
                for i, chunk in enumerate(chunks):
                    logger.info(f"📄 CHUNK {i+1} DEBUG: {chunk.token_count} tokens, first 100 chars: {chunk.content[:100]}...")
                
                processing_stats = state.get("processing_stats", {})
                processing_stats.update({
                    "chunks_created": len(chunks),
                    "chunking_strategy": "sentence-based",
                    "actual_chunk_size_used": self.chunker.chunk_size,
                    "actual_overlap_used": self.chunker.overlap_size
                })
                
                # If only one chunk, we might not need chunk-level summarization
                if len(chunks) == 1:
                    processing_stats["single_chunk"] = True
                    logger.info("📝 CHUNKER DEBUG: Single chunk detected, will skip chunk summarization")
                
                return {**state, "chunks": chunks, "processing_stats": processing_stats}
                
            except Exception as e:
                logger.error(f"❌ CHUNKER DEBUG: Error in chunking - {str(e)}")
                return {**state, "error": f"Error chunking text: {str(e)}"}
        
        async def summarize_chunks(state: SummarizationState) -> SummarizationState:
            """Summarize individual chunks."""
            logger.info("📝 WORKFLOW DEBUG: Starting summarize_chunks node")
            debug_config = state.get("debug_config", {})
            logger.info(f"🐛 WORKFLOW DEBUG: Using temperature={debug_config.get('temperature')} for chunk summarization")
            
            if state.get("error") or not state.get("chunks"):
                return state
            
            try:
                chunks = state["chunks"]
                
                # If only one chunk, skip chunk summarization
                if len(chunks) == 1:
                    logger.info("📝 CHUNK SUMMARY DEBUG: Single chunk, using original content")
                    return {**state, "chunk_summaries": [chunks[0].content]}
                
                # Create prompts for each chunk
                chunk_prompts = []
                for i, chunk in enumerate(chunks):
                    prompt = self._create_chunk_summary_prompt(chunk.content, i + 1, len(chunks))
                    chunk_prompts.append(prompt)
                    logger.info(f"📄 PROMPT DEBUG: Created prompt for chunk {i+1}, prompt length: {len(prompt)} chars")
                
                # Log temperature being used
                logger.info(f"🌡️ TEMPERATURE DEBUG: About to call LLM service with temperature={self.config.temperature}")
                
                # Process chunks asynchronously
                chunk_summaries = await self._process_chunks_async(chunk_prompts)
                
                # Log results
                for i, summary in enumerate(chunk_summaries):
                    logger.info(f"📄 SUMMARY {i+1} DEBUG: {len(summary)} chars, first 100 chars: {summary[:100]}...")
                
                processing_stats = state.get("processing_stats", {})
                processing_stats["chunks_summarized"] = len(chunk_summaries)
                processing_stats["temperature_used"] = self.config.temperature
                
                return {**state, "chunk_summaries": chunk_summaries, "processing_stats": processing_stats}
                
            except Exception as e:
                logger.error(f"❌ CHUNK SUMMARY DEBUG: Error in chunk summarization - {str(e)}")
                return {**state, "error": f"Error summarizing chunks: {str(e)}"}
        
        def create_final_summary(state: SummarizationState) -> SummarizationState:
            """Create the final summary from chunk summaries."""
            logger.info("🎯 WORKFLOW DEBUG: Starting create_final_summary node")
            debug_config = state.get("debug_config", {})
            logger.info(f"🐛 WORKFLOW DEBUG: Using temperature={debug_config.get('temperature')} for final summary")
            
            if state.get("error") or not state.get("chunk_summaries"):
                return state
            
            try:
                # Combine chunk summaries
                combined_summaries = "\n\n".join(state["chunk_summaries"])
                logger.info(f"📄 FINAL SUMMARY DEBUG: Combined summaries length: {len(combined_summaries)} chars")
                
                # Create final summary prompt
                final_prompt = self._create_final_summary_prompt(combined_summaries)
                logger.info(f"📄 FINAL PROMPT DEBUG: Final prompt length: {len(final_prompt)} chars")
                
                # Log temperature being used
                logger.info(f"🌡️ FINAL TEMPERATURE DEBUG: About to call LLM service with temperature={self.config.temperature}")
                
                # Generate final summary
                response = self.llm_service.generate_sync(
                    prompt=final_prompt,
                    temperature=self.config.temperature,
                )
                
                final_summary = response.content.strip()
                logger.info(f"📄 FINAL RESULT DEBUG: Final summary length: {len(final_summary)} chars")
                logger.info(f"📄 FINAL RESULT DEBUG: First 200 chars: {final_summary}...")
                
                # Update processing stats
                processing_stats = state.get("processing_stats", {})
                end_time = time.time()
                processing_time = end_time - processing_stats.get("start_time", 0)
                
                processing_stats.update({
                    "end_time": end_time,
                    "processing_time": processing_time,
                    "final_summary_length": len(final_summary),
                    "final_summary_words": len(final_summary.split()),
                    "compression_ratio": len(state["original_text"]) / len(final_summary) if final_summary else 0,
                    "final_temperature_used": self.config.temperature
                })
                
                logger.info(f"⏱️ TIMING DEBUG: Total processing time: {processing_time:.2f} seconds")
                logger.info(f"📊 COMPRESSION DEBUG: Compression ratio: {processing_stats['compression_ratio']:.2f}x")
                
                return {**state, "final_summary": final_summary, "processing_stats": processing_stats}
                
            except Exception as e:
                logger.error(f"❌ FINAL SUMMARY DEBUG: Error in final summary creation - {str(e)}")
                return {**state, "error": f"Error creating final summary: {str(e)}"}
        
        # Create the workflow graph
        workflow = StateGraph(SummarizationState)
        
        # Add nodes
        workflow.add_node("parse_input", parse_input)
        workflow.add_node("chunk_text", chunk_text)
        workflow.add_node("summarize_chunks", summarize_chunks)
        workflow.add_node("create_final_summary", create_final_summary)
        
        # Define the workflow
        workflow.add_edge(START, "parse_input")
        workflow.add_edge("parse_input", "chunk_text")
        workflow.add_edge("chunk_text", "summarize_chunks")
        workflow.add_edge("summarize_chunks", "create_final_summary")
        workflow.add_edge("create_final_summary", END)
        
        return workflow.compile()
    
    async def _process_chunks_async(self, prompts: List[str]) -> List[str]:
        """Process multiple chunk prompts asynchronously."""
        logger.info(f"🔄 ASYNC DEBUG: Processing {len(prompts)} chunks asynchronously")
        logger.info(f"🌡️ ASYNC TEMPERATURE DEBUG: Using temperature={self.config.temperature}")
        
        async with self.llm_service:
            responses = await self.llm_service.generate_multiple_async(
                prompts, 
                temperature=self.config.temperature
            )
            
            results = [response.content.strip() for response in responses]
            logger.info(f"✅ ASYNC DEBUG: Completed processing {len(results)} chunks")
            return results
    
    def _create_chunk_summary_prompt(self, chunk_text: str, chunk_num: int, total_chunks: int) -> str:
        """Create a prompt for summarizing a text chunk."""
        return f"""You are an expert at summarizing transcript content. Please provide a concise but comprehensive summary of the following transcript segment.

This is chunk {chunk_num} of {total_chunks} from a larger transcript.

Key requirements:
- Capture the main topics and key points discussed
- Preserve important details, names, and specific information
- Keep the summary focused and well-structured
- Maintain the chronological flow of information
- Use clear, professional language

Transcript segment:
{chunk_text}

Summary:"""

    def _create_final_summary_prompt(self, combined_summaries: str) -> str:
        """Create a prompt for the final summary."""
        return f"""You are an expert at creating comprehensive summaries from multiple related text segments. Below are summaries of different parts of a transcript. Please create a final, cohesive summary that:

1. Integrates all the key information from the segments
2. Maintains logical flow and structure
3. Eliminates redundancy while preserving important details
4. Provides a clear overview of the main topics and conclusions
5. Uses professional, clear language
6. Organizes information in a helpful way for the reader

Segment summaries:
{combined_summaries}

Please provide a comprehensive final summary:"""

    async def summarize_vtt_file(self, file_path: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None, temperature: Optional[float] = None) -> SummarizationResult:
        """
        Summarize a VTT file.
        
        Args:
            file_path: Path to the VTT file
            chunk_size: Override chunk size (optional)
            chunk_overlap: Override chunk overlap (optional)
            temperature: Override temperature (optional)
            
        Returns:
            SummarizationResult object
        """
        try:
            logger.info(f"📂 VTT FILE DEBUG: Processing file {file_path}")
            # Parse VTT file
            segments = self.vtt_parser.parse_file(file_path)
            full_text = self.vtt_parser.get_full_transcript()
            logger.info(f"📄 VTT FILE DEBUG: Extracted {len(segments)} segments, {len(full_text)} chars total")
            
            return await self.summarize_text(full_text, chunk_size, chunk_overlap, temperature)
            
        except Exception as e:
            logger.error(f"❌ VTT FILE DEBUG: Error processing VTT file - {str(e)}")
            return SummarizationResult(
                summary="",
                original_length=0,
                summary_length=0,
                chunks_processed=0,
                processing_time=0.0,
                compression_ratio=0.0,
                error=str(e)
            )
    
    async def summarize_vtt_content(self, vtt_content: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None, temperature: Optional[float] = None) -> SummarizationResult:
        """
        Summarize VTT content from a string.
        
        Args:
            vtt_content: VTT content as string
            chunk_size: Override chunk size (optional)
            chunk_overlap: Override chunk overlap (optional)
            temperature: Override temperature (optional)
            
        Returns:
            SummarizationResult object
        """
        try:
            logger.info(f"📄 VTT CONTENT DEBUG: Processing VTT content, {len(vtt_content)} chars")
            # Parse VTT content
            segments = self.vtt_parser.parse_content(vtt_content)
            full_text = self.vtt_parser.get_full_transcript()
            logger.info(f"📄 VTT CONTENT DEBUG: Extracted {len(segments)} segments, {len(full_text)} chars total")
            
            return await self.summarize_text(full_text, chunk_size, chunk_overlap, temperature)
            
        except Exception as e:
            logger.error(f"❌ VTT CONTENT DEBUG: Error processing VTT content - {str(e)}")
            return SummarizationResult(
                summary="",
                original_length=0,
                summary_length=0,
                chunks_processed=0,
                processing_time=0.0,
                compression_ratio=0.0,
                error=str(e)
            )
    
    async def summarize_text(self, text: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None, temperature: Optional[float] = None) -> SummarizationResult:
        """
        Summarize plain text.
        
        Args:
            text: Input text to summarize
            chunk_size: Override chunk size (optional)
            chunk_overlap: Override chunk overlap (optional)
            temperature: Override temperature (optional)
            
        Returns:
            SummarizationResult object
        """
        logger.info("🚀 SUMMARIZE DEBUG: Starting text summarization")
        
        # Update configuration if provided
        if chunk_size is not None or chunk_overlap is not None or temperature is not None:
            new_chunk_size = chunk_size if chunk_size is not None else self.config.chunk_size
            new_chunk_overlap = chunk_overlap if chunk_overlap is not None else self.config.chunk_overlap
            new_temperature = temperature if temperature is not None else self.config.temperature
            
            logger.info("🔄 SUMMARIZE DEBUG: Updating configuration with provided values")
            self.update_config(new_chunk_size, new_chunk_overlap, new_temperature)
        
        logger.info(f"📊 SUMMARIZE DEBUG: Final config - Temperature: {self.config.temperature}, Chunk Size: {self.config.chunk_size}, Overlap: {self.config.chunk_overlap}")
        
        # Create initial state
        initial_state: SummarizationState = {
            "original_text": text,
            "chunks": None,
            "chunk_summaries": None,
            "final_summary": "",
            "processing_stats": None,
            "error": None,
            "debug_config": None
        }
        
        # Run the workflow
        logger.info("🎬 SUMMARIZE DEBUG: Starting LangGraph workflow")
        result_state = await self.workflow.ainvoke(initial_state)
        logger.info("🏁 SUMMARIZE DEBUG: LangGraph workflow completed")
        
        # Create result object
        if result_state.get("error"):
            logger.error(f"❌ SUMMARIZE DEBUG: Error in workflow - {result_state['error']}")
            return SummarizationResult(
                summary="",
                original_length=len(text),
                summary_length=0,
                chunks_processed=0,
                processing_time=0.0,
                compression_ratio=0.0,
                error=result_state["error"]
            )
        
        stats = result_state.get("processing_stats", {})
        result = SummarizationResult(
            summary=result_state.get("final_summary", ""),
            original_length=stats.get("original_length", 0),
            summary_length=stats.get("final_summary_length", 0),
            chunks_processed=stats.get("chunks_summarized", 0),
            processing_time=stats.get("processing_time", 0.0),
            compression_ratio=stats.get("compression_ratio", 0.0)
        )
        
        logger.info(f"✅ SUMMARIZE DEBUG: Summarization completed successfully")
        logger.info(f"📊 RESULT DEBUG: Original: {result.original_length} chars, Summary: {result.summary_length} chars, Ratio: {result.compression_ratio:.2f}x")
        
        return result
    
    def check_service_health(self) -> Dict[str, Any]:
        """
        Check the health of the current LLM service and model availability.
        
        Returns:
            Health check results
        """
        health_status = {
            "llm_provider": self.config.llm_provider,
            "connection_ok": False,
            "model_available": False,
            "model_info": {},
            "timestamp": time.time()
        }
        
        try:
            # Test connection
            health_status["connection_ok"] = self.llm_service.test_connection()
            
            if health_status["connection_ok"]:
                # Check model availability
                health_status["model_available"] = self.llm_service.check_model_availability()
                
                # Get model info
                health_status["model_info"] = self.llm_service.get_model_info()
        
        except Exception as e:
            health_status["error"] = str(e)
        
        return health_status
