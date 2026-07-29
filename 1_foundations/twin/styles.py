"""Styling constants for the digital twin Gradio app with a full-width WhatsApp-style modern design."""

EXAMPLES = [
    "Tell me about your background and AI/ML experience.",
    "What key projects in LLMs, RAG, and AI have you built?",
    "What are your strongest technical skills and programming tools?",
    "How can I get in touch or schedule a meeting with you?",
]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@500;600;700;800&display=swap');

:root {
  --wa-bg: #0b1019;
  --wa-chat-bg: #0f172a;
  --wa-user-bg: linear-gradient(135deg, #059669 0%, #10b981 100%);
  --wa-bot-bg: #1e293b;
  --wa-border: rgba(255, 255, 255, 0.08);
  --wa-text: #f8fafc;
  --wa-muted: #94a3b8;
  --wa-accent: #10b981;
}

footer, .built-with, .show-api, .api-docs { display: none !important; }

html, body, gradio-app {
  background: var(--wa-bg) !important;
  color: var(--wa-text) !important;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
  overflow-x: hidden !important;
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
}

/* ---------- Full Width Layout Container ---------- */
.gradio-container {
  background: transparent !important;
  color: var(--wa-text) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  width: 100% !important;
  max-width: 1380px !important;
  min-width: 0 !important;
  margin: 0 auto !important;
  padding: 24px 32px 40px !important;
}

.gradio-container .main, .gradio-container .contain, .gradio-container .wrap {
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

/* ---------- Title & Futuristic Header ---------- */
.gradio-container h1 {
  font-family: 'Outfit', sans-serif !important;
  font-size: 26px !important;
  font-weight: 800 !important;
  letter-spacing: 0.02em !important;
  background: linear-gradient(135deg, #34d399 0%, #60a5fa 100%);
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  border-left: 4px solid var(--wa-accent);
  padding-left: 16px !important;
  margin: 4px 0 6px !important;
  text-align: left !important;
}

.gradio-container p, .gradio-container .description {
  color: var(--wa-muted) !important;
  font-size: 14.5px !important;
  font-weight: 500 !important;
  margin-bottom: 20px !important;
}

/* ---------- Block Surfaces ---------- */
.block, .form { background: transparent !important; box-shadow: none !important; border: none !important; }

/* Hide default chatbot header labels */
.chatbot > .block-label,
.chatbot > label,
.chatbot .label-wrap,
.chatbot .block-label,
.chatbot > .label-container {
  display: none !important;
}

/* ---------- Full Width Chatbot Panel ---------- */
.chatbot, .chatbot.block {
  background: var(--wa-chat-bg) !important;
  border: 1px solid var(--wa-border) !important;
  border-radius: 20px !important;
  box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6) !important;
  height: 640px !important;
  min-height: 640px !important;
  padding: 28px 24px !important;
  overflow-y: auto !important;
  width: 100% !important;
}

.chatbot .placeholder, .chatbot .placeholder * {
  color: var(--wa-muted) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 15px !important;
}

/* ---------- NEUTRALIZE ALL NESTED GRADIO CONTAINERS ---------- */
/* Strip backgrounds, borders, padding, and shadows from all nested wrapper elements */
.chatbot *,
.chatbot .message-row,
.chatbot .message-row *,
.chatbot .message-wrap,
.chatbot .bubble-wrap,
.chatbot .prose {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  outline: none !important;
}

/* Hide Gradio action buttons / share / copy popovers */
.chatbot .action-buttons,
.chatbot .message-buttons,
.chatbot [data-testid="copy-button"],
.chatbot .icon-button,
.chatbot button.copy,
.chatbot .bot-row button,
.chatbot .user-row button {
  display: none !important;
}

/* ---------- Generous Row Spacing & Flex Alignments ---------- */
.chatbot .message-row {
  margin-bottom: 24px !important;
  display: flex !important;
  width: 100% !important;
}

.chatbot .message-row.user-row,
.chatbot .message-row[data-role="user"] {
  justify-content: flex-end !important;
}

.chatbot .message-row.bot-row,
.chatbot .message-row[data-role="assistant"] {
  justify-content: flex-start !important;
}

/* ---------- WHATSAPP STYLE CHAT BUBBLES ---------- */

/* USER BUBBLE (Right-aligned, WhatsApp Emerald Green) */
.chatbot .message-row.user-row > div,
.chatbot .message-row.user-row .message,
.chatbot .message-row[data-role="user"] > div,
.chatbot .message-row[data-role="user"] .message {
  background: var(--wa-user-bg) !important;
  border-radius: 18px 18px 4px 18px !important;
  color: #ffffff !important;
  padding: 14px 20px !important;
  max-width: 72% !important;
  margin-left: auto !important;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.25) !important;
  word-break: break-word !important;
  display: block !important;
}

/* ASSISTANT / BOT BUBBLE (Left-aligned, Dark Slate Glass) */
.chatbot .message-row.bot-row > div,
.chatbot .message-row.bot-row .message,
.chatbot .message-row[data-role="assistant"] > div,
.chatbot .message-row[data-role="assistant"] .message {
  background: var(--wa-bot-bg) !important;
  border: 1px solid var(--wa-border) !important;
  border-radius: 18px 18px 18px 4px !important;
  color: #f8fafc !important;
  padding: 16px 22px !important;
  max-width: 78% !important;
  margin-right: auto !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
  word-break: break-word !important;
  display: block !important;
}

/* ---------- PARAGRAPH & TYPOGRAPHY INSIDE BUBBLES ---------- */
.chatbot .message-row p,
.chatbot .message-row .prose p {
  font-size: 15px !important;
  line-height: 1.7 !important;
  margin: 0 0 10px 0 !important;
  color: inherit !important;
}

.chatbot .message-row p:last-child,
.chatbot .message-row .prose p:last-child {
  margin-bottom: 0 !important;
}

.chatbot .message-row ul,
.chatbot .message-row ol {
  margin: 8px 0 12px 22px !important;
  padding: 0 !important;
}

.chatbot .message-row li {
  margin-bottom: 6px !important;
  line-height: 1.6 !important;
}

.chatbot .message-row a {
  color: #34d399 !important;
  text-decoration: underline;
}

/* ---------- Textarea & Inputs Row ---------- */
.input-row, .gr-input-row, .chat-input-row {
  margin-top: 18px !important;
  gap: 14px !important;
  display: flex !important;
  align-items: center !important;
}

textarea, input[type="text"] {
  background: #1e293b !important;
  border: 1px solid var(--wa-border) !important;
  border-radius: 16px !important;
  color: #ffffff !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 15px !important;
  padding: 16px 20px !important;
  line-height: 1.5 !important;
  min-height: 56px !important;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4) !important;
  transition: border-color 0.2s ease !important;
  flex: 1 !important;
}

