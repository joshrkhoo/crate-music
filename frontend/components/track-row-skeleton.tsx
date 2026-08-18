type TrackRowSkeletonProps = {
  showSimilarity?: boolean;
};

export function TrackRowSkeleton({ showSimilarity = false }: TrackRowSkeletonProps) {
  return (
    <li className="flex animate-pulse items-center gap-3 rounded-xl px-3 py-2.5">
      <div className="size-16 shrink-0 rounded-md bg-neutral-800" />
      <div className="min-w-0 flex-1 space-y-2">
        <div className="h-4 w-3/4 max-w-xs rounded bg-neutral-800" />
        <div className="h-3 w-1/2 max-w-[10rem] rounded bg-neutral-800" />
        {showSimilarity ? (
          <div className="flex items-center gap-2 pt-0.5">
            <div className="h-1.5 flex-1 rounded-full bg-neutral-800" />
            <div className="h-3 w-8 rounded bg-neutral-800" />
          </div>
        ) : null}
      </div>
    </li>
  );
}

export function TrackListSkeleton({ count = 8 }: { count?: number }) {
  return (
    <ul className="space-y-1 p-1">
      {Array.from({ length: count }, (_, index) => (
        <TrackRowSkeleton key={index} />
      ))}
    </ul>
  );
}

export function DiscoverySkeleton() {
  return (
    <div className="crate-glass animate-pulse space-y-6 rounded-2xl p-5">
      <div className="flex items-center gap-4">
        <div className="size-16 shrink-0 rounded-md bg-neutral-800" />
        <div className="flex-1 space-y-2">
          <div className="h-3 w-16 rounded bg-neutral-800" />
          <div className="h-4 w-48 max-w-full rounded bg-neutral-800" />
          <div className="h-3 w-32 rounded bg-neutral-800" />
        </div>
      </div>
      <div className="space-y-3">
        <div className="h-5 w-40 rounded bg-neutral-800" />
        <ul className="space-y-1">
          {Array.from({ length: 5 }, (_, index) => (
            <TrackRowSkeleton key={index} showSimilarity />
          ))}
        </ul>
      </div>
    </div>
  );
}
