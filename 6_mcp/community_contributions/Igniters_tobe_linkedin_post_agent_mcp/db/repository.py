from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from config.settings import get_settings
from db.schema import SCHEMA
from models.entities import (
    ApprovalDecisionRecord,
    DraftInput,
    DraftRecord,
    IdeaRecord,
    OAuthSessionMetadata,
    PublishedPostRecord,
    ResearchBundleRecord,
    SourceItem,
    VoiceExampleRecord,
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class Repository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            for statement in SCHEMA:
                connection.execute(statement)
            connection.commit()

    def save_idea(self, topic: str, goal: str, notes: str, urls: list[str]) -> IdeaRecord:
        record = IdeaRecord(
            id=str(uuid.uuid4()),
            topic=topic,
            goal=goal,
            notes=notes,
            urls=urls,
            created_at=now_iso(),
        )
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO ideas (id, topic, goal, notes, urls_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (record.id, record.topic, record.goal, record.notes, json.dumps(record.urls), record.created_at),
            )
            connection.commit()
        return record

    def get_idea(self, idea_id: str) -> IdeaRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
        if not row:
            return None
        return IdeaRecord(
            id=row["id"],
            topic=row["topic"],
            goal=row["goal"],
            notes=row["notes"],
            urls=json.loads(row["urls_json"]),
            created_at=row["created_at"],
        )

    def save_research_bundle(
        self,
        idea_id: str,
        query: str,
        summary: str,
        sources: list[SourceItem],
    ) -> ResearchBundleRecord:
        record = ResearchBundleRecord(
            id=str(uuid.uuid4()),
            idea_id=idea_id,
            query=query,
            summary=summary,
            sources=sources,
            created_at=now_iso(),
        )
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO research_bundles (id, idea_id, query, summary, sources_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.idea_id,
                    record.query,
                    record.summary,
                    json.dumps([source.model_dump() for source in record.sources]),
                    record.created_at,
                ),
            )
            connection.commit()
        return record

    def get_research_bundle(self, bundle_id: str) -> ResearchBundleRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM research_bundles WHERE id = ?", (bundle_id,)
            ).fetchone()
        if not row:
            return None
        return ResearchBundleRecord(
            id=row["id"],
            idea_id=row["idea_id"],
            query=row["query"],
            summary=row["summary"],
            sources=[SourceItem.model_validate(item) for item in json.loads(row["sources_json"])],
            created_at=row["created_at"],
        )

    def list_research_bundles(self, idea_id: str | None = None) -> list[ResearchBundleRecord]:
        query = "SELECT * FROM research_bundles"
        params: tuple[Any, ...] = ()
        if idea_id:
            query += " WHERE idea_id = ?"
            params = (idea_id,)
        query += " ORDER BY created_at DESC"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            ResearchBundleRecord(
                id=row["id"],
                idea_id=row["idea_id"],
                query=row["query"],
                summary=row["summary"],
                sources=[SourceItem.model_validate(item) for item in json.loads(row["sources_json"])],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_drafts(
        self,
        idea_id: str,
        bundle_id: str,
        drafts: list[DraftInput],
        parent_draft_id: str | None = None,
        similarity_scores: list[float] | None = None,
    ) -> list[DraftRecord]:
        created_at = now_iso()
        records: list[DraftRecord] = []
        with self.connect() as connection:
            for index, draft in enumerate(drafts):
                record = DraftRecord(
                    id=str(uuid.uuid4()),
                    idea_id=idea_id,
                    bundle_id=bundle_id,
                    parent_draft_id=parent_draft_id,
                    variant=draft.variant,
                    title=draft.title,
                    body=draft.body,
                    cta=draft.cta,
                    link_url=draft.link_url,
                    confidence=draft.confidence,
                    score=draft.score,
                    rationale=draft.rationale,
                    similarity_score=(similarity_scores or [0.0] * len(drafts))[index],
                    status="draft",
                    created_at=created_at,
                    updated_at=created_at,
                )
                connection.execute(
                    """
                    INSERT INTO drafts (
                        id, idea_id, bundle_id, parent_draft_id, variant, title, body, cta, link_url,
                        confidence, score, rationale, similarity_score, status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        record.idea_id,
                        record.bundle_id,
                        record.parent_draft_id,
                        record.variant,
                        record.title,
                        record.body,
                        record.cta,
                        record.link_url,
                        record.confidence,
                        record.score,
                        record.rationale,
                        record.similarity_score,
                        record.status,
                        record.created_at,
                        record.updated_at,
                    ),
                )
                records.append(record)
            connection.commit()
        return records

    def get_draft(self, draft_id: str) -> DraftRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            return None
        return self._draft_from_row(row)

    def list_drafts(self, idea_id: str | None = None, limit: int = 50) -> list[DraftRecord]:
        query = "SELECT * FROM drafts"
        params: list[Any] = []
        if idea_id:
            query += " WHERE idea_id = ?"
            params.append(idea_id)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._draft_from_row(row) for row in rows]

    def update_draft_status(self, draft_id: str, status: str) -> DraftRecord:
        updated_at = now_iso()
        with self.connect() as connection:
            connection.execute(
                "UPDATE drafts SET status = ?, updated_at = ? WHERE id = ?",
                (status, updated_at, draft_id),
            )
            connection.commit()
        draft = self.get_draft(draft_id)
        if not draft:
            raise RuntimeError(f"Draft not found: {draft_id}")
        return draft

    def update_draft_content(
        self,
        draft_id: str,
        title: str,
        body: str,
        cta: str,
        link_url: str | None,
        similarity_score: float,
        status: str,
    ) -> DraftRecord:
        updated_at = now_iso()
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE drafts
                SET title = ?, body = ?, cta = ?, link_url = ?, similarity_score = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, body, cta, link_url, similarity_score, status, updated_at, draft_id),
            )
            connection.commit()
        draft = self.get_draft(draft_id)
        if not draft:
            raise RuntimeError(f"Draft not found: {draft_id}")
        return draft

    def record_approval_decision(
        self,
        draft_id: str,
        decision: str,
        feedback: str = "",
    ) -> ApprovalDecisionRecord:
        record = ApprovalDecisionRecord(
            id=str(uuid.uuid4()),
            draft_id=draft_id,
            decision=decision,
            feedback=feedback,
            created_at=now_iso(),
        )
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO approval_decisions (id, draft_id, decision, feedback, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (record.id, record.draft_id, record.decision, record.feedback, record.created_at),
            )
            connection.commit()
        return record

    def list_approval_decisions(self, draft_id: str) -> list[ApprovalDecisionRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM approval_decisions WHERE draft_id = ? ORDER BY created_at DESC",
                (draft_id,),
            ).fetchall()
        return [
            ApprovalDecisionRecord(
                id=row["id"],
                draft_id=row["draft_id"],
                decision=row["decision"],
                feedback=row["feedback"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_voice_example(self, content: str, source_label: str) -> VoiceExampleRecord:
        record = VoiceExampleRecord(
            id=str(uuid.uuid4()),
            content=content,
            source_label=source_label,
            created_at=now_iso(),
        )
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO voice_examples (id, content, source_label, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (record.id, record.content, record.source_label, record.created_at),
            )
            connection.commit()
        return record

    def list_voice_examples(self, limit: int = 20) -> list[VoiceExampleRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM voice_examples ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            VoiceExampleRecord(
                id=row["id"],
                content=row["content"],
                source_label=row["source_label"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_published_post(
        self,
        draft_id: str,
        post_urn: str,
        author_urn: str,
        payload: dict[str, Any],
        response: dict[str, Any],
        link_url: str | None = None,
    ) -> PublishedPostRecord:
        record = PublishedPostRecord(
            id=str(uuid.uuid4()),
            draft_id=draft_id,
            post_urn=post_urn,
            author_urn=author_urn,
            payload=payload,
            response=response,
            link_url=link_url,
            created_at=now_iso(),
        )
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO published_posts (
                    id, draft_id, post_urn, author_urn, payload_json, response_json, link_url, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.draft_id,
                    record.post_urn,
                    record.author_urn,
                    json.dumps(record.payload),
                    json.dumps(record.response),
                    record.link_url,
                    record.created_at,
                ),
            )
            connection.execute(
                "UPDATE drafts SET status = ?, updated_at = ? WHERE id = ?",
                ("published", record.created_at, draft_id),
            )
            connection.commit()
        return record

    def list_published_posts(self, limit: int = 20) -> list[PublishedPostRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM published_posts ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            PublishedPostRecord(
                id=row["id"],
                draft_id=row["draft_id"],
                post_urn=row["post_urn"],
                author_urn=row["author_urn"],
                payload=json.loads(row["payload_json"]),
                response=json.loads(row["response_json"]),
                link_url=row["link_url"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_oauth_session(self, session: OAuthSessionMetadata) -> OAuthSessionMetadata:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO oauth_session (
                    id, member_sub, person_urn, name, email, access_token_ref, expires_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    member_sub=excluded.member_sub,
                    person_urn=excluded.person_urn,
                    name=excluded.name,
                    email=excluded.email,
                    access_token_ref=excluded.access_token_ref,
                    expires_at=excluded.expires_at,
                    updated_at=excluded.updated_at
                """,
                (
                    session.id,
                    session.member_sub,
                    session.person_urn,
                    session.name,
                    session.email,
                    session.access_token_ref,
                    session.expires_at,
                    session.created_at,
                    session.updated_at,
                ),
            )
            connection.commit()
        return session

    def get_oauth_session(self) -> OAuthSessionMetadata | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM oauth_session WHERE id = 'default'").fetchone()
        if not row:
            return None
        return OAuthSessionMetadata(
            id=row["id"],
            member_sub=row["member_sub"],
            person_urn=row["person_urn"],
            name=row["name"],
            email=row["email"],
            access_token_ref=row["access_token_ref"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _draft_from_row(self, row: sqlite3.Row) -> DraftRecord:
        return DraftRecord(
            id=row["id"],
            idea_id=row["idea_id"],
            bundle_id=row["bundle_id"],
            parent_draft_id=row["parent_draft_id"],
            variant=row["variant"],
            title=row["title"],
            body=row["body"],
            cta=row["cta"],
            link_url=row["link_url"],
            confidence=row["confidence"],
            score=row["score"],
            rationale=row["rationale"],
            similarity_score=row["similarity_score"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@lru_cache(maxsize=1)
def get_repository() -> Repository:
    repository = Repository(get_settings().db_path)
    repository.initialize()
    return repository
