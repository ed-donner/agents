import os
import json
import logging
import asyncio
import uuid
import base64
from pathlib import Path
from typing import Callable, TypedDict, Literal, Any
from dataclasses import dataclass
from langchain_core.runnables import RunnableConfig

from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -- SCHEMAS ---------------------------------------------------------


class BrandConfig(BaseModel):
    name: str
    tagline: str | None = None
    logo_url: str | None = None
    colors: list[str] = Field(default_factory=list)
    fonts: list[str] = Field(default_factory=list)
    tone: str = "neutral"


class LayoutConfig(BaseModel):
    section_order: list[str] = Field(default_factory=list)
    grid_preference: str = "balanced"
    spacing: Literal["compact", "balanced", "spacious"] = "balanced"


class MediaAsset(BaseModel):
    type: str
    url: str


class ContentConfig(BaseModel):
    headline: str
    subheadline: str | None = None
    cta_text: str = "Get Started"
    cta_url: str = "#"
    key_features: list[str] = Field(default_factory=list)
    media_assets: list[MediaAsset] = Field(default_factory=list)


class ConstraintsConfig(BaseModel):
    framework: str | None = None
    accessibility_level: Literal["A", "AA", "AAA"] = "AA"
    browser_support: list[str] = Field(default_factory=list)


class ParsedGuidelines(BaseModel):
    brand: BrandConfig
    layout: LayoutConfig
    content: ContentConfig
    components: list[str] = Field(default_factory=list)
    style_keywords: list[str] = Field(default_factory=list)
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)


class ValidationScores(BaseModel):
    html_quality: float = 0.0
    guideline_conformance: float = 0.0
    visual_render: float = 0.0
    overall: float = 0.0


class ValidationIssue(BaseModel):
    category: Literal["html_quality", "guideline_conformance", "visual_render"]
    severity: Literal["critical", "warning", "info"]
    description: str
    suggestion: str


class ValidationReport(BaseModel):
    passed: bool = False
    iteration: int = 0
    scores: ValidationScores = Field(default_factory=ValidationScores)
    issues: list[ValidationIssue] = Field(default_factory=list)
    planner_feedback: str = ""


# -- PIPELINE STATE --------------------------------------------------


class PipelineState(TypedDict):
    user_prompt: str
    user_feedback: str | None
    planner_feedback: str | None
    guidelines: ParsedGuidelines | None
    plan: str | None
    code: str | None
    screenshot_path: str | None
    validation_report: ValidationReport | None
    iteration: int
    max_iterations: int
    run_count: int
    status: Literal["pending", "planning", "developing", "validating", "done", "error"]
    errors: list[str]


# -- PIPELINE CONFIG -------------------------------------------------


@dataclass
class PipelineConfig:
    """Configuration passed to every agent node via RunnableConfig configurable."""

    on_status: Callable[[str], None] | None = None
    output_dir: str = "./output"


def get_pipeline_config(config: dict) -> PipelineConfig:
    """
    Extract PipelineConfig from a LangGraph RunnableConfig dict.
    LangGraph passes config as a dict with a 'configurable' key.
    """
    configurable = config.get("configurable", {}) if isinstance(config, dict) else {}
    return configurable.get("pipeline_config", PipelineConfig())


# -- LLM CLIENTS -----------------------------------------------------


def get_planner_llm():
    """GPT-4o for the Planner Agent (use gpt-4o until gpt-5 is GA)."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model="gpt-5-nano",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


async def call_gemini(system_prompt: str, user_prompt: str) -> str:
    """
    Call Gemini 2.5 Pro directly via the google-generativeai SDK.
    Bypasses langchain-google-genai entirely to avoid the ModelProfile
    import conflict with langchain-core versions.
    The blocking SDK call is offloaded to a thread executor to stay async-safe.
    """
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite-preview",
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(temperature=0.4),
    )
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: model.generate_content(user_prompt),
    )
    return response.text


def get_validation_llm():
    """Claude Sonnet for the Validation Agent."""
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )


# -- PLANNER AGENT (GPT-4o / GPT-5) ---------------------------------

PLANNER_SYSTEM_PROMPT = """You are a senior UX strategist and brand consultant.
Analyze the user's description and produce a comprehensive design brief.

