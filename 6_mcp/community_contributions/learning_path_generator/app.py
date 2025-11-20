"""
Gradio UI for Learning Path Generator

Provides a simple interface to generate and view learning paths.
"""

import gradio as gr
import asyncio
from path_generator import generate_learning_path
from learning_data import get_path, get_all_paths, mark_step_completed, get_path_progress
import json


def format_path_display(path_data: dict) -> str:
    """Format path data for display in Gradio as HTML."""
    if not path_data:
        return "<p>No path data available.</p>"
    
    output = f"<h1>{path_data.get('goal', 'Learning Path')}</h1>\n"
    output += f"<p><strong>Level:</strong> {path_data.get('level', 'N/A')}</p>\n"
    output += f"<p><strong>Status:</strong> {path_data.get('status', 'unknown')}</p>\n"
    
    progress = get_path_progress(path_data.get('path_id', ''))
    if progress:
        output += f"<p><strong>Progress:</strong> {progress.get('completed_count', 0)}/{progress.get('total_steps', 0)} steps completed "
        output += f"({progress.get('progress_percentage', 0):.1f}%)</p>\n"
    
    steps = path_data.get('steps', [])
    if steps:
        output += "<h2>Learning Steps</h2>\n"
        for idx, step in enumerate(steps, 1):
            completed = "✓" if step.get('completed', False) else "○"
            output += f"<h3>{completed} Step {idx}: {step.get('title', 'Untitled')}</h3>\n"
            
            if step.get('description'):
                output += f"<p>{step.get('description')}</p>\n"
            
            if step.get('estimated_time'):
                output += f"<p><strong>Estimated time:</strong> {step.get('estimated_time')}</p>\n"
            
            resources = step.get('resources', [])
            if resources:
                output += "<p><strong>Resources:</strong></p>\n<ul>\n"
                for resource in resources:
                    title = resource.get('title', 'Untitled')
                    url = resource.get('url', '#')
                    resource_type = resource.get('type', 'link')
                    # Ensure URL is absolute
                    if url and not url.startswith(('http://', 'https://')):
                        url = f"https://{url}"
                    # Use HTML link with target="_blank" to open in new tab
                    output += f"<li><a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">{title}</a> ({resource_type})</li>\n"
                output += "</ul>\n"
            output += "<br>\n"
    else:
        output += "<p>Path is being generated... Please wait.</p>\n"
    
    return output


async def generate_path_async(goal: str, level: str):
    """Async wrapper for path generation."""
    try:
        print(f"Starting path generation for: {goal} ({level})")
        result = await generate_learning_path(goal, level)
        path_id = result.get('path_id')
        trace_url = result.get('trace_url', '')
        
        print(f"Generation complete. Path ID: {path_id}, Trace: {trace_url}")
        
        # Wait a bit and check if path was updated
        await asyncio.sleep(2)
        
        if path_id:
            path = get_path(path_id)
            if path:
                status = path.get('status', 'unknown')
                if status == 'ready' and path.get('steps'):
                    display_text = format_path_display(path)
                    if trace_url:
                        display_text += f"<p><a href=\"{trace_url}\" target=\"_blank\">View Trace</a></p>"
                    return display_text, path_id
                else:
                    # Path exists but not ready yet
                    return f"<p>Path {path_id} is being generated. Status: {status}</p><p>Please wait a moment and click 'Load Path' with the Path ID: <code>{path_id}</code></p><p><a href=\"{trace_url}\" target=\"_blank\">View Trace</a></p>", path_id
            else:
                return f"<p>Path {path_id} was created but not found in storage. Please try again.</p><p><a href=\"{trace_url}\" target=\"_blank\">View Trace</a></p>", path_id
        else:
            # Fallback: find most recent path
            all_paths = get_all_paths()
            latest_path = None
            latest_time = None
            for pid, path in all_paths.items():
                if path.get('goal', '').lower() == goal.lower() and path.get('level') == level:
                    created_at = path.get('created_at', '')
                    if not latest_time or created_at > latest_time:
                        latest_time = created_at
                        latest_path = (pid, path)
            
            if latest_path:
                pid, path = latest_path
                display_text = format_path_display(path)
                if trace_url:
                    display_text += f"<p><a href=\"{trace_url}\" target=\"_blank\">View Trace</a></p>"
                return display_text, pid
            else:
                error_msg = f"<p>Path generation completed but no path found.</p>"
                error_msg += f"<p>Agent output: {result.get('result', 'No output')[:500]}</p>"
                if trace_url:
                    error_msg += f"<p><a href=\"{trace_url}\" target=\"_blank\">View Trace</a></p>"
                return error_msg, ""
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"<p>Error generating path: {str(e)}</p><p>Details:</p><pre>{error_detail}</pre>", ""


