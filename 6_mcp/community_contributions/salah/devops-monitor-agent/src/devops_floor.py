import asyncio
from datetime import datetime, timedelta
from typing import Dict
from .system_monitor import SystemMonitor
from .alert_manager import AlertManager
from .simple_database import get_system_summary, update_agent_status
from .config import config


class DevOpsFloor:
    def __init__(self):
        self.name = "DevOpsFloor"
        self.system_monitor = SystemMonitor()
        self.alert_manager = AlertManager()
        self.monitor_interval = config.MONITOR_INTERVAL
        self.alert_interval = config.ALERT_INTERVAL
        self.cycle_interval = config.CYCLE_INTERVAL
        self.is_running = False
        self.last_monitor_run = None
        self.last_alert_run = None
        self.cycle_count = 0
        
    def should_run_monitor(self) -> bool:
        if not self.last_monitor_run:
            return True
        return (datetime.now() - self.last_monitor_run).seconds >= self.monitor_interval

    def should_run_alerts(self) -> bool:
        if not self.last_alert_run:
            return True
        return (datetime.now() - self.last_alert_run).seconds >= self.alert_interval

    async def run_system_monitor(self):
        try:
            result = await self.system_monitor.run()
            self.last_monitor_run = datetime.now()
            return result
        except Exception as e:
            return None

    async def run_alert_manager(self):
        try:
            result = await self.alert_manager.run()
            self.last_alert_run = datetime.now()
            return result
        except Exception as e:
            return None

    async def run_cycle(self):
        self.cycle_count += 1
        tasks = []
        if self.should_run_monitor():
            tasks.append(("monitor", self.run_system_monitor()))
        if self.should_run_alerts():
            tasks.append(("alerts", self.run_alert_manager()))
        if not tasks:
            return
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

    async def run_continuous(self, duration_minutes: int = 5):
        self.is_running = True
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        try:
            while self.is_running and datetime.now() < end_time:
                await self.run_cycle()
                await asyncio.sleep(self.cycle_interval)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            pass
        finally:
            self.is_running = False

    def stop(self):
        self.is_running = False

    async def run_single_cycle(self):
        try:
            await self.run_cycle()
        except Exception as e:
            raise

    def get_status(self) -> Dict:
        summary = get_system_summary()
        return {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "last_monitor_run": self.last_monitor_run.isoformat() if self.last_monitor_run else None,
            "last_alert_run": self.last_alert_run.isoformat() if self.last_alert_run else None,
            "system_summary": summary,
            "intervals": {
                "monitor": self.monitor_interval,
                "alerts": self.alert_interval
            }
        }