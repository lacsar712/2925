/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e8eaf6',
          100: '#c5cae9',
          200: '#9fa8da',
          300: '#7986cb',
          400: '#5c6bc0',
          500: '#1a1a2e',
          600: '#16213e',
          700: '#0f3460',
          800: '#0a2647',
          900: '#061223',
        },
        profit: '#52c41a',
        loss: '#ff4d4f',
        bond: {
          buy: '#52c41a',
          sell: '#ff4d4f',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'monospace'],
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: false,
  },
}
