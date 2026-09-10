import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : "export",
  images: { unoptimized: true },
};

export default nextConfig;
