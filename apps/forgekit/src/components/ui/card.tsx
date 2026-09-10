import { HTMLAttributes } from "react";

export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl shadow-black/20 ${className}`}
      {...props}
    />
  );
}
