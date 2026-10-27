import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#080d19",
          900: "#111b2d",
          800: "#12121e",
          700: "#1a1a2a",
          600: "#24243a",
        },
        amber: {
          glow: "#f59e0b",
          soft: "#fbbf24",
        },
        violet: {
          glow: "#8b5cf6",
          soft: "#a78bfa",
        },
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(to right, rgba(139,92,246,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(139,92,246,0.06) 1px, transparent 1px)",
        "hero-glow":
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(245,158,11,0.18), transparent), radial-gradient(ellipse 60% 40% at 80% 20%, rgba(139,92,246,0.15), transparent)",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(245,158,11,0.15)",
        "glow-violet": "0 0 40px rgba(139,92,246,0.2)",
      },
    },
  },
  plugins: [],
};

export default config;

