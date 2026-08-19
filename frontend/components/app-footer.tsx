export function AppFooter() {
  return (
    <footer className="mt-auto hidden border-t border-border sm:block">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-muted-foreground sm:flex-row">
        <span className="text-xs font-bold tracking-[0.2em] text-foreground">CRATE</span>
        <nav className="flex flex-wrap justify-center gap-x-5 gap-y-2">
          {["About", "Blog", "Careers", "Privacy", "Terms"].map((item) => (
            <span key={item} className="cursor-default hover:text-foreground">
              {item}
            </span>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          {["Instagram", "Twitter", "Discord"].map((network) => (
            <span
              key={network}
              className="size-8 cursor-default rounded-full border border-border"
              title={network}
              aria-label={network}
            />
          ))}
        </div>
      </div>
    </footer>
  );
}
