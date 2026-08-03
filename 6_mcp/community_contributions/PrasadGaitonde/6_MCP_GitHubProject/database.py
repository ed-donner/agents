import logging

logger = logging.getLogger("github_agent_db")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def write_log(agent_name: str, log_type: str, message: str):
    logger.info(f"[{agent_name}] [{log_type}] {message}")
