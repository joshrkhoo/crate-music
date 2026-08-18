type SimilarityBarProps = {
  value: number;
  className?: string;
  showPercent?: boolean;
};

export function SimilarityBar({
  value,
  className = "",
  showPercent = true,
}: SimilarityBarProps) {
  const percent = Math.round(Math.min(Math.max(value, 0), 1) * 100);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className="h-1 min-w-0 flex-1 overflow-hidden rounded-full bg-neutral-800"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full bg-accent transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
      {showPercent ? (
        <span className="w-8 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
          {percent}%
        </span>
      ) : null}
    </div>
  );
}
