"""Look and feel for the Sidekick app, using the course brand: navy text on light gray,
blue as the working color, gold for moments that need the human, purple as a quiet accent.
In Gradio 6, theme, css and js are passed to launch() rather than to gr.Blocks()."""

import gradio as gr

NAVY = "#032147"
BLUE = "#209DD7"
GOLD = "#FFB706"
PURPLE = "#753991"
GRAY = "#888888"
BACKGROUND = "#F2F2F2"

THEME = gr.themes.Soft(
    primary_hue=gr.themes.Color(
        c50="#F0F9FE", c100="#D0EBF8", c200="#A1D8F2", c300="#75C5EA", c400="#48B1E1",
        c500="#209DD7", c600="#1775A1", c700="#135F83", c800="#0F4E6B", c900="#0B3A50",
        c950="#072735",
    ),
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Montserrat"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=["Courier New", "ui-monospace", "monospace"],
)

CSS = """
.gradio-container { background: #F2F2F2 !important; }

#header { padding: 4px 2px 2px; }
#header .context-label {
    color: #888888; font-size: 11px; font-weight: 600;
    letter-spacing: 0.25em; text-transform: uppercase;
}
#header h1 { color: #032147; font-weight: 700; font-size: 30px; margin: 2px 0 8px; }
#header .brand-bar {
    height: 4px; width: 132px; border-radius: 2px;
    background: linear-gradient(90deg, #209DD7 0%, #753991 60%, #FFB706 100%);
}

#chat, #plan-panel, #ask-panel {
    background: #FFFFFF; border: 1px solid #D0EBF8; border-radius: 12px;
    box-shadow: 0 2px 10px rgba(3, 33, 71, 0.06);
}

#chat .message { font-size: 14px; color: #032147; }

#plan-panel { padding: 16px 18px; }
#plan-panel h3 {
    color: #209DD7; font-size: 12px; font-weight: 700;
    letter-spacing: 0.18em; text-transform: uppercase; margin: 0 0 10px;
}
#plan-panel .placeholder { color: #888888; font-size: 13px; font-style: italic; }
#plan-panel ul { list-style: none; padding: 0; margin: 0; }
#plan-panel li {
    color: #032147; font-size: 13px; line-height: 1.45;
    margin: 8px 0; display: flex; align-items: baseline; gap: 8px;
}
#plan-panel .mark {
    flex: none; width: 12px; height: 12px; border-radius: 50%;
    position: relative; top: 1px;
}
#plan-panel li.pending .mark { border: 2px solid #A1D8F2; background: #F0F9FE; }
#plan-panel li.in_progress .mark { border: 2px solid #753991; background: #CAA5DC; }
#plan-panel li.completed .mark { border: 2px solid #ECAD0A; background: #FFB706; }
#plan-panel li.completed { color: #888888; }

#ask-panel { padding: 6px; }
#ask-panel textarea { color: #032147; font-size: 14px; }
#ask-panel textarea::placeholder { color: #888888; }

#go-button {
    background: #209DD7 !important; color: #FFFFFF !important; border: none !important;
    font-weight: 600; box-shadow: 0 2px 8px rgba(32, 157, 215, 0.35);
}
#go-button:hover { background: #1775A1 !important; }
#approve-button {
    background: #FFB706 !important; color: #032147 !important; border: none !important;
    font-weight: 700; box-shadow: 0 2px 8px rgba(255, 183, 6, 0.4);
}
#approve-button:hover { background: #ECAD0A !important; }
#reset-button {
    background: #FFFFFF !important; color: #BC101F !important;
    border: 1px solid #BC101F !important; font-weight: 600;
}
#reset-button:hover { background: #BC101F !important; color: #FFFFFF !important; }
"""

# The brand is light mode, so steer Gradio away from the system dark preference.
# Served via launch(head=JS), so it runs before the app mounts and there is no dark flash.
JS = """
<script>
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.replace(url.href);
    }
</script>
"""
