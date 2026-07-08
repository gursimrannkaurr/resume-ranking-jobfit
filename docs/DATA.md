# Data

## Sample Resumes (`data/sample_resumes/`)

9 synthetic, clearly fictional resumes as plain `.txt` files, designed to exercise a
range of scoring scenarios:

| File | Persona | Seniority | Domain | Purpose |
|---|---|---|---|---|
| `priya_sharma_data_analyst_senior.txt` | Priya Sharma | Senior (6+ yrs) | Data Analyst | Strong fit for Data Analyst JD |
| `maria_gonzalez_data_analyst_mid.txt` | Maria Gonzalez | Mid (3.5 yrs) | Data Analyst | Good fit, mid-level |
| `daniel_osei_data_analyst_junior.txt` | Daniel Osei | Junior (1.5 yrs) | Data Analyst | Below required experience |
| `james_okafor_backend_senior.txt` | James Okafor | Senior (7 yrs) | Backend Engineer | Strong fit for Backend JD |
| `lena_kowalski_backend_mid.txt` | Lena Kowalski | Mid (4 yrs) | Backend Engineer | Good fit, mid-level |
| `tom_becker_backend_junior.txt` | Tom Becker | Junior (1 yr), bootcamp grad | Backend Engineer | Below required experience/education |
| `aisha_rahman_ml_engineer.txt` | Aisha Rahman | Senior (5 yrs) | ML Engineer | Adjacent domain — partial skill overlap with both JDs |
| `sophia_lindqvist_data_engineer.txt` | Sophia Lindqvist | Mid (4.5 yrs) | Data Engineer | Adjacent domain — partial overlap with Data Analyst JD |
| `carlos_mendez_sales_weak_fit.txt` | Carlos Mendez | Senior (6 yrs) | Sales / Account Management | Deliberately weak fit for both JDs — validates low-score behavior |

Each resume has a realistic structure: name/contact header, summary, work experience
with explicit date ranges (varying formats: `Jan 2020 - Present`, `2019 - 2022`, etc.),
a skills section, and an education line. All names, emails, and companies are
fictional/synthetic — no real people or organizations.

## Sample Job Descriptions (`data/sample_jds/`)

- `data_analyst.txt` — Data Analyst role requiring SQL, Excel, Tableau/Power BI,
  Python/R, 3+ years experience, Bachelor's degree.
- `backend_engineer.txt` — Backend Engineer role requiring Python/Node.js, Docker,
  Kubernetes, AWS, PostgreSQL, 3+ years experience, Bachelor's degree.

## Skills Taxonomy (`api/skills_taxonomy.json`)

A flat JSON object mapping **category name → array of skill strings**, containing
277 skills across 14 categories:

```
programming_languages, web_frontend, web_backend, data_ml, data_engineering,
bi_analytics, cloud_devops, tools_platforms, testing_qa, security,
project_management, soft_skills, mobile, other_technical
```

Matching is **case-insensitive substring/word-boundary matching** — each skill
string is escaped and wrapped in negative lookaround assertions (`(?<![a-z0-9])` /
`(?![a-z0-9])`) so that, e.g., `"R"` does not spuriously match inside `"Regarding"`,
while still correctly matching punctuation-bearing skills like `"C++"`, `"C#"`.

This is a **deliberately simple, explainable** approach — no ML-based Named Entity
Recognition — so that every matched/missing skill in the UI can be traced back to an
exact string match in the resume text. See `memory/DECISIONS.md` for the full
rationale.

### Real deployment considerations

The taxonomy here (277 skills, hand-curated) is a reasonable demo/MVP starting point,
but a production deployment would need:

- A much larger, continuously-maintained skill list (thousands of entries), ideally
  sourced from a labor-market taxonomy (e.g., ESCO, O*NET, LinkedIn Skills Graph) and
  reviewed by domain experts/recruiters for the target industries.
- Synonym/alias handling (e.g., "JS" vs "JavaScript", "ML" vs "Machine Learning") —
  currently each alias would need to be a separate taxonomy entry.
- Regular human review of false positives/negatives as new resumes are processed
  (see `memory/GLOSSARY.md` for definitions of these terms in this context).
- Possibly per-industry taxonomy variants, since a 277-skill general tech taxonomy
  will under-perform for, e.g., healthcare or legal resumes.
