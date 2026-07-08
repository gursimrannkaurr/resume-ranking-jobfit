"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import type { Weights } from "@/lib/types";

const LABELS: Record<keyof Weights, string> = {
  similarity: "Text Similarity",
  skills: "Skill Overlap",
  experience: "Experience Fit",
  education: "Education Fit",
};

export function WeightSliders({
  weights,
  onChange,
}: {
  weights: Weights;
  onChange: (w: Weights) => void;
}) {
  const total = weights.similarity + weights.skills + weights.experience + weights.education;

  function update(key: keyof Weights, value: number) {
    onChange({ ...weights, [key]: value });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scoring Weights</CardTitle>
        <p className="text-sm text-muted-foreground">
          Adjust component weights to re-rank candidates live. Current sum: {total.toFixed(2)}
          {" "}(weights are normalized automatically).
        </p>
      </CardHeader>
      <CardContent className="grid gap-5 sm:grid-cols-2">
        {(Object.keys(LABELS) as (keyof Weights)[]).map((key) => (
          <div key={key} className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>{LABELS[key]}</span>
              <span className="text-muted-foreground">{weights[key].toFixed(2)}</span>
            </div>
            <Slider
              value={[weights[key]]}
              min={0}
              max={1}
              step={0.05}
              onValueChange={(v: number | readonly number[]) =>
                update(key, Array.isArray(v) ? v[0] : (v as number))
              }
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
