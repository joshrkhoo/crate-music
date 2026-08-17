"use client";

import { FormEvent, useEffect, useState } from "react";

import { apiFetch, clearSessionId, loginUrl, setSessionId } from "@/lib/api";

type SpotifyUser = {
  id: string;
  display_name: string | null;
  country: string | null;
};

type MeResponse =
  | { authenticated: false }
  | (SpotifyUser & { authenticated: true });

type PlaylistSummary = {
  id: string;
  name: string;
  track_count: number;
};

type Track = {
  id: string;
  name: string;
  artists: { id: string; name: string }[];
  album: string;
};

type EnrichedTrack = {
  track: Track;
  release_year: number | null;
  genres: string[];
};

type SimilarNeighbor = EnrichedTrack & { similarity: number };

type SimilarResponse = {
  track: EnrichedTrack;
  neighbors: SimilarNeighbor[];
};

type PlaylistImport = {
  id: string;
  name: string;
  tracks: EnrichedTrack[];
};

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

    const controller = new AbortController();
    let timedOut = false;
    const timeout = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 4000);

    apiFetch("/auth/me", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          setUser(null);
          return;
        }
        const data = (await response.json()) as MeResponse;
        if (data.authenticated) {
          setUser({
            id: data.id,
            display_name: data.display_name,
            country: data.country,
          });
        } else {
          setUser(null);
        }
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") {
          if (timedOut) {
            setError("Could not reach the API. Is the backend running?");
          }
          return;
        }
        setError("Could not reach the API. Is the backend running?");
      })
      .finally(() => window.clearTimeout(timeout));

    return () => {
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, []);

  useEffect(() => {
    if (!user) {
      setPlaylists([]);
      setImported(null);
      setSelectedTrackId(null);
      setSimilar(null);
      setRecommendations(null);
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

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" });
    clearSessionId();
    setUser(null);
    setImported(null);
    setPlaylistUrl("");
    setSelectedTrackId(null);
    setSimilar(null);
    setRecommendations(null);
  }

  async function analysePlaylist(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setImporting(true);
    setImported(null);
    setSelectedTrackId(null);
    setSimilar(null);
    setRecommendations(null);

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
    } catch {
      setError("Could not reach the API. Is the backend running?");
    } finally {
      setImporting(false);
    }
  }

  async function showSimilar(trackId: string) {
    setSelectedTrackId(trackId);
    setError(null);
    try {
      const response = await apiFetch(`/spotify/similar/${trackId}`);
      const data = await response.json();
      if (!response.ok) {
        setSimilar(null);
        setError(typeof data.detail === "string" ? data.detail : "Could not find similar tracks.");
        return;
      }
      setSimilar(data as SimilarResponse);
    } catch {
      setSimilar(null);
      setError("Could not reach the API. Is the backend running?");
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

  return (
    <main className="mx-auto flex min-h-full w-full max-w-2xl flex-1 flex-col justify-center px-6 py-16">
      <p className="text-sm tracking-wide text-neutral-500 uppercase">crate</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">
        Music discovery
      </h1>
      <p className="mt-3 text-neutral-500">
        {user
          ? "Import a playlist you own or collaborate on."
          : "Connect Spotify to import one of your playlists."}
      </p>

      <div className="mt-10 rounded-2xl border border-neutral-200 p-6 dark:border-neutral-800">
        {user ? (
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm text-neutral-500">Signed in as</p>
              <p className="text-lg font-medium">
                {user.display_name || user.id}
              </p>
            </div>
            <button
              type="button"
              onClick={logout}
              className="rounded-full border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-900"
            >
              Log out
            </button>
          </div>
        ) : (
          <a
            href={loginUrl()}
            className="inline-flex rounded-full bg-[#1DB954] px-5 py-2.5 text-sm font-medium text-black hover:bg-[#1ed760]"
          >
            Connect Spotify
          </a>
        )}

        {user ? (
          <form className="mt-6 space-y-4" onSubmit={analysePlaylist}>
            {playlists.length > 0 ? (
              <label className="block text-sm">
                <span className="text-neutral-500">Your playlists</span>
                <select
                  className="mt-1 w-full rounded-xl border border-neutral-300 bg-transparent px-3 py-2 dark:border-neutral-700"
                  value=""
                  onChange={(event) => {
                    const playlist = playlists.find((item) => item.id === event.target.value);
                    if (playlist) {
                      setPlaylistUrl(`https://open.spotify.com/playlist/${playlist.id}`);
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
              <p className="text-sm text-neutral-500">
                No owned or collaborative playlists found. Paste a URL to one you own.
              </p>
            )}

            <label className="block text-sm">
              <span className="text-neutral-500">Playlist URL</span>
              <input
                type="text"
                required
                value={playlistUrl}
                onChange={(event) => setPlaylistUrl(event.target.value)}
                placeholder="https://open.spotify.com/playlist/..."
                className="mt-1 w-full rounded-xl border border-neutral-300 bg-transparent px-3 py-2 dark:border-neutral-700"
              />
            </label>

            <button
              type="submit"
              disabled={importing}
              className="rounded-full bg-[#1DB954] px-5 py-2.5 text-sm font-medium text-black hover:bg-[#1ed760] disabled:opacity-60"
            >
              {importing ? "Analysing…" : "Analyse"}
            </button>
          </form>
        ) : null}

        {error ? <p className="mt-4 text-sm text-red-500">{error}</p> : null}
      </div>

      {imported ? (
        <section className="mt-8">
          <h2 className="text-xl font-medium">{imported.name}</h2>
          <p className="mt-1 text-sm text-neutral-500">
            {imported.tracks.length} tracks · click a song to see the closest in this playlist
          </p>
          <button
            type="button"
            onClick={recommendNewSongs}
            disabled={recommending}
            className="mt-4 rounded-full border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:hover:bg-neutral-900"
          >
            {recommending ? "Finding new songs…" : "Recommend new songs"}
          </button>
          {recommending ? (
            <p className="mt-2 text-sm text-neutral-500">
              Last.fm + Spotify search. First run can take 20–40 seconds.
            </p>
          ) : null}
          <ul className="mt-4 space-y-3">
            {imported.tracks.map((item, index) => {
              const artists =
                item.track.artists.map((artist) => artist.name).join(", ") ||
                "Unknown artist";
              const meta = [
                item.release_year,
                item.genres.length ? item.genres.join(", ") : null,
              ]
                .filter(Boolean)
                .join(" · ");
              const selected = selectedTrackId === item.track.id;

              return (
                <li key={`${item.track.id}-${index}`}>
                  <button
                    type="button"
                    onClick={() => showSimilar(item.track.id)}
                    className={`w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-neutral-100 dark:hover:bg-neutral-900 ${
                      selected ? "bg-neutral-100 dark:bg-neutral-900" : ""
                    }`}
                  >
                    <p>
                      {item.track.name} — {artists}
                    </p>
                    {meta ? (
                      <p className="mt-0.5 text-neutral-500">{meta}</p>
                    ) : null}
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}

      {similar ? (
        <section className="mt-8">
          <h2 className="text-xl font-medium">Closest in this playlist</h2>
          <p className="mt-1 text-sm text-neutral-500">
            to {similar.track.track.name}
          </p>
          {similar.neighbors.length === 0 ? (
            <p className="mt-4 text-sm text-neutral-500">
              Need at least two tracks to compare.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {similar.neighbors.map((item, index) => {
                const artists =
                  item.track.artists.map((artist) => artist.name).join(", ") ||
                  "Unknown artist";
                const meta = [
                  `${Math.round(item.similarity * 100)}%`,
                  item.release_year,
                  item.genres.length ? item.genres.join(", ") : null,
                ]
                  .filter(Boolean)
                  .join(" · ");

                return (
                  <li key={`${item.track.id}-${index}`} className="text-sm">
                    <p>
                      {item.track.name} — {artists}
                    </p>
                    <p className="mt-0.5 text-neutral-500">{meta}</p>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      ) : null}

      {recommendations ? (
        <section className="mt-8">
          <h2 className="text-xl font-medium">New songs you might like</h2>
          <p className="mt-1 text-sm text-neutral-500">
            Not in this playlist · scored against your tracks
          </p>
          {recommendations.length === 0 ? (
            <p className="mt-4 text-sm text-neutral-500">
              No new candidates found. Try a playlist with more artists.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {recommendations.map((item, index) => {
                const artists =
                  item.track.artists.map((artist) => artist.name).join(", ") ||
                  "Unknown artist";
                const meta = [
                  `${Math.round(item.similarity * 100)}%`,
                  item.release_year,
                  item.genres.length ? item.genres.join(", ") : null,
                ]
                  .filter(Boolean)
                  .join(" · ");

                return (
                  <li key={`${item.track.id}-${index}`} className="text-sm">
                    <p>
                      {item.track.name} — {artists}
                    </p>
                    <p className="mt-0.5 text-neutral-500">{meta}</p>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      ) : null}
    </main>
  );
}
