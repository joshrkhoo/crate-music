"use client";

import { useRef } from "react";
import type { ReactNode } from "react";

type HorizontalScrollProps = {
  children: ReactNode;
  className?: string;
};

export function HorizontalScroll({ children, className = "" }: HorizontalScrollProps) {
  const railRef = useRef<HTMLDivElement>(null);

  function scrollBy(delta: number) {
    railRef.current?.scrollBy({ left: delta, behavior: "smooth" });
  }

  return (
    <div className={`relative min-w-0 max-w-full overflow-hidden ${className}`}>
      <button
        type="button"
        onClick={() => scrollBy(-280)}
        aria-label="Scroll left"
        className="absolute top-1/2 -left-3 z-10 hidden size-8 -translate-y-1/2 items-center justify-center rounded-full border border-border bg-card text-muted-foreground hover:text-foreground lg:flex"
      >
        ‹
      </button>
      <div ref={railRef} className="crate-rail pb-1">
        {children}
      </div>
      <button
        type="button"
        onClick={() => scrollBy(280)}
        aria-label="Scroll right"
        className="absolute top-1/2 -right-3 z-10 hidden size-8 -translate-y-1/2 items-center justify-center rounded-full border border-border bg-card text-muted-foreground hover:text-foreground lg:flex"
      >
        ›
      </button>
    </div>
  );
}
