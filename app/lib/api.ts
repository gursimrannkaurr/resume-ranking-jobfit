import type {
  Candidate,
  ExplainResponse,
  RankResponse,
  RerankResponse,
  Weights,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function rankCandidates(params: {
  jdText: string;
  jdFile: File | null;
  resumeFiles: File[];
  weights: Weights;
}): Promise<RankResponse> {
  const form = new FormData();
  if (params.jdFile) {
    form.append("jd_file", params.jdFile);
  } else {
    form.append("jd_text", params.jdText);
  }
  form.append("weight_similarity", String(params.weights.similarity));
  form.append("weight_skills", String(params.weights.skills));
  form.append("weight_experience", String(params.weights.experience));
  form.append("weight_education", String(params.weights.education));
  for (const f of params.resumeFiles) {
    form.append("resumes", f);
  }

  const res = await fetch(`${API_BASE_URL}/api/rank`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || "Failed to rank candidates");
  }

  return res.json();
}

export async function rerankCandidates(
  candidates: Candidate[],
  weights: Weights,
): Promise<RerankResponse> {
  const res = await fetch(`${API_BASE_URL}/api/rerank`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidates: candidates.map((c) => ({
        filename: c.filename,
        similarity: c.similarity,
        skill_overlap: c.skill_overlap,
        experience_fit: c.experience_fit,
        education_fit: c.education_fit,
      })),
      weight_similarity: weights.similarity,
      weight_skills: weights.skills,
      weight_experience: weights.experience,
      weight_education: weights.education,
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || "Failed to rerank candidates");
  }

  return res.json();
}

export async function explainCandidate(
  candidate: Candidate,
  jdText: string,
): Promise<ExplainResponse> {
  const res = await fetch(`${API_BASE_URL}/api/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      filename: candidate.filename,
      jd_text: jdText,
      overall_score: candidate.overall_score,
      similarity: candidate.similarity,
      skill_overlap: candidate.skill_overlap,
      experience_years: candidate.experience_years,
      education_level: candidate.education_level,
      matched_skills: candidate.matched_skills,
      missing_skills: candidate.missing_skills,
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || "Failed to get AI note");
  }

  return res.json();
}
