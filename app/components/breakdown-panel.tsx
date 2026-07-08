"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScoreBar } from "@/components/score-bar";
import { explainCandidate } from "@/lib/api";
import { EDUCATION_LABELS, type Candidate } from "@/lib/types";

export function BreakdownPanel({
  candidate,
  jdText,
}: {
  candidate: Candidate;
  jdText: string;
}) {
  const [note, setNote] = useState<string | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExplain() {
    setLoading(true);
    setError(null);
    try {
      const res = await explainCandidate(candidate, jdText);
      setNote(res.note);
      setSource(res.source);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to get AI note");
    } finally {
      setLoading(false);
    }
  }

  const components: { label: string; value: number; colorClass: string }[] = [
    { label: "Similarity", value: candidate.similarity * 100, colorClass: "bg-blue-600" },
    { label: "Skill Overlap", value: candidate.skill_overlap * 100, colorClass: "bg-emerald-600" },
    { label: "Experience Fit", value: candidate.experience_fit * 100, colorClass: "bg-amber-600" },
    { label: "Education Fit", value: candidate.education_fit * 100, colorClass: "bg-purple-600" },
  ];

  return (
    <div className="space-y-4 rounded-lg border bg-muted/30 p-4">
      <div className="grid gap-3 sm:grid-cols-2">
        {components.map((c) => (
          <div key={c.label} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>{c.label}</span>
              <span className="text-muted-foreground">{c.value.toFixed(1)}%</span>
            </div>
            <ScoreBar value={c.value} colorClass={c.colorClass} />
          </div>
        ))}
      </div>

      <div className="text-sm text-muted-foreground">
        {candidate.experience_years} years experience &middot;{" "}
        {EDUCATION_LABELS[candidate.education_level] ?? "Unknown"} education
      </div>

      <div>
        <p className="mb-1 text-sm font-medium">Matched Skills</p>
        <div className="flex flex-wrap gap-1">
          {candidate.matched_skills.length === 0 && (
            <span className="text-xs text-muted-foreground">None</span>
          )}
          {candidate.matched_skills.map((s) => (
            <Badge key={s} className="bg-green-100 text-green-800 hover:bg-green-100">
              {s}
            </Badge>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-1 text-sm font-medium">Missing Skills</p>
        <div className="flex flex-wrap gap-1">
          {candidate.missing_skills.length === 0 && (
            <span className="text-xs text-muted-foreground">None &mdash; full coverage</span>
          )}
          {candidate.missing_skills.map((s) => (
            <Badge variant="outline" key={s} className="border-red-300 text-red-700">
              {s}
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Button size="sm" variant="secondary" onClick={handleExplain} disabled={loading}>
          {loading ? "Generating..." : "Get AI Note"}
        </Button>
        {error && <p className="text-sm text-red-500">{error}</p>}
        {note && (
          <div className="rounded-md border bg-background p-3 text-sm whitespace-pre-line">
            {note}
            <p className="mt-2 text-xs text-muted-foreground">
              Source: {source === "gemini-2.5-flash" ? "Gemini 2.5 Flash" : "Rule-based (no API key set)"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
