import { AlbumArt } from "@/components/album-art";
import { SimilarityBar } from "@/components/similarity-bar";
import { SpotifyLink } from "@/components/spotify-link";
import { SimilarNeighbor, formatArtists } from "@/lib/types";

type SimilarTrackCardProps = {
  item: SimilarNeighbor;
};

export function SimilarTrackCard({ item }: SimilarTrackCardProps) {
  const artists = formatArtists(item.track.artists);
  const genre = item.genres[0];

  return (
    <article className="crate-surface w-[9.5rem] shrink-0 p-2.5 sm:w-[11.5rem] sm:p-3">
      <div className="overflow-hidden rounded-md">
        <AlbumArt
          src={item.track.image_url}
          alt={`${item.track.name} cover`}
          size="md"
          className="!size-[8rem] sm:!size-[8.5rem]"
        />
      </div>
      <div className="mt-3 min-w-0">
        <p className="truncate text-sm font-medium">{item.track.name}</p>
        <p className="truncate text-xs text-muted-foreground">{artists}</p>
        <p className="mt-2 text-xs font-medium text-accent">
          {Math.round(item.similarity * 100)}% match
        </p>
        <SimilarityBar value={item.similarity} showPercent={false} className="mt-1" />
        {genre ? (
          <span className="crate-genre mt-2 inline-flex">{genre}</span>
        ) : null}
      </div>
      <div className="mt-2 flex justify-end">
        <SpotifyLink trackId={item.track.id} trackName={item.track.name} className="opacity-70" />
      </div>
    </article>
  );
}
