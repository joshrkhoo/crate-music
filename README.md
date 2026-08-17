# Music Discovery + Concert Recommendation Engine

## 1. Core idea

Build a web app where someone provides a Spotify playlist and the system analyses their music taste to recommend:

- New songs/artists they haven't discovered
- Nearby concerts from artists they already like
- Nearby concerts from artists they don't know yet but are likely to enjoy

The main differentiator from Spotify recommendations is that we control the similarity/recommendation algorithm and can incorporate additional information such as sound, lyrics, genre, era, artist origin, popularity, etc.

## 2. High-level system

```
                 Spotify Playlist
                        │
                        ▼
               ┌─────────────────┐
               │ Playlist Import │
               └────────┬────────┘
                        │
                     Track[]
                        │
                        ▼
               ┌─────────────────┐
               │ Music Analysis  │
               │    Pipeline     │
               └────────┬────────┘
                        │
                 Song embeddings
                        │
                        ▼
               ┌─────────────────┐
               │ Taste Profile   │
               │ + Clustering    │
               └────────┬────────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
      Music Discovery      Concert Discovery
              │                   │
              ▼                   ▼
        New songs           Nearby events
        New artists         Relevant artists
```

## 3. Stage 1 — Playlist ingestion

This is the first thing to build.

### Input

Ideally:

> Paste your Spotify playlist:
>
> `https://open.spotify.com/playlist/abc123`

We extract:

```
playlist ID = abc123
```

Then convert the playlist into our own structure:

```ts
type Track = {
  id: string
  name: string
  artists: Artist[]
  album: string
}

type Artist = {
  id: string
  name: string
}
```

### Result

```
Playlist
   ↓

[
  Nights — Frank Ocean
  Pink + White — Frank Ocean
  Japanese Denim — Daniel Caesar
  Dark Red — Steve Lacy
  Snooze — SZA
  ...
]
```

### Spotify complication

There are two potential approaches.

#### A. Official Spotify API

```
User → Spotify OAuth → Spotify API → JSON → Track[]
```

Very reliable and structured, but current Spotify API restrictions mean the user needs to authenticate for playlist-item access, and the playlist needs to be theirs/a collaborative playlist.

#### B. Public playlist extraction

```
Public Spotify URL
        ↓
Spotify webpage
        ↓
HTML / embedded data
        ↓
extract songs
        ↓
Track[]
```

Potentially lets us have:

> Paste playlist → instant analysis

with no login.

We haven't established yet whether Spotify's current public page exposes the entire playlist conveniently enough for this to be worthwhile.

**First engineering task:** investigate this.

If it's ugly/brittle, use OAuth.

## 4. Stage 2 — Music enrichment

Spotify only tells us basic information about the tracks.

We want to create significantly richer information.

For example:

```ts
type EnrichedTrack = {
  track: Track

  genres: string[]
  releaseYear: number

  soundEmbedding: number[]
  lyricsEmbedding: number[]

  artistOrigin?: string

  popularity?: number

  // potentially later
  tempo?: number
  energy?: number
  valence?: number
}
```

This will probably require additional music data sources, not just Spotify.

Exactly which sources/models we use is still TBD.

## 5. Stage 3 — Represent songs mathematically

Eventually every song gets represented as a vector.

Conceptually:

```
Pink + White
      ↓
┌──────────────────────┐
│ Sound                │
│ Lyrics               │
│ Genre                │
│ Era                  │
│ Artist information   │
└──────────┬───────────┘
           ↓

[0.82, 0.13, 0.74, 0.22, ...]
```

Then we can calculate:

```
similarity(song A, song B)
```

using something like cosine similarity.

This allows us to ask:

> What songs in our database are mathematically closest to this person's music?

## 6. Stage 4 — Build a taste profile

We probably shouldn't just average their entire playlist.

Imagine:

```
100-song playlist

35 songs → R&B
25 songs → indie
20 songs → house
20 songs → hip-hop
```

Averaging everything could produce a meaningless middle point.

Instead:

