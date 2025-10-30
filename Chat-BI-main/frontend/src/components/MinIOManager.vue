<template>
  <div class="minio-manager-wrapper">
    <v-container fluid class="minio-manager pa-6">
      <!-- 标题行 -->
      <div class="d-flex align-center justify-space-between mb-4">
        <h2 class="text-h4 font-weight-bold">MinIO 文件管理</h2>
        <div class="d-flex gap-2">
          <v-btn
            v-if="selectedFiles.length > 0"
            color="error"
            prepend-icon="mdi-delete-sweep"
            @click="confirmBatchDelete"
            :disabled="deleting"
          >
            批量删除 ({{ selectedFiles.length }})
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-refresh"
            @click="loadFiles"
            :loading="loading"
          >
            刷新
          </v-btn>
        </div>
      </div>

      <!-- 统计卡片 -->
      <v-row v-if="stats" class="mb-4">
        <v-col cols="12" md="4">
          <StatCard
            icon="mdi-file-multiple"
            :value="stats.total_files"
            label="总文件数"
            color="primary"
          />
        </v-col>

        <v-col cols="12" md="4">
          <StatCard
            icon="mdi-database"
            :value="formatSize(stats.total_size)"
            label="总存储空间"
            color="success"
          />
        </v-col>

        <v-col cols="12" md="4">
          <StatCard
            icon="mdi-folder-multiple"
            :value="Object.keys(stats.stats_by_directory || {}).length"
            label="目录数量"
            color="info"
          />
        </v-col>
      </v-row>

      <!-- 过滤器 -->
      <v-row class="mb-4">
        <v-col cols="12" md="6">
          <v-text-field
            v-model="searchQuery"
            label="搜索文件"
            prepend-inner-icon="mdi-magnify"
            clearable
            variant="outlined"
            density="comfortable"
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="prefixFilter"
            label="路径前缀过滤"
            prepend-inner-icon="mdi-filter"
            clearable
            variant="outlined"
            density="comfortable"
            @update:model-value="loadFiles"
          />
        </v-col>
      </v-row>

      <!-- 文件列表表格 -->
      <v-card class="table-container">
        <v-data-table
          v-model="selectedFiles"
          :headers="headers"
          :items="filteredFiles"
          :loading="loading"
          item-value="name"
          show-select
          :items-per-page="20"
          class="file-table"
        >
          <!-- 文件名列 -->
          <template v-slot:item.name="{ item }">
            <div class="d-flex align-center py-2">
              <v-icon class="mr-2">{{ getFileIcon(item.name) }}</v-icon>
              <v-tooltip location="top" max-width="600">
                <template v-slot:activator="{ props }">
                  <span class="text-truncate file-name" v-bind="props">{{ item.name }}</span>
                </template>
                <span>{{ item.name }}</span>
              </v-tooltip>
              <v-btn
                icon="mdi-content-copy"
                size="x-small"
                variant="text"
                color="grey"
                class="ml-2"
                @click="copyFileName(item.name)"
                title="复制文件名"
              />
            </div>
          </template>

          <!-- 大小列 -->
          <template v-slot:item.size="{ item }">
            <v-chip size="small" variant="tonal">
              {{ formatSize(item.size) }}
            </v-chip>
          </template>

          <!-- 最后修改列 -->
          <template v-slot:item.last_modified="{ item }">
            {{ formatDate(item.last_modified) }}
          </template>

          <!-- 类型列 -->
          <template v-slot:item.content_type="{ item }">
            <v-chip size="small" color="primary" variant="outlined">
              {{ item.content_type || 'unknown' }}
            </v-chip>
          </template>

          <!-- 操作列 -->
          <template v-slot:item.actions="{ item }">
            <div class="d-flex gap-1 justify-center">
              <v-tooltip text="下载" location="top">
                <template v-slot:activator="{ props }">
                  <v-btn
                    icon="mdi-download"
                    size="small"
                    variant="text"
                    color="primary"
                    @click="downloadFile(item.name)"
                    v-bind="props"
                  />
                </template>
              </v-tooltip>
              <v-tooltip text="删除" location="top">
                <template v-slot:activator="{ props }">
                  <v-btn
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    color="error"
                    @click="confirmDelete(item)"
                    v-bind="props"
                  />
                </template>
              </v-tooltip>
            </div>
          </template>
        </v-data-table>
      </v-card>
    </v-container>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="deleteDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h5">确认删除</v-card-title>
        <v-card-text>
          确定要删除文件 <strong>{{ fileToDelete?.name }}</strong> 吗？
          <br />
          此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="grey"
            variant="text"
            @click="deleteDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            @click="deleteFile"
            :loading="deleting"
          >
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 批量删除确认对话框 -->
    <v-dialog v-model="batchDeleteDialog" max-width="600">
      <v-card>
        <v-card-title class="text-h5">确认批量删除</v-card-title>
        <v-card-text>
          <p class="mb-2">确定要删除以下 <strong>{{ selectedFiles.length }}</strong> 个文件吗？</p>
          <v-list density="compact" max-height="200" class="overflow-y-auto">
            <v-list-item
              v-for="fileName in selectedFiles"
              :key="fileName"
              :title="fileName"
              density="compact"
            >
              <template v-slot:prepend>
                <v-icon size="small">{{ getFileIcon(fileName) }}</v-icon>
              </template>
            </v-list-item>
          </v-list>
          <v-alert type="warning" variant="tonal" class="mt-3">
            此操作不可撤销！
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="grey"
            variant="text"
            @click="batchDeleteDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            @click="batchDeleteFiles"
            :loading="deleting"
          >
            确认删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar提示 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import StatCard from '@/components/StatCard.vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

