class CredibilityScorer:

    def score(self, url: str) -> float:
        if ".gov" in url or ".edu" in url:
            return 0.9
        if "wikipedia" in url:
            return 0.8
        if "blog" in url:
            return 0.4
        return 0.6