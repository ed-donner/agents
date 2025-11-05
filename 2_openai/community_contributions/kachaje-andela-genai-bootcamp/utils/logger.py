from .local_logger import LocalLogger
import uuid

_logger_instance = None

def get_logger(**kwargs) -> LocalLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LocalLogger(**kwargs)
    return _logger_instance

logger = get_logger()

def trace(name: str, trace_id: str = None, **metadata):
    return logger.trace(name, trace_id=trace_id, **metadata)

def span(name: str, message: str, trace_id: str = None, **metadata):
    """Context manager for custom spans that integrates with local logging."""
    return logger.span(name, message, trace_id=trace_id, **metadata)

def gen_trace_id(prefix: str = "trace") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"

__all__ = ['trace', 'span', 'gen_trace_id', 'logger', 'get_logger']