```
Playlist embeddings
        ↓
    Clustering
        ↓

Cluster A
R&B / soul
Frank Ocean
Daniel Caesar
SZA

Cluster B
Indie
Steve Lacy
...

Cluster C
House
...
```

Now we effectively know:

```
User's taste:

R&B       35%
Indie     25%
House     20%
Hip-hop   20%
```

Each cluster can independently generate recommendations.

## 7. Stage 5 — Music recommendations

We'll need a larger candidate music database.

For example:

```
Our DB

Song 1
Song 2
Song 3
...
Song 100,000
```

Then:

```
User taste clusters
        ↓
Vector search
        ↓
Most similar songs
        ↓
Remove songs already owned
        ↓
Ranking algorithm
        ↓
Recommendations
```

Potentially using:

```
PostgreSQL
+
pgvector
```

for vector similarity search.

## 8. Recommendation algorithm

This is something we get to design.

For example:

```
Similarity score

35% sound
30% lyrical meaning
20% genre
10% era
 5% artist origin
```

These numbers aren't decided yet.

That's part of the experimentation.

We could eventually let users change them:

```
What matters to you?

Sound        █████████░
Lyrics       ██████░░░░
Genre        ███████░░░
Era          ███░░░░░░░
Origin       ██░░░░░░░░
```

## 9. Discovery vs similarity

We don't necessarily want:

```
Frank Ocean listener
       ↓
"Have you heard of Tyler, The Creator?"
```

because that's not very useful.

We want to balance:

```
similarity
+
novelty
```

Potentially:

```
                Safe ←────────────→ Adventurous

Discovery       ███████●──────────
```

**Safe:**

- Very similar
- Fairly popular
- High confidence

**Adventurous:**

- More obscure
- Further from existing taste
- Still relevant

That ranking problem could become one of the most interesting technical parts of the project.

## 10. Stage 6 — Concert discovery

Take the user's artists + newly recommended artists and search concert/event APIs.

```
Taste profile
      │
      ├──── Existing artists
      │
      └──── Recommended artists
                    │
                    ▼
              Concert API
                    │
                    ▼
                Melbourne
                    │
           ┌────────┴─────────┐
           ▼                  ▼
    Known artist        Unknown artist
    concert             concert
```

For example:

**Daniel Caesar** — Melbourne — November 18

Already in your playlist.

But more interestingly:

**Ravyn Lenae** — Melbourne — October 7

Not currently in your playlist.

91% match with your R&B taste.

That combines both halves of the project.

## 11. Potential tech stack

I'd currently lean toward:

```
Frontend
────────
Next.js
TypeScript
React

Backend
───────
Python
FastAPI

ML / data
─────────
Python
scikit-learn
NumPy
embedding models

Database
────────
PostgreSQL
pgvector

External data
─────────────
Spotify
music metadata / lyrics / audio source TBD
concert API
```

You don't need all of this initially.

## 12. Development roadmap

I'd build it in this order:

```
PHASE 1

Spotify playlist
      ↓
Track[]
      ↓
display tracks

──────────────

PHASE 2

Track[]
   ↓
enrich songs with music data
   ↓
song vectors

──────────────

PHASE 3

Song vectors
   ↓
similarity search
   ↓
recommend 20 songs

──────────────

PHASE 4

Playlist
   ↓
cluster different tastes
   ↓
better recommendations

──────────────

PHASE 5

Recommendations
   +
User location
   ↓
Concert API
   ↓
concert recommendations

──────────────

PHASE 6

Improve ranking
novelty
discovery slider
explanations
UI polish
```

## Immediate goal

Don't touch ML yet.

The first milestone should simply be:

```
npm run dev
        ↓
localhost:3000
        ↓
Paste Spotify Playlist
        ↓
[Analyse]
        ↓
Nights — Frank Ocean
Pink + White — Frank Ocean
Japanese Denim — Daniel Caesar
...
```

Once Spotify playlist → `Track[]` works reliably, then move onto the recommendation system.

That also gives a clean starting point: **help me build Phase 1, but don't jump ahead and build the whole project.**
