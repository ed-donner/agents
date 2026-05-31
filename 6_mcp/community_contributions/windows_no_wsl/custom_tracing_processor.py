"""Custom Tracing Processor for capturing and saving trace events."""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
from agents.tracing import TracingProcessor


class CustomTraceProcessor(TracingProcessor):
    """
    A tracing processor that collects all trace and span events,
    organizing them by trace name, and saves them to a JSON file on shutdown.
    """
    
    def __init__(self, output_dir: str = "sandbox"):
        super().__init__()
        # Dictionary to store traces organized by trace id
        # Structure: {trace_id: {"name": str, "start": dict, "end": dict, "children": [], "filename": str, "start_time": str}}
        # Children are stored hierarchically, each child has its own "children" array
        self.traces: Dict[str, Dict[str, Any]] = {}
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _get_trace_id(self, trace_export: dict) -> str:
        """Extract trace_id from trace data."""
        return trace_export.get("id", "unknown_trace_id")
    
    def _get_trace_name(self, trace_export: dict) -> str:
        """Extract trace name from trace data."""
        return trace_export.get("name", "unknown_trace")
    
    def _find_span_in_tree(self, span_id: str, children: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recursively find a span by id in the children tree."""
        for child in children:
            if child["id"] == span_id:
                return child
            # Recursively search in this child's children
            if "children" in child:
                result = self._find_span_in_tree(span_id, child["children"])
                if result:
                    return result
        return None
    
    def _find_parent_for_span(self, parent_id: str, trace_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find the children array where a new span should be added."""
        if not parent_id or parent_id == trace_info["id"]:
            # Direct child of trace
            return trace_info["children"]
        
        # Find the parent span in the tree
        parent_span = self._find_span_in_tree(parent_id, trace_info["children"])
        if parent_span:
            if "children" not in parent_span:
                parent_span["children"] = []
            return parent_span["children"]
        
        # Fallback: add to trace's direct children
        return trace_info["children"]
    
    def _find_trace_for_span(self, span_export: dict) -> str:
        """Find which trace a span belongs to by checking trace_id."""
        trace_id = span_export.get("trace_id")
        
        # Match by trace_id
        if trace_id and trace_id in self.traces:
            return trace_id
        
        # If no match found, try to find any active trace (fallback)
        if self.traces:
            return list(self.traces.keys())[-1]
        
        return "unknown_trace_id"
    
    def on_trace_start(self, trace):
        """Called when a trace starts."""
        trace_export = trace.export()
        id = self._get_trace_id(trace_export)
        trace_name = self._get_trace_name(trace_export)
        workflow_name = trace_export.get("workflow_name")
        
        # Initialize trace storage if this is a new trace
        if id not in self.traces:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Use workflow_name if available, otherwise trace_name
            name_for_file = workflow_name if workflow_name else trace_name
            filename = os.path.join(self.output_dir, f"{name_for_file}-{timestamp}.json")
            self.traces[id] = {
                "id": id,
                "name": trace_name,
                "workflow_name": workflow_name,
                "start": trace_export,
                "end": None,
                "children": [],  # Direct children spans of this trace
                "filename": filename,
                "start_time": timestamp
            }
        
        print(f"on_trace_start: {trace_export}")
    
    def on_trace_end(self, trace):
        """Called when a trace ends."""
        trace_export = trace.export()
        id = self._get_trace_id(trace_export)
        
        # Update trace data with end information
        if id in self.traces:
            self.traces[id]["end"] = trace_export
            print(f"on_trace_end:   {trace_export}")
            
            # Save the trace to disk immediately
            self._save_trace(id)
    
    def on_span_start(self, span):
        """Called when a span starts."""
        span_export = span.export()
        trace_id = self._find_trace_for_span(span_export)
        id = span_export.get("id")
        parent_id = span_export.get("parent_id")
        
        # Initialize trace storage if needed (edge case)
        if trace_id not in self.traces:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"unknown_trace-{timestamp}.json")
            self.traces[trace_id] = {
                "id": trace_id,
                "name": "unknown_trace",
                "workflow_name": None,
                "start": {},
                "end": None,
                "children": [],
                "filename": filename,
                "start_time": timestamp
            }
        
        # Create the span node
        span_node = {
            "id": id,
            "parent_id": parent_id,
            "start": span_export
        }
        
        # Find where to add this span
        parent_children = self._find_parent_for_span(parent_id, self.traces[trace_id])
        parent_children.append(span_node)
        
        print(f"on_span_start: {span_export}")
    
    def on_span_end(self, span):
        """Called when a span ends."""
        span_export = span.export()
        trace_id = self._find_trace_for_span(span_export)
        id = span_export.get("id")
        
        # Find and update the span with end data
        if trace_id in self.traces:
            span_node = self._find_span_in_tree(id, self.traces[trace_id]["children"])
            if span_node:
                span_node["end"] = span_export
            print(f"on_span_end: {span_export}")
    
    def force_flush(self):
        """Flush any buffered events."""
        self._save_all_traces()
        return super().force_flush()
    
    def shutdown(self):
        """Save all collected events to files when shutting down."""
        print("\n=== CustomTraceProcessor Shutdown ===")
        self._save_all_traces()
        print("=== Trace files saved ===\n")
        return super().shutdown()
    
    def _save_all_traces(self):
        """Save all traces to their respective JSON files with hierarchical structure."""
        for trace_id in list(self.traces.keys()):
            self._save_trace(trace_id)
    
    def _save_trace(self, trace_id: str):
        """Save a single trace to its JSON file."""
        if trace_id not in self.traces:
            return
        
        trace_info = self.traces[trace_id]
        filename = trace_info["filename"]
        
        # Create JSON representation of the trace structure
        trace_output = {
            "id": trace_info["id"],
            "name": trace_info["name"],
            "workflow_name": trace_info["workflow_name"],
            "start_time": trace_info["start_time"],
            "start": trace_info["start"],
            "children": trace_info["children"]
        }
        
        # Add end data if it exists
        if trace_info["end"]:
            trace_output["end"] = trace_info["end"]
        
        # Count total spans
        total_spans = self._count_spans(trace_info["children"])
        trace_output["total_spans"] = total_spans
        
        # Save to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(trace_output, f, indent=2, ensure_ascii=False)
            display_name = trace_info["workflow_name"] or trace_info["name"]
            print(f"Saved trace '{display_name}' with {total_spans} spans to {filename}")
        except Exception as e:
            print(f"Error saving {filename}: {e}")
    
    def _count_spans(self, children: List[Dict[str, Any]]) -> int:
        """Recursively count total number of spans in the tree."""
        count = len(children)
        for child in children:
            if "children" in child:
                count += self._count_spans(child["children"])
        return count
