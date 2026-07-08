"use client";

import * as React from "react";
import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ScoreBar } from "@/components/score-bar";
import { BreakdownPanel } from "@/components/breakdown-panel";
import { buildCsv, downloadCsv } from "@/lib/csv";
import { EDUCATION_LABELS, type Candidate } from "@/lib/types";

type SortKey = keyof Pick<
  Candidate,
  "overall_score" | "similarity" | "skill_overlap" | "experience_years" | "education_level"
>;

export function ResultsTable({
  candidates,
  jdText,
}: {
  candidates: Candidate[];
  jdText: string;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("overall_score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [expanded, setExpanded] = useState<string | null>(null);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir(sortDir === "desc" ? "asc" : "desc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const sorted = [...candidates].sort((a, b) => {
    const diff = a[sortKey] - b[sortKey];
    return sortDir === "desc" ? -diff : diff;
  });

  const columns: { key: SortKey; label: string }[] = [
    { key: "overall_score", label: "Overall Score" },
    { key: "similarity", label: "Similarity" },
    { key: "skill_overlap", label: "Skill Overlap" },
    { key: "experience_years", label: "Experience" },
    { key: "education_level", label: "Education" },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Ranked Candidates ({candidates.length})</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={() => downloadCsv(buildCsv(sorted), "resume_ranking.csv")}
        >
          Export CSV
        </Button>
      </div>

      <div className="overflow-x-auto rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Candidate</TableHead>
              {columns.map((c) => (
                <TableHead
                  key={c.key}
                  className="cursor-pointer select-none"
                  onClick={() => toggleSort(c.key)}
                >
                  {c.label}
                  {sortKey === c.key ? (sortDir === "desc" ? " ▼" : " ▲") : ""}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((c) => (
              <React.Fragment key={c.filename}>
                <TableRow
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    setExpanded(expanded === c.filename ? null : c.filename)
                  }
                >
                  <TableCell className="font-medium">{c.filename}</TableCell>
                  <TableCell className="w-40">
                    <div className="flex items-center gap-2">
                      <span className="w-10 text-sm">{c.overall_score.toFixed(1)}</span>
                      <ScoreBar value={c.overall_score} />
                    </div>
                  </TableCell>
                  <TableCell>{(c.similarity * 100).toFixed(1)}%</TableCell>
                  <TableCell>{(c.skill_overlap * 100).toFixed(1)}%</TableCell>
                  <TableCell>{c.experience_years} yrs</TableCell>
                  <TableCell>{EDUCATION_LABELS[c.education_level] ?? "Unknown"}</TableCell>
                </TableRow>
                {expanded === c.filename && (
                  <TableRow key={`${c.filename}-detail`}>
                    <TableCell colSpan={columns.length + 1}>
                      <BreakdownPanel candidate={c} jdText={jdText} />
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
