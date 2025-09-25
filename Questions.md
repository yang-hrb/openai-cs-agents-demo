# Questions

## Question 1
Point out where the Perplexity API is used in this repo?

**Answer:** Every LLM request goes through `python-backend/perplexity_client.py:11-40`, which wraps the Perplexity Chat Completions endpoint. That helper is invoked by the guardrail evaluators in `python-backend/main.py:115-160`, by the agent turn runner in `python-backend/main.py:252-309`, and by the triage router in `python-backend/main.py:420-452`.

========================================
## Question 2 告诉我做了哪些改变code change

- Backend no longer depends on the OpenAI Agents SDK; introduced `python-backend/perplexity_client.py` and refactored `main.py` + `api.py` to call Perplexity for guardrails, triage, and agent responses.
- Updated tooling metadata so seat-map results re-enter the message stream, and streamlined requirements to `fastapi`, `httpx`, `pydantic`, and `uvicorn`.
- Frontend branding switched to Perplexity (new icon, package rename), docs refreshed (`README.md`, `AGENTS.md`, `Questions.md`), and dependency locks regenerated.
