"use client";

import { useEffect, useRef, useState } from "react";

type AppNavProps = {
  userName?: string | null;
  onLogout?: () => void;
};

function initials(name: string | null | undefined): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

export function AppNav({ userName, onLogout }: AppNavProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) return;
    function handleClick(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [menuOpen]);

  return (
    <header className="relative z-[100] border-b border-border bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-4 sm:gap-6 sm:px-6">
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
            <div ref={menuRef} className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((open) => !open)}
                className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-card text-xs font-semibold transition-colors hover:border-accent"
                title={userName}
              >
                {initials(userName)}
              </button>
              {menuOpen ? (
                <div className="absolute right-0 z-[100] mt-2 w-48 overflow-hidden rounded-lg border border-border bg-card shadow-lg shadow-black/60">
                  <div className="border-b border-border px-4 py-3">
                    <p className="truncate text-sm font-medium">{userName}</p>
                  </div>
                  {onLogout ? (
                    <button
                      type="button"
                      onClick={() => {
                        setMenuOpen(false);
                        onLogout();
                      }}
                      className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm text-muted-foreground transition-colors hover:bg-white/[0.03] hover:text-foreground"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="size-4" aria-hidden>
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                        <polyline points="16 17 21 12 16 7" />
                        <line x1="21" y1="12" x2="9" y2="12" />
                      </svg>
                      Sign out
                    </button>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
