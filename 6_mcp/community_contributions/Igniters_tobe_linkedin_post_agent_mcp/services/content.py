from __future__ import annotations

import json
from difflib import SequenceMatcher
from functools import lru_cache

from db.repository import Repository, get_repository
from models.entities import DraftInput, DraftRecord


class ContentService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def save_idea(self, topic: str, goal: str, notes: str = "", urls: list[str] | None = None) -> dict:
        record = self.repository.save_idea(topic=topic, goal=goal, notes=notes, urls=urls or [])
        return record.model_dump()

    def create_draft_set(self, idea_id: str, bundle_id: str, drafts_json: str) -> dict:
        parsed = json.loads(drafts_json)
        drafts = [DraftInput.model_validate(item) for item in parsed]
        similarities = [self._similarity_score(draft) for draft in drafts]
        records = self.repository.save_drafts(
            idea_id=idea_id,
            bundle_id=bundle_id,
            drafts=drafts,
            similarity_scores=similarities,
        )
        return {
            "idea_id": idea_id,
            "bundle_id": bundle_id,
            "draft_ids": [record.id for record in records],
            "drafts": [record.model_dump() for record in records],
        }

    def revise_draft(self, draft_id: str, revised_draft_json: str, feedback: str = "") -> dict:
        original = self.repository.get_draft(draft_id)
        if not original:
            raise RuntimeError(f"Draft not found: {draft_id}")
        parsed = DraftInput.model_validate(json.loads(revised_draft_json))
        similarity = [self._similarity_score(parsed)]
        records = self.repository.save_drafts(
            idea_id=original.idea_id,
            bundle_id=original.bundle_id,
            drafts=[parsed],
            parent_draft_id=original.id,
            similarity_scores=similarity,
        )
        if feedback:
            self.repository.record_approval_decision(original.id, "feedback", feedback)
        return records[0].model_dump()

    def update_draft_content(
        self,
        draft_id: str,
        title: str,
        body: str,
        cta: str = "",
        link_url: str | None = None,
        feedback: str = "",
    ) -> dict:
        original = self.repository.get_draft(draft_id)
        if not original:
            raise RuntimeError(f"Draft not found: {draft_id}")
        if original.status == "published":
            raise RuntimeError("Published drafts cannot be edited.")
        cleaned_title = title.strip()
        cleaned_body = body.strip()
        cleaned_cta = cta.strip()
        cleaned_link = (link_url or "").strip() or None
        if not cleaned_title:
            raise RuntimeError("Draft title cannot be empty.")
        if not cleaned_body:
            raise RuntimeError("Draft body cannot be empty.")
        similarity = self._similarity_score(
            DraftInput(
                variant=original.variant,
                title=cleaned_title,
                body=cleaned_body,
                cta=cleaned_cta,
                link_url=cleaned_link,
                confidence=original.confidence,
                score=original.score,
                rationale=original.rationale,
            )
        )
        updated = self.repository.update_draft_content(
            draft_id=draft_id,
            title=cleaned_title,
            body=cleaned_body,
            cta=cleaned_cta,
            link_url=cleaned_link,
            similarity_score=similarity,
            status="draft",
        )
        if feedback.strip():
            self.repository.record_approval_decision(draft_id, "feedback", feedback)
        return updated.model_dump()

    def approve_draft(self, draft_id: str) -> dict:
        draft = self.repository.update_draft_status(draft_id, "approved")
        decision = self.repository.record_approval_decision(draft_id, "approved")
        return {"draft": draft.model_dump(), "decision": decision.model_dump()}

    def reject_draft(self, draft_id: str, feedback: str = "") -> dict:
        draft = self.repository.update_draft_status(draft_id, "rejected")
        decision = self.repository.record_approval_decision(draft_id, "rejected", feedback)
        return {"draft": draft.model_dump(), "decision": decision.model_dump()}

    def record_feedback(self, draft_id: str, feedback: str) -> dict:
        decision = self.repository.record_approval_decision(draft_id, "feedback", feedback)
        return decision.model_dump()

    def list_drafts(self, idea_id: str | None = None, limit: int = 50) -> list[dict]:
        return [draft.model_dump() for draft in self.repository.list_drafts(idea_id=idea_id, limit=limit)]

    def get_draft(self, draft_id: str) -> dict:
        draft = self.repository.get_draft(draft_id)
        if not draft:
            raise RuntimeError(f"Draft not found: {draft_id}")
        return draft.model_dump()

    def store_style_example(self, content: str, source_label: str) -> dict:
        return self.repository.save_voice_example(content=content, source_label=source_label).model_dump()

    def list_post_history(self, limit: int = 20) -> list[dict]:
        return [item.model_dump() for item in self.repository.list_published_posts(limit=limit)]

    def build_voice_profile(self) -> dict:
        voice_examples = [record.model_dump() for record in self.repository.list_voice_examples(limit=10)]
        recent_posts = [record.model_dump() for record in self.repository.list_published_posts(limit=10)]
        combined_text = [
            example["content"]
            for example in voice_examples
            if example["content"].strip()
        ] + [
            post["payload"].get("specificContent", {})
            .get("com.linkedin.ugc.ShareContent", {})
            .get("shareCommentary", {})
            .get("text", "")
            for post in recent_posts
        ]
        average_length = int(
            sum(len(text) for text in combined_text if text) / max(len([text for text in combined_text if text]), 1)
        )
        return {
            "voice_examples": voice_examples,
            "recent_posts": recent_posts,
            "average_length": average_length,
        }

    def sources_resource(self, bundle_id: str) -> dict:
        bundle = self.repository.get_research_bundle(bundle_id)
        if not bundle:
            raise RuntimeError(f"Research bundle not found: {bundle_id}")
        return bundle.model_dump()

    def draft_resource(self, draft_id: str) -> dict:
        return self.get_draft(draft_id)

    def history_resource(self, limit: int = 10) -> dict:
        return {"published_posts": self.list_post_history(limit=limit)}

    def voice_resource(self) -> dict:
        return self.build_voice_profile()

    def _similarity_score(self, draft: DraftInput) -> float:
        published_posts = self.repository.list_published_posts(limit=20)
        candidate = f"{draft.title}\n{draft.body}".strip().lower()
        if not candidate:
            return 0.0
        scores = []
        for post in published_posts:
            text = (
                post.payload.get("specificContent", {})
                .get("com.linkedin.ugc.ShareContent", {})
                .get("shareCommentary", {})
                .get("text", "")
            )
            if not text:
                continue
            scores.append(SequenceMatcher(None, candidate, text.lower()).ratio())
        return round(max(scores, default=0.0), 3)


@lru_cache(maxsize=1)
def get_content_service() -> ContentService:
    return ContentService(get_repository())
