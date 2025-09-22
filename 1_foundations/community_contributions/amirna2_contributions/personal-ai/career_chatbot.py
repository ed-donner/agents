"""Career Chatbot

AI assistant that represents professionals on their websites, answering
questions about their background while facilitating follow-up contact.

Data models have been refactored into the `models` package to keep this file
focused on orchestration, tool wiring, and runtime logic.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import re

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from typer import prompt
from promptkit import render

# Import refactored data models
from models import (
    ChatbotConfig,
    Evaluation,
    StructuredResponse,
    JobMatchResult,
)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotificationService:
    """Handles push notifications via Pushover"""

    def __init__(self, user_token: Optional[str] = None, app_token: Optional[str] = None):
        self.user_token = user_token or os.getenv("PUSHOVER_USER")
        self.app_token = app_token or os.getenv("PUSHOVER_TOKEN")
        self.api_url = "https://api.pushover.net/1/messages.json"
        self.enabled = bool(self.user_token and self.app_token)

        if self.enabled:
            logger.info("Pushover notification service initialized")
        else:
            logger.warning("Pushover credentials not found - notifications disabled")

    def send(self, message: str) -> bool:
        """Send a push notification"""
        if not self.enabled:
            logger.info(f"Notification (disabled): {message}")
            return False

        try:
            payload = {
                "user": self.user_token,
                "token": self.app_token,
                "message": message
            }
            response = requests.post(self.api_url, data=payload)
            response.raise_for_status()
            logger.info(f"Notification sent: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False


class WebSearchService:
    """Handles web searches and GitHub repository lookups"""

    def __init__(self, github_username: Optional[str] = None):
        self.github_username = github_username
        self.github_api_base = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CareerChatbot/1.0'
        })

        # Check if GitHub token is available for higher rate limits
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            self.session.headers.update({'Authorization': f'token {github_token}'})
            logger.info("GitHub API configured with authentication")
        else:
            logger.info("GitHub API configured without authentication (rate limits apply)")

    def search_github_repos(self, username: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
        """Search GitHub repositories for a user - returns ALL repos with full details"""
        try:
            username = username or self.github_username
            if not username:
                return {"error": "No GitHub username provided", "repos": []}

            # Get user's repositories
            url = f"{self.github_api_base}/users/{username}/repos"
            params = {'sort': 'updated', 'per_page': 100}  # 100 is probably overkill but just in case

            response = self.session.get(url, params=params)
            response.raise_for_status()

            repos = response.json()

            # Filter out forked repositories to show only original work
            repos = [repo for repo in repos if not repo.get('fork', False)]

            # If topic is provided and valid, try to filter (but handle bad inputs gracefully)
            if topic and isinstance(topic, str):
                topic_lower = topic.lower()
                filtered = []
                for repo in repos:
                    # Check topics
                    if any(topic_lower in topic.lower() for topic in repo.get('topics', [])):
                        filtered.append(repo)
                        continue
                    # Check description
                    description = repo.get('description', '') or ''
                    if topic_lower in description.lower():
                        filtered.append(repo)
                        continue
                    # Check name
                    name = repo.get('name', '') or ''
                    if topic_lower in name.lower():
                        filtered.append(repo)
                        continue
                    # Check language
                    language = repo.get('language', '') or ''
                    if topic_lower == language.lower():
                        filtered.append(repo)

                # Only use filtered results if we found matches
                if filtered:
                    repos = filtered

            # Format ALL repos with comprehensive details
            formatted_repos = []
            all_languages = set()

            for repo in repos:  # Return ALL repos, not just 5
                language = repo.get('language')
                if language:
                    all_languages.add(language)

                formatted_repos.append({
                    'name': repo.get('name'),
                    'description': repo.get('description', 'No description'),
                    'url': repo.get('html_url'),
                    'language': language or 'Not specified',
                    'stars': repo.get('stargazers_count', 0),
                    'forks': repo.get('forks_count', 0),
                    'updated': repo.get('updated_at', ''),
                    'created': repo.get('created_at', ''),
                    'topics': repo.get('topics', []),
                    'size': repo.get('size', 0),
                    'is_fork': repo.get('fork', False),
                    'archived': repo.get('archived', False)
                })

            return {
                "username": username,
                "total_repos": len(formatted_repos),
                "languages_used": list(all_languages),
                "topic_searched": topic,
                "repos": formatted_repos
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"error": f"GitHub user '{username}' not found", "repos": []}
            else:
                logger.error(f"GitHub API error: {e}")
                return {"error": f"GitHub API error: {str(e)}", "repos": []}
        except Exception as e:
            logger.error(f"Error searching GitHub: {e}")
            return {"error": f"Error searching GitHub: {str(e)}", "repos": []}

    def get_repo_details(self, repo_name: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a specific repository"""
        try:
            username = username or self.github_username
            if not username:
                return {"error": "No GitHub username provided"}

            url = f"{self.github_api_base}/repos/{username}/{repo_name}"
            response = self.session.get(url)
            response.raise_for_status()

            repo = response.json()

            # Get README content if available
            readme_content = None
            try:
                readme_url = f"{self.github_api_base}/repos/{username}/{repo_name}/readme"
                readme_response = self.session.get(readme_url)
                if readme_response.status_code == 200:
                    readme_data = readme_response.json()
                    if 'content' in readme_data:
                        import base64
                        readme_content = base64.b64decode(readme_data['content']).decode('utf-8')[:500]  # First 500 chars
            except Exception as e:
                logger.debug(f"Could not retrieve README: {e}")
                # Don't let README failure break the entire tool
                pass

            return {
                'name': repo.get('name'),
                'full_name': repo.get('full_name'),
                'description': repo.get('description'),
                'url': repo.get('html_url'),
                'homepage': repo.get('homepage'),
                'language': repo.get('language'),
                'languages_url': repo.get('languages_url'),
                'created_at': repo.get('created_at'),
                'updated_at': repo.get('updated_at'),
                'pushed_at': repo.get('pushed_at'),
                'size': repo.get('size'),
                'stars': repo.get('stargazers_count'),
                'watchers': repo.get('watchers_count'),
                'forks': repo.get('forks_count'),
                'open_issues': repo.get('open_issues_count'),
                'topics': repo.get('topics', []),
                'readme_preview': readme_content
            }

        except Exception as e:
            logger.error(f"Error getting repo details: {e}")
            return {"error": f"Error getting repository details: {str(e)}"}


