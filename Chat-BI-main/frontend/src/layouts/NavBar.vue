<template>
  <v-app-bar app color="primary" dark>
    <!-- 左侧：导航菜单按钮 -->
    <v-menu>
      <template v-slot:activator="{ props }">
        <v-btn icon v-bind="props">
          <v-icon>mdi-menu</v-icon>
        </v-btn>
      </template>
      <v-list>
        <v-list-item
          v-for="item in navigationMenus"
          :key="item.to"
          :to="item.to"
          :disabled="item.disabled"
          link
        >
          <template v-slot:prepend>
            <v-icon>{{ item.icon }}</v-icon>
          </template>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>

    <!-- 中间：Logo和标题 -->
    <v-avatar size="32" color="white" class="mx-2">
      <v-icon color="primary" size="20">mdi-chart-bar</v-icon>
    </v-avatar>
    <v-toolbar-title class="text-h6">Chat BI</v-toolbar-title>

    <v-spacer></v-spacer>

    <!-- 右侧：用户菜单 -->
    <v-menu location="bottom end">
      <template v-slot:activator="{ props }">
        <v-btn icon v-bind="props">
          <v-avatar size="32" color="white">
            <v-icon color="primary" size="20">mdi-account</v-icon>
          </v-avatar>
        </v-btn>
      </template>
      <v-list min-width="200">
        <v-list-item disabled>
          <template v-slot:prepend>
            <v-icon>mdi-account-cog</v-icon>
          </template>
          <v-list-item-title>账户设置</v-list-item-title>
        </v-list-item>

        <v-list-item link to="/system-settings">
          <template v-slot:prepend>
            <v-icon>mdi-cog</v-icon>
          </template>
          <v-list-item-title>系统设置</v-list-item-title>
        </v-list-item>

        <v-list-item link @click="toggleTheme">
          <template v-slot:prepend>
            <v-icon>{{ themeStore.isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
          </template>
          <v-list-item-title>{{ themeStore.isDark ? '浅色模式' : '深色模式' }}</v-list-item-title>
        </v-list-item>

        <v-list-item disabled>
          <template v-slot:prepend>
            <v-icon>mdi-cash-multiple</v-icon>
          </template>
          <v-list-item-title>剩余额度</v-list-item-title>
          <template v-slot:append>
            <span class="text-caption">∞</span>
          </template>
        </v-list-item>

        <v-divider class="my-1"></v-divider>

        <v-list-item disabled>
          <template v-slot:prepend>
            <v-icon>mdi-logout</v-icon>
          </template>
          <v-list-item-title>退出登录</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-app-bar>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { navigationMenus } from '@/config/navigation'
import {
  VAppBar,
  VBtn,
  VIcon,
  VToolbarTitle,
  VAvatar,
  VSpacer,
  VMenu,
  VList,
  VListItem,
  VListItemTitle,
  VDivider,
} from 'vuetify/components'

const themeStore = useThemeStore()

// 初始化主题
onMounted(() => {
  themeStore.initTheme()
})

const toggleTheme = () => {
  themeStore.toggleTheme()
}
</script>

<style scoped>
/* 禁用状态样式 */
:deep(.v-list-item--disabled) {
  opacity: 0.4;
}
</style>