textarea:focus, input[type="text"]:focus {
  border-color: var(--wa-accent) !important;
  outline: none !important;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.3) !important;
}

textarea::placeholder, input::placeholder {
  color: var(--wa-muted) !important;
}

/* ---------- Submit Button ---------- */
button.primary,
button[variant="primary"],
button.submit,
button.submit-button,
.submit-button {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
  border: none !important;
  color: #ffffff !important;
  min-height: 56px !important;
  padding: 0 24px !important;
  border-radius: 16px !important;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3) !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
  font-size: 14px !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}

button.primary:hover,
button.submit:hover,
.submit-button:hover {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%) !important;
  box-shadow: 0 6px 22px rgba(16, 185, 129, 0.5) !important;
  transform: translateY(-1px) !important;
}

button.submit svg,
button.submit-button svg,
.submit-button svg,
button.primary svg {
  width: 20px !important;
  height: 20px !important;
  color: #ffffff !important;
  fill: currentColor !important;
  stroke: currentColor !important;
}

/* ---------- Example Chips ---------- */
.examples, .examples-holder, [data-testid="examples"] {
  background: transparent !important;
  padding: 0 !important;
  margin-top: 20px !important;
}
.examples table, .examples-table { background: transparent !important; border: 0 !important; }

.examples button, .example, [data-testid="examples"] button {
  background: #1e293b !important;
  border: 1px solid var(--wa-border) !important;
  border-radius: 14px !important;
  color: #cbd5e1 !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 12px 18px !important;
  text-align: left !important;
  transition: all 0.2s ease !important;
}

.examples button:hover, .example:hover, [data-testid="examples"] button:hover {
  background: rgba(16, 185, 129, 0.12) !important;
  border-color: var(--wa-accent) !important;
  color: #34d399 !important;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2) !important;
  transform: translateY(-1px) !important;
}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--wa-chat-bg); }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--wa-accent); }

::selection { background: var(--wa-accent); color: #0b1019; }

@media (max-width: 640px) {
  .gradio-container { padding: 16px 12px 32px !important; }
  .chatbot .message-row.user-row > div, .chatbot .message-row.user-row .message { max-width: 88% !important; }
  .chatbot .message-row.bot-row > div, .chatbot .message-row.bot-row .message { max-width: 92% !important; }
}
"""

JS = """
() => {
  document.title = 'AI Digital Agent // Bhupesh Danewa';

  const focusInput = () => {
    const areas = document.querySelectorAll('textarea');
    if (areas.length) areas[areas.length - 1].focus();
  };
  setTimeout(focusInput, 300);

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
