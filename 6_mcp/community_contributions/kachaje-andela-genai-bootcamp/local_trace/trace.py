from contextlib import contextmanager
import time
from pathlib import Path
from datetime import datetime, timezone
import uuid
import json
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field

try:
    from agents import TracingProcessor, Trace, Span as AgentsSpan, add_trace_processor, remove_trace_processor
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    TracingProcessor = None
    Trace = None
    AgentsSpan = None
    add_trace_processor = None
    remove_trace_processor = None


# Thread-local storage for tracking active spans
_thread_local = threading.local()

# Thread-local storage for span mapping (agents library span_id -> local trace span)
_thread_local.span_map = {}


@dataclass
class Span:
    """Represents a span in a trace."""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    status: str = "success"  # "success" or "error"
    error: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for JSON serialization."""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None and v != [] and v != {}}
    
    def add_result_metadata(self, result: Any):
        """Extract and add metadata from a Runner.run() result object."""
        extracted_metadata = _extract_metadata_from_result(result)
        self.attributes.update(extracted_metadata)


def _get_current_span() -> Optional[Span]:
    """Get the current active span from thread-local storage."""
    return getattr(_thread_local, 'current_span', None)


def _set_current_span(span: Optional[Span]):
    """Set the current active span in thread-local storage."""
    _thread_local.current_span = span


def _get_log_file_path() -> Path:
    """Get the log file path based on current date."""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"trace_{date_str}.log"


def _get_json_log_file_path() -> Path:
    """Get the JSON log file path based on current date."""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"trace_{date_str}.jsonl"


def _write_log(message: str):
    """Write a log message to the date-rotated log file."""
    try:
        log_file = _get_log_file_path()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {message}\n")
    except Exception:
        # Silently fail if logging fails to avoid breaking the trace functionality
        pass


def _write_json_log(span: Span):
    """Write a span as JSON to the JSON log file (JSONL format)."""
    try:
        log_file = _get_json_log_file_path()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(span.to_dict(), ensure_ascii=False) + "\n")
    except Exception:
        # Silently fail if logging fails to avoid breaking the trace functionality
        pass


def _extract_metadata_from_result(result: Any) -> Dict[str, Any]:
    """Extract metadata from Runner.run() result object."""
    metadata = {}
    
    if result is None:
        return metadata
    
    # Extract final_output
    if hasattr(result, 'final_output'):
        metadata['output'] = result.final_output
    
    # Extract messages if available
    if hasattr(result, 'messages'):
        messages = result.messages
        if messages:
            # Extract user inputs
            user_messages = [msg.get('content', '') for msg in messages if msg.get('role') == 'user']
            if user_messages:
                metadata['inputs'] = user_messages
            
            # Extract assistant messages
            assistant_messages = [msg.get('content', '') for msg in messages if msg.get('role') == 'assistant']
            if assistant_messages:
                metadata['assistant_responses'] = assistant_messages
    
    # Extract tool calls if available
    if hasattr(result, 'tool_calls') or hasattr(result, 'tool_call_items'):
        tool_calls = []
        # Try different attribute names
        tool_call_data = getattr(result, 'tool_calls', None) or getattr(result, 'tool_call_items', None)
        if tool_call_data:
            for tc in tool_call_data:
                tool_info = {}
                if hasattr(tc, 'name'):
                    tool_info['name'] = tc.name
                elif isinstance(tc, dict):
                    tool_info['name'] = tc.get('name', 'unknown')
                
                if hasattr(tc, 'arguments'):
                    tool_info['arguments'] = tc.arguments
                elif isinstance(tc, dict):
                    tool_info['arguments'] = tc.get('arguments', {})
                
                if hasattr(tc, 'result') or hasattr(tc, 'output'):
                    tool_info['result'] = getattr(tc, 'result', None) or getattr(tc, 'output', None)
                elif isinstance(tc, dict):
                    tool_info['result'] = tc.get('result') or tc.get('output')
                
                tool_calls.append(tool_info)
        
        if tool_calls:
            metadata['tool_calls'] = tool_calls
    
    # Extract token usage if available
    if hasattr(result, 'usage') or hasattr(result, 'token_usage'):
        usage = getattr(result, 'usage', None) or getattr(result, 'token_usage', None)
        if usage:
            token_counts = {}
            if hasattr(usage, 'prompt_tokens') or isinstance(usage, dict):
                token_counts['input_tokens'] = getattr(usage, 'prompt_tokens', None) or (usage.get('prompt_tokens') if isinstance(usage, dict) else None)
            if hasattr(usage, 'completion_tokens') or isinstance(usage, dict):
                token_counts['output_tokens'] = getattr(usage, 'completion_tokens', None) or (usage.get('completion_tokens') if isinstance(usage, dict) else None)
            if hasattr(usage, 'total_tokens') or isinstance(usage, dict):
                token_counts['total_tokens'] = getattr(usage, 'total_tokens', None) or (usage.get('total_tokens') if isinstance(usage, dict) else None)
            if token_counts:
                metadata['token_counts'] = token_counts
    
    # Extract model info if available
    if hasattr(result, 'model') or hasattr(result, 'model_info'):
        model_info = {}
        model_data = getattr(result, 'model', None) or getattr(result, 'model_info', None)
        if model_data:
            if isinstance(model_data, str):
                model_info['name'] = model_data
            elif hasattr(model_data, 'name'):
                model_info['name'] = model_data.name
            elif isinstance(model_data, dict):
                model_info.update(model_data)
        
        if model_info:
            metadata['model_info'] = model_info
    
    return metadata


class LocalTraceProcessor:
    """
    TracingProcessor that automatically creates child spans in local_trace
    when the agents library creates spans.
    
    This class implements the TracingProcessor interface from the agents library
    by providing on_span_start, on_span_end, on_trace_start, on_trace_end methods.
    """
    
    def __init__(self):
        # Thread-local mapping: agents library span_id -> local trace Span object
        self._span_map = {}
        self._lock = threading.Lock()
    
    def _get_span_map(self) -> Dict[str, Span]:
        """Get thread-local span mapping."""
        if not hasattr(_thread_local, 'span_map'):
            _thread_local.span_map = {}
        return _thread_local.span_map
    
    def _extract_span_name(self, agents_span: Any) -> str:
        """Extract a meaningful name from an agents library span."""
        name = "span"
        
        # Try to get name from span_data
        if hasattr(agents_span, 'span_data') and agents_span.span_data:
            span_data = agents_span.span_data
            
            # Try span_data.name first
            if hasattr(span_data, 'name') and span_data.name:
                name = span_data.name
            # Then try span_data.type
            elif hasattr(span_data, 'type') and span_data.type:
                name = span_data.type
            # Try to get tool name if it's a tool call
            elif hasattr(span_data, 'tool_name') and span_data.tool_name:
                name = f"tool:{span_data.tool_name}"
        
        # Fallback to span.name if available
        if name == "span" and hasattr(agents_span, 'name') and agents_span.name:
            name = agents_span.name
        
        return name
    
    def _extract_span_attributes(self, agents_span: Any) -> Dict[str, Any]:
        """Extract attributes from an agents library span."""
        attributes = {}
        
        if hasattr(agents_span, 'span_data') and agents_span.span_data:
            span_data = agents_span.span_data
            
            # Extract type
            if hasattr(span_data, 'type') and span_data.type:
                attributes['type'] = span_data.type
            
            # Extract tool information
            if hasattr(span_data, 'tool_name') and span_data.tool_name:
                attributes['tool_name'] = span_data.tool_name
            if hasattr(span_data, 'tool_arguments') and span_data.tool_arguments:
                attributes['tool_arguments'] = span_data.tool_arguments
            if hasattr(span_data, 'tool_result') and span_data.tool_result:
                attributes['tool_result'] = str(span_data.tool_result)[:500]  # Limit length
            
            # Extract server information
            if hasattr(span_data, 'server') and span_data.server:
                attributes['server'] = span_data.server
            
            # Extract model information
            if hasattr(span_data, 'model') and span_data.model:
                attributes['model'] = span_data.model
        
        # Extract error information
        if hasattr(agents_span, 'error') and agents_span.error:
            attributes['error'] = str(agents_span.error)
        
        return attributes
    
    def on_span_start(self, agents_span: Any) -> None:
        """Called when an agents library span starts. Create a corresponding local trace span."""
        # Check if we're inside a local_trace context
        current_span = _get_current_span()
        if current_span is None:
            # Not in a local_trace context, skip
            return
        
        # Extract span information
        span_name = self._extract_span_name(agents_span)
        span_attributes = self._extract_span_attributes(agents_span)
        
        # Get agents library span ID
        agents_span_id = getattr(agents_span, 'span_id', None) or str(id(agents_span))
        
        # Create a new local trace span
        local_span_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc).isoformat()
        
        new_span = Span(
            span_id=local_span_id,
            trace_id=current_span.trace_id,
            parent_span_id=current_span.span_id,
            name=span_name,
            start_time=start_time,
            attributes=span_attributes
        )
        
        # Store mapping (include parent for restoration)
        span_map = self._get_span_map()
        span_map[agents_span_id] = {
            'local_span': new_span,
            'start_time': start_time,
            'parent_span': current_span  # Store parent for restoration
        }
        
        # Set as current span (so nested spans will be children of this one)
        _set_current_span(new_span)
    
    def on_span_end(self, agents_span: Any) -> None:
        """Called when an agents library span ends. End the corresponding local trace span."""
        # Get agents library span ID
        agents_span_id = getattr(agents_span, 'span_id', None) or str(id(agents_span))
        
        # Get the mapped local span
        span_map = self._get_span_map()
        if agents_span_id not in span_map:
            return
        
        local_span_info = span_map[agents_span_id]
        local_span = local_span_info['local_span']
        
        # Update span with end time and duration
        end_time = datetime.now(timezone.utc).isoformat()
        start_time = datetime.fromisoformat(local_span_info['start_time'].replace('Z', '+00:00'))
        end_time_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration_ms = (end_time_dt - start_time).total_seconds() * 1000
        
        local_span.end_time = end_time
        local_span.duration_ms = round(duration_ms, 2)
        
        # Check for errors
        if hasattr(agents_span, 'error') and agents_span.error:
            local_span.status = "error"
            local_span.error = str(agents_span.error)
            if 'error' not in local_span.attributes:
                local_span.attributes['error'] = str(agents_span.error)
        
        # Update attributes with any final information
        final_attributes = self._extract_span_attributes(agents_span)
        local_span.attributes.update(final_attributes)
        
        # Restore parent span
        parent_span = local_span_info.get('parent_span')
        _set_current_span(parent_span)
        
        # Write the span to the log
        _write_json_log(local_span)
        
        # Remove from mapping
        del span_map[agents_span_id]
    
    def on_trace_start(self, trace: Any) -> None:
        """Called when an agents library trace starts."""
        # We don't need to do anything here since local_trace handles trace creation
        pass
    
    def on_trace_end(self, trace: Any) -> None:
        """Called when an agents library trace ends."""
        # Clean up any remaining spans in the mapping
        span_map = self._get_span_map()
        for agents_span_id, span_info in list(span_map.items()):
            local_span = span_info['local_span']
            if local_span.end_time is None:
                # Span wasn't properly ended, end it now
                end_time = datetime.now(timezone.utc).isoformat()
                start_time = datetime.fromisoformat(span_info['start_time'].replace('Z', '+00:00'))
                end_time_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration_ms = (end_time_dt - start_time).total_seconds() * 1000
                
                local_span.end_time = end_time
                local_span.duration_ms = round(duration_ms, 2)
                _write_json_log(local_span)
        
        # Clear the mapping
        span_map.clear()
    
    def force_flush(self) -> None:
        """Force flush any pending spans."""
        pass
    
    def shutdown(self) -> None:
        """Cleanup on shutdown."""
        span_map = self._get_span_map()
        span_map.clear()


# Global processor instance (will be registered per thread if needed)
_local_trace_processor = None
_processor_lock = threading.Lock()


def _get_local_trace_processor() -> Optional[LocalTraceProcessor]:
    """Get or create the local trace processor instance."""
    global _local_trace_processor
    if _local_trace_processor is None and AGENTS_AVAILABLE:
        with _processor_lock:
            if _local_trace_processor is None:
                _local_trace_processor = LocalTraceProcessor()
    return _local_trace_processor


@contextmanager
def span(name: str, trace_id: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Create a nested span within a trace.
    
    Args:
        name: Name of the span
        trace_id: Optional trace ID. If not provided, uses parent's trace_id or creates new one
        attributes: Optional metadata attributes to attach to the span
    """
    parent_span = _get_current_span()
    
    if trace_id is None:
        if parent_span:
            trace_id = parent_span.trace_id
        else:
            trace_id = str(uuid.uuid4())
    
    span_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc).isoformat()
    
    new_span = Span(
        span_id=span_id,
        trace_id=trace_id,
        parent_span_id=parent_span.span_id if parent_span else None,
        name=name,
        start_time=start_time,
        attributes=attributes or {}
    )
    
    _set_current_span(new_span)
    
    error_occurred = False
    error_message = None
    
    try:
        yield new_span
    except Exception as e:
        error_occurred = True
        error_message = str(e)
        new_span.status = "error"
        new_span.error = error_message
        raise
    finally:
        end_time = datetime.now(timezone.utc).isoformat()
        duration_ms = (datetime.fromisoformat(end_time.replace('Z', '+00:00')) - 
                      datetime.fromisoformat(start_time.replace('Z', '+00:00'))).total_seconds() * 1000
        
        new_span.end_time = end_time
        new_span.duration_ms = round(duration_ms, 2)
        
        _set_current_span(parent_span)
        _write_json_log(new_span)
        
        end_message = f"[SPAN END] {name} (span_id: {new_span.span_id}, duration: {duration_ms/1000:.2f}s)"
        if error_occurred:
            end_message += f" [ERROR: {error_message}]"
        _write_log(end_message)


