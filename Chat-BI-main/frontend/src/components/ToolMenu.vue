<template>
  <div class="tool-menu-wrapper">
    <!-- 工具按钮 -->
    <v-btn
      ref="toolBtnRef"
      icon
      size="small"
      variant="plain"
      class="tool-btn"
      @click="toggleMenu">
      <v-icon>mdi-hexagon-multiple</v-icon>
    </v-btn>

    <!-- 工具菜单悬浮窗 -->
    <Transition name="menu-fade">
      <div
        v-if="showMenu"
        ref="menuRef"
        class="tool-menu-popup"
        :class="{ 'popup-top': position === 'top', 'popup-bottom': position === 'bottom' }">
        <div class="menu-item disabled">
          <v-icon class="menu-icon">mdi-image-plus</v-icon>
          <span class="menu-text">创建图片</span>
        </div>

        <div class="menu-item disabled">
          <v-icon class="menu-icon">mdi-lightbulb-on-outline</v-icon>
          <span class="menu-text">思考时间更长</span>
        </div>

        <div class="menu-item disabled">
          <v-icon class="menu-icon">mdi-telescope</v-icon>
          <span class="menu-text">深度研究</span>
        </div>

        <div class="menu-item disabled">
          <v-icon class="menu-icon">mdi-book-open-variant</v-icon>
          <span class="menu-text">研究与学习</span>
        </div>

        <div class="menu-divider"></div>

        <div class="menu-item disabled">
          <v-icon class="menu-icon">mdi-dots-horizontal</v-icon>
          <span class="menu-text">更多</span>
          <v-icon class="menu-arrow">mdi-chevron-right</v-icon>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

interface Props {
  position?: 'top' | 'bottom'
}

interface Emits {
  (e: 'select', action: string): void
}

const props = withDefaults(defineProps<Props>(), {
  position: 'bottom'
})

const emit = defineEmits<Emits>()

const showMenu = ref(false)
const toolBtnRef = ref<{ $el: HTMLElement } | HTMLElement>()
const menuRef = ref<HTMLElement>()

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const handleMenuClick = (action: string) => {
  emit('select', action)
  showMenu.value = false
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  if (showMenu.value) {
    const target = event.target as Node
    const toolBtnEl = toolBtnRef.value && '$el' in toolBtnRef.value
      ? toolBtnRef.value.$el
      : toolBtnRef.value
    const menu = menuRef.value

    if (
      toolBtnEl && !toolBtnEl.contains(target) &&
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
.tool-menu-wrapper {
  position: relative;
  display: inline-block;
}

.tool-btn {
  flex-shrink: 0;
}

.tool-menu-popup {
  position: absolute;
  left: 0;
  z-index: 1000;
  min-width: 240px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  padding: 8px;
  backdrop-filter: blur(10px);
}

.popup-bottom {
  top: calc(100% + 8px);
}

.popup-top {
  bottom: calc(100% + 8px);
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

.menu-item:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.menu-item:active {
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

.menu-arrow {
  flex-shrink: 0;
  font-size: 18px;
  opacity: 0.6;
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

.menu-fade-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.popup-top.menu-fade-enter-from {
  transform: translateY(8px);
}

.popup-top.menu-fade-leave-to {
  transform: translateY(8px);
}

/* 暗色主题适配 */
:global(.v-theme--dark) .tool-menu-popup {
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}
</style>
