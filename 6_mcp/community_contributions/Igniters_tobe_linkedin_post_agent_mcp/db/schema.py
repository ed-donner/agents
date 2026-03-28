SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS ideas (
        id TEXT PRIMARY KEY,
        topic TEXT NOT NULL,
        goal TEXT NOT NULL,
        notes TEXT NOT NULL,
        urls_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_bundles (
        id TEXT PRIMARY KEY,
        idea_id TEXT NOT NULL,
        query TEXT NOT NULL,
        summary TEXT NOT NULL,
        sources_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS drafts (
        id TEXT PRIMARY KEY,
        idea_id TEXT NOT NULL,
        bundle_id TEXT NOT NULL,
        parent_draft_id TEXT,
        variant TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        cta TEXT NOT NULL,
        link_url TEXT,
        confidence TEXT NOT NULL,
        score REAL NOT NULL,
        rationale TEXT NOT NULL,
        similarity_score REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS approval_decisions (
        id TEXT PRIMARY KEY,
        draft_id TEXT NOT NULL,
        decision TEXT NOT NULL,
        feedback TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS published_posts (
        id TEXT PRIMARY KEY,
        draft_id TEXT NOT NULL,
        post_urn TEXT NOT NULL,
        author_urn TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        response_json TEXT NOT NULL,
        link_url TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS voice_examples (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        source_label TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS oauth_session (
        id TEXT PRIMARY KEY,
        member_sub TEXT NOT NULL,
        person_urn TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        access_token_ref TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
]
