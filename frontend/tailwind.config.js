/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f7f4ee",
        ink: "#1f2933",
        accent: "#0b7285",
        accentWarm: "#d95f02",
        panel: "#fffdfa"
      },
      fontFamily: {
        sans: ["Space Grotesk", "Segoe UI", "sans-serif"],
        serif: ["Spectral", "Georgia", "serif"]
      },
      boxShadow: {
        card: "0 10px 40px -20px rgba(11, 114, 133, 0.45)"
      }
    }
  },
  plugins: []
};
