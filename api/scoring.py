"""
Scoring engine: TF-IDF + cosine similarity, skill overlap, experience fit,
education fit, and the combined weighted score.

All functions are pure and independently testable.
"""
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from api.parsing import (
    extract_education_level,
    extract_experience_years,
    extract_skills,
    load_skills_taxonomy,
)

DEFAULT_WEIGHTS = {
    "similarity": 0.4,
    "skills": 0.3,
    "experience": 0.2,
    "education": 0.1,
}

# Experience is considered a "full fit" (1.0) once the candidate meets or
# exceeds the JD's required years; below that it scales linearly.
DEFAULT_REQUIRED_EXPERIENCE_YEARS = 3.0

# Education fit: JD's required level vs candidate's level. Meeting or
# exceeding required level = 1.0; below scales down per missing level.
DEFAULT_REQUIRED_EDUCATION_LEVEL = 2  # Bachelors


def compute_tfidf_similarity(jd_text: str, resume_texts: list) -> list:
    """
    Fit a TF-IDF vectorizer jointly on [jd_text, *resume_texts] and return
    cosine similarity of each resume vector to the JD vector, in [0, 1].
    """
    if not resume_texts:
        return []

    corpus = [jd_text] + resume_texts
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Empty vocabulary (e.g. all-stopword or empty text)
        return [0.0 for _ in resume_texts]

    jd_vector = tfidf_matrix[0:1]
    resume_vectors = tfidf_matrix[1:]
    sims = cosine_similarity(jd_vector, resume_vectors)[0]
    return [float(max(0.0, min(1.0, s))) for s in sims]


def compute_skill_overlap(
    jd_text: str, resume_text: str, taxonomy: Optional[dict] = None
) -> dict:
    """
    Extract required skills from the JD and candidate skills from the resume
    (both via taxonomy matching), and compute an overlap ratio.
    """
    if taxonomy is None:
        taxonomy = load_skills_taxonomy()

    jd_skills = set(extract_skills(jd_text, taxonomy)["all"])
    resume_skills = set(extract_skills(resume_text, taxonomy)["all"])

    if not jd_skills:
        # No identifiable required skills in JD -> treat overlap as neutral
        return {
            "ratio": 0.0,
            "matched_skills": sorted(resume_skills),
            "missing_skills": [],
            "jd_skills": [],
        }

    matched = jd_skills & resume_skills
    missing = jd_skills - resume_skills
    ratio = len(matched) / len(jd_skills)

    return {
        "ratio": round(ratio, 4),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "jd_skills": sorted(jd_skills),
    }


def compute_experience_fit(
    experience_years: float,
    required_years: float = DEFAULT_REQUIRED_EXPERIENCE_YEARS,
) -> float:
    """
    Linear scaling: 0 years -> 0.0, meets/exceeds required -> 1.0.
    """
    if required_years <= 0:
        return 1.0
    fit = experience_years / required_years
    return round(max(0.0, min(1.0, fit)), 4)


def compute_education_fit(
    education_level: int,
    required_level: int = DEFAULT_REQUIRED_EDUCATION_LEVEL,
) -> float:
    """
    Meeting/exceeding required level -> 1.0. Each level below required
    subtracts 0.34 (roughly 1/3 per level, floored at 0).
    """
    if required_level <= 0:
        return 1.0
    if education_level >= required_level:
        return 1.0
    gap = required_level - education_level
    fit = max(0.0, 1.0 - gap * 0.34)
    return round(fit, 4)


def compute_weighted_score(
    similarity: float,
    skill_overlap: float,
    experience_fit: float,
    education_fit: float,
    weights: Optional[dict] = None,
) -> float:
    """
    score = w1*similarity + w2*skill_overlap + w3*experience_fit + w4*education_fit
    scaled to 0-100. All components must be in [0, 1].
    """
    w = weights or DEFAULT_WEIGHTS
    w_sim = w.get("similarity", DEFAULT_WEIGHTS["similarity"])
    w_skill = w.get("skills", DEFAULT_WEIGHTS["skills"])
    w_exp = w.get("experience", DEFAULT_WEIGHTS["experience"])
    w_edu = w.get("education", DEFAULT_WEIGHTS["education"])

    weight_sum = w_sim + w_skill + w_exp + w_edu
    if weight_sum <= 0:
        weight_sum = 1.0

    raw = (
        w_sim * similarity
        + w_skill * skill_overlap
        + w_exp * experience_fit
        + w_edu * education_fit
    ) / weight_sum

    score = raw * 100
    return round(max(0.0, min(100.0, score)), 2)


def score_candidate(
    jd_text: str,
    resume_text: str,
    similarity: float,
    weights: Optional[dict] = None,
    taxonomy: Optional[dict] = None,
    required_years: float = DEFAULT_REQUIRED_EXPERIENCE_YEARS,
    required_education: int = DEFAULT_REQUIRED_EDUCATION_LEVEL,
) -> dict:
    """
    Full per-candidate scoring pipeline given a precomputed similarity score
    (similarity is computed jointly across the batch via TF-IDF, so it's
    passed in rather than recomputed here).
    """
    overlap = compute_skill_overlap(jd_text, resume_text, taxonomy)
    experience_years = extract_experience_years(resume_text)
    education_level = extract_education_level(resume_text)

    experience_fit = compute_experience_fit(experience_years, required_years)
    education_fit = compute_education_fit(education_level, required_education)

    overall = compute_weighted_score(
        similarity, overlap["ratio"], experience_fit, education_fit, weights
    )

    return {
        "overall_score": overall,
        "similarity": round(similarity, 4),
        "skill_overlap": overlap["ratio"],
        "experience_years": experience_years,
        "experience_fit": experience_fit,
        "education_level": education_level,
        "education_fit": education_fit,
        "matched_skills": overlap["matched_skills"],
        "missing_skills": overlap["missing_skills"],
    }
