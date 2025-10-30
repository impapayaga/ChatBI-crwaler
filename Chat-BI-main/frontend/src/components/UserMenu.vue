<template>
  <div class="user-menu-wrapper">
    <!-- 用户头像按钮 -->
    <div
      ref="userBtnRef"
      class="user-section"
      :class="{ 'user-section--rail': isRail }"
      @click="toggleMenu">
      <v-badge
        :model-value="!settingsStore.embeddingConfigStatus.configured"
        color="error"
        dot
        overlap
        location="top end"
        offset-x="4"
        offset-y="4">
        <v-avatar color="primary" :size="isRail ? 32 : 40" class="user-avatar">
          <v-icon :size="isRail ? 20 : 24">mdi-account</v-icon>
        </v-avatar>
      </v-badge>
      <div v-if="!isRail" class="user-info">
        <div class="user-name">用户</div>
        <div class="user-email text-caption">admin@chatbi.com</div>
      </div>
    </div>

    <!-- 用户菜单悬浮窗 -->
    <Transition name="menu-fade">
      <div
        v-if="showMenu"
        ref="menuRef"
        class="user-menu-popup"
        :class="{ 'popup-rail': isRail }">
        <div class="menu-item disabled">
          <v-icon class="menu-icon">mdi-account-cog</v-icon>
          <span class="menu-text">账户设置</span>
        </div>

        <router-link to="/system-settings" class="menu-link">
          <div class="menu-item" @click="showMenu = false">
            <v-icon class="menu-icon">mdi-cog</v-icon>
            <span class="menu-text">系统设置</span>
            <v-icon
              v-if="!settingsStore.embeddingConfigStatus.configured"
              color="error"
              size="18"
              class="menu-warning">
              mdi-alert-circle
            </v-icon>
          </div>
        </router-link>

        <div class="menu-item" @click="handleThemeToggle">
          <v-icon class="menu-icon">{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
          <span class="menu-text">{{ isDark ? '浅色模式' : '深色模式' }}</span>
        </div>

        <div class="menu-item disabled">
          <v-icon class="menu-icon">mdi-cash-multiple</v-icon>
          <span class="menu-text">剩余额度</span>
          <span class="menu-badge">∞</span>
        </div>

        <div class="menu-divider"></div>

        <div class="menu-item disabled">
          <v-icon class="menu-icon">mdi-logout</v-icon>
          <span class="menu-text">退出登录</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { useSettingsStore } from '@/stores/settings'

interface Props {
  isRail?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isRail: false
})

const themeStore = useThemeStore()
const settingsStore = useSettingsStore()
const isDark = computed(() => themeStore.isDark)

const showMenu = ref(false)
const userBtnRef = ref<HTMLElement>()
const menuRef = ref<HTMLElement>()

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const handleThemeToggle = () => {
  themeStore.toggleTheme()
  // 不关闭菜单，让用户可以看到切换效果
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  if (showMenu.value) {
    const target = event.target as Node
    const userBtn = userBtnRef.value
    const menu = menuRef.value

    if (
      userBtn && !userBtn.contains(target) &&
      menu && !menu.contains(target)
    ) {
      showMenu.value = false
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.user-menu-wrapper {
  position: relative;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-radius: 8px;
}

.user-section:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.user-section--rail {
  justify-content: center;
  padding: 1rem;
}

.user-avatar {
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 0;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 500;
}

.user-email {
  opacity: 0.7;
  font-size: 0.75rem;
}

.user-menu-popup {
  position: fixed;
  bottom: 1rem;
  left: 16rem;
  z-index: 2000;
  min-width: 240px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  padding: 8px;
  backdrop-filter: blur(10px);
}

.user-menu-popup.popup-rail {
  left: 5rem;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
  user-select: none;
}

.menu-item:hover:not(.disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.menu-item:active:not(.disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.12);
}

.menu-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

.menu-icon {
  flex-shrink: 0;
  font-size: 20px;
}

.menu-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.5;
}

.menu-badge {
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 600;
  opacity: 0.8;
}

.menu-warning {
  flex-shrink: 0;
  margin-left: auto;
}

.menu-divider {
  height: 1px;
  background-color: rgba(var(--v-border-color), var(--v-border-opacity));
  margin: 8px 0;
}

/* 动画 */
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* 暗色主题适配 */
:global(.v-theme--dark) .user-menu-popup {
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

/* 菜单链接 */
.menu-link {
  text-decoration: none;
  color: inherit;
  display: block;
}
</style>
