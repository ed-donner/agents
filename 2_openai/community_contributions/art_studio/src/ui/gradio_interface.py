"""
Simplified Gradio Interface for AI Visual Art Studio IDE
Single prompt input that automatically triggers Concept Artist and delegation flow
"""

import gradio as gr
import asyncio
from typing import Dict, Generator
from datetime import datetime

from ..core.art_studio import ArtStudio


def create_gradio_interface(art_studio: ArtStudio):
    """Create a simplified Gradio interface with automatic delegation flow"""
    

    
    # Create the Gradio interface with better styling
    with gr.Blocks(
        title="AI Visual Art Studio IDE",
        theme=gr.themes.Soft(),
        css="""
        .status-completed {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .pipeline-summary {
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #4CAF50;
        }
        
        .final-result {
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #FF9800;
        }
        
        .next-steps {
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #2196F3;
        }
        
        .agent-section {
            background: rgba(255,255,255,0.95);
            color: #333;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #9C27B0;
        }
        
        .agent-section h4 {
            margin: 0 0 1rem 0;
            color: #673AB7;
            font-size: 1.2rem;
        }
        
        .agent-output {
            line-height: 1.6;
            font-size: 0.95rem;
        }
        
        .markdown-content h5 {
            color: #E91E63;
            margin: 1rem 0 0.5rem 0;
            font-size: 1.1rem;
        }
        
        .markdown-content h6 {
            color: #FF5722;
            margin: 0.8rem 0 0.4rem 0;
            font-size: 1rem;
        }
        
        .markdown-content strong {
            color: #3F51B5;
        }
        
        .markdown-content li {
            margin: 0.3rem 0;
            padding-left: 0.5rem;
        }
        
        .status-running {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
            font-size: 1.1rem;
        }
        
        h2, h3 {
            margin: 0 0 1rem 0;
            text-align: center;
        }
        
        ul {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }
        
        li {
            margin: 0.3rem 0;
        }
        """
    ) as interface:
        
        gr.Markdown("# 🎨 AI Visual Art Studio IDE")
        gr.Markdown("Enter your creative vision and watch AI agents collaborate automatically")
        
        with gr.Column():
            # Single prompt input
            with gr.Group():
                gr.Markdown("## 🚀 Creative Vision")
                prompt_input = gr.Textbox(
                    label="Describe what you want to create",
                    placeholder="e.g., Design a magical forest scene with glowing mushrooms and fairy lights...",
                    lines=4,
                    max_lines=6
                )
                
                execute_btn = gr.Button(
                    "🎬 Create with AI Agents", 
                    variant="primary", 
                    size="lg"
                )
            
            # Progress bar at the top
            with gr.Group():
                gr.Markdown("## 📊 AI Agent Pipeline Progress")
                progress_status = gr.Markdown(
                    value="**Ready to create!** Enter your vision above.",
                    label="Current Status"
                )
                step_counter = gr.Markdown(
                    value="**Pipeline Steps:** 0/5",
                    label="Step Progress"
                )
            
            # Results in organized tabs
            with gr.Group():
                gr.Markdown("## 🎉 Creation Results")
                
                with gr.Tabs() as results_tabs:
                    # Concept Artist Tab
                    with gr.TabItem("🎨 Concept Artist", id=0):
                        concept_output = gr.Markdown(
                            value="Concept will appear here after generation.",
                            label="Creative Concept"
                        )
                    
                    # Sketch Artist Tab
                    with gr.TabItem("✏️ Sketch Artist", id=1):
                        sketch_output = gr.Markdown(
                            value="Sketch plan will appear here after generation.",
                            label="Visual Sketch Plan"
                        )
                    
                    # Refinement Artist Tab
                    with gr.TabItem("🔧 Refinement Artist", id=2):
                        refinement_output = gr.Markdown(
                            value="Refinement analysis will appear here after generation.",
                            label="Improvement Guidance"
                        )
                    
                    # Curator Tab
                    with gr.TabItem("📊 Curator", id=3):
                        curator_output = gr.Markdown(
                            value="Final evaluation will appear here after generation.",
                            label="Quality Assessment"
                        )
                    
                    # Art Generator Tab
                    with gr.TabItem("🎨 Art Generator", id=4):
                        art_generator_output = gr.Markdown(
                            value="Generated artwork will appear here after creation.",
                            label="AI-Generated Artwork"
                        )
                        # Add image display for generated artwork
                        artwork_image = gr.Image(
                            label="Generated Artwork",
                            visible=False
                        )
                        download_link = gr.Markdown(
                            value="",
                            label="Download Link",
                            visible=False
                        )
                    
                    # Summary Tab
                    with gr.TabItem("📋 Summary", id=5):
                        summary_output = gr.Markdown(
                            value="Complete pipeline summary will appear here.",
                            label="Pipeline Summary"
                        )
        
        # Event handler with automatic delegation flow
        def execute_automatic_delegation(prompt: str) -> Generator[tuple, None, None]:
            """Execute automatic delegation flow starting with Concept Artist"""
            
            if not prompt.strip():
                yield (
                    "**Please enter your creative vision to begin.**",
                    "**Pipeline Steps:** 0/5",
                    gr.update(selected=0),
                    gr.update(value="Ready to create!"),
                    gr.update(value="Sketch plan will appear here after generation."),
                    gr.update(value="Refinement analysis will appear here after generation."),
                    gr.update(value="Final evaluation will appear here after generation."),
                    gr.update(value="Generated artwork will appear here after creation."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Complete pipeline summary will appear here.")
                )
                return
            
            try:
                # Initial status
                yield (
                    "🚀 **Starting creative process with Concept Artist...**",
                    "**Pipeline Steps:** 1/5 - Concept Artist",
                    gr.update(selected=0),
                    gr.update(value="Initializing..."),
                    gr.update(value="Waiting for concept..."),
                    gr.update(value="Waiting for sketch..."),
                    gr.update(value="Waiting for evaluation..."),
                    gr.update(value="Waiting for artwork generation..."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Pipeline will start soon...")
                )
                
                # Step 1: Concept Artist
                yield (
                    "📝 **Step 1: Concept Artist generating concept...**",
                    "**Pipeline Steps:** 1/5 - Concept Artist Working",
                    gr.update(selected=0),
                    gr.update(value="🎨 **Generating creative concept...**\n\nPlease wait while the AI creates your vision."),
                    gr.update(value="Waiting for concept..."),
                    gr.update(value="Waiting for sketch..."),
                    gr.update(value="Waiting for evaluation..."),
                    gr.update(value="Waiting for artwork generation..."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Step 1/5: Concept Artist working...")
                )
                
                # Execute Concept Artist (using asyncio.run in a separate thread)
                import threading
                import queue
                
                result_queue = queue.Queue()
                
                def run_concept_artist():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(art_studio.execute_agent("concept_artist", prompt))
                        result_queue.put(result)
                    except Exception as e:
                        result_queue.put({"error": str(e)})
                
                thread = threading.Thread(target=run_concept_artist)
                thread.start()
                thread.join()
                concept_result = result_queue.get()
                
                if "error" in concept_result:
                    raise Exception(concept_result["error"])
                
                # Show Concept Artist result
                yield (
                    "✅ **Concept Artist completed!** Moving to Sketch Artist...",
                    "**Pipeline Steps:** 1/5 - Concept Artist ✅ Completed",
                    gr.update(selected=0),
                    gr.update(value=concept_result['output']),
                    gr.update(value="Waiting for concept..."),
                    gr.update(value="Waiting for sketch..."),
                    gr.update(value="Waiting for evaluation..."),
                    gr.update(value="Waiting for artwork generation..."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Step 1/5: Concept Artist ✅ Completed")
                )
                
                # Step 2: Sketch Artist
                yield (
                    "✏️ **Step 2: Sketch Artist creating sketch...**",
                    "**Pipeline Steps:** 2/5 - Sketch Artist",
                    gr.update(selected=1),
                    gr.update(value=concept_result['output']),
                    gr.update(value="✏️ **Creating visual sketch plan...**\n\nPlease wait while the AI develops the sketch."),
                    gr.update(value="Waiting for sketch..."),
                    gr.update(value="Waiting for evaluation..."),
                    gr.update(value="Waiting for artwork generation..."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Step 2/5: Sketch Artist working...")
                )
                
                # Execute Sketch Artist
                def run_sketch_artist():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(art_studio.execute_agent("sketch_artist", concept_result['output']))
                        result_queue.put(result)
                    except Exception as e:
                        result_queue.put({"error": str(e)})
                
                thread = threading.Thread(target=run_sketch_artist)
                thread.start()
                thread.join()
                sketch_result = result_queue.get()
                
                if "error" in sketch_result:
                    raise Exception(sketch_result["error"])
                
                # Show Sketch Artist result
                yield (
                    "✅ **Sketch Artist completed!** Moving to Refinement Artist...",
                    "**Pipeline Steps:** 2/5 - Sketch Artist ✅ Completed",
                    gr.update(selected=1),
                    gr.update(value=concept_result['output']),
                    gr.update(value=sketch_result['output']),
                    gr.update(value="Waiting for sketch..."),
                    gr.update(value="Waiting for evaluation..."),
                    gr.update(value="Waiting for artwork generation..."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Step 2/5: Sketch Artist ✅ Completed")
                )
                
                # Step 3: Refinement Artist
                yield (
                    "🔧 **Step 3: Refinement Artist refining artwork...**",
                    "**Pipeline Steps:** 3/5 - Refinement Artist",
                    gr.update(selected=2),
                    gr.update(value=concept_result['output']),
                    gr.update(value=sketch_result['output']),
                    gr.update(value="🔧 **Analyzing and refining artwork...**\n\nPlease wait while the AI provides improvement guidance."),
                    gr.update(value="Waiting for evaluation..."),
                    gr.update(value="Waiting for artwork generation..."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Step 3/5: Refinement Artist working...")
                )
                
                # Execute Refinement Artist
                def run_refinement_artist():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(art_studio.execute_agent("refinement_artist", sketch_result['output']))
                        result_queue.put(result)
                    except Exception as e:
                        result_queue.put({"error": str(e)})
                
                thread = threading.Thread(target=run_refinement_artist)
                thread.start()
                thread.join()
                refinement_result = result_queue.get()
                
                if "error" in refinement_result:
                    raise Exception(refinement_result["error"])
                
                # Show Refinement Artist result
                yield (
                    "✅ **Refinement Artist completed!** Moving to Curator...",
                    "**Pipeline Steps:** 3/5 - Refinement Artist ✅ Completed",
                    gr.update(selected=2),
                    gr.update(value=concept_result['output']),
                    gr.update(value=sketch_result['output']),
                    gr.update(value=refinement_result['output']),
                    gr.update(value="Waiting for evaluation..."),
                    gr.update(value="Waiting for artwork generation..."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Step 3/5: Refinement Artist ✅ Completed")
                )
                
                # Step 4: Curator
                yield (
                    "📊 **Step 4: Curator evaluating artwork...**",
                    "**Pipeline Steps:** 4/5 - Curator",
                    gr.update(selected=3),
                    gr.update(value=concept_result['output']),
                    gr.update(value=sketch_result['output']),
                    gr.update(value=refinement_result['output']),
                    gr.update(value="📊 **Evaluating artwork quality...**\n\nPlease wait while the AI provides final assessment."),
                    gr.update(value="Waiting for artwork generation..."),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value="Step 4/5: Curator working...")
                )
                
                # Execute Curator
                def run_curator():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(art_studio.execute_agent("curator", refinement_result['output']))
                        result_queue.put(result)
                    except Exception as e:
                        result_queue.put({"error": str(e)})
                
                thread = threading.Thread(target=run_curator)
                thread.start()
                thread.join()
                curator_result = result_queue.get()
                
                if "error" in curator_result:
                    raise Exception(curator_result["error"])
                
                # Check if Curator rating is above 7/10 before proceeding to Art Generator
                curator_rating = art_studio._extract_curator_rating(curator_result['output'])
                
                if curator_rating >= 7.0:
                    # Show Curator result and proceed to Art Generator
                    yield (
                        "✅ **Curator completed!** Rating: {}/10 - Proceeding to Art Generator...".format(curator_rating),
                        "**Pipeline Steps:** 4/5 - Curator ✅ Completed (Rating: {}/10)".format(curator_rating),
                        gr.update(selected=3),
                        gr.update(value=concept_result['output']),
                        gr.update(value=sketch_result['output']),
                        gr.update(value=refinement_result['output']),
                        gr.update(value=curator_result['output']),
                        gr.update(value="Waiting for artwork generation..."),
                        gr.update(visible=False),
                        gr.update(value="", visible=False),
                        gr.update(value="Step 4/5: Curator ✅ Completed - Quality threshold met!")
                    )
                    
                    # Step 5: Art Generator
                    yield (
                        "🎨 **Step 5: Art Generator creating artwork...**",
                        "**Pipeline Steps:** 5/5 - Art Generator",
                        gr.update(selected=4),
                        gr.update(value=concept_result['output']),
                        gr.update(value=sketch_result['output']),
                        gr.update(value=refinement_result['output']),
                        gr.update(value=curator_result['output']),
                        gr.update(value="🎨 **Generating actual artwork...**\n\nPlease wait while DALL-E creates your visual masterpiece."),
                        gr.update(visible=False),
                        gr.update(value="", visible=False),
                        gr.update(value="Step 5/5: Art Generator working...")
                    )
                    
                    # Execute Art Generator with all the context
                    def run_art_generator():
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            result = loop.run_until_complete(art_studio._generate_ai_artwork(
                                concept_result['output'],
                                sketch_result['output'], 
                                refinement_result['output']
                            ))
                            result_queue.put(result)
                        except Exception as e:
                            result_queue.put({"error": str(e)})
                    
                    thread = threading.Thread(target=run_art_generator)
                    thread.start()
                    thread.join()
                    art_result = result_queue.get()
                    
                    if "error" in art_result:
                        raise Exception(art_result["error"])
                    
                    # Extract image URL and display artwork
                    import re
                    image_url_match = re.search(r'\*\*Image URL:\*\* (https?://[^\s]+)', art_result)
                    image_url = image_url_match.group(1) if image_url_match else None
                    
                    # Create download link
                    download_md = f"""
                    ## 📥 Download Your Artwork
                    
                    **Direct Link:** [Click here to download]({image_url}) if image doesn't display
                    
                    **Right-click** on the image above and select "Save image as..." to download
                    """ if image_url else "No image URL found in the result."
                    
                    # Show final completion with artwork
                    summary_md = f"""
                    # 🎉 Your Creative Vision Has Been Realized!

                    ## 🔄 AI Agents Collaboration Summary
                    - **Total Steps:** 5
                    - **Pipeline:** Concept Artist → Sketch Artist → Refinement Artist → Curator → Art Generator
                    - **Status:** ✅ All agents completed successfully!
                    - **Quality Gate:** ✅ Passed (Curator Rating: {curator_rating}/10)

                    ## 📋 Pipeline Overview

                    ### 🎨 Concept Artist
                    - **Status:** ✅ Completed
                    - **Output:** Creative concept and artistic direction

                    ### ✏️ Sketch Artist  
                    - **Status:** ✅ Completed
                    - **Output:** Detailed sketch plan and composition

                    ### 🔧 Refinement Artist
                    - **Status:** ✅ Completed
                    - **Output:** Improvement guidance and technical refinements

                    ### 📊 Curator
                    - **Status:** ✅ Completed
                    - **Output:** Final quality assessment and recommendations
                    - **Rating:** {curator_rating}/10 ✅ **Quality threshold met!**

                    ### 🎨 Art Generator
                    - **Status:** ✅ Completed
                    - **Output:** Actual AI-generated artwork ready for download

                    ## 🚀 Next Steps
                    Your artwork concept is ready for production! The AI agents have provided:
                    - 🎨 Creative concept and artistic direction
                    - ✏️ Detailed sketch plan and composition  
                    - 🔧 Refinement guidance and improvements
                    - 📊 Quality evaluation and recommendations
                    - 🎨 **Actual generated artwork** ready for use

                    **🎯 Ready to proceed with your creative project!**
                    """
                    
                    yield (
                        "🎉 **All agents completed successfully!** Check the Art Generator tab for your artwork!",
                        "**Pipeline Steps:** 5/5 - All Agents ✅ Completed",
                        gr.update(selected=4),
                        gr.update(value=concept_result['output']),
                        gr.update(value=sketch_result['output']),
                        gr.update(value=refinement_result['output']),
                        gr.update(value=curator_result['output']),
                        gr.update(value=art_result),
                        gr.update(value=image_url, visible=True) if image_url else gr.update(visible=False),
                        gr.update(value=download_md, visible=True),
                        gr.update(value=summary_md)
                    )
                    
                else:
                    # Quality threshold not met - skip Art Generator
                    yield (
                        "⚠️ **Curator completed!** Rating: {}/10 - Quality threshold not met for artwork generation.".format(curator_rating),
                        "**Pipeline Steps:** 4/5 - Curator ✅ Completed (Rating: {}/10) - Art Generation Skipped".format(curator_rating),
                        gr.update(selected=3),
                        gr.update(value=concept_result['output']),
                        gr.update(value=sketch_result['output']),
                        gr.update(value=refinement_result['output']),
                        gr.update(value=curator_result['output']),
                        gr.update(value="⚠️ **Art Generation Skipped**\n\nCurator Rating: {}/10\nQuality threshold (7/10) not met.\n\nPlease refine your concept and try again.".format(curator_rating)),
                        gr.update(visible=False),
                        gr.update(value="", visible=False),
                        gr.update(value="Step 4/5: Curator ✅ Completed - Quality threshold not met")
                    )
                    
                    # Show completion without artwork
                    summary_md = f"""
                    # ⚠️ Creative Process Completed - Quality Threshold Not Met

                    ## 🔄 AI Agents Collaboration Summary
                    - **Total Steps:** 4 (Art Generation Skipped)
                    - **Pipeline:** Concept Artist → Sketch Artist → Refinement Artist → Curator
                    - **Status:** ⚠️ Completed but quality threshold not met
                    - **Quality Gate:** ❌ Failed (Curator Rating: {curator_rating}/10)

                    ## 📋 Pipeline Overview

                    ### 🎨 Concept Artist
                    - **Status:** ✅ Completed
                    - **Output:** Creative concept and artistic direction

                    ### ✏️ Sketch Artist  
                    - **Status:** ✅ Completed
                    - **Output:** Detailed sketch plan and composition

                    ### 🔧 Refinement Artist
                    - **Status:** ✅ Completed
                    - **Output:** Improvement guidance and technical refinements

                    ### 📊 Curator
                    - **Status:** ✅ Completed
                    - **Output:** Final quality assessment and recommendations
                    - **Rating:** {curator_rating}/10 ❌ **Quality threshold not met**

                    ### 🎨 Art Generator
                    - **Status:** ⏭️ Skipped
                    - **Reason:** Quality threshold (7/10) not met
                    - **Output:** No artwork generated

                    ## 🔧 Next Steps
                    To generate artwork, you need to:
                    1. **Review the Curator's feedback** in the Curator tab
                    2. **Refine your concept** based on the feedback
                    3. **Try again** with an improved prompt
                    4. **Aim for a Curator rating above 7/10**

                    **💡 Tip:** Focus on the areas the Curator identified for improvement.
                    """
                    
                    yield (
                        "⚠️ **Process completed but quality threshold not met.** Check Curator tab for feedback.",
                        "**Pipeline Steps:** 4/5 - Quality Gate Failed - Art Generation Skipped",
                        gr.update(selected=3),
                        gr.update(value=concept_result['output']),
                        gr.update(value=sketch_result['output']),
                        gr.update(value=refinement_result['output']),
                        gr.update(value=curator_result['output']),
                        gr.update(value="⚠️ **Art Generation Skipped**\n\nCurator Rating: {}/10\nQuality threshold (7/10) not met.\n\nPlease refine your concept and try again.".format(curator_rating)),
                        gr.update(visible=False),
                        gr.update(value="", visible=False),
                        gr.update(value=summary_md)
                    )
                    
            except Exception as e:
                error_md = f"""
                ❌ **Error during creation:** {str(e)}
                
                Please try again or check your configuration.
                """
                yield (
                    error_md,
                    "**Pipeline Steps:** Error occurred",
                    gr.update(selected=0),
                    gr.update(value="Error occurred"),
                    gr.update(value="Error occurred"),
                    gr.update(value="Error occurred"),
                    gr.update(value="Error occurred"),
                    gr.update(value="Error occurred"),
                    gr.update(visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value=error_md)
                )
        
        # Connect the event handler
        execute_btn.click(
            fn=execute_automatic_delegation,
            inputs=[prompt_input],
            outputs=[progress_status, step_counter, results_tabs, concept_output, sketch_output, refinement_output, curator_output, art_generator_output, artwork_image, download_link, summary_output],
            show_progress=True
        )
        
        # Initialize interface
        print("✅ Simplified automatic delegation interface created successfully")
        return interface
