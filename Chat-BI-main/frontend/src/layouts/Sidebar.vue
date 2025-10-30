<template>
  <v-navigation-drawer
    v-model="drawer"
    app
    :rail="miniVariant"
    :permanent="true"
    :width="256"
    class="sidebar-drawer"
  >
    <!-- Logo 区域 -->
    <div class="logo-section" :class="{ 'logo-section--rail': miniVariant }">
      <v-avatar :size="miniVariant ? 32 : 48" color="primary">
        <v-icon :size="miniVariant ? 20 : 32">mdi-chart-bar</v-icon>
      </v-avatar>
      <div v-if="!miniVariant" class="logo-text">
        <h3>Chat BI</h3>
        <p class="text-caption">Luohao Lab</p>
      </div>
    </div>

    <!-- 折叠/展开按钮 - 悬浮在侧边栏右侧边缘 -->
    <v-btn
      icon
      size="x-small"
      variant="flat"
      color="surface"
      class="toggle-btn"
      @click="toggleMiniVariant">
      <v-icon size="16">{{ miniVariant ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
    </v-btn>

    <!-- 主菜单内容 -->
    <v-list class="flex-grow-1">
      <v-tooltip
        v-for="item in navigationMenus"
        :key="item.to"
        :text="item.tooltip || item.title"
        location="end"
        :disabled="!miniVariant"
      >
        <template v-slot:activator="{ props }">
          <v-list-item
            link
            :to="item.to"
            :disabled="item.disabled"
            v-bind="props"
          >
            <template v-slot:prepend>
              <v-icon>{{ item.icon }}</v-icon>
            </template>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
          </v-list-item>
        </template>
      </v-tooltip>
    </v-list>

    <!-- 底部用户头像区域 -->
    <template v-slot:append>
      <UserMenu :is-rail="miniVariant" />
    </template>
  </v-navigation-drawer>
</template>

<script lang="ts" setup>
import { inject } from 'vue'
import {
  VNavigationDrawer,
  VList,
  VListItem,
  VListItemTitle,
  VIcon,
  VAvatar,
  VBtn,
  VTooltip,
} from 'vuetify/components'
import UserMenu from '@/components/UserMenu.vue'
import ConversationHistory from '@/components/ConversationHistory.vue'
import { navigationMenus } from '@/config/navigation'

// 指定 drawer 和 miniVariant 的类型
const drawer = inject<boolean | null | undefined>('drawer')
const miniVariant = inject<boolean>('miniVariant')
const toggleMiniVariant = inject<() => void>('toggleMiniVariant')
</script>

<style scoped>
.sidebar-drawer {
  position: relative;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem 1rem;
}

.logo-section--rail {
  justify-content: center;
  padding: 1rem;
}

.logo-text h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.2;
}

.logo-text p {
  margin: 0;
  opacity: 0.7;
}

.action-buttons-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

/* 折叠按钮 - 悬浮在侧边栏右侧边缘 */
.toggle-btn {
  position: absolute;
  top: 50%;
  right: -12px;
  transform: translateY(-50%);
  z-index: 10;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  opacity: 0.7;
  transition: opacity 0.2s ease, box-shadow 0.2s ease;
}

.toggle-btn:hover {
  opacity: 1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 暗色主题下的边框和阴影 */
:global(.v-theme--dark) .toggle-btn {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

:global(.v-theme--dark) .toggle-btn:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}
</style>
