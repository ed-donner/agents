import gradio as gr
import tempfile
import os
import logging
from typing import Optional, Tuple, Dict, Any
import json

from ..core.summarizer import TranscriptSummarizer, SummarizationResult
from ..utils.config import Config
from ..services.ollama_service import OllamaService # For Ollama-specific health check info
from ..services.gemini_service import GeminiService # For Gemini-specific health check info

# Set up logging for debugging using config
config_instance = Config()
log_level = getattr(logging, config_instance.log_level.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

def create_gradio_interface(config: Config) -> gr.Interface:
    """
    Create and configure the Gradio interface for the transcript summarizer.
    
    Args:
        config: Configuration object
        
    Returns:
        Configured Gradio interface
    """
    
    # Initialize the summarizer
    summarizer = TranscriptSummarizer(config)
    
    async def process_vtt_file(
        file_obj,
        chunk_size: int,
        chunk_overlap: int,
        temperature: float
    ) -> Tuple[str, str, str]:
        """
        Process uploaded VTT file and return summary with statistics.
        
        Args:
            file_obj: Uploaded file object
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlap between chunks
            temperature: LLM temperature
            
        Returns:
            Tuple of (summary, statistics, status_message)
        """
        if file_obj is None:
            return "", "", "❌ Please upload a VTT file."
        
        try:
            logger.info("🎬 GRADIO DEBUG: Starting VTT file processing")
            logger.info(f"🔧 GRADIO CONFIG DEBUG: Received from UI - chunk_size={chunk_size}, chunk_overlap={chunk_overlap}, temperature={temperature}")
            
            # Read file content
            if hasattr(file_obj, 'name'):
                file_path = file_obj.name
                logger.info(f"📂 GRADIO DEBUG: Processing file at path: {file_path}")
            else:
                # Handle case where file_obj is just the content
                with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False) as tmp_file:
                    if isinstance(file_obj, str):
                        tmp_file.write(file_obj)
                    else:
                        tmp_file.write(file_obj.read())
                    file_path = tmp_file.name
                logger.info(f"📂 GRADIO DEBUG: Created temporary file at: {file_path}")
            
            # Process the file with the provided configuration
            logger.info("🚀 GRADIO DEBUG: Calling summarizer with configuration from UI")
            result = await summarizer.summarize_vtt_file(
                file_path, 
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap, 
                temperature=temperature
            )
            
            # Clean up temporary file if created
            if hasattr(file_obj, 'name') and file_path != file_obj.name:
                try:
                    os.unlink(file_path)
                    logger.info("🧹 GRADIO DEBUG: Cleaned up temporary file")
                except:
                    pass
            
            if result.error:
                logger.error(f"❌ GRADIO DEBUG: Summarization error: {result.error}")
                return "", "", f"❌ Error: {result.error}"
            
            # Format statistics
            stats = format_statistics(result)
            
            # Success message
            status_msg = f"✅ Summary generated successfully! Processed {result.chunks_processed} chunks in {result.processing_time:.2f} seconds."
            logger.info(f"✅ GRADIO DEBUG: Processing completed successfully - {status_msg}")
            
            return result.summary, stats, status_msg
            
        except Exception as e:
            logger.error(f"❌ GRADIO DEBUG: Exception in process_vtt_file: {str(e)}")
            return "", "", f"❌ Error processing file: {str(e)}"
    
    def check_system_health() -> str:
        """Check system health and return status."""
        try:
            health = summarizer.check_service_health()
            
            status_lines = ["## System Health Check", ""]
            
            # Connection status
            if health["connection_ok"]:
                status_lines.append(f"✅ Connection to {health['llm_provider'].capitalize()}: OK")
            else:
                status_lines.append(f"❌ Connection to {health['llm_provider'].capitalize()}: FAILED")
            
            # Model availability
            if health["model_available"]:
                status_lines.append(f"✅ Model '{health['model_info'].get('name', 'N/A')}': Available")
            else:
                status_lines.append(f"❌ Model '{health['model_info'].get('name', 'N/A')}': Not available")
                if health['llm_provider'] == 'ollama':
                    status_lines.append(f"   💡 Try running: `ollama pull {config.ollama_model_name}`")
                elif health['llm_provider'] == 'gemini':
                    status_lines.append(f"   💡 Ensure GEMINI_API_KEY is set and model '{config.gemini_model_name}' is accessible.")
            
            # Model info
            model_info = health.get("model_info", {})
            if model_info and "error" not in model_info:
                status_lines.extend([
                    "",
                    "### Model Information:",
                    f"- Provider: {health['llm_provider'].capitalize()}",
                    f"- Model Name: {model_info.get('name', 'N/A')}",
                ])
                if health['llm_provider'] == 'ollama':
                    status_lines.extend([
                        f"- Family: {model_info.get('details', {}).get('family', 'N/A')}",
                        f"- Parameters: {model_info.get('details', {}).get('parameter_size', 'N/A')}",
                        f"- Format: {model_info.get('details', {}).get('format', 'N/A')}"
                    ])
                elif health['llm_provider'] == 'gemini':
                    status_lines.extend([
                        f"- Version: {model_info.get('version', 'N/A')}",
                        f"- Supported Methods: {', '.join(model_info.get('supported_generation_methods', ['N/A']))}"
                    ])
            
            # Configuration
            status_lines.extend([
                "",
                "### Configuration:",
                f"- LLM Provider: {config.llm_provider}",
                f"- Ollama URL: {config.ollama_base_url}",
                f"- Ollama Model: {config.ollama_model_name}",
                f"- Gemini Model: {config.gemini_model_name}",
                f"- Chunk Size: {config.chunk_size} tokens",
                f"- Chunk Overlap: {config.chunk_overlap} tokens",
                f"- Temperature: {config.temperature}"
            ])
            
            return "\n".join(status_lines)
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return f"❌ Health check failed: {str(e)}"
    
    def format_statistics(result: SummarizationResult) -> str:
        """Format processing statistics for display."""
        stats_lines = [
            "## Processing Statistics",
            "",
            f"**Original Length:** {result.original_length:,} characters",
            f"**Summary Length:** {result.summary_length:,} characters", 
            f"**Compression Ratio:** {result.compression_ratio:.1f}x",
            f"**Chunks Processed:** {result.chunks_processed}",
            f"**Processing Time:** {result.processing_time:.2f} seconds",
            "",
            f"**Efficiency:** {result.original_length / result.processing_time:.0f} characters/second"
        ]
        
        return "\n".join(stats_lines)
    
    # Create the Gradio interface
    with gr.Blocks(
        title="Transcript Summarizer",
        theme=gr.themes.Soft(),
        css="""
        .main-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-box {
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        .success {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }
        .error {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        """
    ) as interface:
        
        # Header
        gr.Markdown(
            """
            # 🎯 Transcript Summarizer
            
            Upload your VTT transcript files and get AI-powered summaries using your chosen LLM provider (Ollama or Gemini).
            Handles long transcripts automatically with intelligent chunking.
            """,
            elem_classes=["main-header"]
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                # File upload section
                gr.Markdown("## 📁 Upload Transcript")
                
                file_input = gr.File(
                    label="Upload VTT File",
                    file_types=[".vtt"],
                    type="filepath"
                )
                
                # Configuration section
                gr.Markdown("## ⚙️ Configuration")

                llm_provider_input = gr.Radio(
                    ["ollama", "gemini"],
                    label="LLM Provider",
                    value=config.llm_provider,
                    info="Choose your LLM provider"
                )
                
                with gr.Row():
                    chunk_size_input = gr.Slider(
                        minimum=500,
                        maximum=4000,
                        value=config.chunk_size,
                        step=100,
                        label="Chunk Size (tokens)",
                        info="Maximum tokens per chunk"
                    )
                    
                    chunk_overlap_input = gr.Slider(
                        minimum=0,
                        maximum=500,
                        value=config.chunk_overlap,
                        step=50,
                        label="Chunk Overlap (tokens)",
                        info="Overlap between chunks"
                    )
                
                temperature_input = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=config.temperature,
                    step=0.1,
                    label="Temperature",
                    info="Creativity level (0.0 = focused, 1.0 = creative)"
                )
                
                # Action buttons
                with gr.Row():
                    summarize_btn = gr.Button(
                        "🚀 Generate Summary", 
                        variant="primary",
                        size="lg"
                    )
                    
                    health_btn = gr.Button(
                        "🏥 Check System Health",
                        variant="secondary"
                    )
            
            with gr.Column(scale=3):
                # Status display
                status_output = gr.Markdown(
                    "Ready to process your transcript!",
                    elem_classes=["status-box"]
                )
                
                # Results tabs
                with gr.Tabs():
                    with gr.TabItem("📄 Summary"):
                        summary_output = gr.Textbox(
                            label="Generated Summary",
                            lines=15,
                            max_lines=25,
                            show_copy_button=True,
                            placeholder="Your summary will appear here..."
                        )
                    
                    with gr.TabItem("📊 Statistics"):
                        stats_output = gr.Markdown(
                            "Processing statistics will appear here after summarization."
                        )
                    
                    with gr.TabItem("🔧 System Health"):
                        health_output = gr.Markdown(
                            "Click 'Check System Health' to see system status."
                        )
        
        # Example section
        gr.Markdown(
            """
            ## 💡 Tips
            
            - **VTT Format**: Upload WebVTT subtitle files (.vtt extension)
            - **Long Transcripts**: The system automatically handles transcripts longer than the model's context window
            - **Chunk Size**: Larger chunks = more context per summary, but may hit model limits
            - **Overlap**: Helps maintain continuity between chunks
            - **Temperature**: Lower values = more focused summaries, higher values = more creative
            
            ## 🎬 Sample VTT Format
            ```
            WEBVTT
            
            00:00:00.000 --> 00:00:03.000
            Welcome to our presentation on artificial intelligence.
            
            00:00:03.000 --> 00:00:07.000
            Today we'll discuss the latest developments in machine learning.
            ```
            """
        )
        
        # Event handlers
        summarize_btn.click(
            fn=process_vtt_file,
            inputs=[file_input, chunk_size_input, chunk_overlap_input, temperature_input],
            outputs=[summary_output, stats_output, status_output]
        )
        
        health_btn.click(
            fn=check_system_health,
            outputs=[health_output]
        )
        
        # Auto-run health check on startup
        interface.load(
            fn=check_system_health,
            outputs=[health_output]
        )

        # Update summarizer config when LLM provider changes
        llm_provider_input.change(
            fn=lambda provider: summarizer._initialize_llm_service(Config(llm_provider=provider)),
            inputs=[llm_provider_input],
            outputs=[]
        )
    
    return interface
