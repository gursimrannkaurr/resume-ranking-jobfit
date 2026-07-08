# Glossary

Plain-language definitions of terms used throughout this project.

**TF-IDF (Term Frequency – Inverse Document Frequency)**
A way of scoring how important a word is to a document within a collection of
documents. A word that appears often in one resume but rarely across all the other
resumes/JD gets a high score for that resume — it's a distinctive term. A word that
appears in almost every document (like "the" or "experience") gets a low score
because it doesn't help distinguish one document from another. We use this to turn
each resume and the JD into a vector of "how distinctive is each word here."

**Cosine Similarity**
A way of measuring how similar two vectors are, based on the angle between them,
ignoring their length/magnitude. In this project, once the JD and a resume are each
turned into a TF-IDF vector, cosine similarity gives a score from 0 (completely
different word usage) to 1 (identical word usage pattern) — used as our text
"relevance" signal.

**Entity Extraction**
The process of pulling specific, structured pieces of information out of unstructured
text. Here, "entities" are things like a list of skills, a total number of years of
experience, and an education level — extracted from the raw resume text using
pattern matching (regex and keyword rules), not a general-purpose AI model.

**Weighted Scoring**
Combining several separate scores (similarity, skill overlap, experience fit,
education fit) into one overall number by multiplying each by an "importance" weight
and adding them up. If similarity has a higher weight than education, then similarity
moves the final score more. Weights are configurable per request (see the sliders in
the UI) rather than fixed.

**False Positive (in skill matching)**
A skill the system says a candidate has, but they don't actually have it (or the
match is misleading). Example: matching the skill "R" because the word "regarding"
happens to contain the letter R — this is why we use word-boundary-aware regex
rather than naive substring search. Another example: a resume that lists a skill in
a "skills I want to learn" section still gets matched as if the candidate already has
it, since we don't distinguish context.

**False Negative (in skill matching)**
A skill the candidate actually has, but the system fails to detect it. Example: a
resume says "JS" but the taxonomy only has the entry "JavaScript" — no match occurs
because we require the literal string (or a listed alias) to appear. This is the
main known limitation of substring-based matching versus a more sophisticated
synonym-aware or embedding-based approach (see `docs/DATA.md`).

**Skill Overlap Ratio**
`(number of JD-required skills also found in the resume) / (total number of
JD-required skills found)`. A value from 0 to 1 representing what fraction of the
skills the JD asks for are actually present in the candidate's resume, based on
taxonomy matching against both documents.

**Experience Fit**
How close a candidate's extracted total years of experience is to the role's
required years, scaled linearly from 0 (no experience) to 1 (meets or exceeds the
requirement).

**Education Fit**
How a candidate's detected education level (None/Diploma/Bachelor's/Master's/PhD)
compares to the role's required level, scaled to 1.0 if it meets or exceeds the
requirement, and reduced proportionally for each level below it.

**Overall / Fit Score**
The final 0-100 number shown per candidate, computed as a weighted combination of
similarity, skill overlap, experience fit, and education fit (see
`docs/ARCHITECTURE.md` for the exact formula and a worked example).
