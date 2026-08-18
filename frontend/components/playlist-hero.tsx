import { AlbumArt } from "@/components/album-art";

type PlaylistHeroProps = {
  name: string;
  trackCount: number;
  imageUrl?: string | null;
  indexing: boolean;
  recommending: boolean;
  recommendingDots: string;
  onRecommend: () => void;
  recommendDisabled: boolean;
};

function SpotifyIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="size-4" aria-hidden>
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
    </svg>
  );
}

export function PlaylistHero({
  name,
  trackCount,
  imageUrl,
  indexing,
  recommending,
  recommendingDots,
  onRecommend,
  recommendDisabled,
}: PlaylistHeroProps) {
  return (
    <div className="relative overflow-hidden rounded-lg border border-border">
      {imageUrl ? (
        <>
          <div
            className="absolute inset-0 scale-110 bg-cover bg-center blur-2xl saturate-150"
            style={{ backgroundImage: `url(${imageUrl})` }}
            aria-hidden
          />
          <div className="absolute inset-0 bg-gradient-to-r from-black/85 via-black/75 to-black/60" aria-hidden />
        </>
      ) : (
        <div className="absolute inset-0 bg-card" aria-hidden />
      )}

      <div className="relative flex flex-col gap-5 p-6 sm:flex-row sm:items-end sm:p-8">
        <AlbumArt
          src={imageUrl}
          alt={`${name} cover`}
          size="lg"
          className="shadow-2xl shadow-black/50"
        />
        <div className="min-w-0 flex-1">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{name}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {trackCount} tracks
            {indexing ? " · indexing…" : null}
          </p>
          <button
            type="button"
            onClick={onRecommend}
            disabled={recommendDisabled}
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-spotify px-5 py-2.5 text-sm font-semibold text-black hover:bg-[#1ed760] disabled:opacity-60"
          >
            <SpotifyIcon />
            {recommending ? `Finding new songs${recommendingDots}` : "Recommend new songs"}
          </button>
        </div>
      </div>
    </div>
  );
}
