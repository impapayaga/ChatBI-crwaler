<template>
  <v-app>
    <!-- PC端：显示侧边栏 -->
    <Sidebar v-if="!isMobile" />

    <!-- 移动端：显示顶部导航栏 -->
    <Navbar v-if="isMobile" />

    <v-main class="main-content" :class="{ 'main-content--mobile': isMobile }">
      <router-view />
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { provide, computed, ref, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useSettingsStore } from '@/stores/settings'
import { useDisplay } from 'vuetify'
import Sidebar from './Sidebar.vue'
import Navbar from './NavBar.vue'

const appStore = useAppStore()
const settingsStore = useSettingsStore()
const { mobile } = useDisplay()

// 判断是否为移动端 (小于 960px)
const isMobile = computed(() => mobile.value)

// 通过 computed 提供响应式的值给子组件
provide('drawer', computed(() => appStore.drawer))
provide('miniVariant', computed(() => appStore.miniVariant))
provide('toggleDrawer', () => appStore.toggleDrawer())
provide('toggleMiniVariant', () => appStore.toggleMiniVariant())
provide('isMobile', isMobile)

// 初始化全局设置
onMounted(() => {
  settingsStore.initSettings()
})
</script>

<style>
/* 固定视口布局 */
body, html {
  overflow: hidden;
  height: 100vh;
}

#app, .v-application {
  height: 100vh;
  overflow: hidden;
}

/* v-main 使用 flex 布局填充剩余空间 */
.main-content {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* v-main__wrap 是实际的内容容器，需要滚动 */
.main-content :deep(.v-main__wrap) {
  flex: 1;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* 移动端布局 */
.main-content--mobile :deep(.v-main__wrap) {
  padding-top: 0 !important;
}
</style>
