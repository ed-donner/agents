from __future__ import annotations

import asyncio
import webbrowser

import gradio as gr

from agent.orchestrator import LinkedInPostAgent
from services.content import get_content_service
from services.linkedin import get_linkedin_service
from ui.auth_callback import STORE
from ui.state import (
    compose_post_body,
    draft_choices,
    format_auth_status,
    format_bundle,
    format_draft,
    format_history,
    format_voice_profile,
    parse_urls,
)


content_service = get_content_service()
linkedin_service = get_linkedin_service()
agent = LinkedInPostAgent()


def refresh_auth_status() -> str:
    return format_auth_status(linkedin_service.validate_session())


def start_linkedin_auth() -> tuple[str, str]:
    payload = linkedin_service.get_auth_url()
    STORE.set_expected_state(payload["state"])
    webbrowser.open(payload["auth_url"])
    return payload["auth_url"], "Opened LinkedIn authorization in your browser."


def finalize_linkedin_auth() -> str:
    callback = STORE.consume()
    expected_state = STORE.get_expected_state()
    if callback.error:
        return f"LinkedIn authorization returned an error: {callback.error}"
    if not callback.code:
        return "No callback code received yet."
    if expected_state and callback.state != expected_state:
        return "LinkedIn state mismatch."
    session = linkedin_service.exchange_code(callback.code)
    return (
        "LinkedIn authorization completed.\n"
        f"Name: {session['name']}\n"
        f"Person URN: {session['person_urn']}"
    )


def save_voice_example(content: str, source_label: str) -> tuple[str, str]:
    if not content.strip():
        raise gr.Error("Style example content is required.")
    if not source_label.strip():
        raise gr.Error("Source label is required.")
    content_service.store_style_example(content=content, source_label=source_label)
    profile = content_service.voice_resource()
    return "", format_voice_profile(profile)


def load_voice_profile() -> str:
    return format_voice_profile(content_service.voice_resource())


def generate_drafts(topic: str, goal: str, notes: str, urls_text: str):
    if not topic.strip():
        raise gr.Error("Topic is required.")
    if not goal.strip():
        raise gr.Error("Goal is required.")
    result = asyncio.run(
        agent.generate_drafts(
            topic=topic,
            goal=goal,
            notes=notes,
            urls=parse_urls(urls_text),
        )
    )
    drafts = [content_service.get_draft(draft_id) for draft_id in result.get("draft_ids", [])]
    bundle = content_service.sources_resource(result["bundle_id"]) if result.get("bundle_id") else {"sources": []}
    first_draft = drafts[0] if drafts else None
    return (
        gr.update(
            choices=draft_choices(content_service.list_drafts(limit=50)),
            value=first_draft["id"] if first_draft else None,
        ),
        format_draft(first_draft) if first_draft else "No drafts created.",
        format_bundle(bundle),
        result.get("idea_id", ""),
        result.get("bundle_id", ""),
        first_draft["title"] if first_draft else "",
        first_draft["body"] if first_draft else "",
        first_draft.get("cta", "") if first_draft else "",
        (first_draft.get("link_url") or "") if first_draft else "",
    )


def refresh_drafts():
    drafts = content_service.list_drafts(limit=50)
    return gr.update(choices=draft_choices(drafts))


def show_selected_draft(draft_id: str) -> tuple[str, str, str, str, str, str]:
    if not draft_id:
        return "Select a draft.", "", "", "", "", ""
    draft = content_service.get_draft(draft_id)
    bundle = content_service.sources_resource(draft["bundle_id"])
    return (
        format_draft(draft),
        format_bundle(bundle),
        draft["title"],
        draft["body"],
        draft.get("cta", ""),
        draft.get("link_url") or "",
    )


def approve_selected_draft(draft_id: str, title: str, body: str, cta: str, link_url: str):
    if not draft_id:
        raise gr.Error("Select a draft first.")
    content_service.update_draft_content(
        draft_id=draft_id,
        title=title,
        body=body,
        cta=cta,
        link_url=link_url,
    )
    content_service.approve_draft(draft_id)
    draft = content_service.get_draft(draft_id)
    return (
        format_draft(draft),
        gr.update(choices=draft_choices(content_service.list_drafts(limit=50)), value=draft_id),
        draft["title"],
        draft["body"],
        draft.get("cta", ""),
        draft.get("link_url") or "",
    )


def reject_selected_draft(draft_id: str, feedback: str):
    if not draft_id:
        raise gr.Error("Select a draft first.")
    content_service.reject_draft(draft_id, feedback=feedback)
    draft = content_service.get_draft(draft_id)
    return (
        format_draft(draft),
        gr.update(choices=draft_choices(content_service.list_drafts(limit=50)), value=draft_id),
    )


def revise_selected_draft(
    draft_id: str,
    title: str,
    body: str,
    cta: str,
    link_url: str,
    feedback: str,
):
    if not draft_id:
        raise gr.Error("Select a draft first.")
    revised = content_service.update_draft_content(
        draft_id=draft_id,
        title=title,
        body=body,
        cta=cta,
        link_url=link_url,
        feedback=feedback,
    )
    bundle = content_service.sources_resource(revised["bundle_id"])
    return (
        gr.update(choices=draft_choices(content_service.list_drafts(limit=50)), value=draft_id),
        format_draft(revised),
        format_bundle(bundle),
        revised["title"],
        revised["body"],
        revised.get("cta", ""),
        revised.get("link_url") or "",
    )


