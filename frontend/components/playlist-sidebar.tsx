"use client";

import { AlbumArt } from "@/components/album-art";
import { EnrichedTrack, formatArtists } from "@/lib/types";

type PlaylistSidebarProps = {
  tracks: EnrichedTrack[];
  playlistId?: string;
  selectedTrackId: string | null;
  indexing: boolean;
  onSelectTrack: (trackId: string) => void;
  onChangePlaylist?: () => void;
};

function EqualizerIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor" className="size-3.5 shrink-0 text-accent" aria-hidden>
      <rect x="1" y="5" width="2" height="6" rx="0.5" />
      <rect x="5" y="3" width="2" height="10" rx="0.5" />
      <rect x="9" y="6" width="2" height="4" rx="0.5" />
      <rect x="13" y="4" width="2" height="8" rx="0.5" />
    </svg>
  );
}

export function PlaylistSidebar({
  tracks,
  playlistId,
  selectedTrackId,
  indexing,
  onSelectTrack,
  onChangePlaylist,
}: PlaylistSidebarProps) {
  const spotifyUrl = playlistId
    ? `https://open.spotify.com/playlist/${playlistId}`
    : null;

  return (
    <aside className="crate-surface flex flex-col overflow-hidden">
      <div className="crate-section-label border-b border-border px-4 py-3">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="size-3.5" aria-hidden>
          <path d="M9 18V5l12-2v13" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </svg>
        {tracks.length} tracks
      </div>

      <div className="playlist-scroll max-h-[28rem] flex-1 overflow-y-auto">
        <ul className="p-2">
          {tracks.map((item, index) => {
            const selected = selectedTrackId === item.track.id;
            const artists = formatArtists(item.track.artists);

            return (
              <li key={`${item.track.id}-${index}`}>
                <button
                  type="button"
                  disabled={indexing}
                  onClick={() => onSelectTrack(item.track.id)}
                  className={`flex w-full items-center gap-2.5 rounded-md px-2 py-2 text-left text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                    selected ? "crate-selected" : "hover:bg-white/[0.03]"
                  }`}
                >
                  <AlbumArt
                    src={item.track.image_url}
                    alt={`${item.track.name} cover`}
                    size="xs"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      {selected ? <EqualizerIcon /> : null}
                      <p className="truncate font-medium">{item.track.name}</p>
                    </div>
                    <p className="truncate text-xs text-muted-foreground">{artists}</p>
                  </div>
                  {item.release_year ? (
                    <span className="shrink-0 text-[0.6875rem] tabular-nums text-muted-foreground">
                      {item.release_year}
                    </span>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="flex items-center border-t border-border">
        {spotifyUrl ? (
          <a
            href={spotifyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex flex-1 items-center justify-center gap-1.5 px-4 py-3 text-xs text-muted-foreground hover:text-foreground"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="size-3.5" aria-hidden>
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <path d="M15 3h6v6" />
              <path d="M10 14 21 3" />
            </svg>
            Open in Spotify
          </a>
        ) : null}
        {onChangePlaylist ? (
          <button
            type="button"
            onClick={onChangePlaylist}
            className={`flex items-center justify-center gap-1 px-4 py-3 text-xs text-muted-foreground hover:text-foreground ${
              spotifyUrl ? "border-l border-border" : "flex-1"
            }`}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="size-3.5" aria-hidden>
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
              <path d="M21 3v5h-5" />
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
              <path d="M3 21v-5h5" />
            </svg>
            Change
          </button>
        ) : null}
      </div>
    </aside>
  );
}
