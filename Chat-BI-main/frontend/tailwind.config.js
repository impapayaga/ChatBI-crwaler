// tailwind.config.js
const { colors } = require('./src/styles/colors');

module.exports = {
  darkMode: 'class', // 启用类模式的暗黑模式
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: colors.primary,
        secondary: colors.secondary,
        accent: colors.accent,
        error: colors.error,
        info: colors.info,
        success: colors.success,
        warning: colors.warning,
      },
    },
  },
  plugins: [],
}