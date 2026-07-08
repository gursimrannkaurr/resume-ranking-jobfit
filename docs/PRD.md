# Product Requirements Document — Resume Ranking & Job-Fit Scoring Tool

## Problem

Recruiters and hiring managers routinely screen dozens to hundreds of resumes per
open role. Manual screening is:

- **Slow** — a recruiter may spend 5-10 minutes per resume doing a first pass.
- **Inconsistent** — different reviewers (or the same reviewer on different days)
  apply different implicit weight to skills vs. experience vs. education, leading to
  inconsistent shortlists.
- **Hard to justify** — when a candidate is rejected at the resume stage, it's often
  difficult to articulate *why* in a structured, defensible way.

This tool provides a fast, explainable, adjustable first-pass ranking of a batch of
resumes against a single job description, so a human reviewer can focus their time on
the most promising candidates and have a clear, component-level rationale for every
ranking decision.

## Target User

- **Primary**: an individual recruiter or hiring manager at a small-to-mid-size
  company doing their own first-pass resume screening for a single open role.
- **Secondary**: a job seeker who wants to see how their resume scores against a
  specific job posting, to improve their materials.

## Goals

1. Let a recruiter upload a job description and a batch of resumes and get back a
   ranked shortlist within seconds.
2. Make every score fully explainable — no opaque black-box number. Every candidate's
   overall score decomposes into four visible components (similarity, skills,
   experience, education) with matched/missing skill chips.
3. Let the recruiter interactively adjust the relative importance (weights) of each
   scoring component and see the ranking update live, without re-uploading files.
4. Provide an optional AI-generated recruiter note (3-bullet strengths/gaps summary)
   that is grounded in the extracted data only — never inventing facts.
5. Run entirely on free-tier infrastructure with no required paid API calls.

## Key Features

- Job description input via paste or file upload (.txt/.pdf/.docx).
- Batch resume upload (up to 15 files) via drag-and-drop, .txt/.pdf/.docx.
- TF-IDF + cosine similarity text-relevance scoring.
- Rule-based entity extraction: skills (taxonomy match), years of experience
  (date-range regex), education level (keyword rules).
- Weighted composite score (0-100) with adjustable weights (live re-ranking, no
  re-upload required).
- Sortable results table with score bars, matched/missing skill chips.
- Optional AI-generated recruiter note per candidate (Gemini 2.5 Flash if configured,
  rule-based template otherwise).
- Client-side CSV export of the ranked shortlist.
- One-click demo data (sample JDs and resumes) for instant evaluation.

## Non-Goals

- **Not a full Applicant Tracking System (ATS).** No candidate pipeline management,
  interview scheduling, offer letters, or long-term candidate database.
- **No bias-auditing guarantees.** This tool does not claim to detect or eliminate
  bias in scoring. Skill/keyword-matching approaches can encode their own biases
  (e.g., favoring resumes that use exact JD terminology). Any production use should
  pair this tool with a human-in-the-loop review process and a fairness audit —
  neither of which this project provides or certifies.
- **English-language resumes only.** The skills taxonomy, education keyword rules,
  and TF-IDF stopword list are English-specific. Non-English resumes will score
  poorly regardless of actual candidate quality.
- **Not a resume parser for structured ATS ingestion.** We extract enough structured
  signal (skills, years, education level) to score fit, but we do not attempt to
  fully parse resumes into a canonical structured schema (contact info, full work
  history objects, etc.).
- **No persistent storage or user accounts.** Every ranking run is stateless;
  uploaded files are processed in-memory per request and not stored.

## Success Metrics

- A recruiter can go from "job description in hand" to "ranked shortlist with
  rationale" in under 2 minutes for a batch of 10-15 resumes.
- Score components are visibly and correctly decomposed for 100% of ranked
  candidates (no missing/NaN sub-scores).
- Adjusting weights re-sorts the table in under 1 second (client-server round trip),
  without requiring resume re-upload.
- The tool functions fully (rank, rerank, explain) with zero paid API keys
  configured — `/api/explain` degrades gracefully to a rule-based note.
