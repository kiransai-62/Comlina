/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './features/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          950: '#021A0E',
          900: '#032615',
          800: '#064125', // Exact Comlina brand font color
          700: '#0A5A34',
          600: '#15803D',
          500: '#22C55E',
          100: '#EAF6EE',
          50: '#F4FBF6'
        },
        brand: {
          green: '#064125',
          purple: '#762BC6',
          violet: '#8B3EE2',
          magenta: '#C13399',
          pink: '#EF439F',
          coral: '#F64D6E',
          orange: '#FE8450',
          sparkle: '#F96A64',
          tagline: '#5D6068'
        },
        bg: {
          app: 'var(--bg-app, #FBFBFA)',
          card: 'var(--bg-card, #FFFFFF)',
          subtle: 'var(--bg-subtle, #F7F7F5)'
        }
      },
      borderRadius: {
        lg: "var(--radius, 12px)",
        md: "calc(var(--radius, 12px) - 2px)",
        sm: "calc(var(--radius, 12px) - 4px)",
      }
    },
  },
  plugins: [],
}
