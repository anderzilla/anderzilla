"use client";

import { useState, FormEvent } from "react";

/** UI-only email capture stub — no backend yet. */
export function NewsletterCapture({ className = "" }: { className?: string }) {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setDone(true);
  }

  return (
    <div className={`card border-violet-glow/20 ${className}`}>
      <p className="badge">Newsletter stub</p>
      <h2 className="section-title mt-3">Anderzilla Weekly</h2>
      <p className="mt-2 max-w-xl text-sm text-zinc-400">
        Ship notes, StackPick drops, and geek culture — no fluff. Capture-only UI for now;
        provider wiring comes later.
      </p>
      {done ? (
        <p className="mt-6 text-sm text-amber-soft">
          Thanks — you&apos;re on the stub list. Real delivery lands when Beehiiv/Buttondown
          is wired.
        </p>
      ) : (
        <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-3 sm:flex-row">
          <label className="sr-only" htmlFor="newsletter-email">
            Email
          </label>
          <input
            id="newsletter-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@domain.com"
            className="w-full flex-1 rounded-xl border border-ink-600 bg-ink-800/80 px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-violet-soft/60 focus:outline-none focus:ring-1 focus:ring-violet-glow"
          />
          <button type="submit" className="btn-primary shrink-0">
            Join waitlist
          </button>
        </form>
      )}
    </div>
  );
}
