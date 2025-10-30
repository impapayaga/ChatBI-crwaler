import { createVuetify } from 'vuetify';
import 'vuetify/styles';
import { aliases, mdi } from 'vuetify/iconsets/mdi';
import { colors } from '@/styles/colors';

// 从 localStorage 读取圆角设置
const getRoundedSize = () => {
  const saved = localStorage.getItem('roundedSize');
  return saved || 'lg';
};

const lightTheme = {
  dark: false,
  colors: {
    primary: colors.primary,
    secondary: colors.secondary,
    accent: colors.accent,
    error: colors.error,
    info: colors.info,
    success: colors.success,
    warning: colors.warning,
  },
};

const darkTheme = {
  dark: true,
  colors: {
    primary: colors.primary,
    secondary: colors.secondary,
    accent: colors.accent,
    error: colors.error,
    info: colors.info,
    success: colors.success,
    warning: colors.warning,
  },
};

export default createVuetify({
  theme: {
    defaultTheme: 'lightTheme',
    themes: {
      lightTheme,
      darkTheme,
    },
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  defaults: {
    VBtn: {
      rounded: getRoundedSize(),
    },
    VCard: {
      rounded: getRoundedSize(),
    },
    VTextField: {
      rounded: getRoundedSize(),
    },
    VTextarea: {
      rounded: getRoundedSize(),
    },
    VSheet: {
      rounded: getRoundedSize(),
    },
    VChip: {
      rounded: getRoundedSize(),
    },
    VAlert: {
      rounded: getRoundedSize(),
    },
  },
});