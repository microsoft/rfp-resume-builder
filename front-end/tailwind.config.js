module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
    colors: {
      white:'#fff',
      green:"#7AC143",
      blue: {
        600: "#013088"
      },
      slate:"#667A85",
      gray: {
        700: "#374151",
        800: "#1f2937",
        900: "#111827"
      }
    }
  },
  plugins: [require('@tailwindcss/typography')],
}

