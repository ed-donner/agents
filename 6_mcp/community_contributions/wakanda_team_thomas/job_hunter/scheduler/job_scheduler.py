"""
Job Scheduler - Periodic job search using APScheduler.

Automatically searches for jobs at configured intervals for all profiles.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config import get_settings
from src.db.models import init_database
from src.db.repository import ProfileRepository
from src.manager import HuntManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("job_scheduler")


class JobScheduler:
    """
    Scheduler for periodic job searches.
    
    Runs background job searches for all profiles at configured intervals.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self._session_factory = None
        self._running = False
    
    def _get_session_factory(self):
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = init_database(self.settings.database_url)
        return self._session_factory
    
    async def _search_all_profiles(self):
        """Search jobs for all profiles."""
        logger.info("Starting scheduled job search for all profiles")
        
        session = self._get_session_factory()()
        profile_repo = ProfileRepository(session)
        profiles = profile_repo.get_all()
        
        if not profiles:
            logger.info("No profiles found, skipping search")
            return
        
        manager = HuntManager()
        
        for profile in profiles:
            try:
                keywords = profile.get_keywords()
                if not keywords:
                    skills = profile.get_skills()
                    keywords = [s.get("name", "") for s in skills[:5]]
                
                if not keywords:
                    logger.warning(f"Profile {profile.id} has no keywords, skipping")
                    continue
                
                logger.info(f"Searching jobs for profile {profile.id}: {profile.name}")
                result = await manager.search_only(profile.id, keywords)
                
                logger.info(
                    f"Profile {profile.id}: found {result.jobs_found}, "
                    f"matched {result.jobs_matched}"
                )
                
            except Exception as e:
                logger.error(f"Error searching for profile {profile.id}: {e}")
        
        logger.info("Scheduled job search completed")
    
    def start(self, interval_hours: Optional[int] = None):
        """
        Start the scheduler.
        
        Args:
            interval_hours: Override default search interval
        """
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        interval = interval_hours or self.settings.search_interval_hours
        
        self.scheduler.add_job(
            self._search_all_profiles,
            trigger=IntervalTrigger(hours=interval),
            id="job_search",
            name="Periodic Job Search",
            replace_existing=True,
        )
        
        self.scheduler.start()
        self._running = True
        
        logger.info(f"Scheduler started. Searching every {interval} hours.")
    
    def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return
        
        self.scheduler.shutdown(wait=False)
        self._running = False
        
        logger.info("Scheduler stopped")
    
    async def run_once(self):
        """Run a single job search for all profiles."""
        await self._search_all_profiles()
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running
    
    def get_next_run(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        if not self._running:
            return None
        
        job = self.scheduler.get_job("job_search")
        if job:
            return job.next_run_time
        return None


async def main():
    """Run the scheduler as a standalone process."""
    logger.info("Starting Job Hunter Scheduler")
    
    scheduler = JobScheduler()
    
    logger.info("Running initial search...")
    await scheduler.run_once()
    
    scheduler.start()
    
    try:
        while True:
            next_run = scheduler.get_next_run()
            if next_run:
                logger.info(f"Next search scheduled for: {next_run}")
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
