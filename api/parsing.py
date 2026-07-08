"""
Text extraction and entity parsing for resumes.

Pure, testable functions:
- extract_text_from_bytes(): .txt / .pdf / .docx -> plain text
- extract_skills(): match against skills taxonomy
- extract_experience_years(): regex over date ranges, sum durations
- extract_education_level(): keyword rules -> level 0-4
"""
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

TAXONOMY_PATH = Path(__file__).parent / "skills_taxonomy.json"

TODAY = datetime(2026, 7, 9)

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

EDUCATION_LEVELS = {
    4: [
        "phd", "ph.d", "doctorate", "doctoral", "d.phil",
    ],
    3: [
        "master", "masters", "m.s.", "msc", "m.sc", "mba", "m.tech", "mtech",
        "m.eng", "meng", "postgraduate", "post-graduate", "pg diploma",
    ],
    2: [
        "bachelor", "bachelors", "b.s.", "bsc", "b.sc", "b.tech", "btech",
        "b.e.", "be.", "undergraduate", "b.a.", "ba ", "bba",
    ],
    1: [
        "diploma", "associate degree", "a.a.", "a.s.", "associate's degree",
    ],
}


def load_skills_taxonomy(path: Optional[Path] = None) -> dict:
    p = path or TAXONOMY_PATH
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _flatten_skills(taxonomy: dict) -> list:
    seen = []
    for category, skills in taxonomy.items():
        for s in skills:
            seen.append(s)
    return seen


def extract_text_from_bytes(filename: str, content: bytes) -> str:
    """Extract plain text from .txt, .pdf, or .docx file bytes."""
    ext = Path(filename).suffix.lower()

    if ext == ".txt" or ext == "":
        for encoding in ("utf-8", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError("pypdf is required to parse PDF files")
        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)

    if ext == ".docx":
        try:
            import docx
        except ImportError:
            raise RuntimeError("python-docx is required to parse .docx files")
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError(f"Unsupported file type: {ext}")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_skills(text: str, taxonomy: Optional[dict] = None) -> dict:
    """
    Case-insensitive word-boundary / substring matching of skills taxonomy
    against resume text. Returns dict category -> list of matched skill names,
    plus a flat 'all' list.
    """
    if taxonomy is None:
        taxonomy = load_skills_taxonomy()

    text_lower = text.lower()
    matched_by_category = {}
    all_matched = []

    for category, skills in taxonomy.items():
        matched = []
        for skill in skills:
            skill_lower = skill.lower().strip()
            if not skill_lower:
                continue
            # Build a tolerant pattern: escape special chars, but allow
            # matching as a whole word/phrase (handles "C++", "C#", ".NET" etc)
            pattern = re.escape(skill_lower)
            # Use boundary lookarounds that work even for punctuation-heavy skills
            regex = r"(?<![a-z0-9])" + pattern + r"(?![a-z0-9])"
            if re.search(regex, text_lower):
                matched.append(skill)
        if matched:
            matched_by_category[category] = matched
            all_matched.extend(matched)

    return {"by_category": matched_by_category, "all": sorted(set(all_matched))}


_DATE_RANGE_PATTERNS = [
    # "Jan 2020 - Present", "January 2020 to Present"
    re.compile(
        r"(?P<m1>[A-Za-z]{3,9})\.?\s+(?P<y1>\d{4})\s*(?:-|–|—|to)\s*"
        r"(?P<end>present|current|now|[A-Za-z]{3,9}\.?\s+\d{4})",
        re.IGNORECASE,
    ),
    # "03/2020 to 11/2021", "03/2020 - Present"
    re.compile(
        r"(?P<mo1>\d{1,2})/(?P<y1>\d{4})\s*(?:-|–|—|to)\s*"
        r"(?P<end>present|current|now|\d{1,2}/\d{4})",
        re.IGNORECASE,
    ),
    # "2019-2022", "2019 - 2022", "2019 to Present"
    re.compile(
        r"(?<!\d)(?P<y1>(19|20)\d{2})\s*(?:-|–|—|to)\s*"
        r"(?P<end>present|current|now|(19|20)\d{2})(?!\d)",
        re.IGNORECASE,
    ),
]


def _parse_month_year(month_str: str, year_str: str) -> datetime:
    month_key = month_str.lower().strip(".")
    month_num = MONTHS.get(month_key, 1)
    return datetime(int(year_str), month_num, 1)


def extract_experience_years(text: str, today: Optional[datetime] = None) -> float:
    """
    Regex-extract date ranges (various formats) from resume text and sum
    the durations (in years), handling 'Present'/'Current' as today's date.
    Overlapping ranges are naively summed (kept simple/explainable).
    """
    today = today or TODAY
    total_days = 0.0
    matched_spans = []

    def overlaps(span):
        return any(not (span[1] <= s[0] or span[0] >= s[1]) for s in matched_spans)

    # Pattern 1: Month Year - Month Year / Present
    for m in _DATE_RANGE_PATTERNS[0].finditer(text):
        span = m.span()
        if overlaps(span):
            continue
        try:
            start = _parse_month_year(m.group("m1"), m.group("y1"))
        except (ValueError, KeyError):
            continue
        end_str = m.group("end").lower()
        if end_str in ("present", "current", "now"):
            end = today
        else:
            em = re.match(r"([A-Za-z]{3,9})\.?\s+(\d{4})", m.group("end"), re.IGNORECASE)
            if not em:
                continue
            try:
                end = _parse_month_year(em.group(1), em.group(2))
            except (ValueError, KeyError):
                continue
        if end > start:
            total_days += (end - start).days
            matched_spans.append(span)

    # Pattern 2: MM/YYYY - MM/YYYY / Present
    for m in _DATE_RANGE_PATTERNS[1].finditer(text):
        span = m.span()
        if overlaps(span):
            continue
        try:
            start = datetime(int(m.group("y1")), int(m.group("mo1")), 1)
        except ValueError:
            continue
        end_str = m.group("end").lower()
        if end_str in ("present", "current", "now"):
            end = today
        else:
            em = re.match(r"(\d{1,2})/(\d{4})", m.group("end"))
            if not em:
                continue
            try:
                end = datetime(int(em.group(2)), int(em.group(1)), 1)
            except ValueError:
                continue
        if end > start:
            total_days += (end - start).days
            matched_spans.append(span)

    # Pattern 3: YYYY - YYYY / Present
    for m in _DATE_RANGE_PATTERNS[2].finditer(text):
        span = m.span()
        if overlaps(span):
            continue
        try:
            start = datetime(int(m.group("y1")), 1, 1)
        except ValueError:
            continue
        end_str = m.group("end").lower()
        if end_str in ("present", "current", "now"):
            end = today
        else:
            try:
                end = datetime(int(end_str), 1, 1)
            except ValueError:
                continue
        if end > start:
            total_days += (end - start).days
            matched_spans.append(span)

    years = round(total_days / 365.25, 2)
    return max(years, 0.0)


def extract_education_level(text: str) -> int:
    """
    Keyword-rule based education level detection.
    Returns highest level found: PhD=4, Masters=3, Bachelors=2, Diploma/Assoc=1, None=0
    """
    text_lower = text.lower()
    for level in (4, 3, 2, 1):
        for keyword in EDUCATION_LEVELS[level]:
            if keyword in text_lower:
                return level
    return 0
