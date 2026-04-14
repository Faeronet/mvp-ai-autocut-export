import { cn } from "./button";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-xl border border-border bg-white/80 p-6 shadow-sm backdrop-blur", className)}
      {...props}
    />
  );
}
