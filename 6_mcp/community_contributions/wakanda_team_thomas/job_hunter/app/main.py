"""
Job Hunter - Streamlit UI

Run with: uv run streamlit run app/main.py
"""

import asyncio
import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config import get_settings
from src.db.models import init_database
from src.db.repository import ProfileRepository, JobRepository
from src.manager import HuntManager


settings = get_settings()
SessionFactory = init_database(settings.database_url)


def get_repositories():
    """Get database repositories."""
    session = SessionFactory()
    return ProfileRepository(session), JobRepository(session)


st.set_page_config(
    page_title="Job Hunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar():
    """Render the sidebar navigation."""
    st.sidebar.title("Job Hunter")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Upload Resume", "Profile", "Jobs Dashboard", "Settings"],
        label_visibility="collapsed",
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Quick Stats**")
    
    profile_repo, job_repo = get_repositories()
    profiles = profile_repo.get_all()
    
    if profiles:
        st.sidebar.metric("Profiles", len(profiles))
        
        total_jobs = 0
        matched_jobs = 0
        for profile in profiles:
            stats = job_repo.get_stats(profile.id)
            total_jobs += stats.total_jobs
            matched_jobs += stats.applied_jobs + stats.interview_jobs
        
        st.sidebar.metric("Total Jobs", total_jobs)
        st.sidebar.metric("Applied/Interview", matched_jobs)
    else:
        st.sidebar.info("No profiles yet")
    
    return page


def render_upload_page():
    """Render the resume upload page."""
    st.title("Upload Resume")
    st.markdown("Upload your resume to start job hunting. Supported formats: PDF, DOCX")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=["pdf", "docx"],
            help="Max file size: 1 MB",
        )
        
        match_threshold_pct = st.slider(
            "Match Score Threshold (%)",
            min_value=50,
            max_value=100,
            value=60,
            step=5,
            help="Only jobs with match score above this threshold will be saved",
        )
        match_threshold = match_threshold_pct / 100.0
        
        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name}")
            
            if st.button("Start Job Hunt", type="primary"):
                with st.spinner("Processing resume and searching for jobs..."):
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=Path(uploaded_file.name).suffix
                    ) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    
                    try:
                        manager = HuntManager()
                        result = asyncio.run(manager.hunt(tmp_path, match_threshold=match_threshold))
                        
                        if result.status == "completed":
                            st.success("Job hunt completed!")
                            
                            col_a, col_b, col_c = st.columns(3)
                            col_a.metric("Profile ID", result.profile_id)
                            col_b.metric("Jobs Found", result.jobs_found)
                            col_c.metric("Jobs Matched", f"{result.jobs_matched} ({match_threshold_pct}%+)")
                            
                            st.info(f"Duration: {result.duration_seconds:.2f}s")
                            
                            if result.trace_url:
                                st.markdown(f"[View Trace]({result.trace_url})")
                        else:
                            st.error(f"Hunt failed: {result.error}")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    
                    finally:
                        Path(tmp_path).unlink(missing_ok=True)
    
    with col2:
        st.markdown("### How it works")
        st.markdown("""
        1. **Parse Resume** - Extract text and structure data
        2. **Build Profile** - Create searchable profile
        3. **Search Jobs** - Query multiple job boards
        4. **Match & Save** - Filter matches above threshold
        """)
        
        st.markdown("### Job Boards")
        st.markdown("""
        - RemoteOK
        - Remotive
        - Arbeitnow
        
        Only 100% remote worldwide positions.
        """)


