# Deployment

## Local Development

**Backend:**

```powershell
cd resume-ranking-jobfit
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api.index:app --reload --port 8000
```

**Frontend** (separate terminal):

```powershell
cd resume-ranking-jobfit\app
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`, backend at `http://localhost:8000`. The
frontend reads `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`) — see
`app/.env.local.example`.

## Deploying to Vercel

This project uses Vercel's hybrid Next.js + Python pattern: the Next.js app in
`app/` is the primary framework build, and `api/index.py` is auto-detected as a
Python serverless function, routed via `vercel.json`.

Steps:

1. Push this repository to a Git provider (GitHub/GitLab/Bitbucket) connected to
   Vercel — **note**: this project is currently not a git repo; initialize one and
   push before connecting to Vercel.
2. In the Vercel dashboard, "Add New Project" → import the repository.
3. Vercel should detect Next.js automatically. Confirm the settings match
   `vercel.json`:
   - Install command: `cd app && npm install && cd .. && pip install -r requirements.txt`
   - Build command: `cd app && npm run build`
   - Output directory: `app/.next`
4. Set environment variables in the Vercel project settings:
   - `GEMINI_API_KEY` (optional — enables AI-generated recruiter notes in
     `/api/explain`; omit for free-tier operation, the endpoint gracefully falls
     back to a rule-based note)
   - `NEXT_PUBLIC_API_URL` — set to your deployed domain, e.g.
     `https://your-project.vercel.app` (or leave unset if using same-origin `/api/*`
     rewrites, in which case update `app/lib/api.ts` calls to use relative paths in
     production)
5. Deploy. Vercel builds the Next.js frontend and the `api/index.py` FastAPI
   function; `vercel.json` rewrites `/api/*` requests to the Python function.

## File Upload Size / Count Limits

**Resume batch is capped at 15 files per `/api/rank` request.** This is enforced
server-side (`api/index.py`, returns HTTP 400 with a clear message above the cap).
Rationale:

- **Vercel serverless function execution time limits.** Hobby-tier functions have a
  default max duration around 10s (configurable up to 60s on the tiers this project
  targets, set via `vercel.json`'s `functions.api/index.py.maxDuration`). Parsing 15
  resumes (especially PDFs) + fitting a TF-IDF vectorizer + running full entity
  extraction per resume is designed to comfortably fit within that window; 50+ files
  risks timing out, especially on cold starts.
- **Payload size limits.** Vercel serverless functions have request body size limits
  (typically several MB depending on plan). A batch of 15 resumes, even as PDFs, is
  well within this; uncapped batches risk 413 errors before our own validation even
  runs.
- **UX**: a ranked table of 50+ rows is harder for a recruiter to meaningfully scan
  than a curated top-15 shortlist; encouraging smaller batches nudges toward the
  tool's intended "first-pass shortlist" use case rather than bulk processing.

If a recruiter has more than 15 resumes, the documented workaround is to split into
multiple batches and run `/api/rank` multiple times (the client-side CSV export can
then be manually combined).

## Cold Start Considerations

- The FastAPI function loads `scikit-learn`, `pandas`, `numpy`, `pypdf`, and
  `python-docx` at import time. On Vercel's Python runtime, cold starts for this
  dependency set are typically in the low single-digit seconds. This is acceptable
  for an interactive-but-not-instant recruiting tool; if cold starts become an issue
  under real usage, consider:
  - Trimming unused imports (e.g., `pandas` is not strictly required by the API
    layer itself, only used in notebooks — could be dropped from the deployed
    function's dependency set if bundle size/cold start becomes a concern).
  - Using Vercel's Fluid Compute / keeping functions warm via a scheduled health
    check ping to `/api/health`.
- `google-generativeai` is imported lazily (inside the `/api/explain` handler, only
  when `GEMINI_API_KEY` is set) specifically to avoid adding its import cost to
  every cold start of the more frequently-hit `/api/rank` endpoint.

## Environment Variables Summary

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | No | Enables AI-generated recruiter notes via Gemini 2.5 Flash on `/api/explain`. Missing/invalid key falls back to a rule-based note — never crashes. |
| `NEXT_PUBLIC_API_URL` | No (defaults to `http://localhost:8000`) | Base URL the frontend uses to call the FastAPI backend. |
