import type { Candidate } from "./types";

export function buildCsv(candidates: Candidate[]): string {
  const headers = [
    "filename",
    "overall_score",
    "similarity",
    "skill_overlap",
    "experience_years",
    "experience_fit",
    "education_level",
    "education_fit",
    "matched_skills",
    "missing_skills",
  ];

  const escape = (val: string) => `"${val.replace(/"/g, '""')}"`;

  const rows = candidates.map((c) =>
    [
      escape(c.filename),
      c.overall_score,
      c.similarity,
      c.skill_overlap,
      c.experience_years,
      c.experience_fit,
      c.education_level,
      c.education_fit,
      escape(c.matched_skills.join("; ")),
      escape(c.missing_skills.join("; ")),
    ].join(","),
  );

  return [headers.join(","), ...rows].join("\n");
}

export function downloadCsv(csv: string, filename: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
