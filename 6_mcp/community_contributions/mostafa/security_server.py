'''
MCP Server for Agentic Security Checks on Linux.
Tools provide system inspection, threat intel, RAG knowledge base, and reporting.
'''

import hashlib
import os
import re
import subprocess
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from pathlib import Path
import psutil
import logging
import requests
from typing import Any
from dotenv import load_dotenv


# Configuration

REPORT_DIR = Path('./sandbox_reports')
REPORT_DIR.mkdir(exist_ok=True)


load_dotenv(override=True)

mcp = FastMCP('security_inspector')


def safe_run(cmd: list[str], timeout: int = 10) -> str:
    '''
    Run a system command safely with a timeout and return its output.
    '''
    try:
        result = subprocess.run(cmd, capture_output=True,
                                text=True, timeout=timeout)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logging.error(
            f'Command {' '.join(cmd)} timed out after {timeout} seconds.')
        return f'Error: Command timed out after {timeout} seconds.'
    except Exception as e:
        logging.error(f'Error running command {' '.join(cmd)}: {e}')
        return f'Error running command: {e}'

# Tools for system inspection


@mcp.tool()
def get_system_baseline():
    '''
    Get the system baseline configuration.

    Returns a JSON string with OS details, uptime, load average, CPU cores, memory info, and logged-in users.
    '''
    uname = os.uname()
    load = psutil.getloadavg()
    mem = psutil.virtual_memory()
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    users = [{'name': u.name, 'terminal': u.terminal, 'host': u.host}
             for u in psutil.users()]
    data = {
        'os': f'{uname.sysname} {uname.release} {uname.version}',
        'kernel': uname.release,
        'uptime_seconds': (datetime.now() - boot_time).total_seconds(),
        'load_average': [load[0], load[1], load[2]],
        'cpu_cores': psutil.cpu_count(logical=False),
        'memory': {
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3)
        },
        'logged_in_users': users,
    }
    return json.dumps(data, indent=2)


@mcp.tool()
def list_services():
    '''
    List systemd services and their active status.

    Returns a list of dictionaries with service name, load state, active state, sub state, and description for each running or failed service.
    '''
    try:
        cmd = ['systemctl', 'list-units', '--type=service',
               '--state=running,failed', '--no-pager', '--no-legend']
        result = safe_run(cmd)
        print(f'Raw systemctl output:\n{result}')
        lines = result.split('\n')

        services = []
        for line in lines:
            if not line.strip():
                continue
            # Remove leading non-alphanumeric characters and extra spaces
            line = re.sub(r'^[^\w\s]+\s*', '', line.strip())
            parts = line.split(maxsplit=4)
            if len(parts) >= 4:
                name, load, status, sub_state, description = parts
                services.append({
                    'name': name,
                    'load': load,
                    'status': status,
                    'sub_state': sub_state,
                    'description': description
                })
        return json.dumps(services[:50], indent=2)
    except Exception as e:
        logging.error(f'Error listing services: {e}')
        return f'Error listing services: {e}'


@mcp.tool()
def list_sockets_and_ports():
    '''
    List listening TCP/UDP ports and associated processe names.

    Returns a list of dictionaries with protocol, local address, port, process name, and PID for each listening socket.
    '''
    connections = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid) if conn.pid else None
                pname = proc.name() if proc else 'unknown'
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pname = 'unknown'
            addr = conn.laddr
            connections.append({
                'protocol': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                'address': addr.ip,
                'port': addr.port,
                'process': pname,
                'pid': conn.pid
            })
    return json.dumps(connections, indent=2)


