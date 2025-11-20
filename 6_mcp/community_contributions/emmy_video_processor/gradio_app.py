import os
from pathlib import Path

import gradio as gr
from agents import set_default_openai_client
from dotenv import load_dotenv
from openai import AsyncOpenAI

from video_processor.agent import process_request

load_dotenv()
async_openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=10,
    max_retries=0,
)
set_default_openai_client(async_openai_client)
MODEL = "gpt-4o-mini"


async def handle_request(video_file, user_request, progress=gr.Progress()):
    if not video_file:
        return "Please upload a video file first!", None, None

    if not user_request or user_request.strip() == "":
        return "Please describe what you'd like to do with the video!", None, None

    progress(0.1, desc="Analyzing request...")
    video_path = video_file

    if not video_path or not os.path.exists(str(video_path)):
        return f"❌ Error: Invalid video file path: {video_path}", None, None

    progress(0.3, desc="Processing with AI...")
    message, output_files = await process_request(video_path, user_request, MODEL)

    progress(0.9, desc="Finalizing...")
    if output_files:
        if not isinstance(output_files, list):
            output_files = [output_files]

        video_output = None
        image_file = None

        for file_path in output_files:
            if os.path.exists(file_path):
                ext = Path(file_path).suffix.lower()
                if ext in [".jpg", ".png", ".jpeg"]:
                    image_file = file_path
                else:
                    video_output = file_path

        if image_file and video_output:
            return message, video_output, image_file
        if image_file:
            return message, None, image_file
        if video_output:
            return message, video_output, None

    return message, None, None


with gr.Blocks(title="AI Video Processor", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
    # 🎬 AI-Powered Video Processor (Agentic)
    Upload a video and describe what you want to do with it in natural language!

    **✨ Now with Multi-Step Intelligence:**

    **Simple requests:**
    - "Extract the audio as MP3"
    - "Resize to 720p"

    **Complex requests (agent executes multiple steps automatically):**
    - "Optimize this for Instagram" → Resize to 1080x1080 + Compress to <100MB
    - "Make this perfect for WhatsApp" → Resize to 720p + Compress to <16MB
    - "Prepare for email" → Compress + Resize to 480p + Verify size <25MB
    - "Get me a thumbnail and the audio" → Extract thumbnail + Extract audio
    """
    )

    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.Video(label="Upload Video", height=300)

            with gr.Accordion("📊 Quick Actions", open=False):
                gr.Markdown("Or use these preset commands:")
                quick_compress = gr.Button("🗜️ Compress (Medium Quality)")
                quick_audio = gr.Button("🎵 Extract Audio (MP3)")
                quick_720p = gr.Button("📺 Resize to 720p")

        with gr.Column(scale=1):
            request_input = gr.Textbox(
                label="What do you want to do?",
                placeholder="E.g., 'Make this video smaller and convert to WebM'",
                lines=3,
            )

            process_btn = gr.Button("✨ Process Video", variant="primary", size="lg")

            output_message = gr.Textbox(label="Result", lines=5)

            with gr.Row():
                output_video = gr.File(label="Output File")
                output_image = gr.Image(label="Thumbnail", visible=True)

    gr.Markdown(
        """
    ---
    ### 🛠️ Available Operations:
    - **Compress**: Reduce file size (low/medium/high quality)
    - **Extract Audio**: Get MP3, WAV, AAC, or FLAC
    - **Convert Format**: MP4, WebM, AVI, MOV, MKV, GIF
    - **Resize**: 480p, 720p, 1080p, 1440p, 4K
    - **Thumbnail**: Extract preview image

    ### 💡 Tips:
    - **Be goal-oriented**: "Make this ready for YouTube" (agent figures out the steps!)
    - **Mention platforms**: The agent knows Instagram, YouTube, WhatsApp, Email requirements
    - **Combine operations**: "Compress and resize to 720p" or "Get thumbnail and audio"
    - **The agent is autonomous**: It will execute multiple steps automatically until your goal is met
    - All processing happens locally - your files stay private!
    """
    )

    process_btn.click(
        fn=handle_request,
        inputs=[video_input, request_input],
        outputs=[output_message, output_video, output_image],
    )

    quick_compress.click(
        fn=lambda v: "Compress this video to medium quality",
        inputs=[],
        outputs=[request_input],
    ).then(
        fn=handle_request,
        inputs=[video_input, request_input],
        outputs=[output_message, output_video, output_image],
    )

    quick_audio.click(
        fn=lambda: "Extract the audio as high quality MP3",
        inputs=[],
        outputs=[request_input],
    ).then(
        fn=handle_request,
        inputs=[video_input, request_input],
        outputs=[output_message, output_video, output_image],
    )

    quick_720p.click(
        fn=lambda: "Resize this video to 720p",
        inputs=[],
        outputs=[request_input],
    ).then(
        fn=handle_request,
        inputs=[video_input, request_input],
        outputs=[output_message, output_video, output_image],
    )


if __name__ == "__main__":
    import subprocess

    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg found!")
    except Exception:
        print("❌ FFmpeg not found! Please install FFmpeg first.")
        print("   MacOS: brew install ffmpeg")
        print("   Ubuntu: sudo apt install ffmpeg")
        print("   Windows: Download from ffmpeg.org")
        raise SystemExit(1)

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )
