"""Styling for the chat app: a single-column, ChatGPT/Gemini-style layout with a lapis-blue palette."""

import gradio as gr

EXAMPLES = [
    "Tell me about your background and experience.",
    "What kinds of projects are you working on now?",
    "What are your strongest technical skills?",
    "How can I get in touch with you?",
]

def greeting(name):
    """Shown in the empty chat, above the suggestion chips."""
    return f"""
<div class="twin-hello">
  <h2>Hi, I'm {name.split()[0]}.</h2>
  <p>Ask me anything about my career, skills and experience</p>
</div>
"""


THEME = gr.themes.Base(
    font=[gr.themes.GoogleFont("Figtree"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
)

CSS = """
/* ---------- Palette: "Lapis" ----------
   Gradio puts `.dark` on <body> in dark mode; light is the default. */
:root, body {
  --lapis: #2d4fd6;
  --lapis-hover: #2340b8;
  --cerulean: #17a2c4;
  --bg: #f3f5fb;
  --surface: #ffffff;
  --user-bubble: #e4e9fb;
  --line: #dde2f0;
  --ink: #121735;
  --muted: #5f6687;
  --on-accent: #ffffff;
  --shadow: 0 4px 18px -8px rgba(30, 50, 140, 0.18);
}
body.dark {
  --lapis: #8ea6ff;
  --lapis-hover: #a9bbff;
  --cerulean: #5fd0ea;
  --bg: #0e1428;
  --surface: #161d38;
  --user-bubble: #222c55;
  --line: #29325a;
  --ink: #e7eaf8;
  --muted: #959cc0;
  --on-accent: #0e1428;
  --shadow: 0 8px 28px -12px rgba(0, 0, 0, 0.6);
}

footer, .built-with, .show-api, .api-docs { display: none !important; }

html, body, gradio-app, .gradio-container, .main, .contain {
  background: var(--bg) !important;
  color: var(--ink) !important;
}

/* ---------- Single centered column ---------- */
.gradio-container {
  max-width: 820px !important;
  margin: 0 auto !important;
  padding: 0 20px 20px !important;
}
.gradio-container .main, .gradio-container .wrap, .gradio-container .contain {
  width: 100% !important;
  max-width: 100% !important;
}
.block, .form, .gr-group, .styler, .row {
  background: transparent !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  border: 0 !important;
  box-shadow: none !important;
}

/* ---------- Top bar wordmark ---------- */
.gradio-container h1 {
  display: flex !important;
  align-items: center;
  gap: 10px;
  font-size: 17px !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em !important;
  color: var(--ink) !important;
  text-align: left !important;
  margin: 0 !important;
  padding: 18px 0 10px !important;
}
.gradio-container h1::before {
  content: "";
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--lapis), var(--cerulean));
}

/* ---------- Chat area: no frame, just the page ---------- */
.chatbot, .chatbot.block, .bubble-wrap, .message-wrap {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.chatbot > .block-label, .chatbot .block-label, .chatbot > label { display: none !important; }
.chatbot .icon-button-wrapper.top-panel { background: transparent !important; border: 0 !important; }

/* Let the chat area grow to fill the window so the composer sits at the bottom */
.gradio-container { min-height: 100vh !important; }
.block:has(> .wrapper > .bubble-wrap) { flex: 1 1 auto !important; display: flex !important; flex-direction: column !important; min-height: 0 !important; }
.block:has(> .wrapper > .bubble-wrap) > .wrapper { flex: 1 1 auto !important; display: flex !important; flex-direction: column !important; min-height: 0 !important; }
.bubble-wrap { flex: 1 1 auto !important; height: auto !important; min-height: 0 !important; }

/* ---------- Empty state greeting (the one bold moment) ---------- */
.placeholder-content, .chatbot .placeholder { background: transparent !important; }
.twin-hello { text-align: left; margin: 0 0 8px; }
.gradio-container .placeholder .twin-hello h2,
.twin-hello h2 {
  font-size: clamp(34px, 6vw, 48px) !important;
  font-weight: 600 !important;
  letter-spacing: -0.035em !important;
  line-height: 1.1 !important;
  margin: 0 0 10px !important;
  padding: 0 !important;
  border: 0 !important;
  background-image: linear-gradient(100deg, var(--lapis) 10%, var(--cerulean) 90%) !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  color: transparent !important;
  width: fit-content;
  animation: twin-rise 0.6s cubic-bezier(.2, .7, .2, 1) both;
}
.twin-hello p {
  font-size: 20px !important;
  line-height: 1.4 !important;
  color: var(--muted) !important;
  margin: 0 !important;
}
@keyframes twin-rise {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) { .twin-hello h2 { animation: none; } }

/* ---------- Suggestion chips: 2x2 grid like ChatGPT ---------- */
.placeholder-content { align-items: stretch !important; justify-content: center !important; }
.placeholder { width: 100% !important; justify-content: flex-start !important; }
.examples {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 10px !important;
  width: 100% !important;
  max-width: 100% !important;
  margin-top: 28px !important;
  padding: 0 !important;
}
.example { width: 100% !important; max-width: none !important; padding: 14px 16px !important; }
.example {
  background: var(--surface) !important;
  border: 1px solid var(--line) !important;
  border-radius: 16px !important;
  color: var(--ink) !important;
  box-shadow: none !important;
  transition: border-color .15s ease, background .15s ease;
}
.example:hover, .example:focus-visible {
  border-color: var(--lapis) !important;
  background: var(--user-bubble) !important;
}
.example-text, .example-content, .example * {
  color: var(--ink) !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  text-align: left !important;
}

/* ---------- Messages ---------- */
.message-row { background: transparent !important; border: 0 !important; margin: 6px 0 !important; }
.message-row .message, .message-row .message-content, .message-row .bubble {
  font-size: 15.5px !important;
  line-height: 1.65 !important;
  box-shadow: none !important;
}
.message-row .message p, .message-row .prose p {
  font-size: 15.5px !important;
  line-height: 1.65 !important;
  margin: 0 0 10px !important;
  color: inherit !important;
}
.message-row .message p:last-child, .message-row .prose p:last-child { margin-bottom: 0 !important; }

/* You: soft pill on the right */
.message-row.user-row > .flex-wrap > .message {
  background: var(--user-bubble) !important;
  color: var(--ink) !important;
  border: 0 !important;
  border-radius: 22px !important;
  padding: 10px 18px !important;
  width: fit-content !important;
  max-width: 80% !important;
}
/* Keep the row full width so the bubble's 80% cap is measured against the
   chat column, not against the text itself (which squeezed short messages). */
.message-row.user-row,
.message-row.user-row > .flex-wrap {
  width: 100% !important;
  max-width: 100% !important;
  justify-content: flex-end !important;
}

/* Assistant: plain text, no bubble, like ChatGPT/Gemini */
.message-row.bot-row > .flex-wrap > .message {
  background: transparent !important;
  color: var(--ink) !important;
  border: 0 !important;
  padding: 4px 0 !important;
  max-width: 100% !important;
}
.message-row .message .message {
  background: transparent !important;
  padding: 0 !important;
  max-width: none !important;
  border-radius: 0 !important;
}
.message-row .message * { color: inherit; }
.message-row .message a { color: var(--lapis) !important; text-underline-offset: 3px; }
.message-row .message code {
  background: var(--user-bubble) !important;
  border-radius: 6px;
  padding: 1px 6px;
}

/* Copy / retry / undo buttons under messages: bare icons, no boxes */
.icon-button-wrapper, .icon-button-wrapper *, .message-buttons, .message-buttons * {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.message-buttons button, .icon-button {
  color: var(--muted) !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.message-buttons button:hover, .icon-button:hover { color: var(--lapis) !important; }

/* ---------- Composer: one rounded floating field ---------- */
.input-container {
  background: var(--surface) !important;
  border: 1px solid var(--line) !important;
  border-radius: 28px !important;
  box-shadow: var(--shadow) !important;
  padding: 6px 6px 6px 18px !important;
  align-items: center !important;
  transition: border-color .15s ease;
}
.input-container:focus-within { border-color: var(--lapis) !important; }
.input-container .block, .input-container .form { border-radius: 0 !important; }

textarea {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  color: var(--ink) !important;
  font-size: 15.5px !important;
  line-height: 1.5 !important;
  padding: 10px 0 !important;
  resize: none !important;
}
textarea::placeholder { color: var(--muted) !important; }

/* Round send / stop button */
.submit-button, .stop-button {
  width: 40px !important;
  height: 40px !important;
  min-width: 40px !important;
  max-width: 40px !important;
  padding: 0 !important;
  border-radius: 50% !important;
  border: 0 !important;
  background: var(--lapis) !important;
  color: var(--on-accent) !important;
  display: inline-grid !important;
  place-items: center !important;
  align-self: flex-end !important;
  transition: background .15s ease, opacity .15s ease;
}
.submit-button:hover, .stop-button:hover { background: var(--lapis-hover) !important; }
.submit-button:disabled { opacity: 0.35; cursor: default; }
.submit-button svg, .stop-button svg {
  width: 18px !important;
  height: 18px !important;
  color: var(--on-accent) !important;
  fill: currentColor;
}

/* Visible keyboard focus everywhere */
button:focus-visible, .example:focus-visible {
  outline: 2px solid var(--lapis) !important;
  outline-offset: 2px !important;
}

::selection { background: var(--lapis); color: var(--on-accent); }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--line); border-radius: 8px; }

@media (max-width: 640px) {
  .gradio-container { padding: 0 16px 12px !important; }
  .gradio-container .main { padding: 8px 0 !important; }
  .twin-hello p { font-size: 17px !important; }
  .message-row.user-row > .flex-wrap > .message { max-width: 88% !important; }
  .examples { grid-template-columns: 1fr !important; }
}
"""

JS = """
() => {
  const focusInput = () => {
    const areas = document.querySelectorAll('textarea');
    if (areas.length) areas[areas.length - 1].focus();
  };
  setTimeout(focusInput, 300);

  // Re-focus the message field whenever Gradio re-enables it
  // (i.e. after the assistant finishes responding).
  const watchTextarea = (area) => {
    if (area.dataset.twinWatched) return;
    area.dataset.twinWatched = '1';
    let wasDisabled = area.disabled || area.readOnly;
    new MutationObserver(() => {
      const isDisabled = area.disabled || area.readOnly;
      if (wasDisabled && !isDisabled) area.focus();
      wasDisabled = isDisabled;
    }).observe(area, { attributes: true, attributeFilter: ['disabled', 'readonly'] });
  };

  const scan = () => document.querySelectorAll('textarea').forEach(watchTextarea);
  setTimeout(scan, 500);
  new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
}
"""
