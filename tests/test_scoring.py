import pytest

from api.parsing import load_skills_taxonomy
from api.scoring import (
    compute_education_fit,
    compute_experience_fit,
    compute_skill_overlap,
    compute_tfidf_similarity,
    compute_weighted_score,
    score_candidate,
)


@pytest.fixture(scope="module")
def taxonomy():
    return load_skills_taxonomy()


# --- compute_tfidf_similarity ---------------------------------------------------

def test_tfidf_similarity_identical_text_is_high():
    jd = "Looking for a Python developer with strong SQL and AWS experience."
    resumes = [jd]
    sims = compute_tfidf_similarity(jd, resumes)
    assert len(sims) == 1
    assert sims[0] > 0.9


def test_tfidf_similarity_unrelated_text_is_low():
    jd = "Looking for a Python backend developer with AWS and Docker experience."
    resumes = ["Professional chef with 10 years of experience in French cuisine and baking."]
    sims = compute_tfidf_similarity(jd, resumes)
    assert sims[0] < 0.3


def test_tfidf_similarity_ranks_more_relevant_higher():
    jd = "Seeking a data analyst skilled in SQL, Excel, and Tableau for reporting."
    relevant = "Data analyst experienced in SQL, Excel dashboards, and Tableau reporting."
    irrelevant = "Chef specializing in pastry and dessert preparation."
    sims = compute_tfidf_similarity(jd, [relevant, irrelevant])
    assert sims[0] > sims[1]


def test_tfidf_similarity_empty_resume_list():
    assert compute_tfidf_similarity("some jd text", []) == []


def test_tfidf_similarity_bounds():
    jd = "Python engineer"
    resumes = ["Python engineer", "completely different content about gardening"]
    sims = compute_tfidf_similarity(jd, resumes)
    for s in sims:
        assert 0.0 <= s <= 1.0


# --- compute_skill_overlap -------------------------------------------------------

def test_skill_overlap_full_match(taxonomy):
    jd = "Required skills: Python, SQL, AWS"
    resume = "Skills: Python, SQL, AWS, Docker"
    result = compute_skill_overlap(jd, resume, taxonomy)
    assert result["ratio"] == 1.0
    assert set(result["matched_skills"]) == {"Python", "SQL", "AWS"}
    assert result["missing_skills"] == []


def test_skill_overlap_partial_match(taxonomy):
    jd = "Required skills: Python, SQL, AWS, Docker"
    resume = "Skills: Python, SQL"
    result = compute_skill_overlap(jd, resume, taxonomy)
    assert result["ratio"] == 0.5
    assert "Docker" in result["missing_skills"]
    assert "AWS" in result["missing_skills"]


def test_skill_overlap_no_jd_skills(taxonomy):
    jd = "We want someone great and hardworking with a positive attitude only."
    resume = "Skills: Python, SQL"
    result = compute_skill_overlap(jd, resume, taxonomy)
    assert result["ratio"] == 0.0
    assert result["jd_skills"] == []


# --- compute_experience_fit -------------------------------------------------------

def test_experience_fit_meets_requirement():
    assert compute_experience_fit(5, required_years=3) == 1.0


def test_experience_fit_below_requirement():
    fit = compute_experience_fit(1.5, required_years=3)
    assert 0.4 <= fit <= 0.6


def test_experience_fit_zero_years():
    assert compute_experience_fit(0, required_years=3) == 0.0


def test_experience_fit_zero_required_years():
    assert compute_experience_fit(0, required_years=0) == 1.0


# --- compute_education_fit ---------------------------------------------------------

def test_education_fit_meets_requirement():
    assert compute_education_fit(2, required_level=2) == 1.0


def test_education_fit_exceeds_requirement():
    assert compute_education_fit(4, required_level=2) == 1.0


def test_education_fit_below_requirement():
    fit = compute_education_fit(0, required_level=2)
    assert fit < 1.0
    assert fit >= 0.0


def test_education_fit_one_level_below():
    fit = compute_education_fit(1, required_level=2)
    assert 0.6 <= fit <= 0.7


# --- compute_weighted_score --------------------------------------------------------

def test_weighted_score_all_ones_is_100():
    score = compute_weighted_score(1.0, 1.0, 1.0, 1.0)
    assert score == 100.0


def test_weighted_score_all_zeros_is_0():
    score = compute_weighted_score(0.0, 0.0, 0.0, 0.0)
    assert score == 0.0


def test_weighted_score_default_weights_worked_example():
    # similarity=0.8, skills=0.6, experience=0.5, education=1.0
    # default weights: 0.4/0.3/0.2/0.1
    # = 0.4*0.8 + 0.3*0.6 + 0.2*0.5 + 0.1*1.0
    # = 0.32 + 0.18 + 0.10 + 0.10 = 0.70 -> 70.0
    score = compute_weighted_score(0.8, 0.6, 0.5, 1.0)
    assert score == 70.0


def test_weighted_score_custom_weights():
    weights = {"similarity": 1.0, "skills": 0.0, "experience": 0.0, "education": 0.0}
    score = compute_weighted_score(0.5, 1.0, 1.0, 1.0, weights)
    assert score == 50.0


def test_weighted_score_normalizes_when_weights_dont_sum_to_1():
    # weights sum to 2.0 -> should still normalize correctly
    weights = {"similarity": 2.0, "skills": 0.0, "experience": 0.0, "education": 0.0}
    score = compute_weighted_score(0.5, 0.0, 0.0, 0.0, weights)
    assert score == 50.0


def test_weighted_score_bounds():
    score = compute_weighted_score(1.0, 1.0, 1.0, 1.0)
    assert 0.0 <= score <= 100.0


# --- score_candidate (integration of the pipeline) ----------------------------------

def test_score_candidate_end_to_end(taxonomy):
    jd = (
        "We are hiring a Data Analyst with 3+ years of experience. "
        "Required skills: Python, SQL, Tableau, Excel. "
        "Bachelor's degree required."
    )
    resume = (
        "Data Analyst with experience: Jan 2020 - Present. "
        "Skills: Python, SQL, Tableau. "
        "Education: Bachelor of Science in Statistics."
    )
    sim = compute_tfidf_similarity(jd, [resume])[0]
    result = score_candidate(jd, resume, sim, taxonomy=taxonomy)

    assert 0 <= result["overall_score"] <= 100
    assert result["skill_overlap"] > 0
    assert "Python" in result["matched_skills"]
    assert "Excel" in result["missing_skills"]
    assert result["experience_years"] > 5
    assert result["education_level"] == 2
