export type SpotifyUser = {
  id: string;
  display_name: string | null;
  country: string | null;
};

export type PlaylistSummary = {
  id: string;
  name: string;
  track_count: number;
};

export type Artist = {
  id: string;
  name: string;
};

export type Track = {
  id: string;
  name: string;
  artists: Artist[];
  album: string;
  image_url?: string | null;
};

export type EnrichedTrack = {
  track: Track;
  release_year: number | null;
  genres: string[];
};

export type SimilarNeighbor = EnrichedTrack & { similarity: number };

export type SimilarResponse = {
  track: EnrichedTrack;
  neighbors: SimilarNeighbor[];
};

export type PlaylistImport = {
  id: string;
  name: string;
  image_url?: string | null;
  tracks: EnrichedTrack[];
  embeddings_ready?: boolean;
};

export function formatArtists(artists: Artist[]): string {
  return artists.map((artist) => artist.name).join(", ") || "Unknown artist";
}

export function spotifyTrackUrl(trackId: string): string {
  if (trackId.startsWith("lfm:")) {
    const payload = trackId.slice(4);
    const separator = payload.indexOf("|");
    if (separator >= 0) {
      const name = decodeURIComponent(payload.slice(0, separator));
      const artist = decodeURIComponent(payload.slice(separator + 1));
      return `https://open.spotify.com/search/${encodeURIComponent(`${name} ${artist}`)}`;
    }
  }
  return `https://open.spotify.com/track/${trackId}`;
}