class DocumentLoader:
    """Loads and processes professional documents"""

    @staticmethod
    def load_pdf(path: str) -> str:
        """Load text content from a PDF file"""
        try:
            reader = PdfReader(path)
            content = ""
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    content += text

            # Debug logging for PDF content
            content_length = len(content)
            webrtc_found = "WebRTC" in content
            websocket_found = "WebSocket" in content

            logger.info(f"Loaded PDF: {path} - Length: {content_length} chars")
            logger.info(f"PDF Debug - WebRTC found: {webrtc_found}, WebSocket found: {websocket_found}")

            # Log a snippet around WebRTC if found
            if webrtc_found:
                webrtc_index = content.find("WebRTC")
                snippet = content[max(0, webrtc_index-50):webrtc_index+50]
                logger.info(f"WebRTC context: ...{snippet}...")

            return content
        except Exception as e:
            logger.error(f"Failed to load PDF {path}: {e}")
            return ""

    @staticmethod
    def load_text(path: str) -> str:
        """Load content from a text file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"Loaded text file: {path}")
            return content
        except Exception as e:
            logger.error(f"Failed to load text file {path}: {e}")
            return ""


class Evaluator:
    """Evaluates AI responses for accuracy and hallucinations"""

    def __init__(self, config: ChatbotConfig, context: Dict[str, str]):
        self.config = config
        self.context = context
        # Use a different model for evaluation to avoid bias
        self.evaluator_client = OpenAI(
                                    api_key=os.getenv("GEMINI_API_KEY"),
                                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                                )
        # Initial system prompt without GitHub context will generic footer
        self.system_prompt = self._create_evaluator_prompt()

    def _create_evaluator_prompt(self, decision_criteria_footer=None) -> str:
        """Create the evaluator system prompt"""
        if decision_criteria_footer is None:
            decision_criteria_footer = "Mark UNACCEPTABLE only if: unsupported claims, missing tool usage when needed, or behavioral rules violated."

        # Get current date for evaluator context
        current_date = datetime.now().strftime("%B %d, %Y")

        # Debug logging for evaluator context
        resume_length = len(self.context['resume'])
        linkedin_length = len(self.context['linkedin'])
        summary_length = len(self.context['summary'])
        resume_has_webrtc = "WebRTC" in self.context['resume']
        resume_has_websocket = "WebSocket" in self.context['resume']

        logger.debug(f"EVALUATOR CONTEXT DEBUG:")
        logger.debug(f"  Resume length: {resume_length} chars, WebRTC: {resume_has_webrtc}, WebSocket: {resume_has_websocket}")
        logger.debug(f"  LinkedIn length: {linkedin_length} chars")
        logger.debug(f"  Summary length: {summary_length} chars")

        if resume_has_webrtc:
            webrtc_index = self.context['resume'].find("WebRTC")
            snippet = self.context['resume'][max(0, webrtc_index-50):webrtc_index+50]
            logger.debug(f"  WebRTC context in resume: ...{snippet}...")

        vars = {
            "config": self.config,
            "context": self.context,
            "job_match_threshold": self.config.job_match_threshold if self.config else "Good",
            "decision_criteria_footer": decision_criteria_footer,
            "current_date": current_date
        }
        prompt = render("prompts/evaluator.md", vars)
        return prompt


    def _create_user_prompt(self, reply: str, message: str, history: List[Dict]) -> str:
        """Create the user prompt for evaluation"""
        # Include the last N messages from the history. e.g., last 6 messages for more context
        history_str = "\n".join([f"{h['role']}: {h['content']}" for h in history[-6:]])

        return f"""Here's the conversation context:

