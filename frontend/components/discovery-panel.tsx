import { AlbumArt } from "@/components/album-art";
import { HorizontalScroll } from "@/components/horizontal-scroll";
import { RecommendationCard } from "@/components/recommendation-card";
import { SimilarTrackCard } from "@/components/similar-track-card";
import { SimilarNeighbor, SimilarResponse, EnrichedTrack, formatArtists } from "@/lib/types";

type DiscoveryPanelProps = {
  selectedTrack: EnrichedTrack | null;
  similar: SimilarResponse | null;
  recommendations: SimilarNeighbor[] | null;
  indexing: boolean;
  loadingSimilar: boolean;
  recommending: boolean;
  similarError: string | null;
  onRetrySimilar?: () => void;
  onRetryRecommend?: () => void;
};

function SparkleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="size-3.5 text-accent" aria-hidden>
      <path d="M12 2l1.2 4.2L17.5 8 13.2 9.2 12 13.5 10.8 9.2 6.5 8l4.3-1.8L12 2zm7 7l.6 2.2L22 12l-2.4.8L19 15l-.6-2.2L16 12l2.4-.8L19 9zm-14 3l.8 2.8L9 17l-2.2.7L6 20l-.8-2.8L3 17l2.2-.7L6 14z" />
    </svg>
  );
}

function NeighborSkeletonCard() {
  return (
    <div className="crate-surface w-[11.5rem] animate-pulse p-3">
      <div className="aspect-square rounded-md bg-neutral-800" />
      <div className="mt-3 space-y-2">
        <div className="h-3.5 w-3/4 rounded bg-neutral-800" />
        <div className="h-3 w-1/2 rounded bg-neutral-800" />
        <div className="h-2.5 w-16 rounded bg-neutral-800" />
        <div className="h-1 w-full rounded-full bg-neutral-800" />
      </div>
    </div>
  );
}

