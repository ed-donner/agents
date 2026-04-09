"""Hosts allowed for psychoeducation fetches (exact hostname match, no subdomains wildcard)."""

ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        "www.nimh.nih.gov",
        "www.nhs.uk",
        "www.who.int",
        "www.apa.org",
        "www.mhanational.org",
    }
)


def is_allowed_host(hostname: str) -> bool:
    h = hostname.lower().rstrip(".")
    return h in ALLOWED_HOSTS
