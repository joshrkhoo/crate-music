"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { AppFooter } from "@/components/app-footer";
import { AppNav } from "@/components/app-nav";
import { DiscoveryPanel } from "@/components/discovery-panel";
import { LandingPage } from "@/components/landing-page";
import { PlaylistHero } from "@/components/playlist-hero";
import { PlaylistSidebar } from "@/components/playlist-sidebar";
import { apiFetch, clearSessionId, setSessionId } from "@/lib/api";
import type {
  PlaylistImport,
  PlaylistSummary,
  SimilarNeighbor,
  SimilarResponse,
  SpotifyUser,
} from "@/lib/types";

type MeResponseLocal =
  | { authenticated: false }
  | (SpotifyUser & { authenticated: true });

function useLoadingDots(active: boolean) {
  const [dots, setDots] = useState(".");

  useEffect(() => {
    if (!active) {
      setDots(".");
      return;
    }
    const frames = [".", "..", "..."];
    let index = 0;
    const timer = window.setInterval(() => {
      index = (index + 1) % frames.length;
      setDots(frames[index]);
    }, 400);
    return () => window.clearInterval(timer);
  }, [active]);

  return dots;
}

export default function Home() {
  const [user, setUser] = useState<SpotifyUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [playlists, setPlaylists] = useState<PlaylistSummary[]>([]);
  const [playlistUrl, setPlaylistUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [imported, setImported] = useState<PlaylistImport | null>(null);
  const [selectedTrackId, setSelectedTrackId] = useState<string | null>(null);
  const [similar, setSimilar] = useState<SimilarResponse | null>(null);
  const [recommendations, setRecommendations] = useState<SimilarNeighbor[] | null>(null);
  const [recommending, setRecommending] = useState(false);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [similarError, setSimilarError] = useState<string | null>(null);
  const [indexing, setIndexing] = useState(false);
  const [ready, setReady] = useState(false);
  const analysingDots = useLoadingDots(importing);
  const recommendingDots = useLoadingDots(recommending);
  const indexingDots = useLoadingDots(indexing);
  const similarRequestRef = useRef<AbortController | null>(null);
  const discoveryRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauthError = params.get("error");
    const sid = params.get("sid");

    if (sid) {
      setSessionId(sid);
    }
    if (oauthError) {
      setError(oauthError);
    }
    if (sid || oauthError) {
      window.history.replaceState({}, "", "/");
    }

    let cancelled = false;

    (async () => {
      try {
        const response = await Promise.race([
          apiFetch("/auth/me"),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error("timeout")), 4000),
          ),
        ]);
        if (cancelled) return;
        if (!response.ok) {
          setUser(null);
          setReady(true);
          return;
        }
        const data = (await response.json()) as MeResponseLocal;
        if (cancelled) return;
        if (!data.authenticated) {
          setUser(null);
          setReady(true);
          return;
        }
        const authedUser: SpotifyUser = {
          id: data.id,
          display_name: data.display_name,
          country: data.country,
        };

        let restoredPlaylist: PlaylistImport | null = null;
        let restoredSimilar: SimilarResponse | null = null;
        let restoredRecommendations: SimilarNeighbor[] | null = null;
        try {
          const restoreRes = await apiFetch("/spotify/playlist/restore");
          if (cancelled) return;
          if (restoreRes.ok) {
            const restoreData = (await restoreRes.json()) as {
              playlist: PlaylistImport | null;
              last_similar: SimilarResponse | null;
              last_recommendations: SimilarNeighbor[] | null;
            };
            if (restoreData.playlist && restoreData.playlist.tracks.length > 0) {
              restoredPlaylist = restoreData.playlist;
            }
            restoredSimilar = restoreData.last_similar ?? null;
            restoredRecommendations = restoreData.last_recommendations ?? null;
          }
        } catch {}

        if (cancelled) return;
        setUser(authedUser);
        if (restoredPlaylist) {
          setImported(restoredPlaylist);
          if (!restoredPlaylist.embeddings_ready) {
            setIndexing(true);
          }
        }
        if (restoredSimilar) {
          setSimilar(restoredSimilar);
          setSelectedTrackId(restoredSimilar.track.track.id);
        }
        if (restoredRecommendations && restoredRecommendations.length > 0) {
          setRecommendations(restoredRecommendations);
        }
        setReady(true);
      } catch {
        if (cancelled) return;
        setError("Could not reach the API. Is the backend running?");
        setReady(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!user) {
      setPlaylists([]);
      setImported(null);
      setSelectedTrackId(null);
      setSimilar(null);
      setRecommendations(null);
      setSimilarError(null);
      setLoadingSimilar(false);
      setIndexing(false);
      return;
    }

    apiFetch("/spotify/playlists")
      .then(async (response) => {
        if (!response.ok) {
          return;
        }
        const data = (await response.json()) as { playlists: PlaylistSummary[] };
        setPlaylists(data.playlists);
      })
      .catch(() => {
        setError("Could not load your playlists.");
      });
  }, [user]);

  useEffect(() => {
    if (!indexing) {
      return;
    }

    let cancelled = false;

    async function checkStatus() {
      try {
        const response = await apiFetch("/spotify/playlist/status");
        const data = await response.json();
        if (cancelled) {
          return;
        }
        if (data.embedding_error) {
          setIndexing(false);
          setError("Could not build similarity index. Try Analyse again.");
          return;
        }
        if (data.embeddings_ready) {
          setIndexing(false);
        }
      } catch {
        if (!cancelled) {
          setIndexing(false);
          setError("Could not reach the API. Is the backend running?");
        }
      }
    }

    checkStatus();
    const interval = window.setInterval(checkStatus, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [indexing]);

  function resetPlaylistView() {
    setImported(null);
    setSelectedTrackId(null);
    setSimilar(null);
    setRecommendations(null);
    setSimilarError(null);
    setLoadingSimilar(false);
    setIndexing(false);
  }

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" });
    clearSessionId();
    setUser(null);
    setImported(null);
    setPlaylistUrl("");
    setSelectedTrackId(null);
    setSimilar(null);
    setRecommendations(null);
    setSimilarError(null);
    setLoadingSimilar(false);
    setIndexing(false);
  }

  async function analysePlaylist(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setImporting(true);
    setImported(null);
    setSelectedTrackId(null);
    setSimilar(null);
    setRecommendations(null);
    setSimilarError(null);
    setLoadingSimilar(false);
    setIndexing(false);

    try {
      const response = await apiFetch("/spotify/playlist", {
        method: "POST",
        body: JSON.stringify({ url: playlistUrl }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Could not import that playlist.");
        return;
      }
      setImported(data as PlaylistImport);
      setIndexing(data.embeddings_ready === false);
    } catch {
      setError("Could not reach the API. Is the backend running?");
    } finally {
      setImporting(false);
    }
  }

  async function showSimilar(trackId: string) {
    if (indexing) {
      return;
    }
    if (trackId === selectedTrackId && similar?.track.track.id === trackId && !similarError) {
      return;
    }

    similarRequestRef.current?.abort();
    const controller = new AbortController();
    similarRequestRef.current = controller;

    setSelectedTrackId(trackId);
    setSimilarError(null);
    setLoadingSimilar(true);

    if (window.innerWidth < 1024) {
      window.requestAnimationFrame(() => {
        discoveryRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }

    try {
      const response = await apiFetch(`/spotify/similar/${trackId}`, {
        signal: controller.signal,
      });
      const data = await response.json();
      if (controller.signal.aborted) {
        return;
      }
      if (!response.ok) {
        const message =
          typeof data.detail === "string" ? data.detail : "Could not find similar tracks.";
        setSimilarError(message);
        return;
      }
      setSimilar(data as SimilarResponse);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }
      if (controller.signal.aborted) {
        return;
      }
      setSimilarError("Could not reach the API. Is the backend running?");
    } finally {
      if (!controller.signal.aborted) {
        setLoadingSimilar(false);
      }
    }
  }

  function retrySimilar() {
    if (selectedTrackId) {
      void showSimilar(selectedTrackId);
    }
  }

  async function recommendNewSongs() {
    setError(null);
    setRecommending(true);
    setRecommendations(null);
    try {
      const response = await apiFetch("/spotify/recommend", { method: "POST" });
      const data = await response.json();
      if (!response.ok) {
        setError(
          typeof data.detail === "string"
            ? data.detail
            : "Could not get recommendations.",
        );
        return;
      }
      setRecommendations((data.recommendations ?? []) as SimilarNeighbor[]);
    } catch {
      setError("Could not reach the API. Is the backend running?");
    } finally {
      setRecommending(false);
    }
  }

  const userLabel = user?.display_name || user?.id || null;
  const selectedTrack =
    imported?.tracks.find((item) => item.track.id === selectedTrackId) ?? null;

  if (!ready) {
    return <div className="min-h-screen bg-black" />;
  }

  return (
    <>
      {imported ? <AppNav userName={userLabel} onLogout={logout} /> : null}
      <main
        className={`mx-auto flex w-full min-w-0 flex-1 flex-col ${
          imported ? "max-w-7xl px-4 py-4 sm:px-6 sm:py-6" : "min-h-[calc(100vh-0px)] bg-black"
        }`}
      >
        {!imported ? (
          <LandingPage
            user={user}
            userLabel={userLabel}
            error={error}
            playlists={playlists}
            playlistUrl={playlistUrl}
            importing={importing}
            analysingDots={analysingDots}
            onPlaylistUrlChange={setPlaylistUrl}
            onAnalyse={analysePlaylist}
            onLogout={logout}
          />
        ) : (
          <div className="min-w-0 space-y-4 sm:space-y-6">
            <PlaylistHero
              name={imported.name}
              trackCount={imported.tracks.length}
              imageUrl={imported.image_url}
              indexing={indexing}
              indexingDots={indexingDots}
              recommending={recommending}
              recommendingDots={recommendingDots}
              onRecommend={recommendNewSongs}
              recommendDisabled={recommending || indexing}
            />

            {indexing ? (
              <p className="text-sm text-muted-foreground">Indexing{indexingDots}</p>
            ) : null}

            {error ? <p className="text-sm text-red-400">{error}</p> : null}

            <div className="grid min-w-0 gap-4 lg:grid-cols-[17rem_minmax(0,1fr)] lg:items-start">
              <div className={`min-w-0 ${selectedTrackId ? "order-2" : "order-1"} lg:order-1`}>
                <PlaylistSidebar
                  tracks={imported.tracks}
                  playlistId={imported.id}
                  selectedTrackId={selectedTrackId}
                  indexing={indexing}
                  onSelectTrack={showSimilar}
                  onChangePlaylist={resetPlaylistView}
                />
              </div>

              <div
                ref={discoveryRef}
                className={`min-w-0 scroll-mt-4 ${selectedTrackId ? "order-1" : "order-2"} lg:order-2`}
              >
                <DiscoveryPanel
                  selectedTrack={selectedTrack}
                  similar={similar}
                  recommendations={recommendations}
                  indexing={indexing}
                  indexingDots={indexingDots}
                  loadingSimilar={loadingSimilar}
                  recommending={recommending}
                  similarError={similarError}
                  onRetrySimilar={retrySimilar}
                  onRetryRecommend={recommendNewSongs}
                />
              </div>
            </div>

          </div>
        )}
      </main>
      {imported ? <AppFooter /> : null}
    </>
  );
}
