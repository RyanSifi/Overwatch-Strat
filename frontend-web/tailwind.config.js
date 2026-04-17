/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Palette OW Coach
        ow: {
          bg:       "#0f1117",   // fond principal sombre
          surface:  "#1a1d2e",   // cartes / panels
          border:   "#2d3152",   // bordures
          accent:   "#4f9cf9",   // bleu OW
          gold:     "#f5a623",   // or / S tier
          purple:   "#9b59b6",   // support
          orange:   "#e67e22",   // DPS
          blue:     "#3498db",   // tank
        },
        tier: {
          S: "#ff6b6b",
          A: "#ffa94d",
          B: "#ffd43b",
          C: "#69db7c",
          D: "#74c0fc",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}