def publish_selected_draft(draft_id: str) -> tuple[str, str]:
    if not draft_id:
        raise gr.Error("Select a draft first.")
    draft = content_service.get_draft(draft_id)
    if draft["status"] != "approved":
        raise gr.Error("Only approved drafts can be published.")
    content = compose_post_body(draft["body"], draft.get("cta", ""))
    if draft.get("link_url"):
        result = linkedin_service.publish_link_post(
            draft_id=draft_id,
            content=content,
            original_url=draft["link_url"],
            title=draft["title"],
            description=draft["rationale"],
        )
    else:
        result = linkedin_service.publish_text_post(draft_id=draft_id, content=content)
    history = format_history(content_service.list_post_history(limit=20))
    return json_dump(result), history


def json_dump(value: dict) -> str:
    import json

    return json.dumps(value, indent=2)


def load_history() -> str:
    return format_history(content_service.list_post_history(limit=20))


def create_app():
    with gr.Blocks(title="LinkedIn Post Agent MCP") as demo:
        gr.Markdown("# LinkedIn Post Agent MCP")
        with gr.Tab("Auth"):
            auth_status = gr.Textbox(label="Auth Status", value=refresh_auth_status(), lines=6)
            auth_url = gr.Textbox(label="Auth URL", lines=3)
            auth_message = gr.Textbox(label="Auth Message", lines=4)
            connect_button = gr.Button("Connect LinkedIn", variant="primary")
            finalize_button = gr.Button("Finalize LinkedIn Auth")
            refresh_auth_button = gr.Button("Refresh Auth Status")
        with gr.Tab("Voice"):
            voice_label = gr.Textbox(label="Example Label", placeholder="Example source")
            voice_content = gr.Textbox(label="Style Example", lines=8)
            save_voice_button = gr.Button("Save Style Example")
            voice_profile = gr.Textbox(label="Voice Profile", value=load_voice_profile(), lines=12)
        with gr.Tab("Drafts"):
            topic = gr.Textbox(label="Topic", placeholder="What do you want to post about?")
            goal = gr.Textbox(label="Goal", placeholder="What outcome should the post drive?")
            notes = gr.Textbox(label="Notes", lines=6)
            urls = gr.Textbox(label="URLs", lines=4, placeholder="One URL per line")
            generate_button = gr.Button("Generate Drafts", variant="primary")
            idea_id = gr.Textbox(label="Idea ID")
            bundle_id = gr.Textbox(label="Bundle ID")
            draft_selector = gr.Dropdown(label="Drafts", choices=draft_choices(content_service.list_drafts(limit=50)))
            feedback = gr.Textbox(label="Feedback", lines=5)
            with gr.Row():
                refresh_drafts_button = gr.Button("Refresh Drafts")
                approve_button = gr.Button("Approve")
                reject_button = gr.Button("Reject")
                revise_button = gr.Button("Revise")
                publish_button = gr.Button("Publish")
            draft_display = gr.Textbox(label="Draft Detail", lines=18)
            sources_display = gr.Textbox(label="Source Bundle", lines=18)
            edit_title = gr.Textbox(label="Edit Title")
            edit_body = gr.Textbox(label="Edit Body", lines=12)
            edit_cta = gr.Textbox(label="Edit CTA", lines=3)
            edit_link_url = gr.Textbox(label="Edit Link URL")
            publish_result = gr.Textbox(label="Publish Result", lines=8)
        with gr.Tab("History"):
            refresh_history_button = gr.Button("Refresh History")
            history_display = gr.Textbox(label="Published History", value=load_history(), lines=20)

        connect_button.click(start_linkedin_auth, outputs=[auth_url, auth_message])
        finalize_button.click(finalize_linkedin_auth, outputs=[auth_message]).then(
            refresh_auth_status, outputs=[auth_status]
        )
        refresh_auth_button.click(refresh_auth_status, outputs=[auth_status])

        save_voice_button.click(
            save_voice_example,
            inputs=[voice_content, voice_label],
            outputs=[voice_content, voice_profile],
        )

        generate_button.click(
            generate_drafts,
            inputs=[topic, goal, notes, urls],
            outputs=[
                draft_selector,
                draft_display,
                sources_display,
                idea_id,
                bundle_id,
                edit_title,
                edit_body,
                edit_cta,
                edit_link_url,
            ],
        )
        refresh_drafts_button.click(refresh_drafts, outputs=[draft_selector])
        draft_selector.change(
            show_selected_draft,
            inputs=[draft_selector],
            outputs=[draft_display, sources_display, edit_title, edit_body, edit_cta, edit_link_url],
        )
        approve_button.click(
            approve_selected_draft,
            inputs=[draft_selector, edit_title, edit_body, edit_cta, edit_link_url],
            outputs=[draft_display, draft_selector, edit_title, edit_body, edit_cta, edit_link_url],
        )
        reject_button.click(
            reject_selected_draft,
            inputs=[draft_selector, feedback],
            outputs=[draft_display, draft_selector],
        )
        revise_button.click(
            revise_selected_draft,
            inputs=[draft_selector, edit_title, edit_body, edit_cta, edit_link_url, feedback],
            outputs=[draft_selector, draft_display, sources_display, edit_title, edit_body, edit_cta, edit_link_url],
        )
        publish_button.click(
            publish_selected_draft,
            inputs=[draft_selector],
            outputs=[publish_result, history_display],
        )
        refresh_history_button.click(load_history, outputs=[history_display])

    return demo
