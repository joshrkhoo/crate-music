"use client";

import { useEffect, useState } from "react";

import { apiFetch, clearSessionId, loginUrl, setSessionId } from "@/lib/api";

type SpotifyUser = {
  id: string;
  display_name: string | null;
  country: string | null;
};

type MeResponse =
  | { authenticated: false }
  | (SpotifyUser & { authenticated: true });

export default function Home() {
  const [user, setUser] = useState<SpotifyUser | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" });
    clearSessionId();
    setUser(null);
  }

  return (
    <main className="mx-auto flex min-h-full w-full max-w-xl flex-1 flex-col justify-center px-6 py-16">
      <p className="text-sm tracking-wide text-neutral-500 uppercase">crate</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">
        Music discovery
      </h1>
      <p className="mt-3 text-neutral-500">
        Connect Spotify to import one of your playlists.
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

        {error ? (
          <p className="mt-4 text-sm text-red-500">
            Spotify login failed: {error}
          </p>
        ) : null}
      </div>
    </main>
  );
}
