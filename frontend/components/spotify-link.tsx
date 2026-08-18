import { spotifyTrackUrl } from "@/lib/types";

type SpotifyLinkProps = {
  trackId: string;
  trackName: string;
  className?: string;
};

export function SpotifyLink({ trackId, trackName, className = "" }: SpotifyLinkProps) {
  return (
    <a
      href={spotifyTrackUrl(trackId)}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(event) => event.stopPropagation()}
      aria-label={`Open ${trackName} in Spotify`}
      className={`shrink-0 rounded-full p-2 text-muted-foreground transition-colors hover:bg-neutral-800 hover:text-foreground ${className}`}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="size-4" aria-hidden>
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
        <path d="M15 3h6v6" />
        <path d="M10 14 21 3" />
      </svg>
    </a>
  );
}
