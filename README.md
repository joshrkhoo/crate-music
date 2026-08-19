# Crate

A music discovery web app that analyses your Spotify playlist and recommends new songs and artists based on your taste profile.

## What it does

1. Paste a Spotify playlist URL
2. The app fetches and displays your tracks
3. Songs are enriched with genre, era, and embedding data
4. A recommendation engine suggests new music based on sound similarity, genre, lyrics, and more

## Tech stack

### Frontend

- **Next.js 16** (React 19, TypeScript)
- **Tailwind CSS 4**

### Backend

- **Python** with **FastAPI**
- **sentence-transformers** for song embeddings
- **NumPy** for vector operations
- **httpx** for async HTTP (Spotify API calls)

## Prerequisites

- Node.js 20+
- Python 3.11+
- A Spotify Developer app (client ID and secret) — see [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## Getting started

### 1. Clone the repo

```bash
git clone <repo-url>
cd crate-music
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

Run the server:

```bash
uvicorn app.main:app --reload
```

The API runs on `http://localhost:8000`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs on `http://localhost:3000`.

## Project structure

```
crate-music/
├── frontend/          Next.js app
│   ├── app/           Pages and layouts
│   └── components/    UI components
├── backend/           FastAPI server
│   └── app/
│       ├── routers/   API endpoints
│       ├── recommend.py
│       ├── embed.py
│       └── enrich.py
└── PLAN.md            Project vision and roadmap
```
