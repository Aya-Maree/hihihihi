/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fdf4ff',
          100: '#fae8ff',
          200: '#f3d0fe',
          300: '#e8abfd',
          400: '#d876fa',
          500: '#c44cf4',
          600: '#a92de0',
          700: '#8e22bc',
          800: '#751f99',
          900: '#611d7c',
        },
      },
    },
  },
  plugins: [],
}
