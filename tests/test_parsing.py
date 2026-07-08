from datetime import datetime

import pytest

from api.parsing import (
    extract_education_level,
    extract_experience_years,
    extract_skills,
    extract_text_from_bytes,
    load_skills_taxonomy,
    normalize_text,
)


@pytest.fixture(scope="module")
def taxonomy():
    return load_skills_taxonomy()


# --- extract_text_from_bytes -------------------------------------------------

def test_extract_text_from_txt_bytes():
    content = "Hello resume world".encode("utf-8")
    text = extract_text_from_bytes("resume.txt", content)
    assert text == "Hello resume world"


def test_extract_text_unsupported_extension():
    with pytest.raises(ValueError):
        extract_text_from_bytes("resume.xyz", b"data")


def test_normalize_text_collapses_whitespace():
    text = normalize_text("Hello   world \r\n\r\n  test")
    assert "Hello world" in text


# --- extract_skills -----------------------------------------------------------

def test_extract_skills_basic_match(taxonomy):
    text = "Experienced with Python, SQL, and AWS. Strong communication skills."
    result = extract_skills(text, taxonomy)
    assert "Python" in result["all"]
    assert "SQL" in result["all"]
    assert "AWS" in result["all"]
    assert "Communication" in result["all"]


def test_extract_skills_case_insensitive(taxonomy):
    text = "proficient in python and REACT"
    result = extract_skills(text, taxonomy)
    assert "Python" in result["all"]
    assert "React" in result["all"]


def test_extract_skills_no_false_word_fragment_match(taxonomy):
    # "R" should not match inside "Regarding" or similar longer words
    text = "Regarding the project timeline, updates will follow."
    result = extract_skills(text, taxonomy)
    assert "R" not in result["all"]


def test_extract_skills_symbol_skill_matches(taxonomy):
    text = "Built systems in C++ and C# over the last 5 years."
    result = extract_skills(text, taxonomy)
    assert "C++" in result["all"]
    assert "C#" in result["all"]


def test_extract_skills_empty_text_returns_empty(taxonomy):
    result = extract_skills("", taxonomy)
    assert result["all"] == []


# --- extract_experience_years -------------------------------------------------

def test_experience_month_year_present():
    text = "Software Engineer, Acme Corp — Jan 2020 - Present"
    years = extract_experience_years(text, today=datetime(2026, 1, 1))
    assert 5.9 <= years <= 6.1


def test_experience_year_range():
    text = "Data Analyst at Foo Inc, 2019-2022"
    years = extract_experience_years(text)
    assert 2.9 <= years <= 3.1


def test_experience_slash_date_format():
    text = "Backend Developer, 03/2020 to 11/2021"
    years = extract_experience_years(text)
    assert 1.5 <= years <= 1.8


def test_experience_multiple_ranges_sum():
    text = (
        "Experience:\n"
        "Senior Engineer, Jan 2021 - Present\n"
        "Junior Engineer, Jan 2018 - Dec 2020\n"
    )
    years = extract_experience_years(text, today=datetime(2022, 1, 1))
    # (2022-2021)=1 year + (2020-2018)=~3 years = ~4 years
    assert years >= 3.5


def test_experience_no_dates_returns_zero():
    text = "A resume with no discernible date ranges at all."
    years = extract_experience_years(text)
    assert years == 0.0


def test_experience_current_keyword():
    text = "Product Manager, Mar 2022 - Current"
    years = extract_experience_years(text, today=datetime(2024, 3, 1))
    assert 1.9 <= years <= 2.1


# --- extract_education_level ---------------------------------------------------

def test_education_phd_detected():
    text = "PhD in Computer Science, Stanford University"
    assert extract_education_level(text) == 4


def test_education_masters_detected():
    text = "Master of Science in Data Science, MIT"
    assert extract_education_level(text) == 3


def test_education_bachelors_detected():
    text = "Bachelor of Technology in Computer Engineering"
    assert extract_education_level(text) == 2


def test_education_diploma_detected():
    text = "Diploma in Information Technology"
    assert extract_education_level(text) == 1


def test_education_none_detected():
    text = "Worked at various companies over the years with no formal degree listed."
    assert extract_education_level(text) == 0


def test_education_picks_highest_level():
    text = "Bachelor of Arts in Economics; later completed a PhD in Statistics."
    assert extract_education_level(text) == 4
