"use client";

import { useCallback, useState } from "react";
import { UploadPanel } from "@/components/upload-panel";
import { WeightSliders } from "@/components/weight-sliders";
import { ResultsTable } from "@/components/results-table";
import { DemoDataButtons } from "@/components/demo-data";
import { rankCandidates, rerankCandidates } from "@/lib/api";
import type { Candidate, Weights } from "@/lib/types";

const DEFAULT_WEIGHTS: Weights = {
  similarity: 0.4,
  skills: 0.3,
  experience: 0.2,
  education: 0.1,
};

export default function Home() {
  const [jdText, setJdText] = useState("");
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRank = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await rankCandidates({ jdText, jdFile, resumeFiles, weights });
      setCandidates(res.candidates);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  }, [jdText, jdFile, resumeFiles, weights]);

  const handleWeightsChange = useCallback(
    async (newWeights: Weights) => {
      setWeights(newWeights);
      if (candidates.length === 0) return;
      try {
        const res = await rerankCandidates(candidates, newWeights);
        const scoreMap = new Map(res.candidates.map((c) => [c.filename, c.overall_score]));
        setCandidates((prev) =>
          prev.map((c) => ({
            ...c,
            overall_score: scoreMap.get(c.filename) ?? c.overall_score,
          })),
        );
      } catch {
        // Rerank failures are non-fatal; keep prior scores displayed.
      }
    },
    [candidates],
  );

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b bg-white">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <h1 className="text-2xl font-bold">Resume Ranking &amp; Job-Fit Scoring Tool</h1>
          <p className="mt-1 text-muted-foreground">
            Upload a job description and a batch of resumes to get a ranked, explainable
            shortlist using TF-IDF similarity + extracted skills, experience, and education.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">
        <DemoDataButtons
          onLoadJd={(text) => {
            setJdText(text);
            setJdFile(null);
          }}
          onLoadResumes={(files) => setResumeFiles(files)}
        />

        <UploadPanel
          jdText={jdText}
          setJdText={setJdText}
          jdFile={jdFile}
          setJdFile={setJdFile}
          resumeFiles={resumeFiles}
          setResumeFiles={setResumeFiles}
          onRank={handleRank}
          isLoading={isLoading}
          error={error}
        />

        <WeightSliders weights={weights} onChange={handleWeightsChange} />

        {candidates.length > 0 && (
          <ResultsTable candidates={candidates} jdText={jdText} />
        )}
      </main>

      <footer className="border-t bg-white py-6 text-center text-sm text-muted-foreground">
        Backend API: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
      </footer>
    </div>
  );
}