interface MinIOFile {
  name: string
  size: number
  last_modified: string
  etag: string
  content_type: string
}

interface Stats {
  total_files: number
  total_size: number
  stats_by_directory: Record<string, any>
}

const loading = ref(false)
const deleting = ref(false)
const files = ref<MinIOFile[]>([])
const stats = ref<Stats | null>(null)
const searchQuery = ref('')
const prefixFilter = ref('')
const deleteDialog = ref(false)
const batchDeleteDialog = ref(false)
const fileToDelete = ref<MinIOFile | null>(null)
const selectedFiles = ref<string[]>([])

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const headers = [
  { title: '文件名', key: 'name', sortable: true },
  { title: '大小', key: 'size', sortable: true },
  { title: '最后修改', key: 'last_modified', sortable: true },
  { title: '类型', key: 'content_type', sortable: true },
  { title: '操作', key: 'actions', sortable: false, align: 'center' as const }
]

const filteredFiles = computed(() => {
  if (!searchQuery.value) return files.value

  const query = searchQuery.value.toLowerCase()
  return files.value.filter(file =>
    file.name.toLowerCase().includes(query)
  )
})

const loadFiles = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/api/minio/files`, {
      params: {
        prefix: prefixFilter.value || '',
        recursive: true
      }
    })

    files.value = response.data.files || []
    await loadStats()
  } catch (error: any) {
    showSnackbar('加载文件列表失败: ' + (error.response?.data?.detail || error.message), 'error')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/minio/stats`)
    stats.value = response.data
  } catch (error: any) {
    console.error('加载统计信息失败:', error)
  }
}

