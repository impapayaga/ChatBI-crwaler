<template>
  <v-menu :close-on-content-click="false" location="bottom" max-width="400">
    <template v-slot:activator="{ props }">
      <v-btn icon size="small" variant="text" v-bind="props" class="dataset-btn">
        <v-badge :content="datasets.length" :model-value="datasets.length > 0" color="primary" overlap>
          <v-icon>mdi-database</v-icon>
        </v-badge>
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span class="text-subtitle-1">我的数据集</span>
        <v-btn icon size="x-small" variant="text" @click="refreshDatasets" :loading="loading">
          <v-icon size="18">mdi-refresh</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-0" style="max-height: 400px; overflow-y: auto;">
        <!-- 数据集列表 -->
        <v-list v-if="datasets.length > 0" density="compact" class="dataset-list">
          <v-list-item v-for="dataset in datasets" :key="dataset.id" :title="dataset.logical_name || dataset.name"
            :subtitle="getDatasetSubtitle(dataset)" class="dataset-list-item" @click="selectDataset(dataset)">
            <template v-slot:prepend>
              <v-icon :color="getDatasetIconColor(dataset)">
                {{ getDatasetIcon(dataset) }}
              </v-icon>
            </template>

            <template v-slot:append>
              <v-menu location="start">
                <template v-slot:activator="{ props }">
                  <v-btn icon size="x-small" variant="text" v-bind="props" @click.stop>
                    <v-icon size="18">mdi-dots-vertical</v-icon>
                  </v-btn>
                </template>
                <v-list density="compact">
                  <v-list-item @click="viewDatasetDetails(dataset)">
                    <template v-slot:prepend>
                      <v-icon size="18">mdi-information</v-icon>
                    </template>
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>

                  <v-list-item @click="openPreviewDialog(dataset)">
                    <template v-slot:prepend>
                      <v-icon size="18">mdi-table-eye</v-icon>
                    </template>
                    <v-list-item-title>数据预览</v-list-item-title>
                  </v-list-item>

                  <!-- 重新解析 - 使用嵌套菜单确认 -->
                  <v-menu v-if="dataset.parse_status === 'failed'" location="start" :close-on-content-click="false">
                    <template v-slot:activator="{ props: menuProps }">
                      <v-list-item v-bind="menuProps">
                        <template v-slot:prepend>
                          <v-icon size="18" color="warning">mdi-refresh</v-icon>
                        </template>
                        <v-list-item-title class="text-warning">重新解析</v-list-item-title>
                      </v-list-item>
                    </template>
                    <v-card max-width="200">
                      <v-card-text class="text-body-2 pa-3">
                        确定要重新解析吗？
                      </v-card-text>
                      <v-card-actions class="pa-2 pt-0">
                        <v-spacer></v-spacer>
                        <v-btn size="small" variant="text" @click="() => { }">取消</v-btn>
                        <v-btn size="small" variant="text" color="warning" @click="retryParse(dataset.id)">
                          确定
                        </v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-menu>

                  <!-- 删除 - 使用嵌套菜单确认 -->
                  <v-menu location="start" :close-on-content-click="false">
                    <template v-slot:activator="{ props: menuProps }">
                      <v-list-item v-bind="menuProps">
                        <template v-slot:prepend>
                          <v-icon size="18" color="error">mdi-delete</v-icon>
                        </template>
                        <v-list-item-title class="text-error">删除</v-list-item-title>
                      </v-list-item>
                    </template>
                    <v-card max-width="200">
                      <v-card-text class="text-body-2 pa-3">
                        确定要删除吗？<br>此操作不可恢复。
                      </v-card-text>
                      <v-card-actions class="pa-2 pt-0">
                        <v-spacer></v-spacer>
                        <v-btn size="small" variant="text" @click="() => { }">取消</v-btn>
                        <v-btn size="small" variant="text" color="error" @click="deleteDataset(dataset.id)">
                          删除
                        </v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-menu>
                </v-list>
              </v-menu>
            </template>
          </v-list-item>
        </v-list>

        <!-- 空状态 -->
        <div v-else class="pa-6 text-center">
          <v-icon size="48" color="grey-lighten-1">mdi-database-off</v-icon>
          <p class="text-body-2 text-medium-emphasis mt-2">
            暂无数据集
          </p>
          <p class="text-caption text-medium-emphasis">
            上传数据文件开始分析
          </p>
        </div>
      </v-card-text>
    </v-card>
  </v-menu>

  <!-- 数据集详情对话框 -->
  <v-dialog v-model="detailsDialog" max-width="700px">
    <v-card v-if="selectedDataset">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" :color="getStatusColor(selectedDataset.parse_status)">
          {{ getStatusIcon(selectedDataset.parse_status) }}
        </v-icon>
        {{ selectedDataset.logical_name || selectedDataset.name }}
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pt-4">
        <!-- 基本信息 -->
        <div class="text-subtitle-2 mb-3 text-medium-emphasis">
          <v-icon size="18" class="mr-1">mdi-information-outline</v-icon>
          基本信息
        </div>
        <v-list density="compact" class="mb-4">
          <v-list-item>
            <template v-slot:prepend>
              <v-icon size="20">mdi-file</v-icon>
            </template>
            <v-list-item-title class="text-body-2">文件名</v-list-item-title>
            <v-list-item-subtitle class="text-body-2">{{ selectedDataset.name }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="selectedDataset.file_size">
            <template v-slot:prepend>
              <v-icon size="20">mdi-file-document-outline</v-icon>
            </template>
            <v-list-item-title class="text-body-2">文件大小</v-list-item-title>
            <v-list-item-subtitle class="text-body-2">{{ formatFileSize(selectedDataset.file_size)
              }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="selectedDataset.parse_status === 'parsed'">
            <template v-slot:prepend>
              <v-icon size="20">mdi-chart-box</v-icon>
            </template>
            <v-list-item-title class="text-body-2">数据规模</v-list-item-title>
            <v-list-item-subtitle class="text-body-2">
              {{ selectedDataset.row_count.toLocaleString() }} 行 × {{ selectedDataset.column_count }} 列
            </v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="selectedDataset.description">
            <template v-slot:prepend>
              <v-icon size="20">mdi-text</v-icon>
            </template>
            <v-list-item-title class="text-body-2">描述</v-list-item-title>
            <v-list-item-subtitle class="text-body-2">{{ selectedDataset.description }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>

        <!-- 处理流程 -->
        <div class="text-subtitle-2 mb-3 text-medium-emphasis">
          <v-icon size="18" class="mr-1">mdi-timeline-check-outline</v-icon>
          处理流程
        </div>

        <!-- 步骤指示器 -->
        <div class="mb-4">
          <v-timeline side="end" density="compact" truncate-line="both" align="start">
            <!-- 步骤1: 文件解析 -->
            <v-timeline-item :dot-color="getStepDotColor(selectedDataset.parse_status)" size="small"
              :icon="getStepIcon(selectedDataset.parse_status)">
              <template v-slot:opposite>
                <div class="text-caption text-medium-emphasis">步骤 1</div>
              </template>
              <div>
                <div class="text-body-2 font-weight-medium mb-1">文件解析</div>
                <v-chip :color="getStatusColor(selectedDataset.parse_status)" size="x-small" variant="flat">
                  {{ getStatusText(selectedDataset.parse_status) }}
                </v-chip>

                <v-progress-linear
                  v-if="selectedDataset.parse_status === 'parsing' && selectedDataset.parse_progress !== undefined"
                  :model-value="selectedDataset.parse_progress" color="primary" height="4" rounded
                  class="mt-2"></v-progress-linear>

                <div v-if="selectedDataset.parse_status === 'failed' && selectedDataset.error_message"
                  class="text-caption text-error mt-1">
                  <v-icon size="14" color="error">mdi-alert-circle</v-icon>
                  {{ selectedDataset.error_message }}
                </div>
              </div>
            </v-timeline-item>

            <!-- 步骤2: 数据分片 -->
            <v-timeline-item :dot-color="getStepDotColor(selectedDataset.chunk_status)" size="small"
              :icon="getStepIcon(selectedDataset.chunk_status)">
              <template v-slot:opposite>
                <div class="text-caption text-medium-emphasis">步骤 2</div>
              </template>
              <div>
                <div class="text-body-2 font-weight-medium mb-1">数据分片</div>
                <v-chip :color="getChunkStatusColor(selectedDataset.chunk_status)" size="x-small" variant="flat">
                  {{ getChunkStatusText(selectedDataset.chunk_status) }}
                </v-chip>

                <v-progress-linear
                  v-if="selectedDataset.chunk_status === 'chunking' && selectedDataset.chunk_progress !== undefined"
                  :model-value="selectedDataset.chunk_progress" color="primary" height="4" rounded
                  class="mt-2"></v-progress-linear>

                <div v-if="selectedDataset.chunk_status === 'failed'" class="mt-2">
                  <div v-if="selectedDataset.chunk_error" class="text-caption text-error mt-1 mb-2">
                    <v-icon size="14" color="error">mdi-alert-circle</v-icon>
                    错误: {{ selectedDataset.chunk_error }}
                  </div>
                  <v-btn size="x-small" color="warning" variant="tonal" prepend-icon="mdi-refresh"
                    @click="retryChunk(selectedDataset.id)">
                    重新分片
                  </v-btn>
                </div>

                <div v-if="selectedDataset.chunk_status === 'pending' && selectedDataset.parse_status === 'parsed'"
                  class="mt-2">
                  <div class="text-caption text-medium-emphasis mb-2">
                    数据分片尚未开始
                  </div>
                  <v-btn size="x-small" color="primary" variant="tonal" prepend-icon="mdi-play"
                    @click="retryChunk(selectedDataset.id)">
                    开始分片
                  </v-btn>
                </div>

                <div v-if="selectedDataset.chunk_status === 'completed'" class="text-caption text-success mt-1">
                  <v-icon size="14" color="success">mdi-check</v-icon>
                  分片完成
                </div>
              </div>
            </v-timeline-item>

            <!-- 步骤3: 向量化 -->
            <v-timeline-item :dot-color="getStepDotColor(selectedDataset.vectorize_status)" size="small"
              :icon="getStepIcon(selectedDataset.vectorize_status)">
              <template v-slot:opposite>
                <div class="text-caption text-medium-emphasis">步骤 3</div>
              </template>
              <div>
                <div class="text-body-2 font-weight-medium mb-1">向量化生成</div>
                <v-chip :color="getVectorizeStatusColor(selectedDataset.vectorize_status)" size="x-small"
                  variant="flat">
                  {{ getVectorizeStatusText(selectedDataset.vectorize_status) }}
                </v-chip>

                <v-progress-linear
                  v-if="selectedDataset.vectorize_status === 'vectorizing' && selectedDataset.vectorize_progress !== undefined"
                  :model-value="selectedDataset.vectorize_progress" color="secondary" height="4" rounded
                  class="mt-2"></v-progress-linear>

                <div v-if="selectedDataset.vectorize_status === 'failed'" class="mt-2">
                  <div v-if="selectedDataset.vectorize_error" class="text-caption text-error mt-1 mb-2">
                    <v-icon size="14" color="error">mdi-alert-circle</v-icon>
                    错误: {{ selectedDataset.vectorize_error }}
                  </div>
                  <div class="text-caption text-medium-emphasis mb-2">
                    注: 数据集仍可用于基本查询
                  </div>
                  <v-btn size="x-small" color="warning" variant="tonal" prepend-icon="mdi-refresh"
                    @click="retryVectorize(selectedDataset.id)">
                    重新向量化
                  </v-btn>
                </div>

                <div
                  v-if="selectedDataset.vectorize_status === 'pending' && selectedDataset.chunk_status === 'completed'"
                  class="mt-2">
                  <div class="text-caption text-medium-emphasis mb-2">
                    向量化尚未开始
                  </div>
                  <v-btn size="x-small" color="primary" variant="tonal" prepend-icon="mdi-play"
                    @click="retryVectorize(selectedDataset.id)">
                    开始向量化
                  </v-btn>
                </div>

                <div v-if="selectedDataset.vectorize_status === 'completed'" class="text-caption text-success mt-1">
                  <v-icon size="14" color="success">mdi-check</v-icon>
                  已支持智能语义检索
                </div>
              </div>
            </v-timeline-item>
          </v-timeline>
        </div>

        <!-- 时间信息 -->
        <div class="text-subtitle-2 mb-3 text-medium-emphasis">
          <v-icon size="18" class="mr-1">mdi-clock-outline</v-icon>
          时间信息
        </div>
        <v-list density="compact">
          <v-list-item>
            <template v-slot:prepend>
              <v-icon size="20">mdi-clock-plus-outline</v-icon>
            </template>
            <v-list-item-title class="text-body-2">上传时间</v-list-item-title>
            <v-list-item-subtitle class="text-body-2">{{ formatDate(selectedDataset.created_at)
              }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="selectedDataset.updated_at && selectedDataset.updated_at !== selectedDataset.created_at">
            <template v-slot:prepend>
              <v-icon size="20">mdi-clock-edit-outline</v-icon>
            </template>
            <v-list-item-title class="text-body-2">更新时间</v-list-item-title>
            <v-list-item-subtitle class="text-body-2">{{ formatDate(selectedDataset.updated_at)
              }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="detailsDialog = false">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Snackbar 提示 -->
  <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="snackbar.timeout" location="top">
    {{ snackbar.message }}
    <template v-slot:actions>
      <v-btn variant="text" @click="snackbar.show = false">
        关闭
      </v-btn>
    </template>
  </v-snackbar>

  <!-- 数据集预览对话框 -->
  <DatasetPreviewDialog
    v-model="previewDialog"
    :dataset="previewDataset"
    @use-dataset="handleUseDataset"
    @retry-processing="handleRetryProcessing"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, onUnmounted, watch, computed } from 'vue'
import axios from 'axios'
import { useDatasetStore, type Dataset } from '@/stores/dataset'
import DatasetPreviewDialog from './DatasetPreviewDialog.vue'

// 移除重复的Dataset接口定义，使用store中的类型

interface Emits {
  (e: 'selectDataset', dataset: Dataset): void
}

const emit = defineEmits<Emits>()

// 使用数据集store
const datasetStore = useDatasetStore()

// 本地状态
const detailsDialog = ref(false)
const selectedDataset = ref<Dataset | null>(null)
const previewDialog = ref(false)
const previewDataset = ref<Dataset | null>(null)

// Snackbar 状态
const snackbar = reactive({
  show: false,
  message: '',
  color: 'success',
  timeout: 3000
})

// 从store获取数据
const datasets = computed(() => datasetStore.datasets)
const loading = computed(() => datasetStore.loading)

// 定时刷新器
let refreshInterval: number | null = null

// 显示提示
const showMessage = (message: string, color: string = 'success', timeout: number = 3000) => {
  snackbar.message = message
  snackbar.color = color
  snackbar.timeout = timeout
  snackbar.show = true
}

// 获取数据集列表（使用store）
const fetchDatasets = async () => {
  try {
    await datasetStore.fetchDatasets()
  } catch (error) {
    console.error('获取数据集列表失败:', error)
  }
}

// 刷新数据集列表
const refreshDatasets = () => {
  datasetStore.refreshDatasets()
}

// 选择数据集
const selectDataset = (dataset: Dataset) => {
  if (dataset.parse_status === 'parsed') {
    emit('selectDataset', dataset)
  } else {
    showMessage('该数据集尚未解析完成，请稍后再试', 'warning')
  }
}

// 查看数据集详情
const viewDatasetDetails = (dataset: Dataset) => {
  selectedDataset.value = dataset
  detailsDialog.value = true
}

// 打开数据集预览对话框
const openPreviewDialog = (dataset: Dataset) => {
  previewDataset.value = dataset
  previewDialog.value = true
}

// 处理预览对话框中的使用数据集事件
const handleUseDataset = (dataset: Dataset) => {
  emit('selectDataset', dataset)
}

// 处理预览对话框中的重新处理事件
const handleRetryProcessing = (dataset: Dataset) => {
  if (dataset.parse_status === 'failed') {
    retryParse(dataset.id)
  }
}

// 重新解析数据集
const retryParse = async (id: string) => {
  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/dataset/${id}/retry_parse`
    )
    showMessage('已开始重新解析，请稍后刷新查看结果', 'info', 4000)
    fetchDatasets()
  } catch (error: any) {
    console.error('重新解析失败:', error)
    const errorMessage = error.response?.data?.message || '重新解析失败'
    showMessage(`重新解析失败: ${errorMessage}`, 'error', 5000)
  }
}

// 重新生成embedding
const retryEmbedding = async (id: string) => {
  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/dataset/${id}/retry_embedding`
    )
    showMessage('已开始重新生成向量索引，这可能需要几分钟...', 'info', 4000)

    // 关闭详情对话框
    detailsDialog.value = false

    // 刷新数据集列表
    setTimeout(() => {
      fetchDatasets()
    }, 1000)
  } catch (error: any) {
    console.error('重新生成embedding失败:', error)
    const errorMessage = error.response?.data?.detail || '重新生成失败'
    showMessage(`重新生成失败: ${errorMessage}`, 'error', 5000)
  }
}

// 删除数据集
const deleteDataset = async (id: string) => {
  try {
    await axios.delete(
      `${import.meta.env.VITE_API_BASE_URL}/api/dataset/${id}`
    )
    showMessage('数据集已删除', 'success')
    fetchDatasets()
  } catch (error: any) {
    console.error('删除数据集失败:', error)
    const errorMessage = error.response?.data?.message || '删除失败'
    showMessage(`删除失败: ${errorMessage}`, 'error', 5000)
  }
}

// 获取数据集图标（综合考虑parse、chunk和vectorize状态）
const getDatasetIcon = (dataset: Dataset) => {
  // 解析失败
  if (dataset.parse_status === 'failed') {
    return 'mdi-alert-circle'
  }
  // 解析中或等待
  if (dataset.parse_status === 'parsing' || dataset.parse_status === 'pending') {
    return 'mdi-loading mdi-spin'
  }
  // 解析完成，检查后续步骤
  if (dataset.parse_status === 'parsed') {
    // 检查分片状态
    if (dataset.chunk_status === 'failed') {
      return 'mdi-alert'  // 分片失败
    }
    if (dataset.chunk_status === 'chunking' || dataset.chunk_status === 'pending') {
      return 'mdi-loading mdi-spin'  // 分片中或等待
    }

    // 分片完成，检查向量化状态
    if (dataset.chunk_status === 'completed') {
      if (dataset.vectorize_status === 'failed') {
        return 'mdi-alert'  // 向量化失败
      }
      if (dataset.vectorize_status === 'vectorizing' || dataset.vectorize_status === 'pending') {
        return 'mdi-loading mdi-spin'  // 向量化中或等待
      }
      if (dataset.vectorize_status === 'completed') {
        return 'mdi-check-circle'  // 全部完成
      }
    }
  }
  return 'mdi-help-circle'
}

// 获取数据集图标颜色
const getDatasetIconColor = (dataset: Dataset) => {
  // 解析失败
  if (dataset.parse_status === 'failed') {
    return 'error'
  }
  // 解析中或等待
  if (dataset.parse_status === 'parsing' || dataset.parse_status === 'pending') {
    return 'primary'
  }
  // 解析完成，检查后续步骤
  if (dataset.parse_status === 'parsed') {
    // 检查分片状态
    if (dataset.chunk_status === 'failed') {
      return 'error'  // 分片失败，红色
    }
    if (dataset.chunk_status === 'chunking' || dataset.chunk_status === 'pending') {
      return 'primary'  // 分片中或等待，蓝色
    }

    // 分片完成，检查向量化状态
    if (dataset.chunk_status === 'completed') {
      if (dataset.vectorize_status === 'failed') {
        return 'error'  // 向量化失败，红色
      }
      if (dataset.vectorize_status === 'vectorizing' || dataset.vectorize_status === 'pending') {
        return 'primary'  // 向量化中或等待，蓝色
      }
      if (dataset.vectorize_status === 'completed') {
        return 'success'  // 全部完成，绿色
      }
    }
  }
  return 'grey'
}

// 获取状态图标（仅用于parse_status）
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'pending':
      return 'mdi-clock-outline'
    case 'parsing':
      return 'mdi-loading mdi-spin'
    case 'parsed':
      return 'mdi-check-circle'
    case 'failed':
      return 'mdi-alert-circle'
    default:
      return 'mdi-help-circle'
  }
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'pending':
      return 'grey'
    case 'parsing':
      return 'primary'
    case 'parsed':
      return 'success'
    case 'failed':
      return 'error'
    default:
      return 'grey'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'pending':
      return '等待解析'
    case 'parsing':
      return '解析中'
    case 'parsed':
      return '已完成'
    case 'failed':
      return '解析失败'
    default:
      return '未知'
  }
}