@mcp.tool()
def get_cpu_mem_processes(n: int = 10):
    '''
    Returns top N CPU and top N memory consuming processes on the system as:
    a JSON object with two lists: 'top_cpu' and 'top_memory', each containing dictionaries with process name, PID, and usage percentage.

        @param n: Number of top processes to return for CPU and memory usage (default is 10).

    Note: should be called twice with a delay in between to get accurate CPU usage, as psutil calculates CPU percent based on the time between calls.

    '''
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            mem_usage = proc.info['memory_info'].rss / (1024**2)  # in MB
            cpu_usage = proc.info['cpu_percent']
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'memory_usage': f'{mem_usage:5.1f}MB',
                'cpu_usage': f'{cpu_usage:5.1f}%'
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by memory/CPU usage and return top N processes for each.
    top_mem = sorted(processes, key=lambda p: float(
        p['memory_usage'].rstrip('MB')), reverse=True)[:n]
    top_cpu = sorted(processes, key=lambda p: float(
        p['cpu_usage'].rstrip('%')), reverse=True)[:n]

    data = {
        'top_cpu': [{
            'pid': p['pid'],
            'name': p['name'],
            'cpu_usage': p['cpu_usage']
        } for p in top_cpu],
        'top_memory': [{
            'pid': p['pid'],
            'name': p['name'],
            'memory_usage': p['memory_usage']  # in MB
        } for p in top_mem]
    }
    # TODO: Fix the first call returning 0% CPU usage for all processes, likely due to how psutil calculates CPU percent (needs a delay or prior call)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_recent_logs(lines: int = 20):
    '''
    Get last N lines from syslog, auth.log, and dmesg errors/warnings.

        @param lines: Number of lines to retrieve from each log source (default is 20).

    Returns a string containing the recent log entries from each source, prefixed with the log file name for clarity. If no logs are found or an error occurs, appropriate messages are included in the output.
    '''
    log_files = ['/var/log/syslog', '/var/log/auth.log']
    logs = []
    for log_file in log_files:
        if os.path.exists(log_file):
            cmd = ['tail', f'-n{lines}', log_file]
            try:
                result = safe_run(cmd, timeout=5)
                if result:
                    logs.append(f'\n--- {log_file} ---\n')
                    log_lines = result.split('\n')
                    logs.extend([f'{line.strip()}' for line in log_lines])
            except Exception as e:
                logging.error(f'Error reading {log_file}: {e}')
                logs.append(f'Error reading {log_file}: {e}')

    # Get dmesg errors/warnings
    try:
        cmd = ['dmesg', '-T', '--level=err,warn']
        dmsg = safe_run(cmd, timeout=5)
        if dmsg:
            logs.append('\n--- dmesg (errors/warnings) ---\n')
            dmesg_lines = dmsg.split('\n')[-lines:]
            logs.extend([f'dmesg: {line.strip()}' for line in dmesg_lines])
        else:
            logs.append(
                '\n--- dmesg (errors/warnings) ---\nNo recent dmesg errors/warnings found.')
    except Exception as e:
        print(f'Error running dmesg: {e}')
        logging.error(f'Error running dmesg: {e}')
        logs.append(f'Error running dmesg: {e}')
    return '\n'.join(logs) or 'No recent logs found.'

    # TODO: Add more log sources (e.g., application logs, custom log paths)


# @mcp.tool()
# def add_to_knowledge_base(doc: str, metadata: dict[str, Any] | None = None):
#     '''
#     Add a new entry to the security knowledge base.
#     '''
#     if metadata is None:
#         metadata = {'source': 'agent', 'timestamp': datetime.now().isoformat()}
#     doc_id = f'doc_{datetime.now().timestamp()}_{hash(doc)} % 10000'
#     try:
#         kb.add(documents=[doc], metadatas=[metadata], ids=[doc_id])
#         return f'Entry added to knowledge base with ID: {doc_id}'
#     except Exception as e:
#         logging.error(f'Error adding to knowledge base: {e}')
#         return f'Error adding to knowledge base: {e}'


# Reporting

@mcp.tool()
def write_report(report: str, filename: str | None = None):
    '''
    Write a security report to a sandbox directory.

        @param report: The content of the report to write.
        @param filename: Optional filename for the report. If not provided, a timestamped filename will be generated.

    Returns a message indicating the absolute path of the saved file.
    '''
    if filename is None:
        filename = f'report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md'
    report_path = REPORT_DIR / filename
    report_path.write_text(report)
    return f'Report written to {report_path.absolute()}'


# Deep-Dive Tools

@mcp.tool()
def get_process_details(pid: int):
    '''
    Get detailed information about a specific process by PID, including command line, environment variables, open files, and network connections.

        @param pid: The process ID to get details for.

    Returns a JSON string with detailed information about the process, including its name, executable path, current working directory, command line arguments, parent process info, creation time, username, CPU and memory usage, environment variables, open files (limited to the first 20), and active network connections. If the process does not exist or an error occurs, an appropriate message is returned.
    '''
    try:
        proc = psutil.Process(pid)
        details = {
            'pid': pid,
            'name': proc.name(),
            'exe': proc.exe(),
            'cwd': proc.cwd(),
            'cmdline': proc.cmdline(),
            'parent': {'pid': proc.ppid(), 'name': proc.parent().name() if proc.parent() else 'N/A'},
            'create_time': datetime.fromtimestamp(proc.create_time()).isoformat(),
            'username': proc.username(),
            'cpu_percent': proc.cpu_percent(interval=0.1),
            'memory_info': {
                'rss_in_MB': proc.memory_info().rss // (1024**2),
                'vms_in_MB': proc.memory_info().vms // (1024**2),
                'percent': proc.memory_percent()
            },
            'environ': proc.environ(),
            # Limit to first 20 open files
            'open_files': [{'path': f.path, 'fd': f.fd} for f in proc.open_files()[:20]],
            'connections': [{
                'fd': c.fd,
                'family': c.family.name if hasattr(c.family, 'name') else str(c.family),
                'type': c.type.name if hasattr(c.type, 'name') else str(c.type),
                'local_address': f'{c.laddr.ip}:{c.laddr.port}' if c.laddr else '',
                'remote_address': f'{c.raddr.ip}:{c.raddr.port}' if c.raddr else '',
                'status': c.status
            } for c in proc.net_connections(kind='inet')]
        }
        return json.dumps(details, indent=2)
    except psutil.NoSuchProcess:
        return f'No process found with PID {pid}.'
    except Exception as e:
        logging.error(f'Error getting process details for PID {pid}: {e}')
        return f'Error getting process details: {e}'