def generate_path_sync(goal: str, level: str):
    """Synchronous wrapper for Gradio."""
    return asyncio.run(generate_path_async(goal, level))


def load_path_display(path_id: str):
    """Load and display a path by ID."""
    if not path_id:
        return "<p>Please enter a path ID or generate a new path.</p>"
    
    path = get_path(path_id)
    if path:
        return format_path_display(path)
    else:
        return f"<p>Path {path_id} not found.</p>"


def mark_step_complete_sync(path_id: str, step_id: str):
    """Mark a step as completed."""
    try:
        if not path_id or not step_id:
            return "<p>Please provide both path_id and step_id.</p>"
        
        result = mark_step_completed(path_id, step_id)
        path = get_path(path_id)
        if path:
            return format_path_display(path)
        else:
            return f"<p>Step marked complete: {result}</p>"
    except Exception as e:
        return f"<p>Error: {str(e)}</p>"


def list_paths():
    """List all available paths."""
    all_paths = get_all_paths()
    if not all_paths:
        return "<p>No learning paths created yet.</p>"
    
    output = "<h2>Available Learning Paths</h2>\n"
    for path_id, path in all_paths.items():
        goal = path.get('goal', 'Untitled')
        level = path.get('level', 'N/A')
        status = path.get('status', 'unknown')
        progress = get_path_progress(path_id)
        progress_pct = progress.get('progress_percentage', 0)
        
        output += f"<h3>{goal} ({level})</h3>\n"
        output += f"<ul>\n"
        output += f"<li><strong>Path ID:</strong> <code>{path_id}</code></li>\n"
        output += f"<li><strong>Status:</strong> {status}</li>\n"
        output += f"<li><strong>Progress:</strong> {progress_pct:.1f}%</li>\n"
        output += f"</ul>\n<br>\n"
    
    return output


# Create Gradio interface
with gr.Blocks(title="Learning Path Generator") as demo:
    gr.Markdown(
        """
        # 🎓 Learning Path Generator
        
        Generate personalized learning paths dynamically by searching for the best free resources online.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=2):
            goal_input = gr.Textbox(
                label="What do you want to learn?",
                placeholder="e.g., Learn Python, Web Development, Machine Learning",
                lines=2
            )
            level_dropdown = gr.Dropdown(
                choices=["beginner", "intermediate", "advanced"],
                value="beginner",
                label="Experience Level"
            )
            generate_btn = gr.Button("Generate Learning Path", variant="primary")
            status_text = gr.Markdown("", visible=False)
            path_display = gr.HTML(label="Learning Path")
        
        with gr.Column(scale=1):
            gr.Markdown("### Path Management")
            
            path_id_input = gr.Textbox(
                label="Path ID",
                placeholder="Enter path ID to load"
            )
            load_path_btn = gr.Button("Load Path")
            
            gr.Markdown("### Progress Tracking")
            step_id_input = gr.Textbox(
                label="Step ID",
                placeholder="e.g., step-1"
            )
            mark_complete_btn = gr.Button("Mark Step Complete")
            
            gr.Markdown("### All Paths")
            list_paths_btn = gr.Button("List All Paths")
            paths_list = gr.HTML()
    
    # Event handlers
    generate_btn.click(
        fn=lambda goal, level: ("<p>⏳ Generating learning path... This may take 30-60 seconds. Please wait...</p>", ""),
        inputs=[goal_input, level_dropdown],
        outputs=[path_display, path_id_input]
    ).then(
        fn=generate_path_sync,
        inputs=[goal_input, level_dropdown],
        outputs=[path_display, path_id_input]
    )
    
    load_path_btn.click(
        fn=load_path_display,
        inputs=[path_id_input],
        outputs=[path_display]
    )
    
    mark_complete_btn.click(
        fn=mark_step_complete_sync,
        inputs=[path_id_input, step_id_input],
        outputs=[path_display]
    )
    
    list_paths_btn.click(
        fn=list_paths,
        outputs=[paths_list]
    )


if __name__ == "__main__":
    demo.launch()

