#!/usr/bin/env python3
"""
Simple web UI for viewing traces.
Run with: python -m local_trace.trace_ui
Then visit http://localhost:5050
"""

from flask import Flask, render_template_string, jsonify, request
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any
import glob

app = Flask(__name__)


def load_traces() -> List[Dict[str, Any]]:
    """Load all traces from JSON log files."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return []
    
    traces = []
    trace_map = {}
    
    json_files = sorted(glob.glob(str(logs_dir / "trace_*.jsonl")), reverse=True)
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        span_data = json.loads(line)
                        trace_id = span_data.get("trace_id")
                        
                        if trace_id not in trace_map:
                            trace_map[trace_id] = {
                                "trace_id": trace_id,
                                "name": span_data.get("name", "Unknown"),
                                "start_time": span_data.get("start_time"),
                                "end_time": span_data.get("end_time"),
                                "duration_ms": span_data.get("duration_ms", 0),
                                "status": span_data.get("status", "success"),
                                "spans": []
                            }
                        
                        trace_map[trace_id]["spans"].append(span_data)
                        
                        if span_data.get("end_time"):
                            span_end = span_data.get("end_time")
                            if not trace_map[trace_id]["end_time"] or span_end > trace_map[trace_id]["end_time"]:
                                trace_map[trace_id]["end_time"] = span_end
                                trace_map[trace_id]["duration_ms"] = span_data.get("duration_ms", 0)
                        
                        if span_data.get("status") == "error":
                            trace_map[trace_id]["status"] = "error"
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
            continue
    
    traces = list(trace_map.values())
    traces.sort(key=lambda x: x.get("start_time", ""), reverse=True)
    
    for trace in traces:
        trace["spans"] = _build_span_hierarchy(trace["spans"])
    
    return traces


def _build_span_hierarchy(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build hierarchical structure of spans."""
    span_map = {span["span_id"]: span for span in spans}
    root_spans = []
    
    for span in spans:
        span["children"] = []
        parent_id = span.get("parent_span_id")
        if parent_id and parent_id in span_map:
            parent = span_map[parent_id]
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(span)
        else:
            root_spans.append(span)
    
    return root_spans


