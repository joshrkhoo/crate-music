# Metadata embeddings (Phase 2B)

This is how crate turns a playlist track into a vector, and why that vector is useful later.

## What the model is

We use **all-MiniLM-L6-v2**, a small sentence-transformer.

It is not a chatbot. It does not generate text, recommend songs, or listen to audio. It only does one job:

**text → a list of 384 numbers (a vector)**

Those numbers are a compressed representation of the *meaning* of the text, not of the recording.

The Hugging Face “unauthenticated requests” warning is only about downloading the model files. It is not required for embeddings to work locally.

## What we feed it

For every enriched track we build the **same** text block, in the same field order:

```
artist: Dijon
track: The Dress
album: Absolutely
year: 2021
genres: alternative r&b, indie soul
```

Missing year or genres stay as empty values. We do not switch to a different sentence shape. That keeps comparisons fair: every song is described the same way.

This text is metadata only (who, what, when, genre tags). It is **not** the sound of the song and **not** the lyrics.

## What comes out

The model returns a **384-dimensional vector**, then we **L2-normalize** it so its length is 1.

Example (shortened):

```
The Dress → [0.12, -0.04, 0.31, ..., 0.08]   (384 numbers, length = 1)
```

After Analyse, these live in backend memory. Inspect them at:

http://127.0.0.1:8000/embeddings

The frontend does not show the raw numbers. Restarting the backend clears them; Analyse again to rebuild.

## How a vector helps

Once every song is a point in the same 384-d space, **closeness ≈ similarity of metadata**.

Because the vectors are normalized, closeness is **cosine similarity**, which is just a dot product:

```
similarity(A, B) = embedding_A · embedding_B
```

- `1.0` — identical direction (very similar metadata text)
- `0.0` — unrelated
- negative — opposite direction (rare for this kind of embedding)

That lets us later ask:

- Which songs in this playlist are nearest to *The Dress*?
- Which catalog songs sit near this listener’s R&B cluster?

No if-statements like `if genre == "r&b"`. The model already folded artist, title, album, year, and genres into one comparable object.

## What it cannot do yet

Two tracks with the same artist, era, and genre tags will land close together **even if they sound different**. The model never heard the audio.

| Signal | In this vector? | When |
| --- | --- | --- |
| Artist, title, album, year, genres | Yes | 2B (now) |
| Lyrics / meaning of the words | No | 2C |
| Actual sound | No | 2D |

2B is the pipeline proof: import → enrich → one metadata vector per track. Recommendations, clustering, and pgvector come after this works.
