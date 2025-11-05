"""
Custom local logging solution to replace OpenAI traces.
Logs agent operations locally with detailed information.
"""

import json
import logging
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
import threading


@dataclass
class LogEntry:
    """Represents a single log entry."""
    trace_id: str
    timestamp: str
    level: str  # 'trace', 'span', 'agent', 'tool', 'error'
    name: str
    message: str
    data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    parent_id: Optional[str] = None


class LocalLogger:
    """Custom logger that replaces OpenAI traces with local logging."""
    
    def __init__(
        self,
        log_dir: str = "logs",
        log_file: Optional[str] = None,
        db_file: Optional[str] = None,
        console: bool = True,
        log_level: str = "INFO"
    ):
        """
        Initialize the local logger.
        
        Args:
            log_dir: Directory to store log files (relative to this file's directory)
            log_file: Specific log file path (default: log_dir/traces.jsonl)
            db_file: SQLite database file path (default: log_dir/traces.db)
            console: Whether to log to console
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        # Determine base directory (parent of utils/)
        base_dir = Path(__file__).parent.parent
        self.log_dir = base_dir / log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = Path(log_file) if log_file else self.log_dir / "traces.jsonl"
        self.db_file = Path(db_file) if db_file else self.log_dir / "traces.db"
        self.console = console
        self.log_level = getattr(logging, log_level.upper())
        
        # Setup console logging
        if self.console:
            self.console_logger = logging.getLogger("agent_logger")
            self.console_logger.setLevel(self.log_level)
            if not self.console_logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
                )
                self.console_logger.addHandler(handler)
        
        # Initialize database
        self._init_database()
        
        # Thread-local storage for trace context
        self._local = threading.local()
    
    def _init_database(self):
        """Initialize SQLite database for structured logging."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,
                    duration_ms REAL,
                    parent_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trace_id ON traces(trace_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON traces(timestamp)')
            conn.commit()
    
    def _write_log(self, entry: LogEntry):
        """Write log entry to all configured outputs."""
        # Write to JSONL file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(entry)) + '\n')
        
        # Write to database
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO traces (trace_id, timestamp, level, name, message, data, duration_ms, parent_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.trace_id,
                entry.timestamp,
                entry.level,
                entry.name,
                entry.message,
                json.dumps(entry.data) if entry.data else None,
                entry.duration_ms,
                entry.parent_id
            ))
            conn.commit()
        
        # Write to console
        if self.console:
            level_colors = {
                'trace': '\033[36m',  # Cyan
                'span': '\033[34m',   # Blue
                'agent': '\033[32m',  # Green
                'tool': '\033[33m',   # Yellow
                'error': '\033[31m',  # Red
            }
            color = level_colors.get(entry.level, '')
            reset = '\033[0m'
            
            duration_str = f" ({entry.duration_ms:.2f}ms)" if entry.duration_ms else ""
            self.console_logger.info(
                f"{color}[{entry.level.upper()}]{reset} {entry.name}: {entry.message}{duration_str}"
            )
    
    def _create_entry(
        self,
        trace_id: str,
        level: str,
        name: str,
        message: str,
        data: Optional[Dict] = None,
        duration_ms: Optional[float] = None,
        parent_id: Optional[str] = None
    ) -> LogEntry:
        """Create a log entry."""
        return LogEntry(
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            name=name,
            message=message,
            data=data,
            duration_ms=duration_ms,
            parent_id=parent_id
        )
    
    @contextmanager
    def trace(self, name: str, trace_id: Optional[str] = None, **metadata):
        """
        Context manager for tracing agent operations.
        Replaces OpenAI's trace() function.
        
        Usage:
            with logger.trace("Research trace", trace_id="custom_id"):
                result = await Runner.run(agent, input)
        """
        trace_id = trace_id or f"trace_{uuid.uuid4().hex[:16]}"
        start_time = time.time()
        
        # Store trace context
        if not hasattr(self._local, 'trace_stack'):
            self._local.trace_stack = []
        
        parent_id = self._local.trace_stack[-1] if self._local.trace_stack else None
        self._local.trace_stack.append(trace_id)
        
        try:
            # Log trace start
            self._write_log(self._create_entry(
                trace_id=trace_id,
                level="trace",
                name=name,
                message=f"Started: {name}",
                data=metadata,
                parent_id=parent_id
            ))
            
            yield trace_id
            
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            self._write_log(self._create_entry(
                trace_id=trace_id,
                level="error",
                name=name,
                message=f"Error in {name}: {str(e)}",
                data={"error": str(e), "error_type": type(e).__name__, **metadata},
                duration_ms=duration_ms,
                parent_id=parent_id
            ))
            raise
        finally:
            # Log trace end
            duration_ms = (time.time() - start_time) * 1000
            self._local.trace_stack.pop()
            
            self._write_log(self._create_entry(
                trace_id=trace_id,
                level="trace",
                name=name,
                message=f"Ended: {name}",
                data={"status": "completed", **metadata},
                duration_ms=duration_ms,
                parent_id=parent_id
            ))
    
    @contextmanager
    def span(self, name: str, message: str, trace_id: Optional[str] = None, **metadata):
        """
        Context manager for custom spans.
        Integrates with the local logger and respects the current trace context.
        
        Usage:
            with logger.span("custom_operation", "Processing data", key="value"):
                # Your code here
                result = process_data()
        """
        # Get trace_id from current context or use provided one
        if trace_id is None:
            if hasattr(self._local, 'trace_stack') and self._local.trace_stack:
                trace_id = self._local.trace_stack[-1]
            else:
                trace_id = f"span_{uuid.uuid4().hex[:16]}"
        
        start_time = time.time()
        parent_id = self._local.trace_stack[-1] if hasattr(self._local, 'trace_stack') and self._local.trace_stack else None
        
        try:
            # Log span start
            self._write_log(self._create_entry(
                trace_id=trace_id,
                level="span",
                name=name,
                message=f"Started: {message}",
                data=metadata,
                parent_id=parent_id
            ))
            
            yield
            
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            self._write_log(self._create_entry(
                trace_id=trace_id,
                level="error",
                name=name,
                message=f"Error in {name}: {str(e)}",
                data={"error": str(e), "error_type": type(e).__name__, **metadata},
                duration_ms=duration_ms,
                parent_id=parent_id
            ))
            raise
        finally:
            # Log span end
            duration_ms = (time.time() - start_time) * 1000
            self._write_log(self._create_entry(
                trace_id=trace_id,
                level="span",
                name=name,
                message=f"Ended: {message}",
                data={"status": "completed", **metadata},
                duration_ms=duration_ms,
                parent_id=parent_id
            ))

    def log_agent_call(
        self,
        trace_id: str,
        agent_name: str,
        input_text: str,
        output: Optional[str] = None,
        duration_ms: Optional[float] = None,
        tool_calls: Optional[List[Dict]] = None,
        error: Optional[str] = None
    ):
        """Log an agent call."""
        parent_id = self._local.trace_stack[-1] if hasattr(self._local, 'trace_stack') and self._local.trace_stack else None
        
        data = {
            "input": input_text[:500] if len(input_text) > 500 else input_text,  # Truncate long inputs
            "output_length": len(output) if output else 0,
        }
        
        if tool_calls:
            data["tool_calls"] = tool_calls
        
        if error:
            data["error"] = error
        
        level = "error" if error else "agent"
        message = f"Agent '{agent_name}' called" + (f": {error}" if error else "")
        
        self._write_log(self._create_entry(
            trace_id=trace_id,
            level=level,
            name=agent_name,
            message=message,
            data=data,
            duration_ms=duration_ms,
            parent_id=parent_id
        ))
    
    def log_tool_call(
        self,
        trace_id: str,
        tool_name: str,
        arguments: Dict,
        result: Optional[Any] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Log a tool call."""
        parent_id = self._local.trace_stack[-1] if hasattr(self._local, 'trace_stack') and self._local.trace_stack else None
        
        data = {
            "arguments": arguments,
            "result": str(result)[:500] if result else None,  # Truncate long results
        }
        
        if error:
            data["error"] = error
        
        level = "error" if error else "tool"
        message = f"Tool '{tool_name}' called" + (f": {error}" if error else "")
        
        self._write_log(self._create_entry(
            trace_id=trace_id,
            level=level,
            name=tool_name,
            message=message,
            data=data,
            duration_ms=duration_ms,
            parent_id=parent_id
        ))
    
    def log_span(
        self,
        trace_id: str,
        name: str,
        message: str,
        data: Optional[Dict] = None,
        duration_ms: Optional[float] = None
    ):
        """Log a span (generic operation)."""
        parent_id = self._local.trace_stack[-1] if hasattr(self._local, 'trace_stack') and self._local.trace_stack else None
        
        self._write_log(self._create_entry(
            trace_id=trace_id,
            level="span",
            name=name,
            message=message,
            data=data,
            duration_ms=duration_ms,
            parent_id=parent_id
        ))
    
    def get_trace(self, trace_id: str) -> List[Dict]:
        """Retrieve all log entries for a given trace ID."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM traces 
                WHERE trace_id = ? 
                ORDER BY timestamp ASC
            ''', (trace_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def search_traces(
        self,
        name: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Search traces with filters."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT DISTINCT trace_id FROM traces WHERE 1=1"
            params = []
            
            if name:
                query += " AND name LIKE ?"
                params.append(f"%{name}%")
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            trace_ids = [row['trace_id'] for row in cursor.fetchall()]
            
            # Get full traces
            all_entries = []
            for tid in trace_ids:
                all_entries.extend(self.get_trace(tid))
            
            return all_entries

