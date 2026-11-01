/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0a192f',
          800: '#112240',
        },
        amber: {
          500: '#f59e0b',
        },
      },
    },
  },
  plugins: [],
}
