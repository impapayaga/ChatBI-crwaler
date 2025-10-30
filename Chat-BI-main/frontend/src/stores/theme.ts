import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useTheme } from 'vuetify'

export const useThemeStore = defineStore('theme', () => {
  const vuetifyTheme = useTheme()

  // 从 localStorage 读取保存的主题，默认为 light
  const isDark = ref<boolean>(
    localStorage.getItem('theme') === 'dark' ||
    (localStorage.getItem('theme') === null && window.matchMedia('(prefers-color-scheme: dark)').matches)
  )

  // 初始化主题
  const initTheme = () => {
    vuetifyTheme.global.name.value = isDark.value ? 'darkTheme' : 'lightTheme'
  }

  // 切换主题
  const toggleTheme = () => {
    isDark.value = !isDark.value
    vuetifyTheme.global.name.value = isDark.value ? 'darkTheme' : 'lightTheme'
  }

  // 设置主题
  const setTheme = (dark: boolean) => {
    isDark.value = dark
    vuetifyTheme.global.name.value = dark ? 'darkTheme' : 'lightTheme'
  }

  // 监听主题变化，持久化到 localStorage
  watch(isDark, (newValue) => {
    localStorage.setItem('theme', newValue ? 'dark' : 'light')
    // 更新 HTML 的 class，方便 Tailwind 的 dark: 前缀使用
    if (newValue) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, { immediate: true })

  return {
    isDark,
    initTheme,
    toggleTheme,
    setTheme
  }
})