{history_str}

Latest User message: {message}

Latest Agent response: {reply}

Please evaluate this response with STRICTNESS:
1. Check EVERY factual claim against the provided context
2. If the Agent mentions ANY specific detail (skills, technologies, experiences, tools) not explicitly in the context, mark as UNACCEPTABLE
3. If the Agent should have said "I don't have that information", but instead made something up, mark as UNACCEPTABLE
4. Look for common hallucinations like claiming experience with technologies not mentioned in the resume/LinkedIn

Is this response acceptable? Provide specific feedback about any issues."""

    def rerun(self, reply: str, message: str, history: List[Dict], feedback: str) -> StructuredResponse:
        """Regenerate structured response with feedback from failed evaluation"""
        base_system_prompt = self._create_base_system_prompt()
        vars = {
            'base_system_prompt': base_system_prompt,
            'reply': reply,
            'feedback': feedback
        }
        updated_system_prompt = render('prompts/chat_rerun.md', vars)

        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]

        # Generate new structured response with parsed output
        response = self.evaluator_client.beta.chat.completions.parse(
            model=self.config.evaluator_model,
            messages=messages,
            response_format=StructuredResponse
        )
        system_fp = getattr(response, "system_fingerprint", None)
        logging.debug("EVAL: served_model=%s system_fp=%s", response.model, system_fp)

        return response.choices[0].message.parsed

    def _create_base_system_prompt(self) -> str:
        """Create base system prompt without evaluation context"""
        vars = {
            'config': self.config,
            'context': self.context
        }
        return render('prompts/chat_base.md', vars)

    def evaluate_structured(self, structured_reply: StructuredResponse, message: str, history: List[Dict]) -> Evaluation:
        """Evaluate a structured response with reasoning and evidence"""
        try:
            # Create enhanced user prompt that includes the structured information
            is_job_matching = self._is_job_matching_context(structured_reply, message, history)

            # Check if GitHub tools were used
            logger.info(f"STRUCTURED REPLY TOOLS_USED: {structured_reply.tools_used}")
            github_tools_used = any(tool in structured_reply.tools_used for tool in ['search_github_repos', 'get_repo_details', 'functions.search_github_repos', 'functions.get_repo_details'])
            logger.info(f"GITHUB TOOLS USED: {github_tools_used}")

            if is_job_matching:
                evaluation_criteria = f"""Please evaluate this job matching response with REASONABLE STANDARDS:
