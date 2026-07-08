"use client";

import { Button } from "@/components/ui/button";

const JD_OPTIONS = [
  { label: "Data Analyst JD", path: "/sample-data/jds/data_analyst.txt" },
  { label: "Backend Engineer JD", path: "/sample-data/jds/backend_engineer.txt" },
];

const RESUME_SET = [
  "/sample-data/resumes/priya_sharma_data_analyst_senior.txt",
  "/sample-data/resumes/daniel_osei_data_analyst_junior.txt",
  "/sample-data/resumes/maria_gonzalez_data_analyst_mid.txt",
  "/sample-data/resumes/james_okafor_backend_senior.txt",
  "/sample-data/resumes/lena_kowalski_backend_mid.txt",
  "/sample-data/resumes/tom_becker_backend_junior.txt",
  "/sample-data/resumes/aisha_rahman_ml_engineer.txt",
  "/sample-data/resumes/carlos_mendez_sales_weak_fit.txt",
  "/sample-data/resumes/sophia_lindqvist_data_engineer.txt",
];

async function fetchAsFile(path: string): Promise<File> {
  const res = await fetch(path);
  const blob = await res.blob();
  const name = path.split("/").pop() || "file.txt";
  return new File([blob], name, { type: "text/plain" });
}

export function DemoDataButtons({
  onLoadJd,
  onLoadResumes,
}: {
  onLoadJd: (text: string) => void;
  onLoadResumes: (files: File[]) => void;
}) {
  async function loadJd(path: string) {
    const res = await fetch(path);
    const text = await res.text();
    onLoadJd(text);
  }

  async function loadResumes() {
    const files = await Promise.all(RESUME_SET.map(fetchAsFile));
    onLoadResumes(files);
  }

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/30 p-3 text-sm">
      <span className="font-medium">One-click demo data:</span>
      {JD_OPTIONS.map((opt) => (
        <Button
          key={opt.path}
          variant="outline"
          size="sm"
          onClick={() => loadJd(opt.path)}
        >
          {opt.label}
        </Button>
      ))}
      <Button variant="outline" size="sm" onClick={loadResumes}>
        Load Sample Resumes (9)
      </Button>
    </div>
  );
}
