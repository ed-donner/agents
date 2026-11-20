import re

from crewai.telemetry.tracing.last_run import read_last_run


TRACE_URL_PATTERN = re.compile(r"https://app\.crewai\.com\S*")


def extract_trace_url(text: str) -> str | None:
    match = TRACE_URL_PATTERN.search(text)
    return match.group(0).rstrip(".,);]") if match else None


def latest_trace_url(previous_execution_id: str | None) -> str | None:
    record = read_last_run()
    if not record:
        return None
    execution_id = record.get("execution_id")
    if not execution_id or execution_id == previous_execution_id:
        return None
    trace_url = record.get("trace_url")
    return str(trace_url) if trace_url else None
