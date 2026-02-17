import logging

# --- Logging Setup ---
def setup_logging():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logging.getLogger('hypercorn.error').name = 'hypercorn'
    return logging.getLogger(__name__)