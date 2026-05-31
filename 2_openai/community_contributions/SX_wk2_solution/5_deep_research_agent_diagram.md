# Deep Research Agent — Process Diagram

flowchart TD
    User(["👤 User"])

    User -->|"Enters research topic"| ClarifierAgent

    subgraph Step1["Step 1 — Clarification"]
        ClarifierAgent["🤖 Clarifier Agent\nGenerates 3 questions"]
    end

    ClarifierAgent -->|"Ask exactly 3 clarifying questions"| User
    User -->|"Provides answers"| ResearchInterface

    subgraph Step2["Step 2 — Planning"]
        ResearchInterface["⚙️ research_interface\nBuilds research context"]
        ResearchInterface --> PlannerAgent["🧭 Planner Agent\nGenerates 3 search queries"]
    end

    subgraph Step3["Step 3 — Search (concurrent)"]
        PlannerAgent -->|"query 1"| Search1["🌐 Search Agent"]
        PlannerAgent -->|"query 2"| Search2["🌐 Search Agent"]
        PlannerAgent -->|"query 3"| Search3["🌐 Search Agent"]
    end

    Search1 & Search2 & Search3 -->|"📚 combined_results"| ["🧪 Analyser Agent"]

    subgraph Step4["Step 4 — Analysis Loop (max 2 iterations)"]
        AnalyserAgent["🧪 Analyser Agent\nIs research complete?"]
        AnalyserAgent -->|"No — 🔁 Additional research needed with feedback provided"| PlannerAgent
    end

    AnalyserAgent -->|"Yes — ✅ Research complete"| WriterAgent

    subgraph Step5["Step 5 — Writing"]
        WriterAgent["✍️ Writer Agent\nProduces ReportData\n(summary, markdown_report,\nfollow_up_questions)"]
    end

    subgraph Step6["Step 6 — Review"]
        ReviewerAgent["📝 Reviewer Agent\nApproves or rewrites\nReportData"]
    end

    subgraph Step7["Step 7 — Email"]
        HTMLConversion["⚙️ Builds HTML-format email from\nall ReportData fields"]
        EmailAgent["📧 Email Agent\nPicks subject line\nSends via SendGrid"]
    end

    WriterAgent -->|"markdown_report"| ReviewerAgent
    ReviewerAgent -->|"ReportData"| HTMLConversion
    HTMLConversion -->|"HTML string"| EmailAgent
    EmailAgent -->|"✅ Email sent"| Inbox(["📬 Recipient Inbox"])

    ReviewerAgent -->|"markdown_report"| GradioUI(["🖥️ Gradio UI\nDisplays final report"])
```

## Agent Roles Summary

| Agent | Input | Output |
|---|---|---|
| **Clarifier** | Research topic | 3 clarifying questions |
| **Planner** | Topic + context | 3 search queries |
| **Search** (×3) | 1 search query | 2–3 paragraph summary |
| **Analyser** | All summaries | Complete: yes/no + reason |
| **Writer** | Topic + summaries | `ReportData` (markdown report) |
| **Reviewer** | Markdown report | `ReportData` (approved/rewritten) |
| **Email** | HTML report | Sends email via SendGrid |