1. Is the reasoning sound for professional skill assessment?
2. Are technical inferences reasonable (e.g., ROS2 experience → DDS knowledge)?
3. Were appropriate tools used for job analysis?
4. Does the response provide useful insights for recruitment?
5. CRITICAL: Match level hierarchy is Very Strong > Strong > Good > Moderate > Weak > Very Weak
6. CRITICAL: If job match is "{self.config.job_match_threshold if self.config else 'Good'}" or HIGHER in the hierarchy (Strong, Very Strong), facilitating contact is CORRECT behavior
7. CRITICAL: If job match is LOWER in the hierarchy than "{self.config.job_match_threshold if self.config else 'Good'}" (Moderate, Weak, Very Weak), declining contact is CORRECT behavior

Job matching responses should be evaluated for practical utility, not pedantic precision.
Accept reasonable technical inferences and contact facilitation decisions based on match level."""
            else:
                if github_tools_used:
                    evaluation_criteria = """Please evaluate this response with REASONABLE STANDARDS for GitHub tool usage:
1. GitHub tools (search_github_repos, get_repo_details) were used to gather additional information
2. Repository details like stars, forks, creation dates, programming languages, topics are LEGITIMATE from GitHub API
3. Technical project details obtained from GitHub tools are acceptable
4. Only reject if claims obviously contradict the professional background
5. The agent appropriately used tools to provide detailed project information

When GitHub tools are used, trust the additional technical details they provide.
Is this response acceptable? Provide specific feedback about any issues."""
                else:
                    evaluation_criteria = """Please evaluate this response with STRICTNESS:
1. Check EVERY factual claim against the provided context
2. If the Agent mentions ANY specific detail not explicitly in the context, mark as UNACCEPTABLE
3. If the Agent should have said "I don't have that information", but instead made something up, mark as UNACCEPTABLE
4. Look for common hallucinations and unsupported claims

Is this response acceptable? Provide specific feedback about any issues."""

            newline = '\n'
            user_prompt = f"""Here's the conversation context:

{newline.join([f"{h['role']}: {h['content']}" for h in history[-3:]])}

Latest User message: {message}

Agent's structured response:
Response: {structured_reply.response}
Reasoning: {structured_reply.reasoning}
Tools used: {structured_reply.tools_used}
Facts used: {structured_reply.facts_used}

