import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        rl: {
          page: '#F5F4F0',
          section: '#EEEDEA',
          inverse: '#111010',
          border: '#111010',
          muted: '#6B6B6B',
          amber: '#E8A020',
          'source-fl': '#00A65A',
          'source-kwork': '#EA580C',
          'source-youdo': '#2563EB',
          'source-tg': '#0088CC',
        },
      },
      fontFamily: {
        display: ['var(--font-display)', 'system-ui', 'sans-serif'],
        sans: ['var(--font-body)', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        neo: '5px 5px 0 #111010',
        'neo-hover': '8px 8px 0 #111010',
        'neo-sm': '3px 3px 0 #111010',
      },
      maxWidth: {
        container: '1120px',
        feed: '900px',
      },
    },
  },
  plugins: [],
}

export default config
