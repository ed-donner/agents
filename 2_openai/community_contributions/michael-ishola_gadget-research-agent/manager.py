"""Planner, research, and comparison agents for BudgetBuy AI."""

from __future__ import annotations

import json

from agents import (
    Agent,
    ModelSettings,
    Runner,
    trace,
    WebSearchTool,
)
from agents.exceptions import InputGuardrailTripwireTriggered

from schemas import (
    GadgetScopeCheck,
    NotificationDispatch,
    Recommendation,
    RankedProduct,
    ResearchOutput,
    ShoppingPlan,
)
from tools import (
    score_products,
    send_email,
    send_push,
    enforce_gadget_only,
)

gadget_guardrail_agent = Agent(
    name="BudgetBuyGadgetGuardrailAgent",
    instructions=(
        "You are a strict scope checker for a gadget shopping assistant.\n"
        "Return is_gadget_request=true only if the user request is clearly about buying gadgets/electronics "
        "such as phones, laptops, tablets, headphones/earbuds, monitors, TVs, cameras, gaming consoles, "
        "routers, wearables, chargers, or accessories.\n"
        "If the request is for non-gadget categories (e.g., food, fashion, furniture, insurance, batteries "
        "for home inverter systems, appliances, travel), return is_gadget_request=false with a short message "
        "explaining this assistant only supports gadget shopping."
    ),
    model="gpt-4o-mini",
    output_type=GadgetScopeCheck,
)


planner_agent = Agent(
    name="BudgetBuyPlannerAgent",
    instructions=(
        "You are a gadget shopping planner. Read the user request and output a concise plan with:\n"
        "- category\n"
        "- normalized query for product lookup\n"
        "- hard_constraints as bullet-like strings\n"
        # "- include_notifications true/false\n"
        "Allowed categories are gadget-only: smartphone, laptop, tablet, smartwatch, earbuds, "
        "headphones, gaming_console, monitor, tv, camera, router, power_bank, accessory.\n"
        "If request is not a gadget, set category to unsupported_non_gadget."
    ),
    model="gpt-4o-mini",
    output_type=ShoppingPlan,
    input_guardrails=[enforce_gadget_only],
)

research_agent = Agent(
    name="BudgetBuyResearchAgent",
    instructions=(
        "Research to find up to 8 real gadget products in the requested category and budget."
        " Prefer ecommerce or manufacturer pages with prices and specs."
        # " Extract candidates into structured fields."
        " For missing numeric values, use 0."
        " For missing text values, use 'unknown'."
        " Store three key gadget specs in key_specs.spec_1/spec_2/spec_3."
        " Set battery_life_hours where available."
        " Convert prices to NGN integers where possible and exclude products clearly above budget."
    ),
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
    tools=[WebSearchTool(search_context_size="low")],
    output_type=ResearchOutput,
)

comparison_agent = Agent(
    name="BudgetBuyComparisonAgent",
    instructions=(
        "First call score_products exactly once with the candidates JSON string. "
        "Then explain tradeoffs in plain language for the provided ranked shortlist. "
        "Focus on gadget value: budget fit, specs/performance, battery life, warranty, and availability."
    ),
    model="gpt-4o-mini",
)

notification_agent = Agent(
    name="BudgetBuyNotificationAgent",
    instructions=(
        "You manage user notifications for gadget shortlist updates.\n"
        "If email is provided, call send_email exactly once.\n"
        "If push_enabled is true, call send_push exactly once.\n"
        "If both are requested, call both tools.\n"
        "Return a single concise status string summarizing what was sent."
    ),
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
    tools=[send_email, send_push],
    output_type=NotificationDispatch,
)


