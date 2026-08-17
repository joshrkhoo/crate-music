# Deploy crate: Vercel + Railway

First public deploy is a split:

- **Vercel** — Next.js frontend (`frontend/`)
- **Railway** — FastAPI + MiniLM (`backend/`)

Do not put FastAPI on Vercel. The embedding model and in-memory sessions need a long-running Python process.

Local `http://127.0.0.1` still works. Add production URLs next to the local ones; do not replace them.

## 1. Railway (API)

Create a new service from this repo with **root directory `backend`**. Railway should pick up `backend/Dockerfile`.

Healthcheck: `GET /health`

Optional: attach a volume at `/app/.cache` so `all-MiniLM-L6-v2` is not re-downloaded on every deploy. First boot still downloads the model and can take a few minutes.

Recommend can take 20–40 seconds. Do not put this backend on a 10s serverless timeout.

### Backend env vars

| Name | Production value |
| --- | --- |
| `SPOTIFY_CLIENT_ID` | same as local |
| `SPOTIFY_CLIENT_SECRET` | same as local |
| `SPOTIFY_REDIRECT_URI` | `https://<railway-host>/auth/spotify/callback` |
| `FRONTEND_URL` | `https://<vercel-host>` (no trailing slash) |
| `LASTFM_API_KEY` | same as local |
| `COOKIE_SECURE` | optional; defaults to true when `FRONTEND_URL` is `https://` |
| `PORT` | set by Railway |

`COOKIE_SECURE` and CORS both follow `FRONTEND_URL`. HTTPS frontend → secure cookies and CORS only for that origin. Local `http://127.0.0.1:3000` still allows `localhost` and `127.0.0.1`.

Sessions stay in process memory. A Railway restart logs everyone out. That is expected for v1.

## 2. Vercel (frontend)

Import the same repo. Set **root directory** to `frontend`.

### Frontend env vars

| Name | Production value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://<railway-host>` (no trailing slash) |

This is baked in at **build** time. Set the Railway URL, then deploy (or redeploy) Vercel.

There is no `/api` rewrite in this pass. The browser calls Railway directly with `Authorization: Bearer <sid>`.

## 3. Spotify Developer Dashboard

Keep the local redirect URI and add the Railway one:

- `http://127.0.0.1:8000/auth/spotify/callback`
- `https://<railway-host>/auth/spotify/callback`

Must match `SPOTIFY_REDIRECT_URI` exactly.

Spotify Dev Mode still applies: only users you add under User Management can log in. A public URL is not a public app.

## 4. Order

1. Deploy Railway and copy the public API URL.
2. Set `SPOTIFY_REDIRECT_URI` and `FRONTEND_URL` on Railway (you can use a placeholder frontend URL, then update it).
3. Add the Railway callback URI in the Spotify dashboard.
4. Deploy Vercel with `NEXT_PUBLIC_API_URL` pointing at Railway.
5. Set Railway `FRONTEND_URL` to the Vercel URL and redeploy the API if you used a placeholder.
6. Redeploy Vercel if the Railway URL changed after the first frontend build.

## 5. After deploy

Open the Vercel URL (not `localhost`). Log in, Analyse a playlist you own, then Recommend. If login loops, the Spotify redirect URI or `FRONTEND_URL` does not match.