{evaluation_criteria}"""

            # Check if GitHub tool results should be included in system prompt
            github_context = self._extract_github_context_from_history(history)
            system_prompt = self._create_evaluator_prompt_with_github(github_context) if github_context else self._create_evaluator_prompt()

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = self.evaluator_client.beta.chat.completions.parse(
                model=self.config.evaluator_model,
                messages=messages,
                response_format=Evaluation,
                temperature=0.0
            )
            system_fp = getattr(response, "system_fingerprint", None)
            logging.debug("EVAL: served_model=%s system_fp=%s", response.model, system_fp)

            evaluation = response.choices[0].message.parsed
            logger.info(f"EVALUATION RESULT: {'PASS' if evaluation.is_acceptable else 'FAIL'}")
            logger.info(f"AGENT RESPONSE: {structured_reply.response}")
            logger.info(f"AGENT REASONING: {structured_reply.reasoning}")
            logger.info(f"EVALUATOR FEEDBACK: {evaluation.feedback}")
            return evaluation

        except Exception as e:
            logger.error(f"Structured evaluation failed: {e}")
            return Evaluation(is_acceptable=True, feedback=f"Evaluation error: {str(e)}")

    def _external_tools_used(self, history: List[Dict]) -> bool:
        """Check if tools with external data (GitHub, job matching) were used in the conversation"""
        for message in history:
            if message.get('role') == 'tool':
                content = message.get('content', '')
                print(f"TOOL CONTENT DEBUG: {content}")  # Temporary debug
                # Check for GitHub tool results
                if any(indicator in content for indicator in ['repos', 'languages_found', 'total_repos', 'github.com']):
                    return True
                # Check for job matching tool results
                if any(indicator in content for indicator in ['overall_match_level', 'skill_assessments', 'should_facilitate_contact']):
                    print("JOB MATCHING TOOL DETECTED!")  # Temporary debug
                    return True
        print("NO EXTERNAL TOOLS DETECTED")  # Temporary debug
        return False

    def _is_github_context(self, structured_reply: StructuredResponse) -> bool:
        """Check if GitHub tools were used"""
        return any(tool in structured_reply.tools_used for tool in ['search_github_repos', 'get_repo_details'])

    def _is_job_matching_context(self, structured_reply: StructuredResponse, message: str, history: List[Dict]) -> bool:
        """Check if this is a job matching context"""
        # Check if job matching tool was used
        if 'evaluate_job_match' in structured_reply.tools_used:
            return True

        # Check if response contains job matching indicators
        response_content = structured_reply.response.lower()
        if any(indicator in response_content for indicator in ['match level', 'skills breakdown', 'overall match', 'job fit']):
            return True

        # Check if message contains job posting indicators
        message_content = message.lower()
        if any(indicator in message_content for indicator in ['job description', 'role', 'position', 'hiring', 'candidate']):
            return True

        return False

    def _create_evaluator_prompt_with_github(self, github_context: str) -> str:
        """Create evaluator prompt including GitHub tool results as valid context"""
        if github_context:
            # Get base evaluator content WITHOUT footer (empty string)
            base_evaluator_prompt = self._create_evaluator_prompt("")

            # Get current date for GitHub evaluator context
            current_date = datetime.now().strftime("%B %d, %Y")

            vars = {
                "base_evaluator_prompt": base_evaluator_prompt,
                "github_context": github_context,
                "current_date": current_date
            }
            return render("prompts/evaluator_with_github_context.md", vars)
        else:
            return self._create_evaluator_prompt()

    def _extract_github_context_from_history(self, history: List[Dict]) -> str:
        """Extract GitHub tool results from conversation history"""
        github_context = ""

        for message in history:
            if message.get('role') == 'tool':
                content = message.get('content', '')
                # Check if this is GitHub tool content (repo details or repo search results)
                if any(indicator in content for indicator in [
                    'full_name', 'html_url', 'stargazers_count', 'watchers_count', 'forks_count',
                    'open_issues_count', 'created_at', 'updated_at', 'topics', 'repos', 'github.com'
                ]):
                    github_context += f"\n{content}"

        return github_context.strip()


class ToolRegistry:
    """Manages AI agent tools and their execution"""

    def __init__(self, notification_service: NotificationService, web_search_service: Optional[WebSearchService] = None,
                 openai_client: Optional[OpenAI] = None, context: Optional[Dict[str, str]] = None,
                 config: Optional[ChatbotConfig] = None):
        self.notification_service = notification_service
        self.web_search_service = web_search_service
        self.openai_client = openai_client
        self.context = context or {}
        self.config = config
        self.tools = self._create_tool_definitions()

    def _create_tool_definitions(self) -> List[Dict]:
        """Create tool definitions for the AI agent"""
        record_user_details = {
            "name": "record_user_details",
            "strict": True,
            "description": (
                "Use this tool ONLY AFTER a user has explicitly provided their email address in response to an offer to facilitate contact. "
                "This tool records the user's contact details. "
                "IMPORTANT: DO NOT use this tool unless the user has given you their email. Do not make up an email address."
            ),
            "parameters": {
                "type": "object",
                "strict": True,
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The email address explicitly provided by the user. Do not invent this."
                    },
                    "name": {
                        "type": "string",
                        "description": "The user's name if they provided it. If not, use 'Visitor'."
                    },
                    "notes": {
                        "type": "string",
                        "description": (
                            "Detailed notes about the conversation context and why the user wants to be contacted. "
                            "Include the original question or job match details."
                        )
                    }
                },
                "required": ["email", "name", "notes"],
                "additionalProperties": False
            }
        }


        evaluate_job_match = {
            "name": "evaluate_job_match",
            "strict": True,
            "description": (
                "Analyze how well the candidate matches a job posting. Use this when someone asks "
                "about job fit, role suitability, or provides a job description to evaluate. "
                "Returns detailed analysis with match levels and recommendations."
            ),
            "parameters": {
                "type": "object",
                "strict": True,
                "properties": {
                    "job_description": {
                        "type": "string",
                        "description": "The FULL, COMPLETE, UNEDITED job description text exactly as provided by the user. Do NOT summarize, extract, or truncate - include ALL details including company info, salary, responsibilities, requirements, and nice-to-haves."
                    },
                    "role_title": {
                        "type": "string",
                        "description": "The job title or role name"
                    }
                },
                "required": ["job_description", "role_title"],
                "additionalProperties": False
            }
        }

        tools = [
            {"type": "function", "function": record_user_details},
            {"type": "function", "function": evaluate_job_match}
        ]

        # Add GitHub search tools if web search service is available
        if self.web_search_service:
            search_github = {
                "name": "search_github_repos",
                "strict": True,
                "description": (
                    "Get ALL GitHub repositories with full details including languages, topics, stars, etc. "
                    "Call WITHOUT parameters to get everything, then analyze the returned data. "
                    "Returns list of all repos with language field showing what each is written in."
                ),
                "parameters": {
                    "type": "object",
                    "strict": True,
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                }
            }

            get_repo_info = {
                "name": "get_repo_details",
                "strict": True,
                "description": "Get detailed information about a specific GitHub repository",
                "parameters": {
                    "type": "object",
                    "strict": True,
                    "properties": {
                        "repo_name": {
                            "type": "string",
                            "description": "The name of the repository to get details for"
                        }
                    },
                    "required": ["repo_name"],
                    "additionalProperties": False
                }
            }

            tools.extend([
                {"type": "function", "function": search_github},
                {"type": "function", "function": get_repo_info}
            ])

        return tools

    def record_user_details(self, email: str, name: str = "Visitor", notes: str = "not provided") -> Dict:
        """Record user contact details and prepare notification"""
        message = f"Recording interest from {name} with email {email} and notes: {notes}"
        logger.info(f"Recorded user details: {email}, {name}")
        return {
            "recorded": "ok",
            "pending_notification": message
        }


    def evaluate_job_match(self, job_description: str, role_title: str) -> Dict:
        """Evaluate how well the candidate matches a job using LLM analysis"""
        if not self.openai_client or not self.context:
            return {"error": "Job matching requires OpenAI client and context"}

        logger.info(f"🎯 Evaluating job match for role: {role_title}")
        vars = {
            "role_title": role_title,
            "job_description": job_description,
            "config": self.config,
            "context": self.context,
        }

        # Create analysis prompt
        analysis_prompt = render("prompts/job_match_analysis.md", vars)

        try:
            response = self.openai_client.beta.chat.completions.parse(
                model=self.config.job_matching_model if self.config else "gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional job matching analyst."},
                    {"role": "user", "content": analysis_prompt}
                ],
                response_format=JobMatchResult
            )
            system_fp = getattr(response, "system_fingerprint", None)
            logging.debug("MATCH: served_model=%s system_fp=%s", response.model, system_fp)

            result = response.choices[0].message.parsed
            logger.info(f"Job match analysis completed: {result.overall_match_level} match for {role_title}")

            result_dict = result.model_dump()

            # Add pending notification for high matches
            if result.should_facilitate_contact:
                result_dict["pending_notification"] = f"High job match found ({result.overall_match_level}): {role_title}"

            return result_dict

        except Exception as e:
            logger.error(f"Job matching analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    def handle_tool_calls(self, tool_calls) -> tuple[List[Dict], List[str]]:
        """Execute tool calls from the AI agent and collect pending notifications"""
        results = []
        pending_notifications = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            logger.info(f"Tool called: {tool_name} with args: {arguments}")

            # Execute the appropriate tool
            if tool_name == "record_user_details":
                result = self.record_user_details(**arguments)
            elif tool_name == "search_github_repos" and self.web_search_service:
                topic = arguments.get('topic')
                result = self.web_search_service.search_github_repos(topic=topic)
            elif tool_name == "get_repo_details" and self.web_search_service:
                repo_name = arguments.get('repo_name')
                result = self.web_search_service.get_repo_details(repo_name)
            elif tool_name == "evaluate_job_match":
                result = self.evaluate_job_match(**arguments)
            else:
                logger.warning(f"Unknown tool called: {tool_name}")
                result = {}

            # Extract pending notifications
            if isinstance(result, dict) and "pending_notification" in result:
                pending_notifications.append(result.pop("pending_notification"))

            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })

        return results, pending_notifications


class CareerChatbot:
    """Main chatbot class that orchestrates the AI assistant"""

    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.openai_client = OpenAI()

        # Initialize services
        self.notification_service = NotificationService()
        self.web_search_service = WebSearchService(github_username=config.github_username) if config.github_username else None
        self.document_loader = DocumentLoader()

        # Load professional context
        self.context = self._load_context()

        # Initialize tool registry with context
        self.tool_registry = ToolRegistry(self.notification_service, self.web_search_service,
                                          self.openai_client, self.context, self.config)
        self.evaluator = Evaluator(self.config, self.context)
        self.system_prompt = self._create_system_prompt()

        logger.info(f"CareerChatbot initialized for {config.name}")

    def _load_context(self) -> Dict[str, str]:
        """Load all professional context documents"""
        context = {
            "resume": self.document_loader.load_pdf(self.config.resume_path),
            "linkedin": self.document_loader.load_pdf(self.config.linkedin_path),
            "summary": self.document_loader.load_text(self.config.summary_path)
        }
        return context

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the AI assistant"""

        # Prepare GitHub tools context if available
        github_tools = ""
        if self.web_search_service:
            github_tools = (
                "You can use the `search_github_repos` tool to find open source projects and repositories. "
                "Use the `get_repo_details` tool to get detailed information about specific repositories."
            )

        vars = {
          'config': self.config,        # Access as {config.name}, {config.job_match_threshold}
          'context': self.context,      # Access as {context.summary}, {context.linkedin}, etc.
          'github_tools': github_tools  # Access as {github_tools} (for conditional content)
        }
        chat_init_prompt = render('prompts/chat_init.md', vars)
        return chat_init_prompt


    def chat(self, message: str, history: List[Dict[str, str]], max_retries: int = 3) -> str:
        """Main chat function that processes user messages with evaluation and Lab 3 retry approach"""
        logger.info(f"🔄 PROCESSING message: '{message[:50]}...'")

        # Generate initial response with tools
        messages = [{"role": "system", "content": self.system_prompt}] + history + [{"role": "user", "content": message}]
        structured_reply, pending_notifications = self._generate_response_with_tools(messages)

        # Safety check - ensure we have a valid structured_reply
        if not structured_reply:
            logger.error("No structured reply received from _generate_response_with_tools")
            return "I apologize, but I'm experiencing technical difficulties. Please try again."

        # For evaluation, use the original history (tool results will be detected from tools_used field)
        evaluation_history = history

        # Systematic evaluation with Lab 3 approach
        for attempt in range(max_retries):
            try:
                # Evaluate the current reply using history that includes tool results
                evaluation = self.evaluator.evaluate_structured(structured_reply, message, evaluation_history)

                if evaluation.is_acceptable:
                    logger.info(f"✅ PASSED evaluation on attempt {attempt + 1}/{max_retries}\n")

                    # Send notifications only after successful evaluation
                    for notification in pending_notifications:
                        self.tool_registry.notification_service.send(notification)

                    return structured_reply.response if structured_reply else "I apologize, but I'm experiencing technical difficulties."
                else:
                    logger.warning(f"❌ FAILED evaluation on attempt {attempt + 1}/{max_retries}: {evaluation.feedback[:100]}...\n")

                    # If we haven't exhausted retries, regenerate using Lab 3 rerun approach
                    if attempt < max_retries - 1:
                        logger.info("🔄 Regenerating response with feedback...")
                        # Clear pending notifications from failed attempt
                        pending_notifications.clear()
                        new_reply = self.evaluator.rerun(structured_reply.response, message, history, evaluation.feedback)
                        if new_reply:
                            structured_reply = new_reply
                        else:
                            logger.error("Rerun returned None, keeping original reply")
                    else:
                        logger.warning(f"⚠️ Max retries ({max_retries}) reached. Returning final attempt.")
                        return structured_reply.response if structured_reply else "I apologize, but I'm experiencing technical difficulties."

            except Exception as eval_error:
                logger.error(f"Evaluation failed: {eval_error}")
                # If evaluation fails, return the response we have
                return structured_reply.response if structured_reply else "I apologize, but I'm experiencing technical difficulties."

        return structured_reply.response if structured_reply else "I apologize, but I'm experiencing technical difficulties."

    def _generate_response_with_tools(self, messages: List[Dict]) -> tuple[StructuredResponse, List[str]]:
        """Generate response handling tool calls and collect pending notifications"""
        done = False
        all_pending_notifications = []

        while not done:
            try:
                # Call the LLM with tools and structured output
                response = self.openai_client.beta.chat.completions.parse(
                    model=self.config.model,
                    messages=messages,
                    tools=self.tool_registry.tools,
                    tool_choice="auto",
                    response_format=StructuredResponse
                )
                system_fp = getattr(response, "system_fingerprint", None)
                logging.debug("CHAT: served_model=%s system_fp=%s", response.model, system_fp)

                finish_reason = response.choices[0].finish_reason

                # Handle tool calls if needed
                if finish_reason == "tool_calls":
                    message_obj = response.choices[0].message
                    tool_calls = message_obj.tool_calls
                    results, pending_notifications = self.tool_registry.handle_tool_calls(tool_calls)
                    all_pending_notifications.extend(pending_notifications)
                    messages.append(message_obj)
                    messages.extend(results)
                else:
                    done = True
                    return response.choices[0].message.parsed, all_pending_notifications

            except Exception as e:
                logger.error(f"Structured response parsing failed: {e}")
                # Fallback: try without structured output
                try:
                    fallback_response = self.openai_client.chat.completions.create(
                        model=self.config.model,
                        messages=messages,
                        tools=self.tool_registry.tools,
                        tool_choice="auto"
                    )

                    # Create a basic structured response from the fallback
                    content = fallback_response.choices[0].message.content or "I apologize, but I encountered an error processing your request."
                    fallback_structured = StructuredResponse(
                        response=content,
                        reasoning="Fallback response due to parsing error",
                        tools_used=[],
                        facts_used=[]
                    )
                    return fallback_structured, all_pending_notifications

                except Exception as fallback_error:
                    logger.error(f"Fallback response also failed: {fallback_error}")
                    # Ultimate fallback
                    error_response = StructuredResponse(
                        response="I apologize, but I'm experiencing technical difficulties. Please try again.",
                        reasoning="Error handling response",
                        tools_used=[],
                        facts_used=[]
                    )
                    return error_response, all_pending_notifications

    def create_initial_greeting(self) -> str:
        """Create the initial greeting message"""
        return f"""👋 Hello! I'm an AI assistant designed by {self.config.name} and representing them professionally.

I can answer questions about {self.config.name}'s career, experience, and professional background based on their resume and LinkedIn profile.

If you have questions I can't answer from the available information, I'll be happy to arrange for {self.config.name} to respond to you personally via email.

How can I help you today?"""

    def launch_interface(self):
        """Launch the Gradio interface"""
        # Create chatbot with initial message
        chatbot = gr.Chatbot(
            value=[
                {"role": "assistant", "content": self.create_initial_greeting()}
            ],
            type="messages",
            height=700,
            show_copy_button=True,
            show_copy_all_button=True,
        )

        # Create and launch the interface
        interface = gr.ChatInterface(
            self.chat,
            type="messages",
            chatbot=chatbot,
            examples=[
                "What is the professional background?",
                "What companies has this person worked at?",
                "Where did they go to school?",
                "What are their main skills?"
            ],
            title=f"{self.config.name}'s AI Assistant"
        )

        interface.launch()


def main():
    """Main entry point for the application"""
    # Load environment variables
    load_dotenv(override=True)

    # Create configuration
    # Extract GitHub username from summary or environment variable
    github_username = os.getenv("GITHUB_USERNAME")  # Can be set to actual username
    config = ChatbotConfig(
        name="Amir Nathoo",
        github_username=github_username  # Set to actual GitHub username if available
    )

    # Initialize and launch chatbot
    chatbot = CareerChatbot(config)
    chatbot.launch_interface()


if __name__ == "__main__":
    main()
