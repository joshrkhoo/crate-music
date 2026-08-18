import { AlbumArt } from "@/components/album-art";
import { SimilarNeighbor, formatArtists, spotifyTrackUrl } from "@/lib/types";

type RecommendationCardProps = {
  item: SimilarNeighbor;
};

export function RecommendationCard({ item }: RecommendationCardProps) {
  const artists = formatArtists(item.track.artists);

  return (
    <article className="crate-surface flex w-[18rem] items-center gap-3 p-3">
      <AlbumArt
        src={item.track.image_url}
        alt={`${item.track.name} cover`}
        size="sm"
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{item.track.name}</p>
        <p className="truncate text-xs text-muted-foreground">{artists}</p>
        <span className="crate-badge mt-1.5">Not in playlist</span>
      </div>
      <a
        href={spotifyTrackUrl(item.track.id)}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Open ${item.track.name} in Spotify`}
        className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border text-muted-foreground transition-colors hover:border-accent hover:text-accent"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" className="size-3.5 ml-0.5" aria-hidden>
          <path d="M8 5v14l11-7z" />
        </svg>
      </a>
    </article>
  );
}
