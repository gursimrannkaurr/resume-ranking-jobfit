"""
FastAPI app: Resume Ranking & Job-Fit Scoring Tool API.

Endpoints:
  POST /api/rank     - JD + up to 15 resume files -> ranked candidate list
  POST /api/rerank   - component scores + new weights -> recomputed overall scores
  POST /api/explain  - one candidate's data + JD -> AI (or rule-based) recruiter note
  GET  /api/health   - simple health check
"""
import os
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.parsing import extract_text_from_bytes, load_skills_taxonomy, normalize_text
from api.scoring import (
    DEFAULT_REQUIRED_EDUCATION_LEVEL,
    DEFAULT_REQUIRED_EXPERIENCE_YEARS,
    DEFAULT_WEIGHTS,
    compute_tfidf_similarity,
    compute_weighted_score,
    score_candidate,
)

MAX_RESUME_FILES = 15

app = FastAPI(
    title="Resume Ranking & Job-Fit Scoring API",
    description="TF-IDF + entity-extraction based resume ranking against a job description.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_TAXONOMY = load_skills_taxonomy()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/rank")
async def rank_candidates(
    jd_text: Optional[str] = Form(None),
    weight_similarity: float = Form(DEFAULT_WEIGHTS["similarity"]),
    weight_skills: float = Form(DEFAULT_WEIGHTS["skills"]),
    weight_experience: float = Form(DEFAULT_WEIGHTS["experience"]),
    weight_education: float = Form(DEFAULT_WEIGHTS["education"]),
    required_years: float = Form(DEFAULT_REQUIRED_EXPERIENCE_YEARS),
    required_education: int = Form(DEFAULT_REQUIRED_EDUCATION_LEVEL),
    jd_file: Optional[UploadFile] = File(None),
    resumes: List[UploadFile] = File(...),
):
    if len(resumes) == 0:
        raise HTTPException(status_code=400, detail="At least one resume file is required.")

    if len(resumes) > MAX_RESUME_FILES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Too many resumes uploaded ({len(resumes)}). Maximum allowed is "
                f"{MAX_RESUME_FILES} per request due to serverless function time/payload "
                "limits on Vercel (see docs/DEPLOYMENT.md). Please split into multiple batches."
            ),
        )

    # Resolve JD text: prefer uploaded file, fall back to pasted text
    resolved_jd_text = ""
    if jd_file is not None:
        jd_bytes = await jd_file.read()
        try:
            resolved_jd_text = extract_text_from_bytes(jd_file.filename, jd_bytes)
        except (ValueError, RuntimeError) as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse JD file: {e}")
    elif jd_text:
        resolved_jd_text = jd_text

    resolved_jd_text = normalize_text(resolved_jd_text)
    if not resolved_jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required (paste text or upload a file).")

    weights = {
        "similarity": weight_similarity,
        "skills": weight_skills,
        "experience": weight_experience,
        "education": weight_education,
    }

    candidate_texts = []
    filenames = []
    for f in resumes:
        raw = await f.read()
        try:
            text = extract_text_from_bytes(f.filename, raw)
        except (ValueError, RuntimeError) as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse resume '{f.filename}': {e}")
        candidate_texts.append(normalize_text(text))
        filenames.append(f.filename)

    similarities = compute_tfidf_similarity(resolved_jd_text, candidate_texts)

    results = []
    for filename, text, sim in zip(filenames, candidate_texts, similarities):
        scored = score_candidate(
            resolved_jd_text,
            text,
            sim,
            weights=weights,
            taxonomy=_TAXONOMY,
            required_years=required_years,
            required_education=required_education,
        )
        scored["filename"] = filename
        results.append(scored)

    results.sort(key=lambda r: r["overall_score"], reverse=True)
    return {"candidates": results, "weights": weights}


class ComponentScores(BaseModel):
    filename: str
    similarity: float
    skill_overlap: float
    experience_fit: float
    education_fit: float


class RerankRequest(BaseModel):
    candidates: List[ComponentScores]
    weight_similarity: float = DEFAULT_WEIGHTS["similarity"]
    weight_skills: float = DEFAULT_WEIGHTS["skills"]
    weight_experience: float = DEFAULT_WEIGHTS["experience"]
    weight_education: float = DEFAULT_WEIGHTS["education"]


@app.post("/api/rerank")
def rerank(req: RerankRequest):
    weights = {
        "similarity": req.weight_similarity,
        "skills": req.weight_skills,
        "experience": req.weight_experience,
        "education": req.weight_education,
    }
    results = []
    for c in req.candidates:
        overall = compute_weighted_score(
            c.similarity, c.skill_overlap, c.experience_fit, c.education_fit, weights
        )
        results.append({"filename": c.filename, "overall_score": overall})
    results.sort(key=lambda r: r["overall_score"], reverse=True)
    return {"candidates": results, "weights": weights}


class ExplainRequest(BaseModel):
    filename: str
    jd_text: str
    overall_score: float
    similarity: float
    skill_overlap: float
    experience_years: float
    education_level: int
    matched_skills: List[str] = []
    missing_skills: List[str] = []


EDUCATION_LABELS = {0: "None listed", 1: "Diploma/Associate", 2: "Bachelor's", 3: "Master's", 4: "PhD"}


def _rule_based_note(req: ExplainRequest) -> str:
    top_matched = req.matched_skills[:6] or ["none identified"]
    top_missing = req.missing_skills[:6] or ["none — full skill coverage"]
    edu_label = EDUCATION_LABELS.get(req.education_level, "Unknown")
    return (
        f"- Strengths: candidate matches {len(req.matched_skills)} required skill(s) "
        f"including {', '.join(top_matched)}, with {req.experience_years} years of "
        f"extracted experience and a {edu_label} education level.\n"
        f"- Fit signal: text similarity to the JD is {round(req.similarity * 100, 1)}%, "
        f"and skill overlap is {round(req.skill_overlap * 100, 1)}%, yielding an overall "
        f"fit score of {req.overall_score}/100.\n"
        f"- Gaps: missing skills mentioned in the JD include {', '.join(top_missing)}; "
        "recommend probing these in a screening call before proceeding."
    )


@app.post("/api/explain")
def explain(req: ExplainRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"note": _rule_based_note(req), "source": "rule_based"}

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""You are a recruiting assistant. Using ONLY the facts given below
(do not invent skills, experience, or facts not listed), write a concise 3-bullet
recruiter note: 1-2 bullets on strengths, 1-2 on gaps/risks.

Candidate: {req.filename}
Overall fit score: {req.overall_score}/100
Text similarity to JD: {round(req.similarity * 100, 1)}%
Skill overlap: {round(req.skill_overlap * 100, 1)}%
Experience (years, extracted): {req.experience_years}
Education level: {EDUCATION_LABELS.get(req.education_level, "Unknown")}
Matched skills: {', '.join(req.matched_skills) or 'none'}
Missing skills (present in JD, not found in resume): {', '.join(req.missing_skills) or 'none'}

Respond with exactly 3 bullet points, no preamble.
"""
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Empty response from Gemini")
        return {"note": text, "source": "gemini-2.5-flash"}
    except Exception:
        # Any failure (no network, bad key, quota, SDK error) -> graceful fallback
        return {"note": _rule_based_note(req), "source": "rule_based_fallback"}
