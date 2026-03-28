import asyncio
import json
import os
import random
import time
from crewai.tools import BaseTool
from pydantic import Field


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class JobApplyTool(BaseTool):
    """Fills and submits job application forms using Playwright browser automation."""

    name: str = "job_apply"
    description: str = (
        "Attempts to fill and submit a job application on a given platform. "
        "Input should be a JSON string with keys: "
        "'url' (job posting URL), 'platform' (linkedin/indeed/greenhouse/generic), "
        "'candidate_name', 'candidate_email', 'candidate_phone', "
        "'resume_path' (path to tailored resume file), "
        "'cover_letter_text' (cover letter content). "
        "Returns a JSON result with status (submitted/failed/blocked) and details."
    )

    def _run(self, application_data: str) -> str:
        try:
            data = json.loads(application_data)
        except json.JSONDecodeError:
            return json.dumps({
                "status": "failed",
                "error": "Invalid JSON input. Provide url, platform, candidate info, resume_path, cover_letter_text."
            })

        url = data.get("url", "")
        platform = data.get("platform", "generic")
        candidate = {
            "name": data.get("candidate_name", ""),
            "email": data.get("candidate_email", ""),
            "phone": data.get("candidate_phone", ""),
        }
        resume_path = data.get("resume_path", "")
        cover_letter = data.get("cover_letter_text", "")

        if not url:
            return json.dumps({"status": "failed", "error": "No URL provided."})

        try:
            result = asyncio.get_event_loop().run_until_complete(
                self._apply(url, platform, candidate, resume_path, cover_letter)
            )
        except RuntimeError:
            result = asyncio.run(
                self._apply(url, platform, candidate, resume_path, cover_letter)
            )

        return json.dumps(result)

    async def _apply(
        self, url: str, platform: str, candidate: dict, resume_path: str, cover_letter: str
    ) -> dict:
        from playwright.async_api import async_playwright

        screenshot_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))), "output", "screenshots"
        )
        os.makedirs(screenshot_dir, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

                # Check for CAPTCHA
                if await self._detect_captcha(page):
                    screenshot_path = os.path.join(screenshot_dir, f"blocked_captcha_{int(time.time())}.png")
                    await page.screenshot(path=screenshot_path)
                    return {
                        "status": "blocked",
                        "error": "CAPTCHA detected. Manual intervention required.",
                        "screenshot_path": screenshot_path,
                        "url": url,
                    }

                # Check for login wall
                if await self._detect_login_wall(page):
                    screenshot_path = os.path.join(screenshot_dir, f"blocked_login_{int(time.time())}.png")
                    await page.screenshot(path=screenshot_path)
                    return {
                        "status": "blocked",
                        "error": f"Login required on {platform}. Manual login needed.",
                        "screenshot_path": screenshot_path,
                        "url": url,
                    }

                # Platform-specific application flow
                if platform == "linkedin":
                    result = await self._apply_linkedin(page, candidate, resume_path, cover_letter)
                elif platform == "indeed":
                    result = await self._apply_indeed(page, candidate, resume_path, cover_letter)
                elif platform == "greenhouse":
                    result = await self._apply_greenhouse(page, candidate, resume_path, cover_letter)
                else:
                    result = await self._apply_generic(page, candidate, resume_path, cover_letter)

                # Take post-submission screenshot
                screenshot_path = os.path.join(screenshot_dir, f"applied_{platform}_{int(time.time())}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot_path"] = screenshot_path
                result["url"] = url

                return result

            except Exception as e:
                screenshot_path = os.path.join(screenshot_dir, f"error_{platform}_{int(time.time())}.png")
                try:
                    await page.screenshot(path=screenshot_path)
                except Exception:
                    screenshot_path = None

                return {
                    "status": "failed",
                    "error": str(e),
                    "screenshot_path": screenshot_path,
                    "url": url,
                }
            finally:
                await browser.close()

    async def _detect_captcha(self, page) -> bool:
        captcha_selectors = [
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
            "#captcha",
            ".g-recaptcha",
            "[data-sitekey]",
            "iframe[title*='reCAPTCHA']",
        ]
        for selector in captcha_selectors:
            if await page.query_selector(selector):
                return True
        return False

    async def _detect_login_wall(self, page) -> bool:
        login_indicators = [
            "input[type='password']",
            "form[action*='login']",
            "form[action*='signin']",
            "[data-test='sign-in']",
            "#login-form",
        ]
        for selector in login_indicators:
            if await page.query_selector(selector):
                # Check if this is actually a login page vs an application form
                page_text = await page.inner_text("body")
                if any(phrase in page_text.lower() for phrase in ["sign in to", "log in to", "create an account"]):
                    return True
        return False

    async def _apply_linkedin(self, page, candidate: dict, resume_path: str, cover_letter: str) -> dict:
        """Handle LinkedIn Easy Apply flow."""
        try:
            # Click Easy Apply button
            easy_apply_btn = await page.query_selector(".jobs-apply-button, button[aria-label*='Easy Apply']")
            if not easy_apply_btn:
                return {"status": "blocked", "error": "No Easy Apply button found. May require external application."}

            await easy_apply_btn.click()
            await asyncio.sleep(random.uniform(2, 3))

            # Fill form fields as they appear
            await self._fill_common_fields(page, candidate)

            # Upload resume if file input exists
            if resume_path and os.path.exists(resume_path):
                file_input = await page.query_selector("input[type='file']")
                if file_input:
                    await file_input.set_input_files(resume_path)
                    await asyncio.sleep(1)

            # Navigate through multi-step form
            for step in range(5):
                next_btn = await page.query_selector(
                    "button[aria-label='Continue to next step'], "
                    "button[aria-label='Review your application'], "
                    "button[aria-label='Submit application']"
                )
                if not next_btn:
                    break

                btn_label = await next_btn.get_attribute("aria-label") or ""
                if "submit" in btn_label.lower():
                    await next_btn.click()
                    await asyncio.sleep(2)
                    return {"status": "submitted", "error": None}

                await next_btn.click()
                await asyncio.sleep(random.uniform(1, 2))
                await self._fill_common_fields(page, candidate)

            return {"status": "submitted", "error": None}

        except Exception as e:
            return {"status": "failed", "error": f"LinkedIn apply error: {str(e)}"}

    async def _apply_indeed(self, page, candidate: dict, resume_path: str, cover_letter: str) -> dict:
        """Handle Indeed application flow."""
        try:
            apply_btn = await page.query_selector(
                "#indeedApplyButton, "
                "button[id*='applyButton'], "
                "a[href*='apply']"
            )
            if apply_btn:
                await apply_btn.click()
                await asyncio.sleep(random.uniform(2, 3))

            await self._fill_common_fields(page, candidate)

            if resume_path and os.path.exists(resume_path):
                file_input = await page.query_selector("input[type='file']")
                if file_input:
                    await file_input.set_input_files(resume_path)
                    await asyncio.sleep(1)

            # Fill cover letter if textarea exists
            if cover_letter:
                cover_textarea = await page.query_selector(
                    "textarea[name*='cover'], textarea[id*='cover'], "
                    "textarea[placeholder*='cover letter']"
                )
                if cover_textarea:
                    await cover_textarea.fill(cover_letter)

            # Click through and submit
            for _ in range(5):
                submit_btn = await page.query_selector(
                    "button[type='submit'], "
                    "button:has-text('Submit'), "
                    "button:has-text('Apply'), "
                    "button:has-text('Continue')"
                )
                if submit_btn:
                    btn_text = (await submit_btn.inner_text()).lower()
                    await submit_btn.click()
                    await asyncio.sleep(random.uniform(1, 2))

                    if "submit" in btn_text or "apply" in btn_text:
                        return {"status": "submitted", "error": None}
                else:
                    break

            return {"status": "submitted", "error": None}

        except Exception as e:
            return {"status": "failed", "error": f"Indeed apply error: {str(e)}"}

    async def _apply_greenhouse(self, page, candidate: dict, resume_path: str, cover_letter: str) -> dict:
        """Handle Greenhouse ATS application flow."""
        try:
            await self._fill_common_fields(page, candidate)

            if resume_path and os.path.exists(resume_path):
                file_input = await page.query_selector("input[type='file'][name*='resume'], input[type='file']")
                if file_input:
                    await file_input.set_input_files(resume_path)
                    await asyncio.sleep(1)

            if cover_letter:
                cover_textarea = await page.query_selector(
                    "textarea[name*='cover'], #cover_letter, textarea[id*='cover']"
                )
                if cover_textarea:
                    await cover_textarea.fill(cover_letter)

            submit_btn = await page.query_selector(
                "input[type='submit'], button[type='submit'], "
                "button:has-text('Submit Application')"
            )
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(2)
                return {"status": "submitted", "error": None}

            return {"status": "failed", "error": "Could not find submit button on Greenhouse form."}

        except Exception as e:
            return {"status": "failed", "error": f"Greenhouse apply error: {str(e)}"}

    async def _apply_generic(self, page, candidate: dict, resume_path: str, cover_letter: str) -> dict:
        """Generic application form handler with field detection."""
        try:
            await self._fill_common_fields(page, candidate)

            if resume_path and os.path.exists(resume_path):
                file_inputs = await page.query_selector_all("input[type='file']")
                for file_input in file_inputs:
                    name = await file_input.get_attribute("name") or ""
                    accept = await file_input.get_attribute("accept") or ""
                    if "resume" in name.lower() or "cv" in name.lower() or ".pdf" in accept:
                        await file_input.set_input_files(resume_path)
                        await asyncio.sleep(1)
                        break
                else:
                    if file_inputs:
                        await file_inputs[0].set_input_files(resume_path)
                        await asyncio.sleep(1)

            if cover_letter:
                textareas = await page.query_selector_all("textarea")
                for textarea in textareas:
                    name = (await textarea.get_attribute("name") or "").lower()
                    placeholder = (await textarea.get_attribute("placeholder") or "").lower()
                    label_text = name + " " + placeholder
                    if any(kw in label_text for kw in ["cover", "letter", "message", "why"]):
                        await textarea.fill(cover_letter)
                        break

            submit_btn = await page.query_selector(
                "button[type='submit'], input[type='submit'], "
                "button:has-text('Submit'), button:has-text('Apply')"
            )
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(2)
                return {"status": "submitted", "error": None}

            return {"status": "failed", "error": "Could not find submit button on application form."}

        except Exception as e:
            return {"status": "failed", "error": f"Generic apply error: {str(e)}"}

    async def _fill_common_fields(self, page, candidate: dict):
        """Fill common form fields like name, email, phone."""
        field_mappings = [
            (["name", "full_name", "fullname", "applicant_name"], candidate.get("name", "")),
            (["first_name", "firstname", "fname"], candidate.get("name", "").split()[0] if candidate.get("name") else ""),
            (["last_name", "lastname", "lname"], " ".join(candidate.get("name", "").split()[1:]) if candidate.get("name") else ""),
            (["email", "e-mail", "email_address"], candidate.get("email", "")),
            (["phone", "telephone", "mobile", "phone_number"], candidate.get("phone", "")),
        ]

        for field_names, value in field_mappings:
            if not value:
                continue
            for field_name in field_names:
                selectors = [
                    f"input[name*='{field_name}']",
                    f"input[id*='{field_name}']",
                    f"input[placeholder*='{field_name.replace('_', ' ')}']",
                    f"input[aria-label*='{field_name.replace('_', ' ')}']",
                ]
                for selector in selectors:
                    el = await page.query_selector(selector)
                    if el:
                        current = await el.get_attribute("value") or ""
                        if not current:
                            await el.fill(value)
                        break