You receive:
- user_prompt: the user's natural language description
- user_feedback (optional, HIGHEST PRIORITY): direct improvement requests
  from the user after reviewing a previous version
- replanning_feedback (optional): structured critique from the validation
  agent about technical/conformance issues

Rules:
- user_feedback overrides everything — treat it as hard constraints
- replanning_feedback overrides your own preferences when not contradicted
  by user_feedback
- Infer missing values intelligently — never leave critical fields empty
- colors must be actual harmonious hex codes matching the brand personality
- style_keywords must be specific and actionable (not vague like "modern")
- section_order must reflect conversion best practices for the described product
- Output ONLY the JSON object. No prose, no markdown fences.

JSON schema to follow exactly:
{
  "brand": {
    "name": "string",
    "tagline": "string or null",
    "logo_url": "string or null",
    "colors": ["#hex1", "#hex2", "#hex3"],
    "fonts": ["Font Name 1", "Font Name 2"],
    "tone": "string"
  },
  "layout": {
    "section_order": ["navbar", "hero", "features", ...],
    "grid_preference": "string",
    "spacing": "compact|balanced|spacious"
  },
  "content": {
    "headline": "string",
    "subheadline": "string or null",
    "cta_text": "string",
    "cta_url": "#",
    "key_features": ["feature1", "feature2"],
    "media_assets": [{"type": "image", "url": "https://example.com/image.jpg"}]
  },
  "components": ["navbar", "hero", "features", "testimonials", "footer"],
  "style_keywords": ["keyword1", "keyword2"],
  "constraints": {
    "framework": null,
    "accessibility_level": "AA",
    "browser_support": ["Chrome", "Firefox", "Safari"]
  }
}
"""


def build_planner_prompt(state: PipelineState) -> str:
    """Build the user prompt for the Planner agent."""
    prompt = f"Generate a complete design brief for the following homepage:\n\nUSER PROMPT: {state['user_prompt']}\n"

    if state.get("user_feedback"):
        prompt += f"\nUSER FEEDBACK (HIGHEST PRIORITY — override everything else):\n{state['user_feedback']}\n"

    if state.get("planner_feedback"):
        prompt += f"\nINTERNAL VALIDATION FEEDBACK (apply unless contradicted by user feedback):\n{state['planner_feedback']}\n"

    prompt += "\nReturn ONLY valid JSON. No prose, no code fences."
    return prompt


async def planner_agent(state: PipelineState, config: dict) -> PipelineState:
    """
    Planner Agent — uses GPT-5 to generate structured design guidelines
    from the user's natural language prompt.
    """
    logger.info("Running Planner Agent")
    pipeline_cfg = get_pipeline_config(config)

    state["status"] = "planning"
    state["iteration"] = state.get("iteration", 0) + 1

    if pipeline_cfg.on_status:
        pipeline_cfg.on_status(
            "🎯 **Planner Agent** *(GPT-5)* — Analyzing requirements..."
        )

    try:
        llm = get_planner_llm()
        prompt = build_planner_prompt(state)

        response = await llm.ainvoke(
            [("system", PLANNER_SYSTEM_PROMPT), ("human", prompt)]
        )

        content = response.content.strip()
        # Strip markdown fences if present
        for fence in ["```json", "```"]:
            if content.startswith(fence):
                content = content[len(fence) :]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        guidelines_data = json.loads(content)
        guidelines = ParsedGuidelines(**guidelines_data)

        state["guidelines"] = guidelines
        state["status"] = "developing"

        if pipeline_cfg.on_status:
            colors = guidelines.brand.colors[:3]
            color_str = " · ".join(colors) if colors else "not specified"
            components_str = (
                " → ".join(guidelines.components)
                if guidelines.components
                else "not specified"
            )
            style_str = (
                ", ".join(guidelines.style_keywords)
                if guidelines.style_keywords
                else "not specified"
            )
            msg = (
                f"🎯 **Planner Agent** *(GPT-5)* — Brief ready\n\n"
                f'**Brand:** {guidelines.brand.name} — "{guidelines.brand.tagline or "no tagline"}"\n'
                f"**Tone:** {guidelines.brand.tone}\n"
                f"**Palette:** {color_str}\n"
                f"**Components:** {components_str}\n"
                f"**Style:** {style_str}\n"
            )
            pipeline_cfg.on_status(msg)

    except json.JSONDecodeError as e:
        logger.error(f"Planner: JSON parse error: {e}")
        state["errors"].append(f"Planner JSON error: {str(e)}")
        state["status"] = "error"
    except Exception as e:
        logger.error(f"Planner agent error: {e}")
        state["errors"].append(f"Planner error: {str(e)}")
        state["status"] = "error"

    return state


# -- DEVELOPER AGENT (Gemini 2.5 Pro) --------------------------------

DEVELOPER_SYSTEM_PROMPT = """You are an expert frontend developer specialized in building modern,
high-converting homepages.

