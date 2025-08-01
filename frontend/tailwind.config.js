/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class', // 클래스 기반 다크모드 활성화
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        secondary: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
        },
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        // 개선된 다크모드 색상
        dark: {
          bg: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          surface: '#475569',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'bounce-in': 'bounceIn 0.6s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceIn: {
          '0%': { transform: 'scale(0.3)', opacity: '0' },
          '50%': { transform: 'scale(1.05)' },
          '70%': { transform: 'scale(0.9)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    // Typography 플러그인 대신 커스텀 prose 스타일
    function({ addUtilities }) {
      const newUtilities = {
        '.prose': {
          color: '#374151',
          maxWidth: '65ch',
          '& p': {
            marginTop: '1.25em',
            marginBottom: '1.25em',
          },
          '& h1': {
            color: '#111827',
            fontWeight: '800',
            fontSize: '2.25em',
            marginTop: '0',
            marginBottom: '0.8888889em',
            lineHeight: '1.1111111',
          },
          '& h2': {
            color: '#111827',
            fontWeight: '700',
            fontSize: '1.5em',
            marginTop: '2em',
            marginBottom: '1em',
            lineHeight: '1.3333333',
          },
          '& h3': {
            color: '#111827',
            fontWeight: '600',
            fontSize: '1.25em',
            marginTop: '1.6em',
            marginBottom: '0.6em',
            lineHeight: '1.6',
          },
          '& strong': {
            color: '#111827',
            fontWeight: '600',
          },
          '& code': {
            color: '#111827',
            fontWeight: '600',
            fontSize: '0.875em',
          },
          '& ul': {
            marginTop: '1.25em',
            marginBottom: '1.25em',
            paddingLeft: '1.625em',
          },
          '& ol': {
            marginTop: '1.25em',
            marginBottom: '1.25em',
            paddingLeft: '1.625em',
          },
          '& li': {
            marginTop: '0.5em',
            marginBottom: '0.5em',
          },
        },
        '.dark .prose-invert': {
          color: '#d1d5db',
          '& p': {
            color: '#d1d5db',
          },
          '& h1': {
            color: '#f9fafb',
          },
          '& h2': {
            color: '#f9fafb',
          },
          '& h3': {
            color: '#f9fafb',
          },
          '& strong': {
            color: '#f9fafb',
          },
          '& code': {
            color: '#f9fafb',
          },
        }
      }
      addUtilities(newUtilities)
    }
  ],
}