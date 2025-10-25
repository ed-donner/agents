#!/usr/bin/env python3
import logging
import sys
from backend.api import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('trading_sim.log')
    ]
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting Trading Simulation Platform")
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
    logger.info("Trading Simulation Platform stopped")
