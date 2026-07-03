from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException
from typing import List
import time
from backend.utils.logger import get_logger

logger = get_logger()

MAX_RETRIES = 3
BASE_DELAY = 2


def search_code_examples(query: str, language: str) -> List[str]:
    search_query = f"{query} {language} code example"
    results = []

    for attempt in range(MAX_RETRIES):
        try:
            if attempt == 0:
                logger.log_web_search(query=search_query, language=language)
            else:
                logger.logger.info(
                    f"Web Search retry attempt {attempt + 1}/{MAX_RETRIES} for query='{search_query}'"
                )

            with DDGS() as ddgs:
                for result in ddgs.text(search_query, max_results=5):
                    if result.get("body"):
                        results.append(result["body"])

            logger.log_web_search(
                query=search_query, language=language, results_count=len(results)
            )
            return results[:5]

        except DuckDuckGoSearchException as e:
            error_msg = str(e)
            is_rate_limit = (
                "ratelimit" in error_msg.lower() or "rate limit" in error_msg.lower()
            )

            if is_rate_limit and attempt < MAX_RETRIES - 1:
                delay = BASE_DELAY * (2**attempt)
                logger.log_web_search(
                    query=search_query,
                    language=language,
                    error=f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})",
                )
                time.sleep(delay)
                continue
            else:
                if is_rate_limit:
                    logger.log_web_search(
                        query=search_query,
                        language=language,
                        error=f"Rate limit exceeded after {MAX_RETRIES} attempts. Returning empty results to allow workflow to continue.",
                    )
                else:
                    logger.log_web_search(
                        query=search_query, language=language, error=error_msg
                    )
                return []

        except Exception as e:
            error_msg = str(e)
            logger.log_web_search(
                query=search_query, language=language, error=error_msg
            )
            return []

    return []
