import { SITE } from "../../content/affiliates";

export function Credibility() {
  return (
    <section
      className="card grid gap-8 border-violet-glow/25 sm:p-8 md:grid-cols-[1.5fr_1fr]"
      aria-labelledby="builder-title"
    >
      <div>
        <p className="badge">Built by AnderZilla</p>
        <h2 id="builder-title" className="section-title mt-4">
          Engineering experience, applied.
        </h2>
        <p className="mt-4 leading-relaxed text-zinc-300">
          Senior Software Engineer and hands-on architect with 15+ years
          building production systems across mobile, web, and backend, in
          banking, industrial, and agritech environments.
        </p>
        <a
          href={SITE.social.linkedin}
          className="btn-ghost mt-4 -ml-3 text-amber-soft"
          target="_blank"
          rel="noopener noreferrer"
        >
          View professional background on LinkedIn →
        </a>
      </div>
      <div className="border-t border-ink-600 pt-6 md:border-l md:border-t-0 md:pl-8 md:pt-0">
        <h3 className="text-sm font-semibold text-white">Working stack</h3>
        <p className="mt-3 leading-relaxed text-zinc-400">
          Python · FastAPI · React · Next.js · TypeScript · React Native
        </p>
        <p className="mt-6 text-sm text-zinc-400">Curitiba, Brazil · Remote</p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-400">
          Practical tools and technical perspectives for people who build, play,
          and explore.
        </p>
      </div>
    </section>
  );
}