class BudgetBuyManager:
    """Orchestrates planner -> researcher -> comparison and optional notifications."""

    async def run(
        self,
        user_request: str,
        budget_ngn: int,
        email: str = "",
        push_enabled: bool = False,
    ):
        with trace("BudgetBuy Research"):
            yield "[status] Planning your shopping strategy..."
            try:
                plan = await self._plan(user_request, budget_ngn)
            except InputGuardrailTripwireTriggered:
                yield (
                    "Gadget-only scope: this assistant handles gadget shopping research only "
                    "(phones, laptops, tablets, earbuds, TVs, consoles, accessories)."
                )
                return
            if plan.category == "unsupported_non_gadget":
                yield (
                    "This assistant currently supports gadget shopping only "
                    "(e.g., phones, laptops, tablets, earbuds, TVs, consoles)."
                )
                return

            yield "[status] Researching products and specs..."
            research = await self._research(plan, budget_ngn)
            if not research.candidates:
                yield "No products found within your budget and constraints."
                return

            yield "[status] Comparing candidates and explaining tradeoffs..."
            recommendation = await self._compare(plan, research)

            if email.strip() or push_enabled:
                recommendation.notify_message = await self._notify(
                    email=email,
                    push_enabled=push_enabled,
                    summary=recommendation.final_summary,
                    tradeoffs=recommendation.tradeoffs,
                )
            yield self._render_markdown(recommendation)

    async def _plan(
        self,
        user_request: str,
        budget_ngn: int,
    ) -> ShoppingPlan:
        payload = (
            f"Request: {user_request}\n"
            f"Budget (NGN): {budget_ngn}"
        )
        result = await Runner.run(planner_agent, payload)
        plan = result.final_output_as(ShoppingPlan)
        plan.hard_constraints.append(f"budget_ngn <= {budget_ngn}")
        return plan

    async def _research(self, plan: ShoppingPlan, budget_ngn: int) -> ResearchOutput:
        payload = (
            f"Category: {plan.category}\n"
            f"Query: {plan.query}\n"
            f"Budget (NGN): {budget_ngn}\n"
            f"Constraints: {plan.hard_constraints}"
        )
        result = await Runner.run(research_agent, payload)
        research = result.final_output_as(ResearchOutput)
        filtered = [p for p in research.candidates if p.price_ngn <= budget_ngn]
        return ResearchOutput(candidates=filtered)

    async def _compare(
        self,
        plan: ShoppingPlan,
        research: ResearchOutput,
    ) -> Recommendation:
        candidates_json = json.dumps([p.model_dump() for p in research.candidates])
        payload = (
            f"Category: {plan.category}\n"
            f"Constraints: {plan.hard_constraints}\n"
            f"Candidates JSON: {candidates_json}"
        )
        result = await Runner.run(comparison_agent, payload)

        ranked = score_products([p.model_dump() for p in research.candidates])
        shortlist = [
            RankedProduct(
                product_id=item["product"]["product_id"],
                score=float(item["score"]),
                reason=(
                    f"Category: {item['product']['category']}, "
                    f"Battery: {item['product'].get('battery_life_hours', 0)}h, "
                    f"Warranty: {item['product']['warranty_months']}m, "
                    f"Availability: {item['product']['availability']}, "
                    f"Price: NGN {item['product']['price_ngn']}"
                ),
            )
            for item in ranked[:3]
        ]
        best_product_id = shortlist[0].product_id
        tradeoffs = str(result.final_output)
        return Recommendation(
            best_product_id=best_product_id,
            shortlist=shortlist,
            tradeoffs=tradeoffs,
            final_summary=(
                f"Best under budget: {best_product_id}. "
                f"Shortlist size: {len(shortlist)}."
            ),
        )

    async def _notify(
        self,
        email: str,
        push_enabled: bool,
        summary: str,
        tradeoffs: str,
    ) -> str:
        payload = (
            f"email: {email.strip() or 'none'}\n"
            f"push_enabled: {push_enabled}\n"
            f"email_subject: BudgetBuy shortlist update\n"
            f"email_body: {summary}\n"
            f"push_title: BudgetBuy shortlist ready\n"
            f"push_message: {tradeoffs}"
        )
        result = await Runner.run(notification_agent, payload)
        dispatch = result.final_output_as(NotificationDispatch)
        return dispatch.status

    def _render_markdown(self, recommendation: Recommendation) -> str:
        rows = []
        for idx, item in enumerate(recommendation.shortlist, start=1):
            rows.append(f"{idx}. `{item.product_id}` - score `{item.score}`  \n   {item.reason}")
        notify = (
            f"\n\n### Notifications\n{recommendation.notify_message}"
            if recommendation.notify_message
            else ""
        )
        return (
            f"## BudgetBuy Recommendation\n\n"
            f"**Best pick:** `{recommendation.best_product_id}`\n\n"
            f"### Why this ranking\n{recommendation.tradeoffs}\n\n"
            f"### Shortlist\n" + "\n".join(rows) + notify
        )

