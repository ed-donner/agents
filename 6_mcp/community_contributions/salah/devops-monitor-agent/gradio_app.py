import asyncio
import gradio as gr
from datetime import datetime
import threading
from src.devops_floor import DevOpsFloor
from src.simple_database import (init_database, get_system_summary, cleanup_old_data,
                                 get_active_alerts, get_recent_metrics)
from src.tracers import register_tracer


class MonitorUI:
    def __init__(self):
        self.floor = None
        self.is_running = False
        self.monitoring_thread = None
        init_database()
        register_tracer()

    def get_system_status(self):
        try:
            summary = get_system_summary()
            alerts = get_active_alerts()
            status_text = f"## System Status\n\n**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            status_text += f"### Active Alerts: {summary.get('active_alerts', 0)}\n\n"
            if alerts:
                for alert in alerts[:5]:
                    status_text += f"**{alert['title']}**: {alert['message']}\n"
                    status_text += f"_Created: {alert['created_at']}_\n\n"
            else:
                status_text += "No active alerts\n\n"
            status_text += f"### Agents Status\n\n"
            agents = summary.get('agents', {})
            if agents:
                for agent_name, status in agents.items():
                    status_text += f"**{agent_name}**: {status}\n"
            else:
                status_text += "_No agent runs yet_\n"
            return status_text
        except Exception as e:
            return f"Error getting status: {str(e)}"

    def get_metrics_display(self):
        try:
            metrics = get_recent_metrics(limit=10)
            if not metrics:
                return "No metrics collected yet"
            metrics_text = "## Recent Metrics\n\n| Timestamp | Type | Value | Status |\n|-----------|------|-------|--------|\n"
            for metric in metrics:
                timestamp = metric['timestamp'].split('.')[0] if '.' in metric['timestamp'] else metric['timestamp']
                metrics_text += f"| {timestamp} | {metric['metric_type']} | {metric['value']:.1f}% | {metric['status']} |\n"
            return metrics_text
        except Exception as e:
            return f"Error getting metrics: {str(e)}"

    def get_metrics_summary(self):
        try:
            summary = get_system_summary()
            metrics_summary = summary.get('metrics_summary', {})
            if not metrics_summary:
                return "No metrics data available"
            summary_text = "## Metrics Summary (Last Hour)\n\n"
            for metric_type, data in metrics_summary.items():
                avg = data.get('avg', 0)
                count = data.get('count', 0)
                metric_name = metric_type.replace('_', ' ').title()
                summary_text += f"**{metric_name}**: {avg:.1f}% (avg from {count} readings)\n"
            return summary_text
        except Exception as e:
            return f"Error getting summary: {str(e)}"

    async def run_test_cycle_async(self):
        try:
            self.floor = DevOpsFloor()
            await self.floor.run_single_cycle()
            return "Test cycle completed successfully"
        except Exception as e:
            return f"Test cycle failed: {str(e)}"

    def run_test_cycle(self):
        return asyncio.run(self.run_test_cycle_async())

    async def start_monitoring_async(self, duration_minutes):
        try:
            self.is_running = True
            self.floor = DevOpsFloor()
            await self.floor.run_continuous(duration_minutes=duration_minutes)
            self.is_running = False
            return f"Monitoring completed ({duration_minutes} minutes)"
        except Exception as e:
            self.is_running = False
            return f"Monitoring failed: {str(e)}"

    def start_monitoring(self, duration_minutes):
        if self.is_running:
            return "Monitoring is already running"
        def run_async():
            asyncio.run(self.start_monitoring_async(duration_minutes))
        self.monitoring_thread = threading.Thread(target=run_async, daemon=True)
        self.monitoring_thread.start()
        return f"Monitoring started for {duration_minutes} minutes"

    def stop_monitoring(self):
        if not self.is_running:
            return "Monitoring is not running"
        if self.floor:
            self.floor.stop()
        self.is_running = False
        return "Monitoring stopped"

    def cleanup(self, days):
        try:
            cleanup_old_data(days=days)
            return f"Cleaned up data older than {days} days"
        except Exception as e:
            return f"Cleanup failed: {str(e)}"

    def get_monitoring_status(self):
        return "Monitoring is **RUNNING**" if self.is_running else "Monitoring is **STOPPED**"


