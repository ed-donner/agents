import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(override=True)


class Config:
    BASE_DIR = Path(__file__).parent

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    DOCKER_REGISTRY_USERNAME = os.getenv("DOCKER_REGISTRY_USERNAME")
    DOCKER_REGISTRY_PASSWORD = os.getenv("DOCKER_REGISTRY_PASSWORD")

    REPORT_OUTPUT_DIR = Path(os.getenv("REPORT_OUTPUT_DIR", str(BASE_DIR / "output" / "reports")))
    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    MIN_SEVERITY = os.getenv("MIN_SEVERITY", "MEDIUM")

    TRIVY_TIMEOUT_SECONDS = int(os.getenv("TRIVY_TIMEOUT_SECONDS", "300"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
