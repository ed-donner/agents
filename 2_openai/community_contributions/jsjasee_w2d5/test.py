import asyncio
import threading  # so see that it is on different threads

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException


def fetch_ddg_webpage_content(url: str) -> str:
    try:
        result = DDGS().extract(url)
        return result.get("content", "")

    except (RatelimitException, TimeoutException, DDGSException) as exc:
        return f"Search error: {type(exc).__name__}: {exc}"


def fetch_ddg_results(query: str, number_of_results: int = 5) -> str:
    try:
        print("🔴")
        print(threading.current_thread().name)
        results = DDGS().text(query, max_results=number_of_results)

        if not results:
            return "No results found."

        # THIS return statements returns the summary ('body' key) AND entire webpage (fetch_ddg_webpage_content) - can burn credits fast
        # return "\n\n".join(
        #     f"{item.get('title', '')}\n{item.get('href', '')}\n{item.get('body', '')}\n{fetch_ddg_webpage_content(item['href'])}"
        #     for item in results[:number_of_results]
        # )

        # THIS return statements returns only the summary ('body' key)
        return "\n\n".join(
            f"{item.get('title', '')}\n{item.get('href', '')}\n{item.get('body', '')}"
            for item in results[:number_of_results]
        )

    except (RatelimitException, TimeoutException, DDGSException) as exc:
        return f"Search error: {type(exc).__name__}: {exc}"


async def main() -> None:
    queries = [
        "OpenAI Agents SDK function tools",
        "DuckDuckGo DDGS Python package",
        "Python asyncio.to_thread examples",
    ]

    results = await asyncio.gather(
        *(asyncio.to_thread(fetch_ddg_results, query) for query in queries)
    )

    results_dict = {query: result for query, result in zip(queries, results)}

    print(results_dict)
    return results_dict


if __name__ == "__main__":
    print("🔴")
    print(threading.current_thread().name)
    asyncio.run(main())
