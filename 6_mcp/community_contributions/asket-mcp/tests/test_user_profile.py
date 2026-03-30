from __future__ import annotations

from asket_mcp.store.user_profile import get_user_profile_store


def test_profile_roundtrip(isolated_data_dir):
    s = get_user_profile_store()
    p0 = s.get_profile()
    assert p0.goals == ""
    s.upsert(goals="Learn ML", expertise_level="beginner", roadmap_markdown="# Week 1\n- setup")
    p1 = s.get_profile()
    assert p1.goals == "Learn ML"
    assert p1.expertise_level == "beginner"
    assert "Week 1" in p1.roadmap_markdown
    s.upsert(goals="Advanced ML", expertise_level=None)
    p2 = s.get_profile()
    assert p2.goals == "Advanced ML"
    assert p2.expertise_level == "beginner"
