<template>
  <v-dialog 
    v-model="dialogVisible" 
    max-width="900px" 
    persistent
    scrollable
  >
    <v-card class="dataset-preview-dialog">
      <!-- 标题栏 -->
      <v-card-title class="pa-4 d-flex align-center justify-space-between">
        <div class="d-flex align-center">
          <v-icon class="mr-3" size="24">mdi-database-eye</v-icon>
          <div>
            <div class="text-h6">数据集详情</div>
            <div class="text-caption text-medium-emphasis">{{ dataset?.logical_name || dataset?.name }}</div>
          </div>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="closeDialog"
        />
      </v-card-title>

      <v-divider />

      <!-- 内容区域 -->
      <v-card-text class="pa-0" style="max-height: 70vh;">
        <v-container class="py-4">
          <!-- 基本信息卡片 -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 pa-3">
              <v-icon class="mr-2" size="20">mdi-information-outline</v-icon>
              基本信息
            </v-card-title>
            <v-card-text class="pt-0">
              <v-row>
                <v-col cols="12" md="6">
                  <div class="info-item mb-3">
                    <div class="text-caption text-medium-emphasis mb-1">
                      <v-icon size="16" class="mr-1">mdi-file</v-icon>
                      文件名
                    </div>
                    <div class="text-body-2">{{ dataset?.name || '-' }}</div>
                  </div>
                  <div class="info-item mb-3">
                    <div class="text-caption text-medium-emphasis mb-1">
                      <v-icon size="16" class="mr-1">mdi-weight</v-icon>
                      文件大小
                    </div>
                    <div class="text-body-2">{{ dataset?.file_size ? formatFileSize(dataset.file_size) : '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="text-caption text-medium-emphasis mb-1">
                      <v-icon size="16" class="mr-1">mdi-clock-outline</v-icon>
                      上传时间
                    </div>
                    <div class="text-body-2">{{ dataset?.created_at ? formatDateTime(dataset.created_at) : '-' }}</div>
                  </div>
                </v-col>

                <v-col cols="12" md="6">
                  <div class="info-item mb-3">
                    <div class="text-caption text-medium-emphasis mb-1">
                      <v-icon size="16" class="mr-1">mdi-cog</v-icon>
                      处理状态
                    </div>
                    <div class="d-flex align-center">
                      <v-chip 
                        :color="getStatusColor(dataset?.parse_status || '')" 
                        size="small" 
                        variant="flat"
                        class="mr-2"
                      >
                        <v-icon size="14" class="mr-1">{{ getStatusIcon(dataset?.parse_status || '') }}</v-icon>
                        {{ getStatusText(dataset?.parse_status || '') }}
                      </v-chip>
                    </div>
                  </div>
                  <div class="info-item mb-3">
                    <div class="text-caption text-medium-emphasis mb-1">
                      <v-icon size="16" class="mr-1">mdi-table</v-icon>
                      数据规模
                    </div>
                    <div class="text-body-2">
                      {{ dataset?.row_count || 0 }} 行 × {{ dataset?.column_count || 0 }} 列
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="text-caption text-medium-emphasis mb-1">
                      <v-icon size="16" class="mr-1">mdi-text</v-icon>
                      描述
                    </div>
                    <div class="text-body-2">{{ dataset?.description || '-' }}</div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 数据预览卡片 -->
          <v-card v-if="dataset?.parse_status === 'parsed'" variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 pa-3 d-flex align-center justify-space-between">
              <div>
                <v-icon class="mr-2" size="20">mdi-table-eye</v-icon>
                数据预览
              </div>
              <div class="d-flex gap-2">
                <v-btn 
                  size="small" 
                  variant="outlined" 
                  color="secondary"
                  @click="showOriginalFilePreview"
                >
                  <v-icon size="16" class="mr-1">mdi-file-document-outline</v-icon>
                  查看原文件
                </v-btn>
                <v-btn 
                  size="small" 
                  variant="outlined" 
                  @click="loadPreviewData"
                  :loading="previewLoading"
                >
                  <v-icon size="16" class="mr-1">mdi-refresh</v-icon>
                  刷新
                </v-btn>
              </div>
            </v-card-title>
            <v-card-text class="pt-0">
              <!-- 加载状态 -->
              <div v-if="previewLoading" class="text-center py-8">
                <v-progress-circular indeterminate color="primary" />
                <div class="text-caption text-medium-emphasis mt-2">加载数据预览...</div>
              </div>

              <!-- 预览数据表格 -->
              <div v-else-if="previewData && previewData.length > 0" class="preview-table-container">
                <v-data-table
                  :headers="previewHeaders"
                  :items="previewData"
                  :items-per-page="10"
                  density="compact"
                  class="preview-table"
                  hide-default-footer
                >
                  <template v-for="header in previewHeaders" :key="header.key" v-slot:[`item.${header.key}`]="{ value }">
                    <div class="preview-cell" :title="String(value)">
                      {{ formatPreviewValue(value) }}
                    </div>
                  </template>
                </v-data-table>
                
                <div class="text-caption text-medium-emphasis mt-2 text-center">
                  显示前 {{ Math.min(10, previewData.length) }} 行数据
                </div>
              </div>

              <!-- 无数据状态 -->
              <div v-else class="text-center py-8">
                <v-icon size="48" color="grey-lighten-1">mdi-table-off</v-icon>
                <div class="text-body-2 text-medium-emphasis mt-2">暂无预览数据</div>
                <div class="text-caption text-medium-emphasis">数据可能正在处理中</div>
              </div>
            </v-card-text>
          </v-card>

          <!-- 错误信息卡片 -->
          <v-card v-if="dataset?.parse_status === 'failed'" variant="outlined" color="error" class="mb-4">
            <v-card-title class="text-subtitle-1 pa-3">
              <v-icon class="mr-2" size="20">mdi-alert-circle</v-icon>
              处理错误
            </v-card-title>
            <v-card-text class="pt-0">
              <div class="text-body-2">{{ dataset?.error_message || '数据处理失败，请重新上传或联系管理员' }}</div>
            </v-card-text>
          </v-card>
        </v-container>
      </v-card-text>

      <!-- 操作按钮 -->
      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="text" @click="closeDialog">
          关闭
        </v-btn>
        <v-btn 
          v-if="dataset?.parse_status === 'failed'" 
          color="warning" 
          variant="outlined"
          @click="retryProcessing"
        >
          重新处理
        </v-btn>
        <v-btn 
          v-if="dataset?.parse_status === 'parsed'" 
          color="primary" 
          variant="flat"
          @click="useDataset"
        >
          使用此数据集
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 原文件预览对话框 -->
    <OriginalFilePreviewDialog
      v-model="originalFilePreviewVisible"
      :dataset="dataset"
    />
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { type Dataset } from '@/stores/dataset'
import OriginalFilePreviewDialog from './OriginalFilePreviewDialog.vue'

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
  (e: 'use-dataset', dataset: Dataset): void
  (e: 'retry-processing', dataset: Dataset): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const previewData = ref<any[]>([])
const previewHeaders = ref<any[]>([])
const previewLoading = ref(false)
const originalFilePreviewVisible = ref(false)

// 监听数据集变化，自动加载预览数据
watch(() => props.dataset, (newDataset) => {
  if (newDataset && newDataset.parse_status === 'parsed') {
    loadPreviewData()
  }
}, { immediate: true })

// 方法
const handleDialogUpdate = (value: boolean) => {
  emit('update:modelValue', value)
}

const closeDialog = () => {
  emit('update:modelValue', false)
}

const useDataset = () => {
  if (props.dataset) {
    emit('use-dataset', props.dataset)
    closeDialog()
  }
}

const retryProcessing = () => {
  if (props.dataset) {
    emit('retry-processing', props.dataset)
    closeDialog()
  }
}

// 显示原文件预览
const showOriginalFilePreview = () => {
  originalFilePreviewVisible.value = true
}

// 加载预览数据
const loadPreviewData = async () => {
  if (!props.dataset || props.dataset.parse_status !== 'parsed') return
  
  previewLoading.value = true
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/datasets/${props.dataset.id}/preview`)
    
    if (response.data && response.data.data) {
      previewData.value = response.data.data
      
      // 生成表头
      if (previewData.value.length > 0) {
        const firstRow = previewData.value[0]
        previewHeaders.value = Object.keys(firstRow).map(key => ({
          title: key,
          key: key,
          sortable: false,
          width: '150px'
        }))
      }
    }
  } catch (error) {
    console.error('加载预览数据失败:', error)
    previewData.value = []
    previewHeaders.value = []
  } finally {
    previewLoading.value = false
  }
}

// 工具函数
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatPreviewValue = (value: any): string => {
  if (value === null || value === undefined) return '-'
  const str = String(value)
  return str.length > 50 ? str.substring(0, 50) + '...' : str
}

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'parsed':
    case 'completed':
      return 'success'
    case 'processing':
    case 'pending':
      return 'warning'
    case 'failed':
    case 'error':
      return 'error'
    default:
      return 'grey'
  }
}

const getStatusIcon = (status: string): string => {
  switch (status) {
    case 'parsed':
    case 'completed':
      return 'mdi-check-circle'
    case 'processing':
    case 'pending':
      return 'mdi-clock-outline'
    case 'failed':
    case 'error':
      return 'mdi-alert-circle'
    default:
      return 'mdi-help-circle'
  }
}

const getStatusText = (status: string): string => {
  switch (status) {
    case 'parsed':
      return '已解析'
    case 'completed':
      return '已完成'
    case 'processing':
      return '处理中'
    case 'pending':
      return '等待中'
    case 'failed':
      return '失败'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
}
</script>

<style scoped>
.info-item {
  border-left: 3px solid rgba(var(--v-theme-primary), 0.2);
  padding-left: 12px;
}

.preview-table-container {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
  overflow: hidden;
}

.preview-table :deep(.v-data-table__wrapper) {
  max-height: 400px;
  overflow-y: auto;
}

.preview-cell {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-table :deep(.v-data-table-header) {
  background-color: rgba(var(--v-theme-surface-variant), 0.5);
}

.preview-table :deep(.v-data-table-header th) {
  font-weight: 600;
  font-size: 0.875rem;
}

/* 深色模式适配 */
:global(.v-theme--dark) .info-item {
  border-left-color: rgba(var(--v-theme-primary), 0.3);
}

:global(.v-theme--dark) .preview-table-container {
  border-color: rgba(var(--v-theme-on-surface), 0.2);
}
</style>