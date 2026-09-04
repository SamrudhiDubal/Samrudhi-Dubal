/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef4ff',
          100: '#dbe6fe',
          500: '#3b5bfd',
          600: '#2c47e0',
          700: '#2138b3',
        },
      },
    },
  },
  plugins: [],
};
