import datetime

LOGS = []

def log_action(action: str):
    entry = {
        "timestamp": str(datetime.datetime.now()),
        "action": action
    }
    LOGS.append(entry)
    return entry

def get_logs():
    return LOGS