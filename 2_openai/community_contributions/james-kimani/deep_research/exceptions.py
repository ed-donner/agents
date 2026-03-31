class BadInputError(Exception):
    """User typed something we can't work with."""
    pass


class StepError(Exception):
    """Something went wrong during one of the pipeline steps."""

    def __init__(self, step: str, reason: str):
        self.step = step
        self.reason = reason
        super().__init__(f"{step}: {reason}")
