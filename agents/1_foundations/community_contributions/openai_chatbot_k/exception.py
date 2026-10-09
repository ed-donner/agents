class RateLimitError(Exception):
    def __init__(self, message="Too many requests! Please try again tomorrow.") -> None:
        self.message = message
