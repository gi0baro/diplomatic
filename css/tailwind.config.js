// Single dark theme. darkMode 'selector' with no selector ever present, so stray dark: classes are inert.
module.exports = {
  content: ['../diplomatic/templates/**/*.haml', '../diplomatic/static/js/*.js'],
  darkMode: 'selector',
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#05080c',
          900: '#0a0f15',
          800: '#0f161e',
          700: '#15202b',
          600: '#1d2b38',
          500: '#273846',
        },
        fog: {
          500: '#5f7384',
          400: '#8597a8',
          300: '#b8c7d6',
          200: '#dbe6ef',
        },
        signal: '#9fe8ff',
        ok: '#58d66d',
        warn: '#ffb347',
        alert: '#ff4d4d',
      },
      fontFamily: {
        display: ['"Barlow Condensed"', '"Arial Narrow"', 'system-ui', 'sans-serif'],
        sans: ['Barlow', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(159,232,255,.25), 0 0 18px rgba(159,232,255,.12)',
      },
    },
  },
}
