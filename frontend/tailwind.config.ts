import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: { "2xl": "1280px" },
    },
    extend: {
      colors: {
        bg: {
          DEFAULT: "#FAFBFC",
          subtle: "#F4F6F8",
          elevated: "#FFFFFF",
        },
        ink: {
          DEFAULT: "#0F172A",
          muted: "#475569",
          subtle: "#94A3B8",
          inverse: "#FFFFFF",
        },
        border: {
          DEFAULT: "#E2E8F0",
          strong: "#CBD5E1",
        },
        brand: {
          50: "#EFF8FF",
          100: "#DBEEFE",
          200: "#B6DCFD",
          300: "#82C4FB",
          400: "#48A4F6",
          500: "#1E86EE",
          600: "#0E6BD8",
          700: "#0E56B0",
          800: "#11488F",
          900: "#133E76",
        },
        success: {
          50: "#ECFDF5",
          100: "#D1FAE5",
          500: "#10B981",
          600: "#059669",
          700: "#047857",
        },
        warning: {
          50: "#FFFBEB",
          100: "#FEF3C7",
          500: "#F59E0B",
          600: "#D97706",
          700: "#B45309",
        },
        danger: {
          50: "#FEF2F2",
          100: "#FEE2E2",
          500: "#EF4444",
          600: "#DC2626",
          700: "#B91C1C",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-inter)",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
        ],
      },
      fontSize: {
        "display": ["2.25rem", { lineHeight: "2.5rem", letterSpacing: "-0.02em", fontWeight: "600" }],
        "title": ["1.5rem", { lineHeight: "2rem", letterSpacing: "-0.01em", fontWeight: "600" }],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.06)",
        elevated: "0 4px 12px rgba(15, 23, 42, 0.06), 0 2px 4px rgba(15, 23, 42, 0.04)",
        focus: "0 0 0 3px rgba(30, 134, 238, 0.18)",
      },
      borderRadius: {
        sm: "6px",
        DEFAULT: "10px",
        lg: "14px",
        xl: "18px",
        "2xl": "22px",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "0.55" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.18s ease-out",
        "pulse-soft": "pulse-soft 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