You receive structured design guidelines and a layout plan.
Produce a complete, self-contained HTML/CSS/JS homepage.

TECHNICAL STANDARDS:
- Semantic HTML5 (ARIA labels, proper heading hierarchy)
- CSS custom properties for the entire design system
- Mobile-first responsive (breakpoints: 375px, 768px, 1280px)
- Vanilla JS unless a framework is specified in constraints
- Google Fonts allowed — choose distinctive, characterful pairings
  NEVER use Inter, Roboto, Arial, or system-ui
- Images: use https://picsum.photos with descriptive seeds
- No Lorem Ipsum — generate sharp, on-brand copy

DESIGN STANDARDS:
- Commit fully to the style_keywords — make them unmistakably visible
- Typography: pair a striking display font with a refined body font
- Color: implement brand palette via CSS variables; dominant + sharp accent
- Motion: staggered CSS entrance animations on load, meaningful hover states
- Layout: asymmetry, generous whitespace, grid-breaking elements where fitting
- Accessibility: meet the level in constraints, contrast ratio >= 4.5:1

OUTPUT FORMAT — respond ONLY with these XML tags, no text outside them:
<plan_confirmation>
One paragraph confirming your interpretation of the layout and style direction.
</plan_confirmation>

<code>
Complete self-contained HTML file (CSS in <style>, JS in <script>).
</code>

<decisions>
- [typography]: decision — rationale
- [color]: decision — rationale
- [layout]: decision — rationale
- [animation]: decision — rationale
</decisions>
"""

DEVELOPER_PLAN_PROMPT = """Based on these guidelines, describe your layout strategy ONLY.
Do not write any code yet.

Guidelines:
{guidelines_json}

Provide a concise plan covering:
1. Section structure and order
2. Typography choices (specific Google Font names)
3. Color usage strategy
4. Key animations/interactions
5. Layout approach (grid/flex decisions)
"""

DEVELOPER_CODE_PROMPT = """Based on these guidelines and your plan, produce the complete homepage.

Guidelines:
{guidelines_json}

Your approved plan:
{plan}

