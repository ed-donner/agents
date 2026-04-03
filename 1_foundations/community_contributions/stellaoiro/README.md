---
title: hali-hpv-kenya
app_file: app.py
sdk: gradio
sdk_version: 5.49.1
---

# HALI (this Space)

HPV vaccine companion for Kenya — see `app.py` and `4_lab4_mama_salama.ipynb`.

**Live:** [huggingface.co/spaces/AcharO/hali-hpv-kenya](https://huggingface.co/spaces/AcharO/hali-hpv-kenya)

---

## Week 1 Lab 3 — career chat (separate Space)

To share the LinkedIn PDF + summary chatbot with evaluator-rerun on Hugging Face, create **another** Space (Gradio, blank template) and upload:

- `lab3_career_chat.py` (set as the app file in README or Space settings)
- `me/summary.txt` and **your** `me/linkedin.pdf` (LinkedIn → Profile → More → Save to PDF). It is **gitignored** here so the instructor’s sample PDF is not committed; upload your own file to the Space.
- `requirements.txt` (must include `openai`, `gradio`, `python-dotenv`, `pydantic`, `pypdf`)

**Space secrets:** add `OPENAI_API_KEY`. Optionally add `GOOGLE_API_KEY` so the evaluator uses Gemini like the course notebook; otherwise evaluation uses `gpt-4o-mini`.

**README frontmatter for that Space:**

```yaml
---
title: your-career-twin-lab3
app_file: lab3_career_chat.py
sdk: gradio
sdk_version: 5.49.1
---
```

Local quick share (Gradio tunnel): `python lab3_career_chat.py` with `share=True` if you temporarily add it to `launch()`, or use the notebook `3_lab3_career_twin.ipynb`.