// 获取数据集副标题
const getDatasetSubtitle = (dataset: Dataset) => {
  if (dataset.parse_status === 'parsed') {
    return `${dataset.row_count} 行 × ${dataset.column_count} 列`
  }
  return getStatusText(dataset.parse_status)
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 获取步骤图标
const getStepIcon = (status?: string) => {
  switch (status) {
    case 'pending':
      return 'mdi-clock-outline'
    case 'parsing':
    case 'embedding':
      return 'mdi-loading mdi-spin'
    case 'parsed':
    case 'completed':
      return 'mdi-check'
    case 'failed':
      return 'mdi-alert'
    default:
      return 'mdi-circle-outline'
  }
}

// 获取步骤点颜色
const getStepDotColor = (status?: string) => {
  switch (status) {
    case 'pending':
      return 'grey'
    case 'parsing':
    case 'embedding':
      return 'primary'
    case 'parsed':
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    default:
      return 'grey-lighten-2'
  }
}

// 获取Chunk状态颜色
const getChunkStatusColor = (status?: string) => {
  switch (status) {
    case 'pending':
      return 'grey'
    case 'chunking':
      return 'primary'
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    default:
      return 'grey'
  }
}

// 获取Chunk状态文本
const getChunkStatusText = (status?: string) => {
  switch (status) {
    case 'pending':
      return '等待分片'
    case 'chunking':
      return '分片中'
    case 'completed':
      return '已完成'
    case 'failed':
      return '分片失败'
    default:
      return '未知'
  }
}

// 获取向量化状态颜色
const getVectorizeStatusColor = (status?: string) => {
  switch (status) {
    case 'pending':
      return 'grey'
    case 'vectorizing':
      return 'secondary'
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    default:
      return 'grey'
  }
}

// 获取向量化状态文本
const getVectorizeStatusText = (status?: string) => {
  switch (status) {
    case 'pending':
      return '等待向量化'
    case 'vectorizing':
      return '向量化中'
    case 'completed':
      return '已完成'
    case 'failed':
      return '向量化失败'
    default:
      return '未知'
  }
}

// 重新执行数据分片
const retryChunk = async (id: string) => {
  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/dataset/${id}/retry_chunk`
    )
    showMessage('已开始重新分片，这可能需要几分钟...', 'info', 4000)

    // 关闭详情对话框
    detailsDialog.value = false

    // 刷新数据集列表
    setTimeout(() => {
      fetchDatasets()
    }, 1000)
  } catch (error: any) {
    console.error('重新分片失败:', error)
    const errorMessage = error.response?.data?.detail || '重新分片失败'
    showMessage(`重新分片失败: ${errorMessage}`, 'error', 5000)
  }
}

// 重新执行向量化
const retryVectorize = async (id: string) => {
  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/dataset/${id}/retry_vectorize`
    )
    showMessage('已开始重新向量化，这可能需要几分钟...', 'info', 4000)

    // 关闭详情对话框
    detailsDialog.value = false

    // 刷新数据集列表
    setTimeout(() => {
      fetchDatasets()
    }, 1000)
  } catch (error: any) {
    console.error('重新向量化失败:', error)
    const errorMessage = error.response?.data?.detail || '重新向量化失败'
    showMessage(`重新向量化失败: ${errorMessage}`, 'error', 5000)
  }
}

// 组件挂载时获取数据集列表
onMounted(() => {
  fetchDatasets()

  // 设置定时刷新（仅在有数据处理中的数据集时）
  refreshInterval = setInterval(() => {
    const hasProcessingDatasets = datasetStore.datasets.some(dataset =>
      dataset.parse_status === 'parsing' ||
      dataset.chunk_status === 'chunking' ||
      dataset.vectorize_status === 'vectorizing' ||
      dataset.embedding_status === 'embedding'
    )

    if (hasProcessingDatasets) {
      datasetStore.refreshDatasets()
    }
  }, 10000) // 10秒刷新一次，仅在有处理中的数据集时
})

// 组件卸载时清理
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})

// 暴露刷新方法供父组件调用
defineExpose({
  refreshDatasets
})
</script>

<style scoped>
.dataset-btn {
  flex-shrink: 0;
}
</style>