Now produce the full HTML. Follow the OUTPUT FORMAT exactly.
"""


async def developer_agent(state: PipelineState, config: dict) -> PipelineState:
    """
    Developer Agent — uses Gemini 3.1 Flash Lite Preview to generate the complete homepage
    in two steps: plan first, then code.
    """
    logger.info("Running Developer Agent")
    pipeline_cfg = get_pipeline_config(config)

    state["status"] = "developing"

    if pipeline_cfg.on_status:
        pipeline_cfg.on_status(
            "⚙️ **Developer Agent** *(Gemini 3.1 Flash Lite Preview)* — Planning layout..."
        )

    try:
        guidelines = state.get("guidelines")
        if not guidelines:
            raise ValueError("No guidelines available from Planner")

        guidelines_json = guidelines.model_dump_json(indent=2)

        # Step 1: Generate plan (direct Gemini SDK — no langchain-google-genai)
        plan_text = await call_gemini(
            system_prompt=DEVELOPER_SYSTEM_PROMPT,
            user_prompt=DEVELOPER_PLAN_PROMPT.format(guidelines_json=guidelines_json),
        )
        plan_text = plan_text.strip()
        state["plan"] = plan_text

        if pipeline_cfg.on_status:
            pipeline_cfg.on_status(
                "⚙️ **Developer Agent** *(Gemini 3.1 Flash Lite Preview)* — Generating HTML/CSS/JS..."
            )

        # Step 2: Generate code
        response_text = await call_gemini(
            system_prompt=DEVELOPER_SYSTEM_PROMPT,
            user_prompt=DEVELOPER_CODE_PROMPT.format(
                guidelines_json=guidelines_json,
                plan=plan_text,
            ),
        )

        # Parse XML blocks
        def extract_block(text: str, tag: str) -> str:
            start = text.find(f"<{tag}>")
            end = text.find(f"</{tag}>")
            if start != -1 and end != -1:
                return text[start + len(tag) + 2 : end].strip()
            return ""

        plan_confirmation = extract_block(response_text, "plan_confirmation")
        code = extract_block(response_text, "code")
        decisions_raw = extract_block(response_text, "decisions")

        # Fallback: if no <code> block, use full response (Gemini sometimes ignores format)
        if not code:
            logger.warning("Developer: no <code> block found, using full response")
            code = response_text

        # Strip ```html fences from code if present
        if code.startswith("```html"):
            code = code[7:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()

        decisions = [
            d.strip() for d in decisions_raw.split("\n") if d.strip().startswith("-")
        ]

        # Write to output
        output_dir = Path(pipeline_cfg.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        html_path = output_dir / "homepage.html"
        html_path.write_text(code, encoding="utf-8")

        state["code"] = code
        state["status"] = "validating"

        if pipeline_cfg.on_status:
            decisions_summary = (
                "\n  • ".join(decisions[:3])
                if decisions
                else "Standard modern layout applied"
            )
            plan_short = (
                (plan_confirmation[:250] + "...")
                if len(plan_confirmation) > 250
                else plan_confirmation
            )
            msg = (
                f"⚙️ **Developer Agent** *(Gemini 3.1 Flash Lite Preview)* — Homepage built\n\n"
                f"**Plan:** {plan_short or 'Layout complete'}\n"
                f"**Key decisions:**\n  • {decisions_summary}\n"
                f"**Output:** `{html_path}`\n"
            )
            pipeline_cfg.on_status(msg)

    except Exception as e:
        logger.error(f"Developer agent error: {e}")
        state["errors"].append(f"Developer error: {str(e)}")
        state["status"] = "error"

    return state


# -- VALIDATION AGENT (Claude Sonnet) --------------------------------


async def validate_html_quality(html: str) -> tuple[float, list[ValidationIssue]]:
    """Check HTML quality using BeautifulSoup — no LLM needed."""
    from bs4 import BeautifulSoup

    issues: list[ValidationIssue] = []
    soup = BeautifulSoup(html, "html5lib")
    critical_count = 0
    warning_count = 0

    # Check semantic structure
    semantic_tags = ["header", "main", "footer", "nav", "section"]
    missing_tags = [tag for tag in semantic_tags if not soup.find(tag)]
    if missing_tags:
        critical_count += 1
        issues.append(
            ValidationIssue(
                category="html_quality",
                severity="critical",
                description=f"Missing semantic tags: {', '.join(missing_tags)}",
                suggestion=f"Add missing semantic elements: {', '.join(missing_tags)}",
            )
        )

    # Check alt attributes
    images_without_alt = [img for img in soup.find_all("img") if not img.get("alt")]
    if images_without_alt:
        critical_count += 1
        issues.append(
            ValidationIssue(
                category="html_quality",
                severity="critical",
                description=f"{len(images_without_alt)} image(s) missing alt attributes",
                suggestion="Add descriptive alt attributes to all <img> elements",
            )
        )

    # Check h1 count
    h1_tags = soup.find_all("h1")
    if len(h1_tags) != 1:
        warning_count += 1
        issues.append(
            ValidationIssue(
                category="html_quality",
                severity="warning",
                description=f"Found {len(h1_tags)} <h1> tags (should be exactly 1)",
                suggestion="Use exactly one <h1> per page for proper heading hierarchy",
            )
        )

    # Check inline styles
    inline_styles = soup.find_all(style=True)
    if inline_styles:
        warning_count += 1
        issues.append(
            ValidationIssue(
                category="html_quality",
                severity="warning",
                description=f"{len(inline_styles)} elements use inline style attributes",
                suggestion="Move inline styles to the <style> block using CSS classes",
            )
        )

    # Check viewport meta tag
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        critical_count += 1
        issues.append(
            ValidationIssue(
                category="html_quality",
                severity="critical",
                description="Missing viewport meta tag — page will not be mobile-responsive",
                suggestion='Add <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            )
        )

    # Check unlabeled interactive elements
    unlabeled = []
    for elem in soup.find_all(["a", "button", "input"]):
        if (
            not elem.get("aria-label")
            and not elem.get("title")
            and not elem.get_text(strip=True)
        ):
            unlabeled.append(elem.name)
    if unlabeled:
        warning_count += 1
        issues.append(
            ValidationIssue(
                category="html_quality",
                severity="warning",
                description=f"{len(unlabeled)} interactive element(s) lack accessible labels",
                suggestion="Add aria-label or visible text to all interactive elements",
            )
        )

    score = max(0.0, 1.0 - (critical_count * 0.2) - (warning_count * 0.05))
    return score, issues


async def validate_guideline_conformance(
    guidelines: ParsedGuidelines,
    html: str,
    llm,
) -> tuple[float, list[ValidationIssue]]:
    """Check guideline conformance using Claude Sonnet LLM."""
    # Limit HTML size sent to LLM (first 6000 chars covers structure + CSS vars)
    html_excerpt = html[:6000]

    prompt = f"""You are a QA engineer reviewing a homepage against design guidelines.