const downloadFile = async (filePath: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/minio/download/${filePath}`, {
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filePath.split('/').pop() || 'download')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

    showSnackbar('文件下载成功', 'success')
  } catch (error: any) {
    showSnackbar('下载失败: ' + (error.response?.data?.detail || error.message), 'error')
  }
}

const confirmDelete = (file: MinIOFile) => {
  fileToDelete.value = file
  deleteDialog.value = true
}

const deleteFile = async () => {
  if (!fileToDelete.value) return

  deleting.value = true
  try {
    await axios.delete(`${API_BASE_URL}/api/minio/file/${fileToDelete.value.name}`)
    showSnackbar('文件删除成功', 'success')
    deleteDialog.value = false
    fileToDelete.value = null
    await loadFiles()
  } catch (error: any) {
    showSnackbar('删除失败: ' + (error.response?.data?.detail || error.message), 'error')
  } finally {
    deleting.value = false
  }
}

const confirmBatchDelete = () => {
  if (selectedFiles.value.length === 0) {
    showSnackbar('请先选择要删除的文件', 'warning')
    return
  }
  batchDeleteDialog.value = true
}

const batchDeleteFiles = async () => {
  deleting.value = true
  let successCount = 0
  let failCount = 0

  try {
    for (const fileName of selectedFiles.value) {
      try {
        await axios.delete(`${API_BASE_URL}/api/minio/file/${fileName}`)
        successCount++
      } catch (error) {
        failCount++
        console.error(`删除文件失败: ${fileName}`, error)
      }
    }

    batchDeleteDialog.value = false
    selectedFiles.value = []

    if (failCount === 0) {
      showSnackbar(`成功删除 ${successCount} 个文件`, 'success')
    } else {
      showSnackbar(`成功删除 ${successCount} 个文件，${failCount} 个文件删除失败`, 'warning')
    }

    await loadFiles()
  } catch (error: any) {
    showSnackbar('批量删除失败: ' + (error.response?.data?.detail || error.message), 'error')
  } finally {
    deleting.value = false
  }
}

const formatSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getFileIcon = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase()

  const iconMap: Record<string, string> = {
    csv: 'mdi-file-delimited',
    xlsx: 'mdi-file-excel',
    xls: 'mdi-file-excel',
    parquet: 'mdi-database',
    json: 'mdi-code-json',
    txt: 'mdi-file-document',
    pdf: 'mdi-file-pdf-box',
    png: 'mdi-file-image',
    jpg: 'mdi-file-image',
    jpeg: 'mdi-file-image'
  }

  return iconMap[ext || ''] || 'mdi-file'
}

const showSnackbar = (text: string, color: string = 'success') => {
  snackbar.value = { show: true, text, color }
}

const copyFileName = async (fileName: string) => {
  try {
    await navigator.clipboard.writeText(fileName)
    showSnackbar('文件名已复制到剪贴板', 'success')
  } catch (error) {
    console.error('复制失败:', error)
    showSnackbar('复制失败', 'error')
  }
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
.minio-manager-wrapper {
  height: 100vh;
  width: 100%;
  overflow-y: auto;
}

.minio-manager {
  min-height: 100%;
}

.gap-2 {
  gap: 0.5rem;
}

.file-name {
  max-width: 500px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: help;
}

/* 文件名行容器 */
:deep(.v-data-table__td) .d-flex:has(.file-name) {
  position: relative;
}

/* 复制按钮默认隐藏 */
:deep(.v-data-table__td) .d-flex:has(.file-name) .v-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
}

/* 鼠标悬停时显示复制按钮 */
:deep(.v-data-table__tr:hover) .d-flex:has(.file-name) .v-btn {
  opacity: 1;
}

/* 表格容器 */
.table-container {
  height: auto;
  max-height: calc(100vh - 480px);
  min-height: 500px;
}

/* 表格样式 */
.file-table {
  height: 100%;
}

/* 表格包装器 - 允许内部滚动 */
:deep(.v-table) {
  height: 100%;
}

:deep(.v-table__wrapper) {
  max-height: calc(100vh - 520px);
  min-height: 500px;
  overflow-y: auto !important;
  overflow-x: auto !important;
}

/* 固定表头 */
:deep(.v-data-table__thead) {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 暗色主题下的表头背景 */
:global(.v-theme--dark) :deep(.v-data-table__thead) {
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 复选框列宽度 */
:deep(.v-data-table__td--select),
:deep(.v-data-table__th--select) {
  width: 64px !important;
  min-width: 64px !important;
  padding: 0 16px !important;
}

/* 复选框样式优化 */
:deep(.v-selection-control) {
  justify-content: center;
}

:deep(.v-checkbox .v-selection-control__wrapper) {
  height: 24px;
}

/* 表格行样式 */
:deep(.v-data-table__tr) {
  cursor: default;
}

:deep(.v-data-table__tr:hover) {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
}

/* 表格单元格内边距 */
:deep(.v-data-table__td) {
  padding: 12px 16px !important;
  height: auto !important;
}

:deep(.v-data-table__th) {
  padding: 12px 16px !important;
  font-weight: 600 !important;
}

/* 操作按钮间距 */
.gap-1 {
  gap: 4px;
}

/* 操作列居中对齐 */
:deep(.v-data-table__th:last-child),
:deep(.v-data-table__td:last-child) {
  text-align: center !important;
}

/* 优化复制按钮样式 */
.ml-2 {
  margin-left: 8px;
}

/* Tooltip样式优化 */
:deep(.v-overlay__content) {
  word-break: break-all;
}
</style>
