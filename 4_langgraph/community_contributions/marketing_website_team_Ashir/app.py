"""
Entry point for the Marketing Website Team sidekick without any UI.

This script defines the requirements and success criteria, passes them
to the sidekick, and prints the result once.
"""

import asyncio

from .sidekick import MarketingWebsiteSidekick


async def main() -> None:
    # High-level product requirements given to the team
    requirements = (
        "You are a product team building a marketing website for a digital "
        "marketing agency. The site must have three tabs/pages: Home, About Us, "
        "Contact Us. The Home page should have a strong hero section, an "
        "attractive carousel on the landing area, informative sections, and a "
        "clear header and footer. The Contact Us page must include a cool-looking "
        "contact form that sends data to the backend and stores it in a database. "
        "The site must also include a subscription/newsletter flow that captures "
        "emails and stores them via the backend and database."
    )

    # Explicit success criteria used by the manager/evaluator
    success_criteria = (
        "The final product must provide: (1) a Home tab with hero, carousel, "
        "informational sections, header, and footer; (2) an About Us tab with "
        "clear company information; (3) a Contact Us tab with a styled contact "
        "form wired to backend APIs and a database; and (4) a subscription "
        "experience (section/page) wired to backend APIs and a database to "
        "store subscribers. In addition to descriptions, the backend worker must "
        "write real backend code files (e.g., under sandbox/backend/...), the "
        "frontend worker must write real React files (e.g., under sandbox/frontend/...), "
        "and the QA worker must write at least one QA artefact (e.g., sandbox/qa/test_plan.md) "
        "using the save_file tool. Backend, frontend, and QA work together until these "
        'requirements are clearly implemented in code and tested.'
    )

    message = requirements

    sidekick = MarketingWebsiteSidekick()
    await sidekick.setup()

    history: list[dict] = []
    history = await sidekick.run_superstep(message, success_criteria, history)

    for entry in history:
        role = entry.get("role", "unknown")
        content = entry.get("content", "")
        print(f"{role.upper()}: {content}\n")

    sidekick.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