@contextmanager
def local_trace(name: str, trace_id: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Enhanced local trace context manager for logging agent operations.
    
    Args:
        name: Name of the trace
        trace_id: Optional trace ID. If not provided, generates a UUID
        attributes: Optional metadata attributes to attach to the trace
    
    Yields:
        Span: The trace span object. You can update it with metadata:
            trace.add_result_metadata(result)  # Extract metadata from Runner result
            trace.attributes["custom_key"] = "value"  # Add custom attributes
    
    Example:
        with local_trace("conversation") as trace:
            result = await Runner.run(agent, "message")
            trace.add_result_metadata(result)  # Automatically extract metadata
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    span_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc).isoformat()
    start_time_local = time.time()
    
    root_span = Span(
        span_id=span_id,
        trace_id=trace_id,
        parent_span_id=None,
        name=name,
        start_time=start_time,
        attributes=attributes or {}
    )
    
    _set_current_span(root_span)
    
    processor = None
    if AGENTS_AVAILABLE:
        processor = _get_local_trace_processor()
        if processor:
            try:
                add_trace_processor(processor)
            except Exception:
                # Silently fail if registration fails
                processor = None
    
    start_message = f"[TRACE START] {name} (trace_id: {trace_id})"
    print(start_message)
    _write_log(start_message)
    
    error_occurred = False
    error_message = None
    
    try:
        yield root_span
    except Exception as e:
        error_occurred = True
        error_message = str(e)
        root_span.status = "error"
        root_span.error = error_message
        raise
    finally:
        end_time = datetime.now(timezone.utc).isoformat()
        duration = time.time() - start_time_local
        duration_ms = duration * 1000
        
        root_span.end_time = end_time
        root_span.duration_ms = round(duration_ms, 2)
        
        if processor and AGENTS_AVAILABLE:
            try:
                remove_trace_processor(processor)
            except Exception:
                # Silently fail if unregistration fails
                pass
        
        _set_current_span(None)
        
        if hasattr(_thread_local, 'span_map'):
            span_map = _thread_local.span_map
            to_remove = []
            for agents_span_id, span_info in span_map.items():
                if span_info['local_span'].trace_id == trace_id:
                    to_remove.append(agents_span_id)
            for agents_span_id in to_remove:
                del span_map[agents_span_id]
        
        _write_json_log(root_span)
        
        end_message = f"[TRACE END] {name} (duration: {duration:.2f}s)"
        if error_occurred:
            end_message += f" [ERROR: {error_message}]"
        
        print(end_message)
        _write_log(end_message)
