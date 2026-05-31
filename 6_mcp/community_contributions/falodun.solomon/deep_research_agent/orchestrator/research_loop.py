import asyncio
from memory.state import ResearchState
from mcp_client.utils.response_normalizer import ResponseNormalizer


class ResearchOrchestrator:

    def __init__(
        self,
        planner,
        executor,
        reflection_engine,
        credibility_scorer,
        synthesizer,
        max_concurrency: int = 5,
    ):
        self.planner = planner
        self.executor = executor
        self.reflection_engine = reflection_engine
        self.credibility_scorer = credibility_scorer
        self.synthesizer = synthesizer
        self.semaphore = asyncio.Semaphore(max_concurrency)

    # =========================
    # Helper: Extract URL safely
    # =========================
    def _extract_url(self, item: dict):
        return (
            item.get("url")
            or item.get("link")
            or item.get("href")
        )

    # =========================
    # Process single URL
    # =========================
    async def _process_url(self, url: str, state: ResearchState):

        if not url:
            return None

        if url in state.visited_urls:
            return None

        score = self.credibility_scorer.score(url)

        if score < 0.5:
            return None

        async with self.semaphore:
            state.visited_urls.add(url)

            try:
                # Replace unavailable tool with working one
                result = await self.executor.execute({
                    "tool": "search_web",
                    "input": {"query": url}
                })

                content = ResponseNormalizer.extract_data(result)

                return {
                    "url": url,
                    "content": content,
                    "score": score
                }

            except Exception as e:
                print(f"[ERROR] Processing URL failed: {url}, error: {e}")
                return None

    # =========================
    # Process batch in parallel
    # =========================
    async def _process_batch(self, urls, state):
        tasks = [
            self._process_url(url, state)
            for url in urls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            r for r in results
            if r and not isinstance(r, Exception)
        ]

    # =========================
    # MAIN ENTRY
    # =========================
    async def run(self, query: str):
        state = ResearchState()

        # =========================
        # STEP 1: SEARCH
        # =========================
        search_response = await self.executor.execute({
            "tool": "search_web",
            "input": {"query": query}
        })

        results = ResponseNormalizer.extract_data(search_response)

        # Ensure list
        if not isinstance(results, list):
            results = []

        urls = [
            self._extract_url(r)
            for r in results[:5]
            if self._extract_url(r)
        ]

        print(f"[DEBUG] Extracted URLs: {urls}")

        # =========================
        # STEP 2: PARALLEL PROCESS
        # =========================
        initial_sources = await self._process_batch(urls, state)
        state.sources.extend(initial_sources)

        # =========================
        # STEP 3: REFLECTION
        # =========================
        reflection = await self.reflection_engine.reflect(query, state)

        enough = False

        if isinstance(reflection, dict):
            enough = reflection.get("enough", False)

        # =========================
        # STEP 4: REFINED SEARCH
        # =========================
        if not enough:
            refined_query = await self.planner.refiner.refine(query, state)

            extra_response = await self.executor.execute({
                "tool": "search_web",
                "input": {"query": refined_query}
            })

            extra_results = ResponseNormalizer.extract_data(extra_response)

            if not isinstance(extra_results, list):
                extra_results = []

            extra_urls = [
                self._extract_url(r)
                for r in extra_results[:3]
                if self._extract_url(r)
            ]

            print(f"[DEBUG] Extra URLs: {extra_urls}")

            extra_sources = await self._process_batch(extra_urls, state)
            state.sources.extend(extra_sources)

        # =========================
        # STEP 5: SOURCE RANKING
        # =========================
        state.sources = sorted(
            state.sources,
            key=lambda x: x["score"],
            reverse=True
        )

        # =========================
        # STEP 6: FINAL SYNTHESIS
        # =========================
        final_answer = await self.synthesizer.synthesize(query, state)

        return {
            "answer": final_answer,
            "sources": state.sources
        }