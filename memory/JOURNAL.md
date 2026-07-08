# Build Journal

## Session 1 — Full initial build (2026-07-09)

Started by scaffolding the directory structure per the spec, then built the skills
taxonomy (`api/skills_taxonomy.json`) first since both parsing and scoring depend on
it — curated 277 skills across 14 categories (programming languages, web frontend/
backend, data/ML, data engineering, BI/analytics, cloud/devops, tools, testing,
security, project management, soft skills, mobile, other technical).

Wrote `api/parsing.py` and `api/scoring.py` as pure functions before touching the
FastAPI layer, per the instructions, so they could be unit tested in isolation. The
regex-based experience-duration extractor needed three separate patterns (Month-Year
ranges, MM/YYYY ranges, bare Year ranges) to cover the date formats specified in the
brief; used non-overlapping span tracking so the same date range isn't double-counted
if multiple patterns could technically match the same text region.

**Dead end #1 — Python 3.14 / scikit-learn build failure.** The first attempt to
`pip install -r requirements.txt` in a fresh venv failed hard: pip tried to build
scikit-learn from source because no prebuilt wheel exists yet for Python 3.14 (the
default `python`/`py` on this machine), and the source build failed with a Meson/
Ninja error (`vswhere.exe not recognized`, then a `ninja: error: mkdir(...) No such
file or directory`) tied to the MSVC build tooling. Rather than fight the Windows
C++ build toolchain, checked `py -0p` for other installed interpreters and found
Python 3.12 available. Recreated the venv with `py -3.12 -m venv venv` — this
pulled prebuilt wheels for every dependency and installed cleanly in under a minute.
**Lesson recorded**: pin dev/CI Python to 3.12 for this project until scikit-learn
ships 3.14 wheels; noted this implicitly by not touching `requirements.txt` version
pins (they're fine on 3.12) and relying on the venv's interpreter choice instead.

After fixing the interpreter, wrote `tests/test_parsing.py` and
`tests/test_scoring.py` (43 tests total covering skill matching including a
false-positive guard for substring matches like "R", multiple date-range formats,
education level detection and "pick highest level" behavior, and the weighted score
math including a hand-computed worked example). All 43 passed on first full run
after the venv fix — no test logic needed revision, though this reflects having
written parsing/scoring carefully against the spec's exact formulas before testing,
not a lack of edge cases in general.

Built `api/index.py` (FastAPI) wiring `/api/rank`, `/api/rerank`, `/api/explain`,
plus a `/api/health` check added for convenience during manual verification. Made
`google.generativeai` an import *inside* the `/explain` handler (not at module top
level) specifically so a missing/failed import of that package can never break
`/api/rank`, and so its import cost isn't paid on every cold start.

Started uvicorn locally and curl-tested all three endpoints against the real sample
data (5 sample resumes against the Data Analyst JD). Ranking output was sane —
Priya (senior data analyst, strong skill/experience match) ranked first at 66.09,
Carlos (sales, weak fit) and James (backend engineer, wrong domain) both landed
around 34, confirming the scoring pipeline discriminates sensibly between strong and
weak fits. Also explicitly tested the 15-file cap by sending 16 copies of one resume
and confirmed the 400 error message matches what's documented in `docs/DEPLOYMENT.md`.

Wrote all 9 sample resumes and 2 sample JDs by hand as realistic-but-synthetic
`.txt` content, covering the seniority/domain matrix requested (junior/mid/senior,
data analyst/backend/ML/data engineer/one deliberately weak sales fit).

**Frontend build.** Ran `create-next-app` with TypeScript + Tailwind + App Router.

**Dead end #2 — accidental git init.** `create-next-app` initializes a git repo
inside `app/` by default even without `--git` being explicitly requested (or despite
attempts to avoid it); since the top-level instruction was explicitly "this is NOT a
git repo, do not run git init anywhere," immediately deleted the `app/.git` directory
it created before proceeding, to avoid leaving a nested repo behind.

Tried the shadcn/ui CLI (`npx shadcn@latest init -d -y` then `add button card table
slider badge tabs separator textarea input label progress`) — this worked without
issues on this Windows/PowerShell setup, so no hand-rolled Tailwind fallback was
needed; all UI primitives are genuine shadcn/ui components (backed by `@base-ui/react`
under the hood in this shadcn version, not Radix — a detail worth noting since the
component internals/props differ slightly from older shadcn/Radix-based docs).

Built the frontend: `lib/types.ts`, `lib/api.ts` (typed fetch wrappers for rank/
rerank/explain), `lib/csv.ts` (client-side CSV export, no backend involvement),
and components for upload (drag-and-drop + file browse, JD paste-or-upload), weight
sliders, the sortable results table with inline expandable breakdown panel, and
one-click demo-data buttons that fetch the sample JD/resume `.txt` files from
`app/public/sample-data/` (copied there from `data/` so they're servable as static
assets to the browser).

**Dead end #3 — TypeScript build errors on the shadcn Slider.** `next build`
initially failed twice on `components/weight-sliders.tsx`'s `onValueChange` handler:
first because the callback parameter was implicitly typed `any` against a
`number | readonly number[]` union (this shadcn version's Slider, being base-ui
rather than Radix, supports both single-value and range sliders and types
accordingly), then because an over-eager `number[]` annotation didn't match that
same union. Fixed by typing the handler explicitly as
`(v: number | readonly number[]) => update(key, Array.isArray(v) ? v[0] : v)`.
Also cleaned up a `<>...</>` fragment inside a `.map()` in the results table to use
`<React.Fragment key={...}>` instead, since an unkeyed fragment in a list is a latent
React warning even though it didn't fail the build.

After both fixes, `npm run build` succeeded cleanly (Turbopack build, TypeScript
check, and static page generation all passed with no errors or warnings).

Wrote `vercel.json` for the hybrid Next.js + Python deploy pattern, then all docs
(`README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md` with a Mermaid diagram and a
worked scoring example, `docs/DATA.md`, `docs/DEPLOYMENT.md`) and this journal plus
`memory/DECISIONS.md` (9 ADR entries) and `memory/GLOSSARY.md`.

Generated the two Jupyter notebooks programmatically as valid nbformat 4 JSON, then
actually executed both end-to-end via `jupyter nbconvert --execute --inplace` (after
installing `nbclient`/`nbformat`/`ipykernel`/`nbconvert` into the venv) rather than
just writing static cell source — this caught nothing wrong, but confirms the
notebooks genuinely run against the real sample data and scoring code, not just
syntactically valid but untested cell content.

## Summary of what actually shipped vs. spec

Everything in the spec was implemented as described. The two notable environment-
driven deviations (documented above) were: (1) had to target Python 3.12 rather than
whatever `python`/`py` defaulted to, purely due to scikit-learn wheel availability —
no code changes were needed, just the venv's interpreter selection; (2) the shadcn/ui
CLI worked fine on this Windows/PowerShell setup (no fallback to hand-rolled Tailwind
components was required), contrary to the spec's anticipation that it might not be
feasible.
