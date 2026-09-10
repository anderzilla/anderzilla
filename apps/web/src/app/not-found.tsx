import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-3xl px-6 py-24 text-center">
      <p className="text-sm font-semibold text-amber-400">404</p>
      <h1 className="mt-4 text-3xl font-bold">Page not found</h1>
      <p className="mt-4 text-zinc-400">
        This link may have moved. Explore AnderZilla from the homepage.
      </p>
      <Link href="/" className="mt-8 inline-block font-semibold text-amber-400 underline underline-offset-4">
        Back to AnderZilla
      </Link>
    </section>
  );
}
