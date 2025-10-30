<template>
  <v-dialog
    v-model="dialogVisible"
    max-width="95vw"
    max-height="95vh"
    scrollable
    persistent
  >
    <v-card class="file-preview-dialog">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>{{ dialogTitle }}</span>
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="handleClose"
        />
      </v-card-title>
      
      <v-card-text class="pa-0" style="height: 80vh;">
        <!-- 使用vue-office在线文档预览组件 -->
        <VueOfficePreview
          :dataset="props.dataset"
          @rendered="handleRendered"
          @error="handleError"
          @download="handleDownload"
        />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import VueOfficePreview from './VueOfficePreview.vue'
import { type Dataset } from '@/stores/dataset'

// Props
interface Props {
  modelValue: boolean
  dataset: Dataset | null
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  dataset: null
})

// Emits
interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dialogTitle = computed(() => {
  return props.dataset?.name ? `${props.dataset.name} - 文档预览` : '文档预览'
})

const datasetId = computed(() => {
  return props.dataset?.id || ''
})

// 方法
const handleClose = () => {
  dialogVisible.value = false
}

const handleRendered = () => {
  console.log('文档渲染完成')
}

const handleError = (error: string) => {
  console.error('文档预览错误:', error)
}

const handleDownload = (datasetId: string) => {
  console.log('下载文档:', datasetId)
  // 创建下载链接
  const downloadUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/datasets/${datasetId}/download-original`
  
  // 创建临时链接并触发下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = props.dataset?.name || 'document'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.original-file-preview-dialog {
  height: 80vh;
  max-height: 800px;
}

.original-file-table :deep(.v-data-table__wrapper) {
  height: 100%;
  overflow: auto;
}

.original-file-table :deep(.v-data-table-header) {
  background-color: rgba(var(--v-theme-surface-variant), 0.8);
  position: sticky;
  top: 0;
  z-index: 1;
}

.original-file-table :deep(.v-data-table-header th) {
  font-weight: 600;
  font-size: 0.875rem;
  border-bottom: 2px solid rgba(var(--v-theme-on-surface), 0.12);
}

.table-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 4px 0;
}

.text-content {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.4;
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

/* 深色模式适配 */
:global(.v-theme--dark) .original-file-table :deep(.v-data-table-header) {
  background-color: rgba(var(--v-theme-surface-variant), 0.6);
}

:global(.v-theme--dark) .text-content {
  background-color: rgba(var(--v-theme-surface-variant), 0.2);
  border-color: rgba(var(--v-theme-on-surface), 0.2);
}
</style>