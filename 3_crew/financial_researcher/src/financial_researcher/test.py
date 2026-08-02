from crewai_tools import SerperDevTool

tool = SerperDevTool(
    search_url="https://google.serper.dev/scholar",
    n_results=2,
)

if __name__ == "__main__":
    print(tool.run(search_query="ChatGPT"))