/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ow: {
          bg:       "#04070F",   // fond principal noir bleuté profond
          surface:  "#0B1221",   // cartes / panels
          surface2: "#0F1A2E",   // surface secondaire
          border:   "#1B2D4F",   // bordures subtiles bleues
          accent:   "#F4922B",   // orange OW signature
          cyan:     "#00C2FF",   // bleu cyan OW
          gold:     "#FFD700",   // or
          purple:   "#9B59B6",
          orange:   "#F4922B",
          blue:     "#00C2FF",
        },
        tier: {
          S: "#FF4655",
          A: "#F4922B",
          B: "#FFD700",
          C: "#69db7c",
          D: "#74c0fc",
        },
      },
      fontFamily: {
        sans:    ["Rajdhani", "Barlow", "system-ui", "sans-serif"],
        display: ["Rajdhani", "system-ui", "sans-serif"],
        body:    ["Barlow", "Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "hex-pattern": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='49' viewBox='0 0 28 49'%3E%3Cpath d='M13.99 9.25l13 7.5v15l-13 7.5L1 31.75v-15l12.99-7.5zM3 17.9v12.7l10.99 6.34 11-6.35V17.9l-11-6.34L3 17.9zM0 15l12.98-7.5V0h-2v6.35L0 12.69v2.3zm0 18.5L12.98 41v8h-2v-6.85L0 35.81v-2.3zM15 0v7.5L27.99 15H28v-2.31h-.01L17 6.35V0h-2zm0 49v-8l12.99-7.5H28v2.3h-.01L17 42.15V49h-2z' fill='%231B2D4F' fill-opacity='0.4' fill-rule='evenodd'/%3E%3C/svg%3E\")",
      },
      boxShadow: {
        "ow-glow":       "0 0 20px rgba(244,146,43,0.25), 0 0 40px rgba(244,146,43,0.1)",
        "ow-glow-cyan":  "0 0 20px rgba(0,194,255,0.25), 0 0 40px rgba(0,194,255,0.1)",
        "ow-card":       "0 4px 24px rgba(0,0,0,0.6)",
      },
      clipPath: {
        "ow-btn": "polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%)",
      },
    },
  },
  plugins: [],
}
