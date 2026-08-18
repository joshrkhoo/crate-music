type AppNavProps = {
  userName?: string | null;
};

function initials(name: string | null | undefined): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

export function AppNav({ userName }: AppNavProps) {
  return (
    <header className="border-b border-border bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-6 px-6">
        <div className="flex items-center gap-8">
          <span className="text-sm font-bold tracking-[0.2em]">CRATE</span>
          <nav className="hidden items-center gap-6 text-sm sm:flex">
            <span className="font-medium text-accent">Discover</span>
            <span className="text-muted-foreground">Playlists</span>
            <span className="text-muted-foreground">Browse</span>
          </nav>
        </div>

        <div className="flex flex-1 items-center justify-end gap-3 sm:max-w-xs">
          <label className="relative hidden flex-1 sm:block">
            <span className="sr-only">Search</span>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            >
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input
              type="search"
              placeholder="Search..."
              disabled
              className="w-full rounded-full border border-border bg-card py-2 pr-3 pl-9 text-sm text-muted-foreground"
            />
          </label>
          {userName ? (
            <div
              className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-card text-xs font-semibold"
              title={userName}
            >
              {initials(userName)}
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
