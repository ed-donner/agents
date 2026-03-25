"""Job board API clients."""

from src.job_boards.base import JobBoardClient, JobBoardError
from src.job_boards.remoteok import RemoteOKClient
from src.job_boards.remotive import RemotiveClient
from src.job_boards.arbeitnow import ArbeitnowClient

__all__ = [
    "JobBoardClient",
    "JobBoardError",
    "RemoteOKClient",
    "RemotiveClient",
    "ArbeitnowClient",
]


def get_all_clients() -> list[type[JobBoardClient]]:
    """Return all available job board client classes."""
    return [
        RemoteOKClient,
        RemotiveClient,
        ArbeitnowClient,
    ]