@mcp.tool()
def check_network_connections(pid: int):
    '''
    Get active network connections for a specific PID.

        @param pid: The process ID to check for active network connections.

    Returns a JSON string with the process name and a list of active network connections, including file descriptor, protocol, local and remote addresses, connection status, type, and family. If the process does not exist or an error occurs, an appropriate message is returned.
    '''
    result = {}
    connections = []
    try:
        proc = psutil.Process(pid)
        result['process_name'] = proc.name() if proc else 'unknown'
        for conn in proc.net_connections(kind='inet'):
            addr = conn.laddr
            connections.append({
                'fd': conn.fd,
                'protocol': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                'local_address': f'{addr.ip}:{addr.port}' if addr else '',
                'remote_address': f'{conn.raddr.ip}:{conn.raddr.port}' if conn.raddr else '',
                'status': conn.status,
                'type': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                'family': conn.family.name if hasattr(conn.family, 'name') else str(conn.family)
            })
        result['connections'] = connections
        return json.dumps(result, indent=2)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        result['error'] = f'No process found with PID {pid} or access denied.'
    except Exception as e:
        logging.error(f'Error checking network connections for PID {pid}: {e}')
        result['error'] = f'Error checking network connections: {e}'


@mcp.tool()
def check_file_details(file_path: str):
    '''
    Get details about a file, including size, permissions, owner, last modified time, and hash (SHA256).

        @param file_path: The path to the file to check.

    Returns a JSON string with details about the file, including its existence, path, type (file or directory), size in MB, permissions, owner UID and GID, last modified time, and SHA256 hash (if it's a file smaller than 10MB). If the file does not exist or an error occurs, an appropriate message is returned.
    '''
    try:
        path_obj = Path(file_path)
        stat = path_obj.stat()
        sha256_hash = hashlib.sha256(path_obj.read_bytes()).hexdigest(
        ) if path_obj.is_file() and stat.st_size < 10 * 1024 * 1024 else 'N/A'
        details = {
            'exists': True,
            'path': file_path,
            'is_file': path_obj.is_file(),
            'is_dir': path_obj.is_dir(),
            'size_in_MB': stat.st_size / (1024**2),
            'permissions': oct(stat.st_mode)[-3:],
            'owner_uid': stat.st_uid,
            'owner_gid': stat.st_gid,
            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'sha256': sha256_hash
        }
        return json.dumps(details, indent=2)
    except FileNotFoundError:
        return json.dumps({'error': f'File not found: {file_path}'}, indent=2)
    except Exception as e:
        logging.error(f'Error checking file details for {file_path}: {e}')
        return json.dumps({'error': f'Error checking file details: {e}'}, indent=2)


@mcp.tool()
def check_file_integrity(file_path: str, known_hash: str):
    '''
    Check the integrity of a file by comparing its hash to a known good hash.

        @param file_path: The path to the file to check.
        @param known_hash: The known good SHA256 hash of the file for comparison.

    Returns a message indicating whether the file integrity is verified or if it failed, along with the expected and actual hash values. If an error occurs while checking the file, an appropriate error message is returned.
    '''
    import hashlib
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_hash = hashlib.sha256(file_data).hexdigest()
            if file_hash == known_hash:
                return f'File integrity verified for {file_path}.'
            else:
                return f'File integrity check failed for {file_path}. Expected hash: {known_hash}, Actual hash: {file_hash}'
    except Exception as e:
        logging.error(f'Error checking file integrity for {file_path}: {e}')
        return f'Error checking file integrity: {e}'


