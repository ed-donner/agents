we have create a DEEP RESEARCH AGENT HERE

WE USED ALL THESE THINGS

1. Planning Agent -> from the input queries, generates multiple keywords to search for.

2. Search Agent -> searches the keywords on web using OPENAI's WEBSEARCHTOOL and give   Structured Output

3. Writer Agent -> from the search results, generates a report and returns Structured Output

4. Reviewer Agent -> Reviews the create final report, score it out of 10 and also gives feedback. if score is not satifsactory, asks the writer agent to write it again

5. Input GuardRail -> flags any query which it thinks is sennsitive in nature

6. Output GuardRail -> flags if the final report contains any emojis in it.

7. A Research Manager which is the driver of multri agent orchestration

8 a gradio file for UI