GUIDELINES:
{guidelines.model_dump_json(indent=2)}

HTML (first 6000 chars):
{html_excerpt}

Evaluate these criteria:
1. Are all required components present? (check guidelines.components)
2. Does the copy tone match guidelines.brand.tone?
3. Are brand colors visible in CSS (as hex values or variables)?
4. Are the key_features all mentioned in the content?
5. Does section structure respect guidelines.layout.section_order?

Return ONLY this JSON (no prose, no fences):
{{
  "score": 0.0,
  "issues": [
    {{"description": "string", "suggestion": "string", "severity": "critical|warning|info"}}
  ]
}}
"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        for fence in ["```json", "```"]:
            if content.startswith(fence):
                content = content[len(fence) :]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)
        issues = [
            ValidationIssue(
                category="guideline_conformance",
                severity=i.get("severity", "warning"),
                description=i["description"],
                suggestion=i["suggestion"],
            )
            for i in result.get("issues", [])
        ]
        return float(result.get("score", 0.5)), issues

    except Exception as e:
        logger.error(f"Guideline conformance check error: {e}")
        return 0.5, [
            ValidationIssue(
                category="guideline_conformance",
                severity="warning",
                description=f"Could not evaluate conformance: {str(e)}",
                suggestion="Manual review required",
            )
        ]


