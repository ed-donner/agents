import asyncio

from agents import Runner, gen_trace_id, trace

from tech_agents import clarifier, planner, searcher, analyst


class TechEval:

    async def run(self, question: str):
        tid = gen_trace_id()
        with trace("tech-eval", trace_id=tid):
            yield f"[status] trace: https://platform.openai.com/traces/trace?trace_id={tid}"
            yield "[status] clarifying question..."
            clarified = await self._clarify(question)
            yield f"[status] refined -> {clarified.refined}"

            plan = await self._plan(clarified)
            yield f"[status] searching ({len(plan.tasks)} queries)..."
            results = await self._search_all(plan)
            yield f"[status] analyzing {len(results)} results..."

            verdict = await self._analyze(question, clarified, results)
            yield verdict.full_report

    async def _clarify(self, q):
        r = await Runner.run(clarifier, q)
        return r.final_output

    async def _plan(self, clarified):
        prompt = f"Evaluate: {clarified.refined}\nAngles: {', '.join(clarified.angles)}"
        r = await Runner.run(planner, prompt)
        return r.final_output

    async def _search_all(self, plan):
        jobs = [asyncio.create_task(self._fetch(t)) for t in plan.tasks]
        hits = []
        for coro in asyncio.as_completed(jobs):
            if out := await coro:
                hits.append(out)
        return hits

    async def _fetch(self, task) -> str | None:
        try:
            r = await Runner.run(searcher, f"{task.term}\nContext: {task.rationale}")
            return str(r.final_output)
        except Exception:
            return None

    async def _analyze(self, original, clarified, summaries):
        blob = (
            f"Question: {original}\n"
            f"Refined: {clarified.refined}\n"
            f"Angles: {', '.join(clarified.angles)}\n\n"
            f"Research ({len(summaries)} sources):\n"
            + "\n---\n".join(summaries)
        )
        r = await Runner.run(analyst, blob)
        return r.final_output
