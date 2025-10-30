// Utilities
import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    drawer: true,
    miniVariant: localStorage.getItem('sidebarMini') === 'true' || localStorage.getItem('sidebarMini') === null,
  }),
  actions: {
    toggleDrawer() {
      this.drawer = !this.drawer
    },
    toggleMiniVariant() {
      this.miniVariant = !this.miniVariant
      localStorage.setItem('sidebarMini', String(this.miniVariant))
    },
  },
})
