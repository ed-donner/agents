"""Styling constants for the digital twin Gradio app."""

BLUE = "#3b82f6"
RED = "#ef4444"

EXAMPLES = [
    "Tell me about your background and experience.",
    "What kinds of projects are you working on now?",
    "What are your strongest technical skills?",
    "How can I get in touch with you?",
]

CSS = """
:root {
  --twin-blue: #3b82f6;
  --twin-blue-dark: #2563eb;
  --twin-red: #ef4444;
  --twin-red-dark: #dc2626;
  --twin-bg: #0a0b14;
  --twin-bg-grad: radial-gradient(circle at 18% -12%, rgba(59,130,246,0.18), transparent 42%),
                  radial-gradient(circle at 88% 8%, rgba(239,68,68,0.14), transparent 40%),
                  linear-gradient(160deg, #0a0b14 0%, #12131f 55%, #0c0d16 100%);
  --twin-surface: #14151f;
  --twin-surface-2: #1c1d2a;
  --twin-border: #292b3c;
  --twin-border-strong: #3a3c52;
  --twin-text: #eceef5;
  --twin-muted: #8a8ea0;
  --twin-shadow: 0 10px 28px rgba(0,0,0,0.45);
  --twin-shadow-soft: 0 4px 14px rgba(0,0,0,0.30);
  --twin-shadow-blue: 0 10px 24px rgba(37,99,235,0.35);
  --twin-shadow-red: 0 10px 24px rgba(220,38,38,0.30);
  --twin-radius: 14px;
  --twin-radius-sm: 10px;
  --twin-accent-grad: linear-gradient(135deg, var(--twin-blue) 0%, var(--twin-red) 100%);
  --twin-accent-grad-soft: linear-gradient(135deg, rgba(59,130,246,0.10) 0%, rgba(239,68,68,0.10) 100%);
  --twin-user-grad: linear-gradient(135deg, var(--twin-blue) 0%, var(--twin-blue-dark) 100%);
  --twin-bot-grad: linear-gradient(135deg, var(--twin-surface-2) 0%, var(--twin-surface) 100%);
}

/* Light mode: override neutral palette only — blue/red accents stay identical. */
body:not(.dark) {
  --twin-bg: #f5f7fc;
  --twin-bg-grad: radial-gradient(circle at 18% -12%, rgba(59,130,246,0.14), transparent 46%),
                  radial-gradient(circle at 88% 8%, rgba(239,68,68,0.10), transparent 42%),
                  linear-gradient(160deg, #f5f7fc 0%, #eef1f9 55%, #fbfcff 100%);
  --twin-surface: #ffffff;
  --twin-surface-2: #f2f4fb;
  --twin-border: #e4e7f0;
  --twin-border-strong: #c6cad8;
  --twin-text: #1a1c28;
  --twin-muted: #6a6e7e;
  --twin-shadow: 0 10px 28px rgba(40,50,90,0.10);
  --twin-shadow-soft: 0 4px 14px rgba(40,50,90,0.07);
  --twin-bot-grad: linear-gradient(135deg, #ffffff 0%, #f4f6fc 100%);
}

footer, .built-with, .show-api, .api-docs { display: none !important; }

html, body, gradio-app { background: var(--twin-bg) !important; }

body, gradio-app {
  background-attachment: fixed !important;
}

/* ---------- Stable layout ---------- */
.gradio-container {
  background: var(--twin-bg-grad) !important;
  background-attachment: fixed !important;
  color: var(--twin-text) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  width: 100% !important;
  max-width: 880px !important;
  min-width: 0 !important;
  margin: 0 auto !important;
  padding: 36px 24px 52px !important;
}
.gradio-container .main, .gradio-container .contain, .gradio-container .wrap {
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
}
.gradio-container * { min-width: 0; }

/* ---------- Title ---------- */
.gradio-container h1 {
  display: inline-block;
  font-size: 28px !important;
  font-weight: 800 !important;
  letter-spacing: -0.02em !important;
  padding-left: 14px !important;
  margin: 6px 0 4px !important;
  text-align: left !important;
  position: relative;

  /* Blue -> red gradient text using the app's main accent colors.
     background-image (not shorthand) prevents accidental reset of background-clip.
     A solid fallback color is provided for browsers without background-clip:text. */
  color: var(--twin-blue) !important;
  background-image: linear-gradient(
      90deg,
      var(--twin-blue) 0%,
      var(--twin-blue-dark) 28%,
      #6f7bf5 52%,
      var(--twin-red-dark) 76%,
      var(--twin-red) 100%
    ) !important;
  background-size: 100% 100% !important;
  background-repeat: no-repeat !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  box-decoration-break: clone !important;
  -webkit-box-decoration-break: clone !important;

  /* Match the text gradient on the left accent stripe. */
  border-left: 3px solid transparent;
  border-image: linear-gradient(180deg, var(--twin-blue), var(--twin-red)) 1;
}
.gradio-container .desc, .gradio-container [class*="desc"] {
  color: var(--twin-muted) !important;
  font-size: 14px !important;
  margin-bottom: 18px !important;
}

/* ---------- Rounded corners on structural pieces ---------- */
.chatbot, .block, .form,
button, input, textarea,
.examples button {
  border-radius: var(--twin-radius-sm) !important;
}

/* ---------- Block surfaces ---------- */
.block, .form { background: transparent !important; box-shadow: none !important; }

/* ---------- Hide the Chatbot label / header strip ---------- */
.chatbot > .block-label,
.chatbot > label,
.chatbot .label-wrap,
.chatbot .block-label,
.chatbot > .label-container {
  display: none !important;
}

/* ---------- Chatbot frame ---------- */
.chatbot, .chatbot.block {
  background: var(--twin-bot-grad) !important;
  border: 1px solid var(--twin-border) !important;
  min-height: 460px !important;
  box-shadow: var(--twin-shadow) !important;
}
.chatbot .placeholder, .chatbot .placeholder * { color: var(--twin-muted) !important; }

/* ---------- Message rows: strip parent backgrounds ---------- */
.message-row,
.message-row > div,
.message-row .role,
.message-wrap, .bubble-wrap {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}

/* ---------- Reset borders on every bubble variant first ---------- */
.message-row .message,
.message-row .message-bubble,
.message-row .bubble {
  border: 0 !important;
  padding: 12px 16px !important;
  box-shadow: var(--twin-shadow-soft) !important;
}

/* ---------- Bubble backgrounds ---------- */
.message-row.user-row .message,
.message-row.user-row .message-bubble,
.message-row.user-row .bubble,
.message-row[data-role="user"] .message,
.message-row[data-role="user"] .message-bubble {
  background: var(--twin-user-grad) !important;
  color: #ffffff !important;
  box-shadow: var(--twin-shadow-blue) !important;
}

.message-row.bot-row .message,
.message-row.bot-row .message-bubble,
.message-row.bot-row .bubble,
.message-row[data-role="assistant"] .message,
.message-row[data-role="assistant"] .message-bubble {
  background: var(--twin-bot-grad) !important;
  color: var(--twin-text) !important;
  border: 1px solid var(--twin-border) !important;
}

/* ---------- Accent stripe (blue→red gradient) on assistant rows ----------
   Applied broadly first to cover all bubble variants, then suppressed on any
   nested matching element so the stripe lands on the outermost element only. */
.message-row.bot-row .message,
.message-row.bot-row .bubble,
.message-row.bot-row .message-bubble,
.message-row[data-role="assistant"] .message,
.message-row[data-role="assistant"] .bubble,
.message-row[data-role="assistant"] .message-bubble {
  border-left: 3px solid transparent !important;
  border-image: var(--twin-accent-grad) 1 !important;
  padding-left: 16px !important;
}

.message-row.bot-row .message .message,
.message-row.bot-row .message .bubble,
.message-row.bot-row .message .message-bubble,
.message-row.bot-row .bubble .message,
.message-row.bot-row .bubble .bubble,
.message-row.bot-row .bubble .message-bubble,
.message-row.bot-row .message-bubble .message,
.message-row.bot-row .message-bubble .bubble,
.message-row.bot-row .message-bubble .message-bubble,
.message-row[data-role="assistant"] .message .message,
.message-row[data-role="assistant"] .message .bubble,
.message-row[data-role="assistant"] .message .message-bubble,
.message-row[data-role="assistant"] .bubble .message,
.message-row[data-role="assistant"] .bubble .bubble,
.message-row[data-role="assistant"] .bubble .message-bubble,
.message-row[data-role="assistant"] .message-bubble .message,
.message-row[data-role="assistant"] .message-bubble .bubble,
.message-row[data-role="assistant"] .message-bubble .message-bubble {
  border-left: 0 !important;
  border-image: none !important;
  padding-left: 10px !important;
}

/* ---------- Uniform font size in bubbles ----------
   Force every paragraph in a bubble to the same size so the leaky
   `.prose p:first-of-type` selector can't differ in size. */
.message-row .message,
.message-row .message-bubble,
.message-row .bubble {
  font-size: 14px !important;
  line-height: 1.6 !important;
}
.message-row .message p,
.message-row .message-bubble p,
.message-row .bubble p,
.message-row .prose p {
  font-size: 14px !important;
  line-height: 1.6 !important;
  margin: 0 0 8px !important;
  color: inherit !important;
}
.message-row .message p:last-child,
.message-row .message-bubble p:last-child,
.message-row .bubble p:last-child,
.message-row .prose p:last-child { margin-bottom: 0 !important; }

/* Strip stray internal borders/backgrounds from anything inside a bubble */
.message-row .message *,
.message-row .message-bubble *,
.message-row .bubble * {
  background: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
  color: inherit !important;
}
.message-row .message a,
.message-row .message-bubble a {
  color: #ffffff !important;
  text-decoration: underline;
}
.message-row.bot-row .message a,
.message-row[data-role="assistant"] .message a {
  color: var(--twin-blue) !important;
  text-decoration: underline;
}

/* ---------- Input row alignment ---------- */
.input-row,
.gr-input-row,
.chat-input-row,
form[class*="input"] { align-items: stretch !important; gap: 10px !important; }

textarea, input[type="text"] {
  background: var(--twin-surface) !important;
  border: 1px solid var(--twin-border) !important;
  color: var(--twin-text) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  font-size: 14px !important;
  padding: 12px 16px !important;
  line-height: 1.4 !important;
  min-height: 48px !important;
  box-shadow: var(--twin-shadow-soft) !important;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
textarea:focus, input[type="text"]:focus {
  border-color: var(--twin-blue) !important;
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.25), var(--twin-shadow-soft) !important;
}
textarea::placeholder, input::placeholder { color: var(--twin-muted) !important; }

/* ---------- Buttons ---------- */
button {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  letter-spacing: 0.04em !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  border: 1px solid var(--twin-border) !important;
  background: var(--twin-surface) !important;
  color: var(--twin-text) !important;
  padding: 0 16px !important;
  min-height: 48px !important;
  align-self: stretch !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer;
  box-shadow: var(--twin-shadow-soft) !important;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease, background 0.16s ease, color 0.16s ease;
}
button:hover {
  border-color: var(--twin-blue) !important;
  color: var(--twin-blue) !important;
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(59,130,246,0.22) !important;
}

button.primary,
button[variant="primary"],
button.submit,
button.submit-button,
.submit-button,
button.lg.primary {
  background: var(--twin-accent-grad) !important;
  border: 1px solid transparent !important;
  color: #ffffff !important;
  min-height: 48px !important;
  align-self: stretch !important;
  padding: 0 18px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: var(--twin-shadow-blue) !important;
}
button.primary:hover,
button.submit:hover,
.submit-button:hover,
button.lg.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(37,99,235,0.40) !important;
  color: #ffffff !important;
  border-color: transparent !important;
}

/* ---------- Submit-button icon ---------- */
button.submit svg,
button.submit-button svg,
.submit-button svg,
button.primary svg,
button[variant="primary"] svg {
  width: 18px !important;
  height: 18px !important;
  margin: 0 auto !important;
  display: block !important;
  align-self: center !important;
  color: #ffffff !important;
  fill: currentColor !important;
  stroke: currentColor !important;
}

/* ---------- Examples ---------- */
.examples, .examples-holder, [data-testid="examples"] {
  background: transparent !important;
  padding: 0 !important;
  margin-top: 14px !important;
}
.examples table, .examples-table { background: transparent !important; border: 0 !important; }
.examples button, .example, .examples td button, [data-testid="examples"] button {
  background: var(--twin-surface) !important;
  border: 1px solid var(--twin-border) !important;
  color: var(--twin-text) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 10px 16px !important;
  text-align: left !important;
  min-height: 0 !important;
  align-self: auto !important;
  display: inline-block !important;
  box-shadow: var(--twin-shadow-soft) !important;
  transition: border-color 0.16s ease, color 0.16s ease, transform 0.16s ease, box-shadow 0.16s ease;
}
.examples button:hover, .example:hover, [data-testid="examples"] button:hover {
  border-color: var(--twin-red) !important;
  color: var(--twin-red) !important;
  background: var(--twin-surface) !important;
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(239,68,68,0.18) !important;
}

/* ---------- Icon buttons (clear, retry, copy) ---------- */
.icon-button, .chatbot .icon-button {
  color: var(--twin-muted) !important;
  background: transparent !important;
  border: 0 !important;
  min-height: 0 !important;
  align-self: auto !important;
  padding: 6px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: none !important;
  transition: color 0.16s ease, background 0.16s ease;
}
.icon-button:hover, .chatbot .icon-button:hover {
  color: var(--twin-red) !important;
  background: var(--twin-accent-grad-soft) !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ---------- Theme toggle button ---------- */
#twin-theme-toggle {
  position: fixed !important;
  top: 18px !important;
  right: 22px !important;
  z-index: 9999 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  width: auto !important;
  min-height: 40px !important;
  padding: 0 16px !important;
  border-radius: 999px !important;
  border: 1px solid var(--twin-border) !important;
  background: var(--twin-surface) !important;
  color: var(--twin-text) !important;
  cursor: pointer !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
  box-shadow: var(--twin-shadow-soft) !important;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
}
#twin-theme-toggle:hover {
  border-color: var(--twin-blue) !important;
  color: var(--twin-text) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 8px 20px rgba(59,130,246,0.22) !important;
  background: var(--twin-surface) !important;
}
#twin-theme-toggle .twin-toggle-icon {
  font-size: 16px !important;
  line-height: 1 !important;
  display: inline-block;
}
#twin-theme-toggle .twin-toggle-label {
  font-size: 13px !important;
}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--twin-border-strong);
  border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--twin-blue);
}

/* ---------- Selection ---------- */
::selection {
  background: var(--twin-blue);
  color: #ffffff;
}

/* ---------- Mobile ---------- */
@media (max-width: 640px) {
  .gradio-container { padding: 24px 14px 40px !important; }
  .gradio-container h1 { font-size: 24px !important; }
  #twin-theme-toggle { top: 12px !important; right: 12px !important; padding: 0 12px !important; }
  #twin-theme-toggle .twin-toggle-label { display: none !important; }
}
"""

