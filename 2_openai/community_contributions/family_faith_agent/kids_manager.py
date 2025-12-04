from __future__ import annotations

from typing import AsyncGenerator, List
import html
import textwrap
from datetime import datetime, timedelta

from agents import Runner, trace, gen_trace_id
from kids_bible_agent import joyful_kids_bible_agent, FamilyBiblePlayPlan
from kids_verse_memory_agent import (
    joyful_kids_verse_memory_agent,
    VerseMemoryPlan,
)
from email_agent import email_agent  # Agent that uses the send_email tool inside


class JoyfulKidsManager:
    """
    Orchestrates the Joyful Kids Bible flows.

    - Any series theme (Christmas, Easter, Thankfulness, Everyday Jesus' love, etc.)
    - 5-day series of Bible playtime plans
    - One HTML email
    - Simple suggested calendar reminder (title + time + duration)
    """

    async def run_series(
        self,
        series_theme: str,
        ages: str = "3 and 5",
        duration_minutes: int = 15,
    ) -> AsyncGenerator[str, None]:
        """
        Create a 5-day themed Bible series and send as one HTML email.

        `series_theme` can be: "Christmas", "Easter", "Thankfulness",
        "Fruit of the Spirit", "Everyday Jesus' love", etc.

        Yields status updates and finally a markdown preview of the 5-day series.
        """
        trace_id = gen_trace_id()
        with trace("Joyful Kids Bible - Themed Series", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield f"Creating a 5-day '{series_theme}' Bible series for your family… 🌟"

            day_themes = self._build_day_themes(series_theme)

            plans: List[FamilyBiblePlayPlan] = []
            verse_memories: List[VerseMemoryPlan] = []

            # Generate content for each day, nudging the agent for variety + age-awareness
            for day_title in day_themes:
                prompt = textwrap.dedent(
                    f"""
                    You are designing a playful, age-appropriate family Bible time
                    for little kids.

                    Overall series theme: {series_theme}
                    Today's focus: {day_title}
                    Kids' ages: {ages}
                    Desired duration: {duration_minutes} minutes.

                    Please:
                    - Choose a Bible story and single key verse that fit today's focus.
                    - Make language and activities suitable for these ages.
                    - Use a different mix of activities (movement, crafts, role-play,
                      songs, or quiet reflection) than you might have used before.
                    - Avoid always using the same story or verse across different days
                      in the same series.
                    """
                )

                play_result = await Runner.run(joyful_kids_bible_agent, prompt)
                plan = play_result.final_output_as(FamilyBiblePlayPlan)
                plans.append(plan)

                vm_prompt = textwrap.dedent(
                    f"""
                    Verse: {plan.bible_verse}
                    Reference: {plan.verse_reference}
                    Theme: {series_theme}
                    Today's focus: {day_title}
                    Kids' ages: {ages}

                    Please make the motions and memory game fun and age-appropriate
                    for these kids, and vary the ideas across different days.
                    """
                )
                vm_result = await Runner.run(joyful_kids_verse_memory_agent, vm_prompt)
                verse_memories.append(vm_result.final_output_as(VerseMemoryPlan))

            # Build HTML + send email via email_agent
            html_body = self._build_html_email_series(
                series_theme=series_theme,
                duration_minutes=duration_minutes,
                plans=plans,
                verse_memories=verse_memories,
            )
            subject = f"Joyful Kids Bible – {series_theme} Family Series 🌟"

            # Let email_agent use its send_email tool internally
            await Runner.run(email_agent, html_body)

            yield "Email sent with your 5-day family Bible series! 💌"
            yield self._preview_markdown_series(series_theme, plans, verse_memories)

    # -------- INTERNAL HELPERS --------

    def _build_day_themes(self, series_theme: str) -> List[str]:
        """
        Build 5 day titles based on the overall series theme.

        Special handling for common holidays; otherwise, a generic 5-part journey.
        """
        theme_lower = series_theme.strip().lower()

        if "christmas" in theme_lower:
            return [
                "Day 1 – God’s promise: Angel visits Mary",
                "Day 2 – Journey to Bethlehem",
                "Day 3 – Jesus is born",
                "Day 4 – Shepherds hear the good news",
                "Day 5 – Wise men worship Jesus",
            ]
        if "easter" in theme_lower:
            return [
                "Day 1 – Jesus serves and loves",
                "Day 2 – The cross and God’s forgiveness",
                "Day 3 – The empty tomb: Jesus is alive",
                "Day 4 – Jesus meets His friends",
                "Day 5 – Go and share the good news",
            ]

        # Generic 5-day structure for any theme
        # e.g. Thankfulness, Kindness, Fruit of the Spirit, Everyday Jesus’ love
        return [
            f"Day 1 – {series_theme}: God’s love for us",
            f"Day 2 – {series_theme}: Jesus as our example",
            f"Day 3 – {series_theme}: How we can live this out",
            f"Day 4 – {series_theme}: With family and friends",
            f"Day 5 – {series_theme}: Sharing it with others",
        ]

    def _build_html_email_series(
        self,
        series_theme: str,
        duration_minutes: int,
        plans: List[FamilyBiblePlayPlan],
        verse_memories: List[VerseMemoryPlan],
    ) -> str:
        """HTML for the 5-day series, with a simple suggested calendar reminder."""

        def esc(x: str) -> str:
            return html.escape(x)

        # Suggest a time "today + 2 hours" as a friendly default (local time)
        now = datetime.now()
        suggested_start = now + timedelta(hours=2)
        nice_time = suggested_start.strftime("%A, %B %d at %I:%M %p").lstrip("0")

        days_html: List[str] = []
        for i, (plan, vm) in enumerate(zip(plans, verse_memories), start=1):
            days_html.append(
                f"""
          <div style="border-radius:16px;background:#fffdf8;padding:16px;margin-bottom:16px;">
            <h2 style="font-size:20px;margin-top:0;">Day {i}: {esc(plan.title)}</h2>
            <p><strong>📖 Verse:</strong> {esc(plan.bible_verse)}
               <span style="color:#777;">({esc(plan.verse_reference)})</span></p>
            <p><strong>🕯 Story:</strong> {esc(plan.story_summary)}</p>
            <p><strong>🎲 Game:</strong> {esc(plan.game_instructions)}</p>
            <p><strong>✂️ Activity:</strong> {esc(plan.activity_idea)}</p>
            <p><strong>💬 Talk:</strong></p>
            <ul>
              {''.join(f'<li>{esc(q)}</li>' for q in plan.family_questions)}
            </ul>
            <p><strong>💓 Remember the Verse</strong><br>
               Call &amp; Response: {esc(vm.call_and_response)}<br>
               Motions: {esc(vm.motions_description)}<br>
               Game: {esc(vm.repetition_game)}</p>
            <p><strong>🙏 Prayer:</strong> {esc(plan.short_prayer)}</p>
          </div>
            """
            )

        days_html_combined = "\n".join(days_html)

        # Simple suggested calendar reminder (no .ics link)
        calendar_block = f"""
        <div style="border-radius:16px;background:#fef3c7;padding:16px;margin-top:24px;">
          <h2 style="font-size:18px;margin-top:0;">📅 Suggested Calendar Reminder</h2>
          <p><strong>Title:</strong> Family Bible Time – {esc(series_theme)}</p>
          <p><strong>When:</strong> {esc(nice_time)} (adjust to a time that works best)</p>
          <p><strong>Duration:</strong> about {duration_minutes} minutes</p>
          <p style="font-size:13px;color:#7c2d12;">
            You can create a calendar event on your phone, tablet, or computer using this title and time.
          </p>
        </div>
        """

        return f"""
<html>
  <body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
               background:#fff7f2; color:#333; padding:16px;">
    <div style="max-width:800px;margin:0 auto;border-radius:20px;
                background:#ffffff;box-shadow:0 4px 14px rgba(0,0,0,0.08);
                padding:24px;">
      <h1 style="text-align:center;font-size:26px;margin-bottom:4px;">
        🌟 Joyful Kids Bible – {esc(series_theme)} Family Series 🌟
      </h1>
      <p style="text-align:center;margin-top:0;color:#777;">
        5 simple, playful family devotions for little hearts.
      </p>

      {days_html_combined}

      {calendar_block}

      <p style="font-size:13px;color:#aaa;text-align:center;margin-top:20px;">
        One little moment at a time, you are planting seeds of faith. 🌱
      </p>
    </div>
  </body>
</html>
"""

    def _preview_markdown_series(
        self,
        series_theme: str,
        plans: List[FamilyBiblePlayPlan],
        verse_memories: List[VerseMemoryPlan],
    ) -> str:
        out: List[str] = [f"# Joyful Kids – {series_theme} Family Series\n"]
        for i, (plan, vm) in enumerate(zip(plans, verse_memories), start=1):
            qs = "\n".join(f"- {q}" for q in plan.family_questions)
            out.append(
                f"""
## Day {i}: {plan.title}

**Verse:** {plan.bible_verse} ({plan.verse_reference})

Story: {plan.story_summary}

Game: {plan.game_instructions}

Activity: {plan.activity_idea}

Talk:
{qs}

Verse Memory:
- Call & Response: {vm.call_and_response}
- Motions: {vm.motions_description}
- Game: {vm.repetition_game}

Prayer: {plan.short_prayer}
"""
            )
        return "\n".join(out)
