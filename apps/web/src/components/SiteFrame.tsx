"use client";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Header } from "./Header";
import { Footer } from "./Footer";

export function SiteFrame({ children }: { children: ReactNode }) {
  const path = usePathname();
  if (path === "/") return <>{children}</>;
  return (
    <div className="flex min-h-screen flex-col bg-hero-glow bg-ink-950">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <Header />
      <main id="main-content" tabIndex={-1} className="flex-1">
        {children}
      </main>
      <Footer />
    </div>
  );
}