JS = """
(() => {
  document.title = 'Digital Twin';

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

  // ---------- Dark / light theme toggle ----------
  const STORE_KEY = 'twin-theme';

  const syncToggleLabel = (btn, isDark) => {
    const icon = btn.querySelector('.twin-toggle-icon');
    const label = btn.querySelector('.twin-toggle-label');
    if (icon) icon.textContent = isDark ? '\\u2600\\uFE0F' : '\\u{1F319}';
    if (label) label.textContent = isDark ? 'Light' : 'Dark';
  };

  const applyTheme = (mode) => {
    const isDark = mode === 'dark';
    if (isDark) document.body.classList.add('dark');
    else document.body.classList.remove('dark');
    const btn = document.getElementById('twin-theme-toggle');
    if (btn) syncToggleLabel(btn, isDark);
  };

  const resolveInitialMode = () => {
    const saved = localStorage.getItem(STORE_KEY);
    if (saved === 'dark' || saved === 'light') return saved;
    // Fall back to the OS preference, else default to dark.
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) return 'light';
    return 'dark';
  };

  const mountToggle = () => {
    if (document.getElementById('twin-theme-toggle')) return;
    const btn = document.createElement('button');
    btn.id = 'twin-theme-toggle';
    btn.type = 'button';
    btn.innerHTML =
      '<span class="twin-toggle-icon"></span><span class="twin-toggle-label"></span>';
    btn.addEventListener('click', () => {
      const next = document.body.classList.contains('dark') ? 'light' : 'dark';
      localStorage.setItem(STORE_KEY, next);
      applyTheme(next);
    });
    document.body.appendChild(btn);
    applyTheme(resolveInitialMode());
  };

  mountToggle();
  new MutationObserver(() => {
    // Re-assert the saved mode if Gradio re-renders and drops our class.
    const saved = localStorage.getItem(STORE_KEY);
    if (saved) {
      const wantDark = saved === 'dark';
      const isDark = document.body.classList.contains('dark');
      if (wantDark !== isDark) applyTheme(saved);
    }
    if (!document.getElementById('twin-theme-toggle')) mountToggle();
  }).observe(document.body, { childList: true, subtree: false });
})()
"""