@mcp.tool()
def get_service_config(service_name: str):
    '''
    Get systemd service unit file content and basic status.

        @param service_name: The name of the systemd service (e.g., 'nginx.service').

    Returns a JSON string containing the service name, unit file path and content, active status, and enabled status. If an error occurs while retrieving the service configuration, an appropriate error message is returned.
    '''

    try:
        is_acitve_cmd = ['systemctl', 'is-active', service_name]
        enabled_cmd = ['systemctl', 'is-enabled', service_name]
        # Get unit file content
        unit_file_cmd = ['systemctl', 'cat',
                         service_name, '--no-pager', '--no-legend']
        unit_file_result = safe_run(unit_file_cmd, timeout=5)

        lines = unit_file_result.splitlines()
        if lines and lines[0].startswith('# '):
            unit_path = lines[0][2:].strip()
            content = '\n'.join(lines[1:])
        else:
            unit_path = 'unknown'
            content = unit_file_result
    except Exception as e:
        logging.error(f'Error getting service config for {service_name}: {e}')
        return f'Error getting service config: {e}'

    status = safe_run(is_acitve_cmd, timeout=5)
    enabled = safe_run(enabled_cmd, timeout=5)

    return json.dumps({
        'service_name': service_name,
        'unit_file': {
            'path': unit_path,
            'content': content
        },
        'active': status,
        'enabled': enabled
    }, indent=2)

# Search the web


@mcp.tool()
def search_web(query: str, num_results: int = 5):
    '''
    Search the web for the given query and return top results.

    @param query: The search query string.
    @param num_results: The number of top results to return (default is 5).

    Returns a JSON string containing a list of search results, where each result includes the title, link, and snippet. If an error occurs during the web search, an appropriate error message is returned.
    '''
    serper_api_key = os.getenv('SERPER_API_KEY')
    if not serper_api_key:
        return json.dumps({'error': 'SERPER_API_KEY not set in environment variables'}, indent=2)
    api_url = 'https://google.serper.dev/search'
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'q': query,
        'num': num_results
    }

    try:
        response = requests.post(
            api_url, headers=headers, json=payload, timeout=10
        )
        response.raise_for_status()
        data = response.json()
        results = [{
            'title': item.get('title', ''),
            'link': item.get('link', ''),
            'snippet': item.get('snippet', '')
        } for item in data.get('organic', [])[:num_results]]

        return json.dumps({'results': results}, indent=2)

    except requests.exceptions.RequestException as e:
        logging.error(f'HTTP error during web search: {e}')
        return f'HTTP error during web search: {e}'
    except Exception as e:
        logging.error('Unexpected error during web search: {e}')
        return 'Unexpected error during web search: {e}'


@mcp.tool()
def fetch_url(url: str, max_char: int = 5000):
    '''
    Fetch and extract readable text from a URL.
    Returns JSON with the URL, status, content (plain text, stripped of HTML tags),
    and whether truncation occurred if content exceeds max_char limit.

        @param url: The URL to fetch.
        @param max_char: Maximum number of characters to return from the content (default is 5000).

    Returns a JSON string containing the final URL after redirects, HTTP status code, extracted content (plain text with HTML tags stripped), and a boolean indicating whether the content was truncated due to exceeding the max_char limit. If an error occurs during fetching or processing the URL, an appropriate error message is returned in JSON format.
    '''
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')
        # For HTML, strip tags; for plain text, return as is.
        if 'text/html' in content_type:
            # Simple regex to strip HTML tags (for demonstration purposes)
            text = re.sub(r'<[^>]+>', ' ', response.text)
            # Collapse multiple spaces into one
            text = re.sub(r'\s+', ' ', text).strip()
        else:
            text = response.text.strip()

        truncated = len(text) > max_char
        content = text[:max_char] + '... [truncated]' if truncated else text

        return json.dumps({
            'url': response.url,
            'status': response.status_code,
            'content': content,
            'truncated': truncated
        }, indent=2)
    except requests.exceptions.Timeout as e:
        logging.error(f'Timeout error fetching URL {url}: {e}')
        return json.dumps({'error': f'Timeout error fetching URL: {e}'}, indent=2)
    except requests.exceptions.ConnectionError as e:
        logging.error(f'Connection error fetching URL {url}: {e}')
        return json.dumps({'error': f'Connection error fetching URL: {e}'}, indent=2)
    except requests.exceptions.HTTPError as e:
        logging.error(f'HTTP error fetching URL {url}: {e}')
        return json.dumps({'error': f'HTTP error fetching URL: {e}'}, indent=2)
    except Exception as e:
        logging.error(f'Unexpected error fetching URL {url}: {e}')
        return json.dumps({'error': f'Unexpected error fetching URL: {e}'}, indent=2)


if __name__ == '__main__':
    mcp.run(transport='stdio')