async def validate_visual_render(
    guidelines: ParsedGuidelines,
    html_path: Path,
    output_dir: Path,
    llm,
) -> tuple[float, list[ValidationIssue]]:
    """
    Take desktop + mobile screenshots via Playwright, then ask Claude Vision
    to evaluate them against the style guidelines.
    """
    from playwright.async_api import async_playwright

    issues: list[ValidationIssue] = []
    screenshot_path = output_dir / "screenshot.png"
    mobile_screenshot_path = output_dir / "screenshot_mobile.png"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Desktop screenshot
            page = await browser.new_page(viewport={"width": 1280, "height": 900})
            await page.goto(f"file://{html_path.resolve()}")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=str(screenshot_path), full_page=True)

            # Mobile screenshot
            mobile_page = await browser.new_page(viewport={"width": 375, "height": 812})
            await mobile_page.goto(f"file://{html_path.resolve()}")
            await mobile_page.wait_for_load_state("networkidle")
            await mobile_page.screenshot(
                path=str(mobile_screenshot_path), full_page=True
            )

            await browser.close()

        # Encode screenshots for Claude Vision
        desktop_b64 = base64.standard_b64encode(screenshot_path.read_bytes()).decode()
        mobile_b64 = base64.standard_b64encode(
            mobile_screenshot_path.read_bytes()
        ).decode()

        # Send actual images to Claude Vision
        vision_prompt = [
            {
                "type": "text",
                "text": (
                    f"You are a visual QA reviewer evaluating a homepage.\n\n"
                    f"Style keywords to match: {', '.join(guidelines.style_keywords)}\n"
                    f"Brand colors: {', '.join(guidelines.brand.colors)}\n"
                    f"Tone: {guidelines.brand.tone}\n\n"
                    "Image 1 is the desktop view. Image 2 is the mobile view.\n\n"
                    "Evaluate:\n"
                    "1. Are the style_keywords visually evident?\n"
                    "2. Is the layout well-structured with clear hierarchy?\n"
                    "3. Are there rendering issues (overflow, broken layout, clipping)?\n"
                    "4. Does it feel professional and on-brand?\n"
                    "5. Is the mobile layout properly responsive?\n\n"
                    "Return ONLY JSON (no prose, no fences):\n"
                    '{"score": 0.0, "issues": [{"description": "string", "suggestion": "string", "severity": "critical|warning|info"}]}'
                ),
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": desktop_b64,
                },
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": mobile_b64,
                },
            },
        ]

        vision_response = await llm.ainvoke(
            [{"role": "user", "content": vision_prompt}]
        )
        content = vision_response.content.strip()
        for fence in ["```json", "```"]:
            if content.startswith(fence):
                content = content[len(fence) :]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)
        issues = [
            ValidationIssue(
                category="visual_render",
                severity=i.get("severity", "warning"),
                description=i["description"],
                suggestion=i["suggestion"],
            )
            for i in result.get("issues", [])
        ]
        return float(result.get("score", 0.5)), issues

    except Exception as e:
        logger.error(f"Visual render check error: {e}")
        return 0.5, [
            ValidationIssue(
                category="visual_render",
                severity="warning",
                description=f"Could not evaluate visual render: {str(e)}",
                suggestion="Manual review required",
            )
        ]


