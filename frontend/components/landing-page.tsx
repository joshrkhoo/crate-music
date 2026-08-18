"use client";

import { FormEvent } from "react";

import { loginUrl } from "@/lib/api";
import type { PlaylistSummary, SpotifyUser } from "@/lib/types";

type LandingPageProps = {
  user: SpotifyUser | null;
  userLabel: string | null;
  error: string | null;
  playlists: PlaylistSummary[];
  playlistUrl: string;
  importing: boolean;
  analysingDots: string;
  onPlaylistUrlChange: (url: string) => void;
  onAnalyse: (event: FormEvent) => void;
  onLogout: () => void;
};

function SpotifyIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="size-5 shrink-0" aria-hidden>
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
    </svg>
  );
}

function LandingDecor() {
  return (
    <svg
      className="pointer-events-none absolute inset-0 h-full w-full"
      viewBox="0 0 400 320"
      fill="none"
      aria-hidden
    >
      <circle cx="72" cy="88" r="4" fill="#d4af37" opacity="0.9" />
      <path
        d="M72 92 L72 148"
        stroke="#d4af37"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.7"
      />
      <circle cx="72" cy="152" r="3" fill="#d4af37" opacity="0.5" />
      <path
        d="M88 56 Q160 20 228 72"
        stroke="#d4af37"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeDasharray="4 6"
        opacity="0.55"
      />
      <circle cx="228" cy="72" r="4" fill="#d4af37" opacity="0.85" />
      <circle cx="328" cy="200" r="4" fill="#d4af37" opacity="0.9" />
      <path
        d="M328 196 L328 140"
        stroke="#d4af37"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.7"
      />
      <circle cx="328" cy="136" r="3" fill="#d4af37" opacity="0.5" />
    </svg>
  );
}

function CrateHeroImage() {
  return (
    <div className="relative mx-auto h-56 w-full max-w-sm sm:h-64">
      <LandingDecor />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/design/crate-hero.png"
        alt="Vinyl records in a crate"
        className="relative mx-auto h-full w-auto max-w-full object-contain drop-shadow-2xl"
      />
    </div>
  );
}

export function LandingPage({
  user,
  userLabel,
  error,
  playlists,
  playlistUrl,
  importing,
  analysingDots,
  onPlaylistUrlChange,
  onAnalyse,
  onLogout,
}: LandingPageProps) {
  return (
    <div className="mx-auto flex w-full max-w-lg flex-1 flex-col items-center px-6 py-10 sm:py-16">
      <p className="text-[0.65rem] font-semibold tracking-[0.45em] text-muted-foreground">
        CRATE
      </p>

      <h1 className="mt-8 text-center text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl">
        Dig deeper into
        <br />
        your playlists
      </h1>

      <p className="mt-4 max-w-xs text-center text-sm leading-relaxed text-muted-foreground sm:text-base">
        Find similar tracks, hidden gems,
        <br className="hidden sm:block" />
        and new favorites.
      </p>

      <div className="mt-6 w-full">
        <CrateHeroImage />
      </div>

      <div className="mt-2 w-full max-w-sm">
        {!user ? (
          <>
            <a
              href={loginUrl()}
              className="flex w-full items-center justify-center gap-2.5 rounded-full bg-spotify py-4 text-base font-semibold text-black transition-colors hover:bg-[#1ed760]"
            >
              <SpotifyIcon />
              Connect Spotify
            </a>

            <p className="mt-5 flex items-center justify-center gap-1.5 text-xs text-accent/80">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="size-3.5" aria-hidden>
                <rect x="5" y="11" width="14" height="10" rx="2" />
                <path d="M8 11V8a4 4 0 0 1 8 0v3" />
              </svg>
              Your data is 100% private and secure.
            </p>
          </>
        ) : (
          <div className="crate-surface p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Signed in as</p>
                <p className="font-medium">{userLabel}</p>
              </div>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-full border border-border px-3 py-1.5 text-xs hover:bg-white/[0.03]"
              >
                Log out
              </button>
            </div>

            <form className="mt-5 space-y-4" onSubmit={onAnalyse}>
              {playlists.length > 0 ? (
                <label className="block text-sm">
                  <span className="text-muted-foreground">Your playlists</span>
                  <select
                    className="mt-1 w-full rounded-md border border-border bg-transparent px-3 py-2.5 text-sm"
                    value=""
                    onChange={(event) => {
                      const playlist = playlists.find((item) => item.id === event.target.value);
                      if (playlist) {
                        onPlaylistUrlChange(
                          `https://open.spotify.com/playlist/${playlist.id}`,
                        );
                      }
                    }}
                  >
                    <option value="">Choose a playlist</option>
                    {playlists.map((playlist) => (
                      <option key={playlist.id} value={playlist.id}>
                        {playlist.name} ({playlist.track_count})
                      </option>
                    ))}
                  </select>
                </label>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No owned or collaborative playlists found. Paste a URL to one you own.
                </p>
              )}

              <label className="block text-sm">
                <span className="text-muted-foreground">Playlist URL</span>
                <input
                  type="text"
                  required
                  value={playlistUrl}
                  onChange={(event) => onPlaylistUrlChange(event.target.value)}
                  placeholder="https://open.spotify.com/playlist/..."
                  className="mt-1 w-full rounded-md border border-border bg-transparent px-3 py-2.5 text-sm"
                />
              </label>

              <button
                type="submit"
                disabled={importing}
                className="flex w-full items-center justify-center gap-2 rounded-full bg-spotify py-3.5 text-sm font-semibold text-black hover:bg-[#1ed760] disabled:opacity-60"
              >
                <SpotifyIcon />
                {importing ? `Analysing${analysingDots}` : "Analyse playlist"}
              </button>
            </form>

            <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-accent/80">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="size-3.5" aria-hidden>
                <rect x="5" y="11" width="14" height="10" rx="2" />
                <path d="M8 11V8a4 4 0 0 1 8 0v3" />
              </svg>
              Your data is 100% private and secure.
            </p>
          </div>
        )}

        {error ? <p className="mt-4 text-center text-sm text-red-400">{error}</p> : null}
      </div>
    </div>
  );
}