def create_ui():
    monitor = MonitorUI()
    with gr.Blocks(title="DevOps Monitor Dashboard", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# DevOps Monitor Dashboard\nReal-time system monitoring with AI agents")
        with gr.Row():
            refresh_btn = gr.Button("Refresh Data", variant="secondary", scale=1)
            monitoring_status = gr.Markdown(monitor.get_monitoring_status())
        with gr.Tabs():
            with gr.Tab("Dashboard"):
                with gr.Row():
                    with gr.Column(scale=2):
                        status_display = gr.Markdown(monitor.get_system_status())
                    with gr.Column(scale=1):
                        metrics_summary = gr.Markdown(monitor.get_metrics_summary())
            with gr.Tab("Metrics"):
                metrics_display = gr.Markdown(monitor.get_metrics_display())
            with gr.Tab("Control"):
                gr.Markdown("### Monitoring Controls")
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Start Monitoring")
                        duration_slider = gr.Slider(minimum=1, maximum=60, value=30, step=1, label="Duration (minutes)")
                        start_btn = gr.Button("Start Monitoring", variant="primary")
                        start_output = gr.Textbox(label="Start Status", lines=2)
                    with gr.Column():
                        gr.Markdown("#### Stop Monitoring")
                        stop_btn = gr.Button("Stop Monitoring", variant="stop")
                        stop_output = gr.Textbox(label="Stop Status", lines=2)
                gr.Markdown("---")
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Single Test Cycle")
                        test_btn = gr.Button("Run Test Cycle", variant="secondary")
                        test_output = gr.Textbox(label="Test Status", lines=3)
                    with gr.Column():
                        gr.Markdown("#### Cleanup Old Data")
                        cleanup_days = gr.Slider(minimum=1, maximum=30, value=7, step=1, label="Delete data older than (days)")
                        cleanup_btn = gr.Button("Cleanup", variant="secondary")
                        cleanup_output = gr.Textbox(label="Cleanup Status", lines=2)
            with gr.Tab("Help"):
                gr.Markdown("""
                ## How to Use DevOps Monitor

                ### Dashboard
                - View system status and active alerts
                - See metrics summary with averages

                ### Metrics
                - View recent metric readings
                - Shows CPU, memory, and disk usage

                ### Control Panel
                **Start Monitoring**: Run continuous monitoring for specified duration
                **Stop Monitoring**: Stop the monitoring process
                **Test Cycle**: Run a single monitoring cycle to test the system
                **Cleanup**: Remove old data from database

                ### Configuration
                Edit `.env` file to configure:
                - Monitoring intervals
                - Alert thresholds
                - Email settings (SendGrid)
                - Model settings
                """)

        def refresh_all():
            return (monitor.get_system_status(), monitor.get_metrics_display(),
                    monitor.get_metrics_summary(), monitor.get_monitoring_status())

        refresh_btn.click(fn=refresh_all, outputs=[status_display, metrics_display, metrics_summary, monitoring_status])
        start_btn.click(fn=monitor.start_monitoring, inputs=[duration_slider], outputs=[start_output])
        stop_btn.click(fn=monitor.stop_monitoring, outputs=[stop_output])
        test_btn.click(fn=monitor.run_test_cycle, outputs=[test_output])
        cleanup_btn.click(fn=monitor.cleanup, inputs=[cleanup_days], outputs=[cleanup_output])
        demo.load(fn=refresh_all, outputs=[status_display, metrics_display, metrics_summary, monitoring_status])
    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True, inbrowser=True)
