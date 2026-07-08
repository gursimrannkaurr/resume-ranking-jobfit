# Decisions Log (ADR-style)

## ADR-001: TF-IDF fit per-request, not a persistent pre-trained vectorizer

**Decision**: `compute_tfidf_similarity` fits a fresh `TfidfVectorizer` on
`[jd_text, *resume_texts]` for every `/api/rank` call, rather than training and
persisting a vectorizer/vocabulary ahead of time.

**Why**: The relevant "corpus" for TF-IDF is exactly the JD + the specific batch of
resumes being compared *right now* — vocabulary and IDF weights should reflect that
specific comparison, not some global corpus that may not represent the terms in this
particular JD/resume set. A persistent vectorizer would need periodic retraining as
vocabulary drifts (new tech terms, evolving JD language) and adds an operational
dependency (where is it stored? how is it versioned?) that a stateless serverless
function shouldn't need. Fitting per-request is cheap (well under 100ms for ~15
short documents) so there's no performance reason to persist it either.

**Tradeoff accepted**: Every request pays the (small) cost of re-fitting. Acceptable
given batch sizes are capped at 15 resumes (see ADR-006).

---

## ADR-002: Regex date-range parsing instead of NER for experience extraction

**Decision**: `extract_experience_years` uses three regex patterns (Month-Year
ranges, MM/YYYY ranges, bare Year ranges) rather than a Named Entity
Recognition (NER) model to find date ranges and sum durations.

**Why**: Resume date ranges follow a small number of highly regular formats. A
regex-based approach is free (no model download/inference cost), fully deterministic
and testable (see `tests/test_parsing.py`), and — critically — explainable: we can
show exactly which substring was matched as a date range if we ever need to debug a
wrong duration. An NER model would add latency, a dependency, and non-determinism for
marginal gain on a problem regex handles well.

**Tradeoff accepted**: Unusual date formats (e.g., "Q3 2021 - Q1 2023", non-English
month names) will not be captured and will silently undercount experience. This is
an acceptable gap for a v1 given the English-language-only non-goal already stated
in `docs/PRD.md`.

---

## ADR-003: Rule-based template fallback for `/api/explain`, not a hard dependency on Gemini

**Decision**: `/api/explain` always returns a usable 3-bullet note. If
`GEMINI_API_KEY` is unset, or the Gemini call fails for any reason (network, quota,
malformed response), the endpoint falls back to `_rule_based_note()`, a deterministic
template built from the same structured data that would have been sent to Gemini.

**Why**: This project has a hard zero-cost constraint — it must be fully functional
without any paid API key. Wrapping the Gemini call in try/except with a meaningful
fallback (rather than, say, returning a 500 or an empty note) means the "Get AI Note"
button always does something useful, and a user without a Gemini key never
sees a broken feature.

---

## ADR-004: Default weights 0.4 / 0.3 / 0.2 / 0.1 (similarity / skills / experience / education)

**Decision**: Default scoring weights favor text similarity (0.4) and skill overlap
(0.3) over experience fit (0.2) and education fit (0.1).

**Why**: Text similarity and skill overlap are the most direct, resume-visible
signals of role fit and are least prone to unfairly penalizing non-traditional
candidates (e.g., someone who's self-taught or career-switched but has the right
skills). Education is weighted lowest deliberately — degree requirements are one of
the more commonly-cited sources of unnecessary filtering in hiring, and this tool
should not implicitly encode "degree matters most." Experience sits in the middle:
relevant, but a candidate with slightly less tenure and strong skill/text match
should still be able to rank competitively. These are defaults, not fixed —
weights are fully exposed as sliders in the UI specifically so a recruiter can
recalibrate for their own role/values.

---

## ADR-005: Next.js + FastAPI hybrid on Vercel, rather than a single-framework app

**Decision**: Frontend is a separate Next.js App Router project (`app/`); backend is
a separate FastAPI Python app (`api/`), deployed together on Vercel via its
Python-function-alongside-Next.js pattern (`vercel.json` rewrites).

**Why**: The core scoring engine benefits enormously from Python's data/ML ecosystem
(scikit-learn, pandas, numpy, pypdf, python-docx) — reimplementing TF-IDF cosine
similarity or PDF parsing in JavaScript would be needless extra work and a worse
ecosystem fit. Next.js + Tailwind + shadcn/ui is the more productive choice for a
polished, interactive frontend (sliders, sortable tables, drag-and-drop). Vercel
natively supports deploying both from a single repo/project via its Python runtime
functions, avoiding the need for a separate backend host — keeping the whole project
on free-tier infrastructure with one deploy step.

---

## ADR-006: Cap resume batch size at 15 files per request

**Decision**: `/api/rank` rejects requests with more than 15 resume files with a
400 error.

**Why**: See `docs/DEPLOYMENT.md` for the full rationale — primarily Vercel
serverless function execution time and payload size limits. 15 was chosen as a
number comfortably processable (parsing + scoring) within a ~60s function timeout
even in a cold-start, PDF-heavy worst case, while still being large enough to be a
meaningful "first-pass shortlist" batch size for a single role.

---

## ADR-007: .txt-first sample data, with .pdf/.docx support built but not required for demo

**Decision**: All 9 sample resumes and 2 sample JDs in `data/` are plain `.txt`
files, even though the API supports `.pdf` and `.docx` uploads.

**Why**: Plain text sample data is trivially human-readable/diffable/editable for
anyone reviewing this project, keeps the repo lightweight (no binary PDF/DOCX blobs
to track), and removes any dependency on external tools to *generate* realistic
sample PDFs. The parsing layer (`extract_text_from_bytes`) is still fully
implemented and tested for `.pdf`/`.docx` since real-world resumes are usually one
of those formats — the demo data format is a convenience choice, not a functional
limitation.

---

## ADR-008: Substring/word-boundary skill matching instead of ML-based skill extraction

**Decision**: `extract_skills` matches taxonomy entries against resume text via
case-insensitive regex with boundary lookarounds, not an ML classifier or embedding
similarity search.

**Why**: Same core rationale as ADR-002 (regex over NER) — explainability and zero
cost. A recruiter looking at a "matched skills" chip should be able to trust that the
exact string appeared in the resume, not that some model inferred a related concept.
This keeps false positives/negatives traceable and debuggable (see
`memory/GLOSSARY.md`). The known limitation — no synonym handling (e.g., "JS" vs.
"JavaScript" need separate taxonomy entries) — is accepted for v1 and documented in
`docs/DATA.md`.

---

## ADR-009: Experience/education "fit" scaling uses linear ramps, not hard cutoffs

**Decision**: `compute_experience_fit` scales linearly from 0 to 1 as experience
approaches the required years (rather than a hard 0/1 cutoff at the threshold), and
`compute_education_fit` similarly softens (rather than zeroing out) candidates below
the required education level, losing ~34% fit per level of gap.

**Why**: Hard cutoffs (e.g., "reject anyone under 3 years experience") are a known
source of overly rigid, exclusionary screening — a candidate with 2.5 years and
excellent skill match shouldn't be scored identically to one with 0 years. Linear/
soft scaling keeps borderline-strong candidates visible in the ranked list rather
than artificially suppressed to zero, aligning with this tool's role as a
*first-pass* aid, not an automatic reject mechanism.
