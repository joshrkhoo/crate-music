import { AlbumArt } from "@/components/album-art";
import { GenrePill } from "@/components/genre-pill";
import { SimilarityBar } from "@/components/similarity-bar";
import { SpotifyLink } from "@/components/spotify-link";
import { EnrichedTrack, SimilarNeighbor, formatArtists } from "@/lib/types";

type TrackRowProps = {
  item: EnrichedTrack | SimilarNeighbor;
  selected?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  showSimilarity?: boolean;
  badge?: string;
};

export function TrackRow({
  item,
  selected = false,
  onClick,
  disabled = false,
  showSimilarity = false,
  badge,
}: TrackRowProps) {
  const artists = formatArtists(item.track.artists);
  const similarity = "similarity" in item ? item.similarity : undefined;
  const interactive = Boolean(onClick);

  const details = (
    <div className="min-w-0 flex-1">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-medium">{item.track.name}</p>
          <p className="truncate text-sm text-muted-foreground">{artists}</p>
        </div>
        {badge ? <span className="crate-badge shrink-0">{badge}</span> : null}
      </div>
      {showSimilarity && similarity !== undefined ? (
        <SimilarityBar value={similarity} className="mt-2" />
      ) : null}
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {item.release_year ? (
          <span className="text-xs text-muted-foreground">{item.release_year}</span>
        ) : null}
        {item.genres.slice(0, 2).map((genre) => (
          <GenrePill key={genre} genre={genre} />
        ))}
      </div>
    </div>
  );

  const rowClassName = `group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-colors ${
    selected ? "crate-selected bg-neutral-900/80" : "hover:bg-neutral-900/50"
  } ${disabled ? "opacity-50" : ""}`;

  const art = (
    <AlbumArt
      src={item.track.image_url}
      alt={`${item.track.name} cover`}
      size="md"
      className="transition-transform duration-200 group-hover:scale-[1.02]"
    />
  );

  const spotifyLink = (
    <SpotifyLink
      trackId={item.track.id}
      trackName={item.track.name}
      className={interactive ? "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100" : "opacity-60 hover:opacity-100"}
    />
  );

  if (interactive) {
    return (
      <li>
        <div className={rowClassName}>
          <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            className="flex min-w-0 flex-1 items-center gap-3 text-left disabled:cursor-not-allowed"
          >
            {art}
            {details}
          </button>
          {!disabled ? spotifyLink : null}
        </div>
      </li>
    );
  }

  return (
    <li className={rowClassName}>
      {art}
      {details}
      {spotifyLink}
    </li>
  );
}
