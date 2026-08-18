import type { ReactNode } from "react";

type SectionProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
};

export function Section({ title, subtitle, children, className = "" }: SectionProps) {
  return (
    <section className={className}>
      <h3 className="text-lg font-medium">{title}</h3>
      {subtitle ? <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p> : null}
      <div className="mt-4">{children}</div>
    </section>
  );
}
