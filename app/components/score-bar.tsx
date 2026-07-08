import { cn } from "@/lib/utils";

export function ScoreBar({
  value,
  max = 100,
  className,
  colorClass = "bg-blue-600",
}: {
  value: number;
  max?: number;
  className?: string;
  colorClass?: string;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className={cn("h-2 w-full rounded-full bg-muted overflow-hidden", className)}>
      <div
        className={cn("h-full rounded-full transition-all", colorClass)}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
