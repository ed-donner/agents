import psutil
import time
from datetime import datetime
from typing import Dict, Any
import uuid

from fastmcp import FastMCP
from .simple_database import (
    write_system_metric, create_alert, resolve_alert, get_active_alerts,
    get_recent_metrics, get_system_summary
)
from .config import config

mcp = FastMCP("DevOps Monitor")


@mcp.tool()
def get_system_metrics() -> Dict[str, Any]:
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        try:
            load_avg = psutil.getloadavg()
            load_1min = load_avg[0]
        except (AttributeError, OSError):
            load_1min = 0.0

        process_count = len(psutil.pids())

        metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "load_1min": load_1min,
            "process_count": process_count,
            "timestamp": datetime.now().isoformat()
        }

        write_system_metric("cpu_usage", cpu_percent,
                           "warning" if cpu_percent > config.CPU_WARNING_THRESHOLD else "normal")
        write_system_metric("memory_usage", memory.percent,
                           "warning" if memory.percent > config.MEMORY_WARNING_THRESHOLD else "normal")
        write_system_metric("disk_usage", disk.percent,
                           "warning" if disk.percent > config.DISK_WARNING_THRESHOLD else "normal")

        return {
            "success": True,
            "metrics": metrics,
            "message": f"System metrics collected at {datetime.now().strftime('%H:%M:%S')}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to collect system metrics"
        }


@mcp.tool()
def check_system_health() -> Dict[str, Any]:
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        alerts_created = []
        issues_found = []

        if cpu_percent > config.CPU_WARNING_THRESHOLD:
            alert_id = f"high-cpu-{int(time.time())}"
            severity = "warning" if cpu_percent < config.CPU_CRITICAL_THRESHOLD else "critical"
            create_alert(
                alert_id=alert_id,
                title="High CPU Usage",
                message=f"CPU usage is {cpu_percent:.1f}%",
                severity=severity,
                metadata={"cpu_percent": cpu_percent}
            )
            alerts_created.append(alert_id)
            issues_found.append(f"CPU: {cpu_percent:.1f}%")

        if memory.percent > config.MEMORY_WARNING_THRESHOLD:
            alert_id = f"high-memory-{int(time.time())}"
            severity = "warning" if memory.percent < config.MEMORY_CRITICAL_THRESHOLD else "critical"
            create_alert(
                alert_id=alert_id,
                title="High Memory Usage",
                message=f"Memory usage is {memory.percent:.1f}%",
                severity=severity,
                metadata={"memory_percent": memory.percent}
            )
            alerts_created.append(alert_id)
            issues_found.append(f"Memory: {memory.percent:.1f}%")

        if disk.percent > config.DISK_WARNING_THRESHOLD:
            alert_id = f"high-disk-{int(time.time())}"
            create_alert(
                alert_id=alert_id,
                title="High Disk Usage",
                message=f"Disk usage is {disk.percent:.1f}%",
                severity="warning" if disk.percent < config.DISK_CRITICAL_THRESHOLD else "critical",
                metadata={"disk_percent": disk.percent}
            )
            alerts_created.append(alert_id)
            issues_found.append(f"Disk: {disk.percent:.1f}%")

        try:
            load_avg = psutil.getloadavg()
            cpu_count = psutil.cpu_count()
            if load_avg[0] > cpu_count * config.LOAD_WARNING_MULTIPLIER:
                alert_id = f"high-load-{int(time.time())}"
                create_alert(
                    alert_id=alert_id,
                    title="High System Load",
                    message=f"Load average is {load_avg[0]:.2f} (CPUs: {cpu_count})",
                    severity="warning",
                    metadata={"load_avg": load_avg[0], "cpu_count": cpu_count}
                )
                alerts_created.append(alert_id)
                issues_found.append(f"Load: {load_avg[0]:.2f}")
        except (AttributeError, OSError):
            pass

        status = "healthy" if not issues_found else "issues_detected"

        return {
            "success": True,
            "status": status,
            "issues_found": issues_found,
            "alerts_created": alerts_created,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            },
            "message": f"Health check completed - {status}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Health check failed"
        }


@mcp.tool()
def create_custom_alert(title: str, message: str, severity: str = "warning") -> Dict[str, Any]:
    try:
        alert_id = f"custom-{uuid.uuid4().hex[:8]}"
        create_alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            metadata={"source": "manual", "created_by": "agent"}
        )
        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Alert created: {title}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create alert"
        }


@mcp.tool()
def resolve_system_alert(alert_id: str) -> Dict[str, Any]:
    try:
        resolve_alert(alert_id)
        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Alert {alert_id} resolved"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to resolve alert {alert_id}"
        }


@mcp.tool()
def get_system_alerts(status: str = "active") -> Dict[str, Any]:
    try:
        alerts = get_active_alerts()
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "message": f"Retrieved {len(alerts)} alerts"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve alerts"
        }


@mcp.tool()
def get_metrics_history(metric_type: str = None, limit: int = 20) -> Dict[str, Any]:
    try:
        metrics = get_recent_metrics(limit=limit, metric_type=metric_type)
        return {
            "success": True,
            "metrics": metrics,
            "count": len(metrics),
            "metric_type": metric_type or "all",
            "message": f"Retrieved {len(metrics)} metric records"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve metrics history"
        }


@mcp.tool()
def get_dashboard_data() -> Dict[str, Any]:
    try:
        summary = get_system_summary()
        active_alerts = get_active_alerts()
        recent_metrics = get_recent_metrics(limit=10)
        current_status = get_system_metrics()
        return {
            "success": True,
            "summary": summary,
            "current_metrics": current_status.get("metrics", {}),
            "active_alerts": active_alerts,
            "recent_metrics": recent_metrics,
            "timestamp": datetime.now().isoformat(),
            "message": "Dashboard data retrieved successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve dashboard data"
        }


@mcp.resource("system://status")
def system_status() -> str:
    try:
        summary = get_system_summary()
        alerts = get_active_alerts()
        status_lines = [
            "=== DevOps System Status ===",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Active Alerts:",
        ]
        if alerts:
            for alert in alerts:
                status_lines.append(f"  - [{alert['severity'].upper()}] {alert['title']}: {alert['message']}")
        else:
            status_lines.append("  No active alerts")
        status_lines.extend([
            "",
            "Agent Status:",
        ])
        for agent_name, status in summary.get("agents", {}).items():
            status_lines.append(f"  - {agent_name}: {status}")
        status_lines.extend([
            "",
            "Metrics Summary:",
        ])
        for metric_type, data in summary.get("metrics_summary", {}).items():
            status_lines.append(f"  - {metric_type}: avg={data['avg']:.1f}, count={data['count']}")
        return "\n".join(status_lines)
    except Exception as e:
        return f"Error retrieving system status: {str(e)}"


if __name__ == "__main__":
    mcp.run()