def render_profile_page():
    """Render the profile management page."""
    st.title("Profile Management")
    
    profile_repo, job_repo = get_repositories()
    profiles = profile_repo.get_all()
    
    if not profiles:
        st.info("No profiles yet. Upload a resume to create one.")
        return
    
    profile_options = {f"{p.name} ({p.email})": p.id for p in profiles}
    selected = st.selectbox("Select Profile", list(profile_options.keys()))
    
    if selected:
        profile_id = profile_options[selected]
        profile = profile_repo.get_by_id(profile_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basic Info")
            st.text(f"Name: {profile.name}")
            st.text(f"Email: {profile.email}")
            st.text(f"Phone: {profile.phone or 'N/A'}")
            st.text(f"Location: {profile.location or 'N/A'}")
            
            if profile.summary:
                st.markdown("**Summary**")
                st.text(profile.summary)
        
        with col2:
            st.subheader("Skills")
            skills = profile.get_skills()
            if skills:
                for skill in skills[:10]:
                    level = skill.get("level", "")
                    years = skill.get("years", "")
                    info = []
                    if level:
                        info.append(level)
                    if years:
                        info.append(f"{years}y")
                    extra = f" ({', '.join(info)})" if info else ""
                    st.markdown(f"- {skill['name']}{extra}")
            else:
                st.text("No skills listed")
        
        st.markdown("---")
        
        st.subheader("Keywords for Job Matching")
        keywords = profile.get_keywords()
        if keywords:
            st.markdown(", ".join(keywords))
        else:
            st.text("No keywords")
        
        st.markdown("---")
        
        st.subheader("Search for New Jobs")
        custom_keywords = st.text_input(
            "Additional keywords (comma-separated)",
            placeholder="python, django, aws",
        )
        
        search_threshold_pct = st.slider(
            "Match Score Threshold (%)",
            min_value=50,
            max_value=100,
            value=60,
            step=5,
            key="search_threshold",
        )
        search_threshold = search_threshold_pct / 100.0
        
        if st.button("Search Now"):
            search_keywords = keywords.copy() if keywords else []
            if custom_keywords:
                search_keywords.extend([k.strip() for k in custom_keywords.split(",")])
            
            if not search_keywords:
                st.warning("Please add some keywords to search")
            else:
                with st.spinner("Searching job boards..."):
                    manager = HuntManager()
                    result = asyncio.run(manager.search_only(profile_id, search_keywords, search_threshold))
                    
                    if result.status == "completed":
                        st.success(f"Found {result.jobs_found} jobs, {result.jobs_matched} matched {search_threshold_pct}%+")
                    else:
                        st.error(f"Search failed: {result.error}")


def render_jobs_page():
    """Render the jobs dashboard page."""
    st.title("Jobs Dashboard")
    
    profile_repo, job_repo = get_repositories()
    profiles = profile_repo.get_all()
    
    if not profiles:
        st.info("No profiles yet. Upload a resume to start.")
        return
    
    profile_options = {f"{p.name}": p.id for p in profiles}
    selected = st.selectbox("Select Profile", list(profile_options.keys()))
    
    if not selected:
        return
    
    profile_id = profile_options[selected]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "New", "Applied", "Interview", "Offered", "Rejected"],
        )
    
    with col2:
        min_score = st.slider("Min Match Score", 0.0, 1.0, 0.6, 0.05)
    
    with col3:
        sort_by = st.selectbox("Sort By", ["Match Score", "Date Added", "Company"])
    
    status_value = None if status_filter == "All" else status_filter.lower()
    jobs = job_repo.get_by_profile(profile_id, status=status_value, min_score=min_score)
    
    if sort_by == "Match Score":
        jobs = sorted(jobs, key=lambda j: j.match_score, reverse=True)
    elif sort_by == "Company":
        jobs = sorted(jobs, key=lambda j: j.company.lower())
    
    st.markdown(f"**{len(jobs)} jobs found**")
    st.markdown("---")
    
    if not jobs:
        st.info("No jobs matching the criteria")
        return
    
    for job in jobs:
        with st.expander(f"{job.title} at {job.company} - {job.match_score:.0%}"):
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
                st.markdown(f"**Company:** {job.company}")
                st.markdown(f"**Source:** {job.source}")
                if job.location:
                    st.markdown(f"**Location:** {job.location}")
                if job.salary_range:
                    st.markdown(f"**Salary:** {job.salary_range}")
                
                if job.description:
                    st.markdown("**Description:**")
                    st.text(job.description[:500] + "..." if len(job.description) > 500 else job.description)
                
                skills = job.get_required_skills()
                if skills:
                    st.markdown(f"**Required Skills:** {', '.join(skills)}")
                
                st.markdown(f"[Apply Here]({job.url})")
            
            with col_b:
                st.markdown(f"**Match Score:** {job.match_score:.0%}")
                st.markdown(f"**Status:** {job.status.upper()}")
                
                new_status = st.selectbox(
                    "Update Status",
                    ["new", "applied", "interview", "offered", "rejected"],
                    index=["new", "applied", "interview", "offered", "rejected"].index(job.status),
                    key=f"status_{job.id}",
                )
                
                notes = st.text_area("Notes", value=job.notes or "", key=f"notes_{job.id}")
                
                if st.button("Save", key=f"save_{job.id}"):
                    from src.schemas.job import JobUpdate
                    job_repo.update(job.id, JobUpdate(status=new_status, notes=notes))
                    st.success("Updated!")
                    st.rerun()


def render_settings_page():
    """Render the settings page."""
    st.title("Settings")
    
    st.subheader("Configuration")
    
    st.markdown("**Database**")
    st.code(settings.database_url)
    
    st.markdown("**Match Threshold**")
    st.text(f"{settings.job_match_threshold:.0%}")
    
    st.markdown("**Langfuse**")
    st.text(f"Enabled: {settings.langfuse_enabled}")
    if settings.langfuse_enabled:
        st.text(f"Host: {settings.langfuse_host}")
    
    st.markdown("---")
    
    st.subheader("Database Management")
    
    profile_repo, job_repo = get_repositories()
    profiles = profile_repo.get_all()
    
    st.markdown(f"**Profiles:** {len(profiles)}")
    
    total_jobs = sum(job_repo.get_stats(p.id).total_jobs for p in profiles)
    st.markdown(f"**Total Jobs:** {total_jobs}")
    
    if st.button("Clear All Data", type="secondary"):
        st.warning("This will delete all profiles and jobs!")
        if st.button("Confirm Delete", type="primary"):
            for profile in profiles:
                jobs = job_repo.get_by_profile(profile.id)
                for job in jobs:
                    job_repo.delete(job.id)
                profile_repo.delete(profile.id)
            st.success("All data cleared")
            st.rerun()


def main():
    """Main application entry point."""
    page = render_sidebar()
    
    if page == "Upload Resume":
        render_upload_page()
    elif page == "Profile":
        render_profile_page()
    elif page == "Jobs Dashboard":
        render_jobs_page()
    elif page == "Settings":
        render_settings_page()


if __name__ == "__main__":
    main()
