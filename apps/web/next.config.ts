import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : "export",
  images: { unoptimized: true },
  // Bound static-export workers on high-core Windows hosts and CI runners.
  experimental: { cpus: 4 },
};

export default nextConfig;
