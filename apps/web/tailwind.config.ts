import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // BetLens design system — one-accent rule
        background: "#FFFFFF",
        surface: "#F4F6F9",
        border: "#D9DEE5",
        "text-primary": "#1C2430",
        "text-secondary": "#5B6573",
        accent: {
          DEFAULT: "#0B2545",
          hover: "#13386B",
          tint: "#E8EDF4",
        },
        // Status colors — used sparingly, never for large areas
        live: "#B42318",
        positive: "#067647",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      fontSize: {
        caption: ["12px", { lineHeight: "16px" }],
        "body-sm": ["14px", { lineHeight: "20px" }],
        body: ["16px", { lineHeight: "24px" }],
        "section-title": ["20px", { lineHeight: "28px" }],
        "page-title": ["28px", { lineHeight: "36px" }],
        hero: ["40px", { lineHeight: "48px" }],
      },
      fontWeight: {
        body: "400",
        label: "500",
        heading: "600",
      },
      spacing: {
        // 8px grid
        "0.5": "4px",
        "1": "8px",
        "1.5": "12px",
        "2": "16px",
        "2.5": "20px",
        "3": "24px",
        "4": "32px",
        "5": "40px",
        "6": "48px",
        "8": "64px",
      },
      borderRadius: {
        card: "10px",
        button: "8px",
        input: "8px",
      },
      maxWidth: {
        content: "1280px",
      },
      screens: {
        xs: "360px",
        sm: "768px",
        md: "1024px",
        lg: "1280px",
      },
      boxShadow: {
        popover: "0 4px 16px rgba(0,0,0,0.12)",
      },
      animation: {
        "fade-in": "fadeIn 150ms ease-out",
        "slide-up": "slideUp 200ms ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;