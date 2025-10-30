<template>
  <div class="stat-card">
    <div class="d-flex align-center">
      <div class="stat-icon" :class="color">
        <v-icon size="32" :color="color">{{ icon }}</v-icon>
      </div>
      <div class="ml-4">
        <div class="text-h5 font-weight-bold">{{ value }}</div>
        <div class="text-caption text-medium-emphasis">{{ label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { VIcon } from 'vuetify/components'

interface Props {
  icon: string
  value: string | number
  label: string
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info'
}

withDefaults(defineProps<Props>(), {
  color: 'primary'
})
</script>

<style scoped>
/* 统计卡片 - 浅色填充设计 */
.stat-card {
  padding: 20px;
  border-radius: 12px;
  background: #fafafa;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 暗色主题下的统计卡片 */
:global(.v-theme--dark) .stat-card {
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

:global(.v-theme--dark) .stat-card:hover {
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* 统计图标容器 */
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.stat-icon.primary {
  background: rgba(var(--v-theme-primary), 0.1);
}

.stat-icon.success {
  background: rgba(var(--v-theme-success), 0.1);
}

.stat-icon.info {
  background: rgba(var(--v-theme-info), 0.1);
}

.stat-icon.warning {
  background: rgba(var(--v-theme-warning), 0.1);
}

.stat-icon.error {
  background: rgba(var(--v-theme-error), 0.1);
}

.stat-card:hover .stat-icon {
  transform: scale(1.05);
}
</style>