export function DiscoveryPanel({
  selectedTrack,
  similar,
  recommendations,
  indexing,
  loadingSimilar,
  recommending,
  similarError,
  onRetrySimilar,
  onRetryRecommend,
}: DiscoveryPanelProps) {
  const selectedId = selectedTrack?.track.id;
  const similarMatchesSelection =
    Boolean(selectedId && similar?.track.track.id === selectedId);
  const displayedNeighbors = similarMatchesSelection ? similar?.neighbors ?? [] : [];
  const staleNeighbors =
    loadingSimilar && similar && !similarMatchesSelection ? similar.neighbors : [];
  const visibleNeighbors = displayedNeighbors.length > 0 ? displayedNeighbors : staleNeighbors;
  const neighborsAreStale = displayedNeighbors.length === 0 && staleNeighbors.length > 0;

  const heroTrack = selectedTrack ?? similar?.track ?? null;
  const heroTitle = heroTrack?.track.name ?? "";
  const heroArtists = heroTrack ? formatArtists(heroTrack.track.artists) : "";
  const primaryGenre = heroTrack?.genres[0];

  const showEmptyPrompt = !selectedTrack && !similar && !recommendations?.length && !recommending;
  const showInitialNeighborSkeleton =
    loadingSimilar && !similar && displayedNeighbors.length === 0 && !similarError;

  return (
    <div className="crate-surface flex min-h-[32rem] flex-col space-y-6 rounded-lg p-5 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="crate-section-label">
          <SparkleIcon />
          Discovery
        </div>
        <button
          type="button"
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          title="Similarity is scored from artist, genre, era, and album metadata embeddings."
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="size-3.5" aria-hidden>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 10v6M12 7h.01" />
          </svg>
          About discovery
        </button>
      </div>

      {showEmptyPrompt ? (
        <div className="flex flex-1 flex-col items-center justify-center py-12 text-center">
          <p className="text-sm text-muted-foreground">
            {indexing ? "Building similarity index…" : "Pick a track from your playlist"}
          </p>
          <p className="mt-2 max-w-sm text-xs text-muted-foreground">
            {indexing
              ? "Browse tracks on the left while indexing finishes."
              : "Select any song to see closest matches and discover new tracks."}
          </p>
        </div>
      ) : (
        <>
          {heroTrack ? (
            <div className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end">
              <AlbumArt
                src={heroTrack.track.image_url}
                alt={`${heroTitle} cover`}
                size="xl"
                className="shadow-lg shadow-black/40"
              />
              <div className="min-w-0">
                <h3 className="text-2xl font-bold tracking-tight sm:text-3xl">{heroTitle}</h3>
                <p className="mt-1 text-muted-foreground">{heroArtists}</p>
                {primaryGenre ? (
                  <span className="crate-genre-accent mt-3 inline-flex">{primaryGenre}</span>
                ) : null}
              </div>
            </div>
          ) : null}

          {similarError && !loadingSimilar ? (
            <div className="rounded-lg border border-red-900/40 bg-red-950/20 p-4">
              <p className="text-sm text-red-400">{similarError}</p>
              {onRetrySimilar ? (
                <button
                  type="button"
                  onClick={onRetrySimilar}
                  className="mt-3 rounded-full border border-border px-4 py-2 text-sm hover:bg-white/[0.03]"
                >
                  Try again
                </button>
              ) : null}
            </div>
          ) : null}

          {heroTrack && !similarError ? (
            <section aria-busy={loadingSimilar} className="min-h-[15rem]">
              <div className="flex items-center gap-3">
                <div>
                  <h4 className="text-sm font-semibold">Closest in this playlist</h4>
                  <p className="mt-0.5 text-xs text-muted-foreground">to {heroTitle}</p>
                </div>
                {loadingSimilar ? (
                  <span className="text-xs text-muted-foreground">Updating…</span>
                ) : null}
              </div>

              <div className="relative mt-4 min-h-[12.5rem]">
                {showInitialNeighborSkeleton ? (
                  <HorizontalScroll>
                    {Array.from({ length: 4 }, (_, index) => (
                      <NeighborSkeletonCard key={index} />
                    ))}
                  </HorizontalScroll>
                ) : visibleNeighbors.length === 0 && !loadingSimilar ? (
                  <p className="text-sm text-muted-foreground">
                    Need at least two tracks to compare.
                  </p>
                ) : visibleNeighbors.length > 0 ? (
                  <div
                    className={`transition-opacity duration-300 ${
                      loadingSimilar || neighborsAreStale ? "opacity-45" : "opacity-100"
                    }`}
                  >
                    <HorizontalScroll>
                      {visibleNeighbors.map((item, index) => (
                        <SimilarTrackCard key={`${item.track.id}-${index}`} item={item} />
                      ))}
                    </HorizontalScroll>
                  </div>
                ) : null}
              </div>
            </section>
          ) : null}

          {recommending && !recommendations ? (
            <section>
              <h4 className="text-sm font-semibold">New songs you might like</h4>
              <p className="mt-0.5 text-xs text-muted-foreground">Searching Last.fm and Spotify…</p>
              <div className="mt-4 flex animate-pulse gap-3">
                {Array.from({ length: 3 }, (_, index) => (
                  <div key={index} className="h-20 w-72 rounded-lg bg-neutral-900" />
                ))}
              </div>
            </section>
          ) : null}

          {recommendations ? (
            <section>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h4 className="text-sm font-semibold">New songs you might like</h4>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Not in this playlist · scored against your tracks
                  </p>
                </div>
                {recommendations.length > 0 ? (
                  <span className="text-xs text-muted-foreground">View all</span>
                ) : null}
              </div>
              {recommendations.length === 0 ? (
                <div className="mt-4 space-y-3">
                  <p className="text-sm text-muted-foreground">
                    No new songs found from Last.fm for this playlist.
                  </p>
                  {onRetryRecommend ? (
                    <button
                      type="button"
                      onClick={onRetryRecommend}
                      className="rounded-full border border-border px-4 py-2 text-sm hover:bg-white/[0.03]"
                    >
                      Search again
                    </button>
                  ) : null}
                </div>
              ) : (
                <HorizontalScroll className="mt-4">
                  {recommendations.map((item, index) => (
                    <RecommendationCard key={`${item.track.id}-${index}`} item={item} />
                  ))}
                </HorizontalScroll>
              )}
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}
