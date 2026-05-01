# Job Application Sidekick (Week 4 Lab 4 Exercise)

This project is a LangGraph sidekick for DevOps/Cloud job applications.

It can:
- search online roles,
- match jobs to your CV,
- draft a tailored cover letter,
- run guardrails to keep language human and claims truthful,
- require your approval before submission.

## Run

1. Open `4_lab4_job_application_sidekick.ipynb`
2. Review or edit `candidate_profile.txt` (sanitized profile, no direct PII)
3. Run notebook cells top to bottom

## Safety / Guardrails

- No fake claims not supported by your CV
- Avoid robotic, AI-sounding language
- Keep final submission human-approved

## Notes

This notebook intentionally does not auto-submit on job portals.
It prepares quality drafts and links for manual, approved submission.

The default flow loads `candidate_profile.txt` and applies local PII redaction before LLM calls.