def _format_timestamp(iso_str: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trace Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: #fff;
            border-bottom: 1px solid #e0e0e0;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .traces-list {
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .trace-item {
            border-bottom: 1px solid #e0e0e0;
            padding: 1rem 1.5rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .trace-item:hover {
            background: #f9f9f9;
        }
        
        .trace-item:last-child {
            border-bottom: none;
        }
        
        .trace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .trace-name {
            font-weight: 600;
            font-size: 1.1rem;
            color: #333;
        }
        
        .trace-meta {
            display: flex;
            gap: 1.5rem;
            font-size: 0.9rem;
            color: #666;
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .trace-detail {
            display: none;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e0e0e0;
        }
        
        .trace-detail.active {
            display: block;
        }
        
        .span-tree {
            margin-left: 1rem;
        }
        
        .span-item {
            margin: 0.5rem 0;
            padding: 0.75rem;
            background: #f9f9f9;
            border-left: 3px solid #007bff;
            border-radius: 4px;
        }
        
        .span-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .span-name {
            font-weight: 600;
            color: #007bff;
        }
        
        .span-meta {
            font-size: 0.85rem;
            color: #666;
        }
        
        .span-children {
            margin-left: 1.5rem;
            margin-top: 0.5rem;
        }
        
        .attributes {
            margin-top: 0.75rem;
            padding: 0.75rem;
            background: #fff;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }
        
        .attributes-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #333;
        }
        
        .attr-item {
            margin: 0.25rem 0;
            padding: 0.25rem 0;
        }
        
        .attr-key {
            font-weight: 500;
            color: #555;
        }
        
        .attr-value {
            color: #666;
            margin-left: 0.5rem;
            word-break: break-word;
        }
        
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 0.75rem;
            border-radius: 4px;
            margin-top: 0.5rem;
        }
        
        .tool-call {
            background: #e7f3ff;
            padding: 0.5rem;
            border-radius: 4px;
            margin: 0.25rem 0;
        }
        
        .tool-name {
            font-weight: 600;
            color: #0056b3;
        }
        
        pre {
            background: #f5f5f5;
            padding: 0.5rem;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.85rem;
        }
        
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Trace Viewer</h1>
    </div>
    <div class="container">
        <div class="traces-list" id="tracesList">
            <div class="empty-state">Loading traces...</div>
        </div>
    </div>
    
    <script>
        function loadTraces() {
            fetch('/api/traces')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('tracesList');
                    if (data.length === 0) {
                        container.innerHTML = '<div class="empty-state">No traces found. Run some agent operations to generate traces.</div>';
                        return;
                    }
                    
                    container.innerHTML = data.map(trace => renderTrace(trace)).join('');
                    
                    // Add click handlers
                    document.querySelectorAll('.trace-item').forEach(item => {
                        item.addEventListener('click', function() {
                            const detail = this.querySelector('.trace-detail');
                            detail.classList.toggle('active');
                        });
                    });
                })
                .catch(error => {
                    console.error('Error loading traces:', error);
                    document.getElementById('tracesList').innerHTML = 
                        '<div class="empty-state">Error loading traces. Make sure trace JSON files exist in the logs/ directory.</div>';
                });
        }
        
        function renderTrace(trace) {
            const statusClass = trace.status === 'error' ? 'status-error' : 'status-success';
            const duration = (trace.duration_ms / 1000).toFixed(2);
            const startTime = formatTime(trace.start_time);
            
            return `
                <div class="trace-item">
                    <div class="trace-header">
                        <div>
                            <div class="trace-name">${escapeHtml(trace.name)}</div>
                            <div class="trace-meta">
                                <span>Trace ID: ${trace.trace_id.substring(0, 8)}...</span>
                                <span>Duration: ${duration}s</span>
                                <span>Started: ${startTime}</span>
                                <span class="status-badge ${statusClass}">${trace.status}</span>
                            </div>
                        </div>
                    </div>
                    <div class="trace-detail">
                        ${renderSpans(trace.spans)}
                    </div>
                </div>
            `;
        }
        
        function renderSpans(spans) {
            if (!spans || spans.length === 0) {
                return '<div class="empty-state">No spans</div>';
            }
            
            return spans.map(span => renderSpan(span)).join('');
        }
        
        function renderSpan(span) {
            const duration = span.duration_ms ? (span.duration_ms / 1000).toFixed(2) + 's' : 'N/A';
            const statusClass = span.status === 'error' ? 'status-error' : 'status-success';
            const children = span.children ? renderSpans(span.children) : '';
            
            let attributesHtml = '';
            if (span.attributes && Object.keys(span.attributes).length > 0) {
                attributesHtml = '<div class="attributes"><div class="attributes-title">Attributes:</div>';
                for (const [key, value] of Object.entries(span.attributes)) {
                    let displayValue = value;
                    if (typeof value === 'object') {
                        displayValue = '<pre>' + escapeHtml(JSON.stringify(value, null, 2)) + '</pre>';
                    } else if (typeof value === 'string' && value.length > 200) {
                        displayValue = escapeHtml(value.substring(0, 200)) + '...';
                    } else {
                        displayValue = escapeHtml(String(value));
                    }
                    attributesHtml += `<div class="attr-item"><span class="attr-key">${escapeHtml(key)}:</span><span class="attr-value">${displayValue}</span></div>`;
                }
                attributesHtml += '</div>';
            }
            
            let errorHtml = '';
            if (span.error) {
                errorHtml = `<div class="error-message">Error: ${escapeHtml(span.error)}</div>`;
            }
            
            return `
                <div class="span-item">
                    <div class="span-header">
                        <span class="span-name">${escapeHtml(span.name)}</span>
                        <span class="span-meta">
                            <span class="status-badge ${statusClass}">${span.status}</span>
                            <span>${duration}</span>
                        </span>
                    </div>
                    ${attributesHtml}
                    ${errorHtml}
                    ${children ? '<div class="span-children">' + children + '</div>' : ''}
                </div>
            `;
        }
        
        function formatTime(isoStr) {
            try {
                const date = new Date(isoStr);
                return date.toLocaleString();
            } catch {
                return isoStr;
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Load traces on page load and refresh every 5 seconds
        loadTraces();
        setInterval(loadTraces, 5000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Main page with trace viewer."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/traces')
def api_traces():
    """API endpoint to get all traces."""
    traces = load_traces()
    return jsonify(traces)


@app.route('/api/trace/<trace_id>')
def api_trace(trace_id):
    """API endpoint to get a specific trace by ID."""
    traces = load_traces()
    trace = next((t for t in traces if t["trace_id"] == trace_id), None)
    if trace:
        return jsonify(trace)
    return jsonify({"error": "Trace not found"}), 404


if __name__ == '__main__':
    print("Starting Trace Viewer...")
    print("Visit http://localhost:5050 to view traces")
    app.run(debug=True, host='0.0.0.0', port=5050)

