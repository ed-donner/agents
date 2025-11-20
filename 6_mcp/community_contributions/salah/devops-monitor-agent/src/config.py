import os
from dotenv import load_dotenv

load_dotenv(override=True)


def get_env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return default


def get_env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return default


def get_env_str(key: str, default: str) -> str:
    return os.getenv(key, default)


class Config:
    OPENAI_API_KEY = get_env_str("OPENAI_API_KEY", "")
    MODEL_NAME = get_env_str("MODEL_NAME", "gpt-4o-mini")
    MAX_TURNS_MONITOR = get_env_int("MAX_TURNS_MONITOR", 5)
    MAX_TURNS_ALERT = get_env_int("MAX_TURNS_ALERT", 8)
    MCP_TIMEOUT = get_env_int("MCP_TIMEOUT", 60)
    MONITOR_INTERVAL = get_env_int("MONITOR_INTERVAL", 30)
    ALERT_INTERVAL = get_env_int("ALERT_INTERVAL", 45)
    CYCLE_INTERVAL = get_env_int("CYCLE_INTERVAL", 5)
    DEMO_DURATION = get_env_int("DEMO_DURATION", 2)
    RUN_DURATION = get_env_int("RUN_DURATION", 30)
    DB_FILE = get_env_str("DB_FILE", "devops_monitor.db")
    CLEANUP_DAYS = get_env_int("CLEANUP_DAYS", 7)
    CPU_WARNING_THRESHOLD = get_env_int("CPU_WARNING_THRESHOLD", 80)
    CPU_CRITICAL_THRESHOLD = get_env_int("CPU_CRITICAL_THRESHOLD", 95)
    MEMORY_WARNING_THRESHOLD = get_env_int("MEMORY_WARNING_THRESHOLD", 85)
    MEMORY_CRITICAL_THRESHOLD = get_env_int("MEMORY_CRITICAL_THRESHOLD", 90)
    DISK_WARNING_THRESHOLD = get_env_int("DISK_WARNING_THRESHOLD", 90)
    DISK_CRITICAL_THRESHOLD = get_env_int("DISK_CRITICAL_THRESHOLD", 95)
    LOAD_WARNING_MULTIPLIER = get_env_float("LOAD_WARNING_MULTIPLIER", 2.0)

    @classmethod
    def validate(cls):
        errors = []
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        if cls.MONITOR_INTERVAL < 1:
            errors.append("MONITOR_INTERVAL must be at least 1 second")
        if cls.ALERT_INTERVAL < 1:
            errors.append("ALERT_INTERVAL must be at least 1 second")
        return errors


config = Config()
