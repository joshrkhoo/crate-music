type AlbumArtProps = {
  src?: string | null;
  alt: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
};

const sizes = {
  xs: { box: "size-10", px: 40 },
  sm: { box: "size-12", px: 48 },
  md: { box: "size-16", px: 64 },
  lg: { box: "size-40", px: 160 },
  xl: { box: "size-44", px: 176 },
} as const;

export function AlbumArt({ src, alt, size = "md", className = "" }: AlbumArtProps) {
  const { box, px } = sizes[size];

  if (!src) {
    return (
      <div
        className={`${box} shrink-0 rounded-md bg-neutral-900 ${className}`}
        aria-hidden
      >
        <div className="flex h-full items-center justify-center text-neutral-700">
          <svg viewBox="0 0 24 24" fill="currentColor" className="size-4" aria-hidden>
            <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z" />
          </svg>
        </div>
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element -- Spotify CDN serves fixed URLs; native img avoids upscaling blur from optimizer
    <img
      src={src}
      alt={alt}
      width={px}
      height={px}
      loading="lazy"
      decoding="async"
      className={`${box} shrink-0 rounded-md object-cover ${className}`}
    />
  );
}
