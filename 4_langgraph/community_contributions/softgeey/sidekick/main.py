"""SideKick entry point — starts the FastAPI/Uvicorn server."""

import uvicorn
from config import config

if __name__ == "__main__":
    config.validate()
    uvicorn.run(
        "app:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=False,
        log_level="info",
    )
