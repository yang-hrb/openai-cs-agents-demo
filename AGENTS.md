# Repository Guidelines

## Project Structure & Module Organization
- `python-backend/` houses the FastAPI service: agent orchestration in `main.py`, Perplexity client helpers in `perplexity_client.py`, HTTP endpoints in `api.py`, and dependencies in `requirements.txt`.
- `ui/` is a Next.js 15 app; primary routes live in `app/`, shared UI in `components/`, utilities in `lib/`, and static assets in `public/`.

## Build, Test, and Development Commands
- Backend bootstrap: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` run from `python-backend/`.
- Local API: `python -m uvicorn api:app --reload --port 8000` exposes the chat service at `http://localhost:8000`.
- Frontend install: `npm install` (or `pnpm install`) inside `ui/` keeps the Next.js toolchain aligned.
- Full stack dev: `npm run dev` launches the UI and backend together; isolate layers with `npm run dev:next` or `npm run dev:server` as needed.
- Lint & bundle: run `npm run lint` and `npm run build` in `ui/` before opening a PR.
- Regenerate `ui/package-lock.json` with `npm install --package-lock-only` whenever dependencies change.

## Coding Style & Naming Conventions
- Python follows PEP 8: four-space indents, snake_case naming, type hints on public functions, and lightweight docstrings for guardrails, tools, and hooks.
- TypeScript components stay functional, PascalCase (`AgentPanel`), and colocated with styles; hooks remain camelCase and belong near their consumers.
- Use Tailwind utilities directly in JSX, factor shared patterns with `clsx` or `tailwind-merge`, and prefer the `@/` alias over lengthy relative paths.

## Testing Guidelines
- No automated suite exists yet; smoke-test conversation boot, seat-change handoff, guardrail triggers, and cancellation flows after edits.
- For backend coverage, add `pytest` + `pytest-asyncio` cases hitting FastAPI routes and name files `test_<module>.py`.
- Frontend specs can use Playwright or Vitest; store them as `<Component>.test.tsx` alongside the source and capture agent routing scenarios.

## Commit & Pull Request Guidelines
- Keep commit subjects short and imperative (`Improve seat map guardrail`), optionally prefixing with scopes (`chore:`) and referencing issues `(#[id])`.
- PRs should explain intent, list manual or automated checks, attach screenshots for UI updates, and highlight configuration changes (env vars, Tailwind tokens).
- Split unrelated functional, styling, and config work into separate commits to simplify review.

## Security & Configuration Tips
- Store `PERPLEXITY_API_KEY` (and optional `PPLX_MODEL`) in the environment or a local `.env` ignored by Git; never commit secrets or virtual environments.
- Review the allowed CORS origins in `python-backend/api.py` before deployment and restrict them to trusted hosts.