async def validation_agent(state: PipelineState, config: dict) -> PipelineState:
    """
    Validation Agent — runs 3 parallel checks (HTML quality, guideline conformance,
    visual render) and decides whether to approve or trigger replanning.
    """
    logger.info("Running Validation Agent")
    pipeline_cfg = get_pipeline_config(config)

    state["status"] = "validating"
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 3)

    if pipeline_cfg.on_status:
        pipeline_cfg.on_status(
            f"🔍 **Validation Agent** *(Claude Sonnet)* — Running checks (iteration {iteration}/{max_iter})..."
        )

    try:
        html = state.get("code", "")
        guidelines = state.get("guidelines")

        if not html or not guidelines:
            raise ValueError("No code or guidelines to validate")

        output_dir = Path(pipeline_cfg.output_dir)
        html_path = output_dir / "homepage.html"
        llm = get_validation_llm()

        # Run all 3 checks in parallel
        (
            html_quality_score,
            html_issues,
            conformance_score,
            conformance_issues,
            visual_score,
            visual_issues,
        ) = await _run_checks_parallel(html, guidelines, html_path, output_dir, llm)

        all_issues = html_issues + conformance_issues + visual_issues
        overall = (
            (html_quality_score * 0.25)
            + (conformance_score * 0.40)
            + (visual_score * 0.35)
        )
        critical_count = sum(1 for i in all_issues if i.severity == "critical")
        passed = overall >= 0.75 and critical_count == 0

        # Build ValidationReport
        report = ValidationReport(
            passed=passed,
            iteration=iteration,
            scores=ValidationScores(
                html_quality=html_quality_score,
                guideline_conformance=conformance_score,
                visual_render=visual_score,
                overall=overall,
            ),
            issues=all_issues,
            planner_feedback="",
        )

        # Build planner feedback if not passed
        if not passed:
            critical_issues = [i for i in all_issues if i.severity == "critical"]
            warning_issues = [i for i in all_issues if i.severity == "warning"]
            feedback_parts = [f"REPLANNING REQUIRED — Iteration {iteration}/{max_iter}"]

            if critical_issues:
                feedback_parts.append(
                    "Critical issues: "
                    + "; ".join(
                        f"{i.description} → {i.suggestion}" for i in critical_issues[:3]
                    )
                )
            if warning_issues:
                feedback_parts.append(
                    "Warnings: " + "; ".join(i.description for i in warning_issues[:3])
                )

            top_changes = [f"- {i.suggestion}" for i in all_issues[:3]]
            feedback_parts.append(
                "Priority for next iteration: " + "; ".join(top_changes)
            )
            report.planner_feedback = " | ".join(feedback_parts)
            state["planner_feedback"] = report.planner_feedback

        state["validation_report"] = report
        # Keep status as pending so the graph router can decide
        state["status"] = "done" if passed else "pending"

        if pipeline_cfg.on_status:
            if passed:
                msg = (
                    f"✅ **Validation Agent** *(Claude Sonnet)* — Approved  *(iteration {iteration}/{max_iter})*\n\n"
                    f"| Dimension        | Score  |\n"
                    f"|------------------|--------|\n"
                    f"| HTML Quality     | {html_quality_score * 10:.1f}/10 |\n"
                    f"| Guideline Match  | {conformance_score * 10:.1f}/10 |\n"
                    f"| Visual Render    | {visual_score * 10:.1f}/10 |\n"
                    f"| **Overall**      | **{overall * 10:.1f}/10** |\n"
                )
            else:
                critical_list = (
                    "\n  • ".join(
                        i.description for i in all_issues if i.severity == "critical"
                    )[:3]
                    or "None"
                )
                warning_list = (
                    "\n  • ".join(
                        i.description for i in all_issues if i.severity == "warning"
                    )[:3]
                    or "None"
                )
                msg = (
                    f"❌ **Validation Agent** *(Claude Sonnet)* — Issues found  *(iteration {iteration}/{max_iter})*\n\n"
                    f"**Critical issues:**\n  • {critical_list}\n"
                    f"**Warnings:**\n  • {warning_list}\n"
                    f"↩️ Sending feedback to Planner Agent...\n"
                )
            pipeline_cfg.on_status(msg)

    except Exception as e:
        logger.error(f"Validation agent error: {e}")
        state["errors"].append(f"Validation error: {str(e)}")
        state["status"] = "error"

    return state


async def _run_checks_parallel(
    html: str,
    guidelines: ParsedGuidelines,
    html_path: Path,
    output_dir: Path,
    llm,
) -> tuple[float, list, float, list, float, list]:
    """Run all 3 validation checks concurrently."""
    (
        (html_score, html_issues),
        (conf_score, conf_issues),
        (vis_score, vis_issues),
    ) = await asyncio.gather(
        validate_html_quality(html),
        validate_guideline_conformance(guidelines, html, llm),
        validate_visual_render(guidelines, html_path, output_dir, llm),
    )
    return html_score, html_issues, conf_score, conf_issues, vis_score, vis_issues


# -- GRAPH ASSEMBLY -------------------------------------------------

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


