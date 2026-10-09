import gradio as gr
import pandas as pd
from briefing_database import read_articles, read_reporter, read_log
from enum import Enum

css = """
.dataframe-fix .table-wrap {
    min-height: 200px;
    max-height: 300px;
}
footer{display:none !important}
"""

js = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""


class Color(Enum):
    RED = "#dd0000"
    GREEN = "#00dd00"
    YELLOW = "#dddd00"
    CYAN = "#00dddd"
    MAGENTA = "#aa00dd"
    WHITE = "#87CEEB"


mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
}

names = ["Ada", "Marcus", "Zara"]
beats = ["Tech & AI", "Finance & Markets", "Science & Innovation"]


class ReporterDisplay:
    def __init__(self, name: str, beat: str):
        self.name = name
        self.beat = beat

    def get_title(self) -> str:
        return (
            f"<div style='text-align:center;font-size:34px;'>"
            f"{self.name}"
            f"<span style='color:#ccc;font-size:20px;'>"
            f" — {self.beat}</span></div>"
        )

    def get_article_count(self) -> str:
        articles = read_articles(self.name)
        count = len(articles)
        color = "#336" if count > 0 else "#633"
        return (
            f"<div style='text-align:center;background-color:{color};'>"
            f"<span style='font-size:32px'>{count}</span>"
            f"<span style='font-size:20px'> articles filed</span></div>"
        )

    def get_articles_df(self) -> pd.DataFrame:
        articles = read_articles(self.name, limit=20)
        if not articles:
            return pd.DataFrame(
                columns=["Headline", "Summary", "Sources", "Filed"]
            )
        return pd.DataFrame(
            [
                {
                    "Headline": a["headline"],
                    "Summary": (
                        a["summary"][:120] + "..."
                        if len(a["summary"]) > 120
                        else a["summary"]
                    ),
                    "Sources": a["sources"],
                    "Filed": a["datetime"],
                }
                for a in articles
            ]
        )

    def get_logs(self, previous=None) -> str:
        logs = read_log(self.name, last_n=13)
        response = ""
        for log in logs:
            timestamp, log_type, message = log
            color = mapper.get(log_type, Color.WHITE).value
            response += (
                f"<span style='color:{color}'>"
                f"{timestamp} : [{log_type}] {message}</span><br/>"
            )
        response = (
            f"<div style='height:250px;overflow-y:auto;'>{response}</div>"
        )
        if response != previous:
            return response
        return gr.update()


class ReporterView:
    def __init__(self, reporter: ReporterDisplay):
        self.reporter = reporter
        self.count = None
        self.log = None
        self.articles_table = None

    def make_ui(self):
        with gr.Column():
            gr.HTML(self.reporter.get_title())
            with gr.Row():
                self.count = gr.HTML(self.reporter.get_article_count)
            with gr.Row(variant="panel"):
                self.log = gr.HTML(self.reporter.get_logs)
            with gr.Row():
                self.articles_table = gr.Dataframe(
                    value=self.reporter.get_articles_df,
                    label="Articles",
                    headers=["Headline", "Summary", "Sources", "Filed"],
                    row_count=(5, "dynamic"),
                    col_count=4,
                    max_height=400,
                    elem_classes=["dataframe-fix"],
                )

        timer = gr.Timer(value=120)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[self.count, self.articles_table],
            show_progress="hidden",
            queue=False,
        )
        log_timer = gr.Timer(value=0.5)
        log_timer.tick(
            fn=self.reporter.get_logs,
            inputs=[self.log],
            outputs=[self.log],
            show_progress="hidden",
            queue=False,
        )

    def refresh(self):
        return (
            self.reporter.get_article_count(),
            self.reporter.get_articles_df(),
        )


def create_ui():
    reporters = [
        ReporterDisplay(name, beat) for name, beat in zip(names, beats)
    ]
    views = [ReporterView(r) for r in reporters]

    with gr.Blocks(
        title="Daily Briefing",
        css=css,
        js=js,
        theme=gr.themes.Default(primary_hue="sky"),
        fill_width=True,
    ) as ui:
        gr.Markdown(
            "# Daily Briefing System\n"
            "*3 AI reporters covering Tech, Finance, and Science*"
        )
        with gr.Row():
            for view in views:
                view.make_ui()

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
