"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

const MAX_FILES = 15;

export function UploadPanel({
  jdText,
  setJdText,
  jdFile,
  setJdFile,
  resumeFiles,
  setResumeFiles,
  onRank,
  isLoading,
  error,
}: {
  jdText: string;
  setJdText: (v: string) => void;
  jdFile: File | null;
  setJdFile: (f: File | null) => void;
  resumeFiles: File[];
  setResumeFiles: (f: File[]) => void;
  onRank: () => void;
  isLoading: boolean;
  error: string | null;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jdFileInputRef = useRef<HTMLInputElement>(null);

  function addFiles(files: FileList | File[]) {
    const incoming = Array.from(files);
    const combined = [...resumeFiles, ...incoming].slice(0, MAX_FILES);
    setResumeFiles(combined);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) {
      addFiles(e.dataTransfer.files);
    }
  }

  function removeFile(idx: number) {
    setResumeFiles(resumeFiles.filter((_, i) => i !== idx));
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Job Description</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            placeholder="Paste the job description here..."
            className="min-h-[200px]"
            value={jdText}
            onChange={(e) => {
              setJdText(e.target.value);
              if (jdFile) setJdFile(null);
            }}
          />
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => jdFileInputRef.current?.click()}
            >
              Upload JD file
            </Button>
            <input
              ref={jdFileInputRef}
              type="file"
              accept=".txt,.pdf,.docx"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) {
                  setJdFile(f);
                  setJdText("");
                }
              }}
            />
            {jdFile && (
              <span className="text-sm text-muted-foreground">
                {jdFile.name}{" "}
                <button
                  className="text-red-500 underline"
                  onClick={() => setJdFile(null)}
                  type="button"
                >
                  remove
                </button>
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resumes ({resumeFiles.length}/{MAX_FILES})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex min-h-[140px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center text-sm transition-colors ${
              isDragging
                ? "border-blue-500 bg-blue-50"
                : "border-muted-foreground/30 hover:border-muted-foreground/60"
            }`}
          >
            <p className="font-medium">Drag and drop resumes here</p>
            <p className="text-muted-foreground">or click to browse (.txt, .pdf, .docx) — max {MAX_FILES} files</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".txt,.pdf,.docx"
            className="hidden"
            onChange={(e) => {
              if (e.target.files) addFiles(e.target.files);
              e.target.value = "";
            }}
          />

          {resumeFiles.length > 0 && (
            <ul className="max-h-40 space-y-1 overflow-y-auto text-sm">
              {resumeFiles.map((f, i) => (
                <li
                  key={`${f.name}-${i}`}
                  className="flex items-center justify-between rounded bg-muted px-2 py-1"
                >
                  <span className="truncate">{f.name}</span>
                  <button
                    type="button"
                    className="ml-2 text-red-500"
                    onClick={() => removeFile(i)}
                  >
                    &times;
                  </button>
                </li>
              ))}
            </ul>
          )}

          <Button
            className="w-full"
            onClick={onRank}
            disabled={isLoading || resumeFiles.length === 0 || (!jdText.trim() && !jdFile)}
          >
            {isLoading ? "Ranking..." : "Rank Candidates"}
          </Button>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