def create_pipeline_graph():
    """Create and compile the LangGraph pipeline with conditional replanning loop."""
    from langchain_core.runnables import ensure_config

    graph = StateGraph(PipelineState)

    async def planner_node(state: PipelineState) -> PipelineState:
        config = ensure_config()
        return await planner_agent(state, config)

    async def developer_node(state: PipelineState) -> PipelineState:
        config = ensure_config()
        return await developer_agent(state, config)

    async def validation_node(state: PipelineState) -> PipelineState:
        config = ensure_config()
        return await validation_agent(state, config)

    async def handle_error(state: PipelineState) -> PipelineState:
        config = ensure_config()
        pipeline_cfg = get_pipeline_config(config)
        state["status"] = "error"
        if pipeline_cfg.on_status:
            errors = state.get("errors", ["Unknown error"])
            pipeline_cfg.on_status(f"❌ **Pipeline Error** — {'; '.join(errors[-2:])}")
        return state

    graph.add_node("planner_agent", planner_node)
    graph.add_node("developer_agent", developer_node)
    graph.add_node("validation_agent", validation_node)
    graph.add_node("handle_error", handle_error)

    def route_after_planner(state: PipelineState) -> str:
        """Skip to error handler if planner failed."""
        if state.get("status") == "error":
            return "error"
        return "develop"

    def route_after_developer(state: PipelineState) -> str:
        """Skip validation and go straight to error handler if developer failed."""
        if state.get("status") == "error":
            return "error"
        return "validate"

    graph.set_entry_point("planner_agent")
    graph.add_conditional_edges(
        "planner_agent",
        route_after_planner,
        {"develop": "developer_agent", "error": "handle_error"},
    )
    graph.add_conditional_edges(
        "developer_agent",
        route_after_developer,
        {"validate": "validation_agent", "error": "handle_error"},
    )

    def route_after_validation(state: PipelineState) -> str:
        """
        Route after validation:
        - approved  → END
        - replan    → planner_agent (loop)
        - error     → handle_error
        """
        # Hard error in validation node itself
        if state.get("status") == "error":
            return "error"

        report = state.get("validation_report")
        if report and report.passed:
            return "approved"

        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 3)
        if iteration >= max_iterations:
            state["errors"].append(
                f"Max iterations ({max_iterations}) reached without passing validation"
            )
            return "error"

        return "replan"

    graph.add_conditional_edges(
        "validation_agent",
        route_after_validation,
        {"approved": END, "replan": "planner_agent", "error": "handle_error"},
    )
    graph.add_edge("handle_error", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# -- ENTRY POINT -----------------------------------------------------


async def run_pipeline(
    user_prompt: str,
    user_feedback: str | None = None,
    max_iterations: int = 3,
    on_status: Callable[[str], None] | None = None,
    output_dir: str = "./output",
) -> PipelineState:
    """
    Run the complete multi-agent pipeline.

    Args:
        user_prompt:    Natural language description of the homepage.
        user_feedback:  Optional improvement feedback from the user (subsequent runs).
        max_iterations: Max internal validation loop iterations before hard stop.
        on_status:      Callback called with each agent's status message.
        output_dir:     Directory where homepage.html and screenshots are saved.

    Returns:
        Final PipelineState with status, code, validation_report, etc.
    """
    from langchain_core.runnables import RunnableConfig

    pipeline_cfg = PipelineConfig(on_status=on_status, output_dir=output_dir)

    initial_state: PipelineState = {
        "user_prompt": user_prompt,
        "user_feedback": user_feedback,
        "planner_feedback": None,
        "guidelines": None,
        "plan": None,
        "code": None,
        "screenshot_path": None,
        "validation_report": None,
        "iteration": 0,
        "max_iterations": max_iterations,
        "run_count": 1,
        "status": "pending",
        "errors": [],
    }

    compiled = create_pipeline_graph()

    # FIX: MemorySaver requires a thread_id in configurable
    thread_id = str(uuid.uuid4())

    result = await compiled.ainvoke(
        initial_state,
        config=RunnableConfig(
            configurable={
                "pipeline_config": pipeline_cfg,
                "thread_id": thread_id,  # Required by MemorySaver
            },
            recursion_limit=25,
        ),
    )

    return result


if __name__ == "__main__":

    async def test():
        def print_status(msg: str):
            print("\n" + "=" * 60)
            print(msg)
            print("=" * 60)

        result = await run_pipeline(
            user_prompt=(
                "Build a homepage for a B2B SaaS called Meridian that helps "
                "logistics companies track their fleet in real time. "
                "Bold, technical, trustworthy. Dark theme preferred."
            ),
            on_status=print_status,
        )
        print(f"\nFinal status: {result.get('status')}")
        report = result.get("validation_report")
        if report:
            print(f"Overall score: {report.scores.overall:.2f}")

    asyncio.run(test())
