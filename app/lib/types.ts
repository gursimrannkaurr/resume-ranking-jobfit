export interface Candidate {
  filename: string;
  overall_score: number;
  similarity: number;
  skill_overlap: number;
  experience_years: number;
  experience_fit: number;
  education_level: number;
  education_fit: number;
  matched_skills: string[];
  missing_skills: string[];
}

export interface RankResponse {
  candidates: Candidate[];
  weights: Weights;
}

export interface Weights {
  similarity: number;
  skills: number;
  experience: number;
  education: number;
}

export interface RerankResponseItem {
  filename: string;
  overall_score: number;
}

export interface RerankResponse {
  candidates: RerankResponseItem[];
  weights: Weights;
}

export interface ExplainResponse {
  note: string;
  source: string;
}

export const EDUCATION_LABELS: Record<number, string> = {
  0: "None listed",
  1: "Diploma/Associate",
  2: "Bachelor's",
  3: "Master's",
  4: "PhD",
};
