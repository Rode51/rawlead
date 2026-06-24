import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        void:    "#0e0e0e",
        surface: "#141414",
        snow:    "#e8e8e8",
        muted:   "#555555",
        edge:    "#222222",
        amber:   "#F5A623",
      },
      fontFamily: {
        display: ["var(--font-barlow-condensed)", "var(--font-oswald)", "sans-serif"],
        mono:    ["var(--font-geist-mono)", "var(--font-jetbrains-mono)", "ui-monospace", "monospace"],
      },
      keyframes: {
        letterIn: {
          "0%":   { opacity: "0", transform: "translateY(0.35em)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        ticker: {
          "0%":   { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
      animation: {
        "letter-in": "letterIn 0.65s cubic-bezier(0.22, 1, 0.36, 1) both",
        ticker:      "ticker 50s linear infinite",
      },
    },
  },
  plugins: [],
};
export default config;
